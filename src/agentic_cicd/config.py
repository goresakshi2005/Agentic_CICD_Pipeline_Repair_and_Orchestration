from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List, Dict, Any
import yaml
import os

class Settings(BaseSettings):
    # Core
    debug: bool = False

    # VCS
    vcs_provider: str = "github"
    vcs_token: str = Field(..., env="VCS_TOKEN")
    vcs_repo: str = Field(..., env="VCS_REPO")

    # CI (if different from VCS)
    ci_provider: Optional[str] = None
    ci_token: Optional[str] = None
    ci_url: Optional[str] = None

    # LLM
    llm_provider: str = "gemini"
    llm_api_key: str = Field(..., env="LLM_API_KEY")
    llm_model: str = "gemini-2.5-flash"

    # Notifications
    slack_token: Optional[str] = Field(None, env="SLACK_TOKEN")
    slack_channel: Optional[str] = "#deploy-approvals"

    # Database
    database_url: str = "sqlite:///./app.db"

    # Security scanners (list of commands)
    security_scanners: List[Dict[str, Any]] = []

    # Agents to run (order matters)
    agents: List[str] = ["monitor", "diagnose", "security", "governance", "repair", "release"]

    # Governance rules
    governance: Dict[str, Any] = {
        "critical_files": ["requirements.txt", "Dockerfile", ".github/workflows/"],
        "confidence_threshold": 0.7,
    }

    # Polling interval (seconds)
    poll_interval: int = 60

    class Config:
        env_file = ".env"

    @classmethod
    def from_yaml(cls, path: str):
        with open(path) as f:
            yaml_config = yaml.safe_load(f)
        # Merge with environment (env overrides)
        return cls(**yaml_config)

settings = Settings()  # will load from .env first