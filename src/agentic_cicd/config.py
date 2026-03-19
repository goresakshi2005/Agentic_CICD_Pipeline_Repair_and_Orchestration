from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List, Dict, Any

class Settings(BaseSettings):
    # Core
    debug: bool = False

    # VCS
    vcs_provider: str = "github"
    vcs_token: str = Field(..., env=["VCS_TOKEN", "GITHUB_TOKEN"])
    vcs_repo: str = Field(..., env=["VCS_REPO", "GITHUB_REPO"])

    # CI (if different from VCS)
    ci_provider: Optional[str] = None
    ci_token: Optional[str] = Field(None, env=["CI_TOKEN", "GITHUB_TOKEN"])
    ci_url: Optional[str] = Field(None, env="CI_URL")

    # LLM
    llm_provider: str = Field("gemini", env=["LLM_PROVIDER", "GEMINI_API_KEY"])
    llm_api_key: str = Field(..., env=["LLM_API_KEY", "GEMINI_API_KEY"])
    llm_model: str = Field("gemini-2.5-flash", env="LLM_MODEL")

    # Notifications
    slack_token: Optional[str] = Field(None, env="SLACK_TOKEN")
    slack_channel: Optional[str] = Field("#deploy-approvals", env="SLACK_CHANNEL")

    # Database
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")

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

    # Webhook secret (optional)
    webhook_secret: Optional[str] = Field(None, env="WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()