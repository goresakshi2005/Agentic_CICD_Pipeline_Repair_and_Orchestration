from langgraph.graph import StateGraph, END
from .core.models import WorkflowState
from .agents import monitor, diagnose, security, governance, repair, release
from .adapters import get_vcs_adapter, get_ci_adapter
from .adapters.llm import get_llm_provider
from .notifications import get_notification_provider
import logging

logger = logging.getLogger(__name__)

# Build graph
workflow = StateGraph(WorkflowState)

# Add nodes (each agent's process function)
workflow.add_node("monitor", monitor.MonitorAgent.process)
workflow.add_node("diagnose", diagnose.DiagnoseAgent.process)
workflow.add_node("security_scan", security.SecurityAgent.process)
workflow.add_node("governance", governance.GovernanceAgent.process)
workflow.add_node("repair", repair.RepairAgent.process)
workflow.add_node("release", release.ReleaseAgent.process)

workflow.set_entry_point("monitor")

workflow.add_edge("monitor", "diagnose")
workflow.add_edge("diagnose", "security_scan")
workflow.add_edge("security_scan", "governance")

def after_governance(state: WorkflowState):
    """If approval is required, stop and wait for external approval via /approve.
    Otherwise, proceed to repair."""
    if state.requires_approval:
        return END
    else:
        return "repair"

workflow.add_conditional_edges(
    "governance",
    after_governance,
    {
        "repair": "repair",
        END: END
    }
)

def after_repair(state: WorkflowState):
    if state.fix_plan and state.fix_plan.get("strategy") == "deploy":
        return "release"
    return END

workflow.add_conditional_edges(
    "repair",
    after_repair,
    {
        "release": "release",
        END: END
    }
)

workflow.add_edge("release", END)

agent_graph = workflow.compile()

async def run_workflow(run_id: int):
    """Convenience function to start a workflow with given run_id."""
    from .config import settings
    vcs = get_vcs_adapter()
    ci = get_ci_adapter()
    llm = get_llm_provider()
    notifier = get_notification_provider()

    # Initialize agents with dependencies
    monitor_agent = monitor.MonitorAgent(llm, vcs, ci, notifier)
    diagnose_agent = diagnose.DiagnoseAgent(llm, vcs, ci, notifier)
    security_agent = security.SecurityAgent(llm, vcs, ci, notifier)
    governance_agent = governance.GovernanceAgent(llm, vcs, ci, notifier)
    repair_agent = repair.RepairAgent(llm, vcs, ci, notifier)
    release_agent = release.ReleaseAgent(llm, vcs, ci, notifier)

    # Override node functions with bound methods
    workflow.nodes["monitor"].fn = monitor_agent.process
    workflow.nodes["diagnose"].fn = diagnose_agent.process
    workflow.nodes["security_scan"].fn = security_agent.process
    workflow.nodes["governance"].fn = governance_agent.process
    workflow.nodes["repair"].fn = repair_agent.process
    workflow.nodes["release"].fn = release_agent.process

    initial_state = WorkflowState(run_id=run_id)
    final_state = await agent_graph.ainvoke(initial_state)
    return final_state