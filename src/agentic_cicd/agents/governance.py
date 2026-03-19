import logging
from .base import Agent
from ..utils import is_critical_file
from ..config import settings

logger = logging.getLogger(__name__)

class GovernanceAgent(Agent):
    async def process(self, state: dict) -> dict:
        diag = state.get("diagnosis", {})
        sec = state.get("security_issues", {})
        run_data = state.get("run_data", {})

        state["requires_approval"] = False

        # Security vulnerabilities
        if sec.get("vulnerabilities"):
            state["requires_approval"] = True
            logger.info("Approval required due to security vulnerabilities")

        # Low confidence diagnosis
        threshold = settings.governance.get("confidence_threshold", 0.7)
        if diag.get("confidence", 1.0) < threshold:
            state["requires_approval"] = True
            logger.info("Approval required due to low confidence diagnosis")

        # Critical files changed
        head_commit = run_data.get("head_commit", {})
        modified_files = head_commit.get("modified", [])
        critical = settings.governance.get("critical_files", [])
        if any(is_critical_file(f, critical) for f in modified_files):
            state["requires_approval"] = True
            logger.info("Approval required due to changes in critical files")

        # If approval needed, send notification and update DB
        if state["requires_approval"] and self.notifier:
            await self.notifier.send_approval_request(
                str(state["run_id"]),
                diag,
                state.get("fix_plan")
            )
            # Update database status to pending (handled in graph)
        return state