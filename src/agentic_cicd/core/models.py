from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class WorkflowState(BaseModel):
    run_id: int
    run_data: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    test_output: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    diagnosis: Optional[Dict[str, Any]] = None
    security_issues: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    fix_plan: Optional[Dict[str, Any]] = None
    pr_url: Optional[str] = None
    deployment_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ApprovalRequest(BaseModel):
    run_id: int
    approved: bool
    user: str