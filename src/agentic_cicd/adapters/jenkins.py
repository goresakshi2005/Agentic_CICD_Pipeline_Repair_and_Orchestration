from ..core.interfaces import CIProvider
from typing import Dict, Any, Optional, List

class JenkinsAdapter(CIProvider):
    def __init__(self, url: str, token: str):
        raise NotImplementedError("Jenkins adapter is not yet implemented")