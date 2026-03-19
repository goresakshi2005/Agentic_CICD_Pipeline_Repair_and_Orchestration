from .base import Agent
import logging

logger = logging.getLogger(__name__)

class MonitorAgent(Agent):
    async def process(self, state: dict) -> dict:
        run_id = state["run_id"]
        logger.info(f"Monitor agent processing run {run_id}")
        run_data = await self.ci.get_run(str(run_id))
        if not run_data:
            state["error"] = f"Run {run_id} not found"
            return state

        logs = await self.ci.get_logs(str(run_id))
        test_output = await self.ci.get_test_results(str(run_id))

        state.update({
            "run_data": run_data,
            "logs": logs,
            "test_output": test_output,
            "branch": run_data.get("head_branch"),
            "commit_sha": run_data.get("head_sha"),
        })
        return state