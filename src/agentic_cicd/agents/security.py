import asyncio
import json
import subprocess
import logging
from .base import Agent

logger = logging.getLogger(__name__)

class SecurityAgent(Agent):
    async def process(self, state: dict) -> dict:
        logger.info("Running security scan")
        # Example: run safety check
        loop = asyncio.get_event_loop()

        def run_safety():
            result = subprocess.run(["safety", "check", "--json"], capture_output=True, text=True)
            return result.stdout

        try:
            output = await loop.run_in_executor(None, run_safety)
            issues = json.loads(output) if output else {}
        except Exception as e:
            logger.error(f"Safety scan failed: {e}")
            issues = {"error": str(e)}

        state["security_issues"] = issues
        if issues.get("vulnerabilities"):
            state["requires_approval"] = True
        return state