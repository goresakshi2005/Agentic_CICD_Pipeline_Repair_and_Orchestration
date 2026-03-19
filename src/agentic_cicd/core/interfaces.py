from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class VCSProvider(ABC):
    """Version Control System provider (GitHub, GitLab, etc.)"""

    @abstractmethod
    async def get_commit(self, sha: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def create_branch(self, branch_name: str, base_branch: str) -> bool:
        pass

    @abstractmethod
    async def create_pr(self, title: str, body: str, head: str, base: str) -> Optional[str]:
        """Return PR URL if created."""
        pass

    @abstractmethod
    async def get_file_content(self, path: str, ref: str) -> Optional[str]:
        pass

    @abstractmethod
    async def update_file(self, path: str, content: str, message: str, branch: str) -> bool:
        pass


class CIProvider(ABC):
    """CI platform provider (GitHub Actions, GitLab CI, Jenkins)"""

    @abstractmethod
    async def get_run(self, run_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_logs(self, run_id: str) -> Optional[str]:
        pass

    @abstractmethod
    async def get_test_results(self, run_id: str) -> str:
        pass

    @abstractmethod
    async def list_runs(self, status: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def trigger_workflow(self, workflow_id: str, ref: str, inputs: Dict) -> bool:
        pass


class LLMProvider(ABC):
    """Large Language Model provider"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass


class NotificationProvider(ABC):
    """Notification service (Slack, Teams, email)"""

    @abstractmethod
    async def send_approval_request(self, run_id: str, diagnosis: dict, fix_plan: dict = None):
        pass