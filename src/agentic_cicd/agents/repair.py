import json
import time
import logging
from langchain_core.prompts import ChatPromptTemplate
from .base import Agent
from ..knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

repair_prompt = ChatPromptTemplate.from_messages([("human", """
Based on the diagnosis, propose a fix.

Root cause: {root_cause}
Fix type: {fix_type}
Details: {details}
Security issues: {security}
Current relevant files: {repo_files}
Past fixes: {past_fixes}

Output JSON:
{{
  "strategy": "file_update|retry|rollback|deploy",
  "files_to_change": [{{"path": "...", "new_content": "..."}}],
  "commit_message": "...",
  "pr_title": "...",
  "pr_body": "...",
  "retry": false
}}
""")])

class RepairAgent(Agent):
    async def process(self, state: dict) -> dict:
        diag = state["diagnosis"]
        sec = state.get("security_issues", {})

        # Fetch common files from repo
        repo_files = {}
        for f in ["requirements.txt", "setup.py", "Dockerfile", ".github/workflows/ci.yml"]:
            content = await self.vcs.get_file_content(f, state.get("branch", "main"))
            if content:
                repo_files[f] = content

        kb = KnowledgeBase()
        past_docs = kb.search(diag["root_cause"])
        past_fixes = "\n".join([doc.page_content for doc in past_docs]) if past_docs else "None"

        prompt = repair_prompt.format(
            root_cause=diag["root_cause"],
            fix_type=diag["suggested_fix_type"],
            details=diag.get("details", ""),
            security=json.dumps(sec),
            repo_files=json.dumps(repo_files),
            past_fixes=past_fixes
        )
        response = await self.llm.generate(prompt)
        try:
            fix_plan = json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse fix plan JSON: {e}")
            fix_plan = {
                "strategy": "other",
                "files_to_change": [],
                "commit_message": "Auto-fix",
                "pr_title": "Auto-fix pipeline failure",
                "pr_body": response,
                "retry": False
            }
        state["fix_plan"] = fix_plan

        # If no approval required, apply immediately
        if not state.get("requires_approval"):
            pr_url = await self._apply_fix(fix_plan, state.get("branch", "main"))
            state["pr_url"] = pr_url
            kb.add_fix(
                problem=diag["root_cause"],
                solution=fix_plan.get("pr_body", ""),
                fix_type=diag["suggested_fix_type"],
                success=pr_url is not None,
                pr_url=pr_url
            )
        return state

    async def _apply_fix(self, fix_plan: dict, base_branch: str) -> str | None:
        if fix_plan.get("retry"):
            success = await self.ci.trigger_workflow("ci.yml", ref=base_branch, inputs={})
            return "retry_triggered" if success else None

        if not fix_plan.get("files_to_change"):
            return None

        branch_name = f"auto-fix-{int(time.time())}"
        if not await self.vcs.create_branch(branch_name, base_branch):
            return None

        for fc in fix_plan["files_to_change"]:
            await self.vcs.update_file(fc["path"], fc["new_content"], fix_plan["commit_message"], branch_name)

        pr_url = await self.vcs.create_pr(
            title=fix_plan["pr_title"],
            body=fix_plan["pr_body"],
            head=branch_name,
            base=base_branch
        )
        return pr_url