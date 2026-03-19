from .monitor import MonitorAgent
from .diagnose import DiagnoseAgent
from .security import SecurityAgent
from .governance import GovernanceAgent
from .repair import RepairAgent
from .release import ReleaseAgent

_agent_classes = {
    "monitor": MonitorAgent,
    "diagnose": DiagnoseAgent,
    "security": SecurityAgent,
    "governance": GovernanceAgent,
    "repair": RepairAgent,
    "release": ReleaseAgent,
}

def get_agent(name: str, llm, vcs, ci, notifier):
    cls = _agent_classes.get(name)
    if not cls:
        raise ValueError(f"Unknown agent: {name}")
    return cls(llm, vcs, ci, notifier)