from abc import ABC, abstractmethod
from typing import Dict, Any
from ..core.interfaces import LLMProvider, VCSProvider, CIProvider, NotificationProvider

class Agent(ABC):
    def __init__(self, llm: LLMProvider, vcs: VCSProvider, ci: CIProvider, notifier: NotificationProvider):
        self.llm = llm
        self.vcs = vcs
        self.ci = ci
        self.notifier = notifier

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass