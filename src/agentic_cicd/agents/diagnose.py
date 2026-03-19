import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from .base import Agent
from ..knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

diagnose_prompt = ChatPromptTemplate.from_messages([("human", """
Analyze this CI/CD failure.

Commit Message: {commit_message}
Changed files: {diff}
Logs (last 2000 chars): {logs}
Test output: {test_output}
Similar past issues: {similar_issues}

Output JSON:
{{
  "root_cause": "...",
  "confidence": 0.0-1.0,
  "suggested_fix_type": "dependency|test_failure|syntax_error|config_error|flaky_test|deploy_failure|other",
  "details": "...",
  "requires_approval": true/false
}}
""")])

class DiagnoseAgent(Agent):
    async def process(self, state: dict) -> dict:
        commit_sha = state["commit_sha"]
        commit = await self.vcs.get_commit(commit_sha)
        if not commit:
            state["diagnosis"] = {"root_cause": "Could not fetch commit details", "confidence": 0.0}
            return state

        diff = "\n".join([f"{f['filename']}: {f['status']}" for f in commit.get("files", [])])
        kb = KnowledgeBase()
        similar_docs = kb.search(state["logs"][:500] if state["logs"] else "")
        similar_text = "\n".join([doc.page_content for doc in similar_docs]) if similar_docs else "None"

        prompt = diagnose_prompt.format(
            commit_message=commit["commit"]["message"],
            diff=diff,
            logs=state["logs"][-2000:] if state["logs"] else "",
            test_output=state.get("test_output", ""),
            similar_issues=similar_text
        )
        response = await self.llm.generate(prompt)
        try:
            diagnosis = json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse diagnosis JSON: {e}")
            diagnosis = {
                "root_cause": "Unknown",
                "confidence": 0.0,
                "suggested_fix_type": "other",
                "details": "",
                "requires_approval": True
            }
        state["diagnosis"] = diagnosis
        return state