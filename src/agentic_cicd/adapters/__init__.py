from .github import GitHubAdapter
from ..config import settings

def get_vcs_adapter():
    if settings.vcs_provider == "github":
        return GitHubAdapter(settings.vcs_token, settings.vcs_repo)
    # elif ... add others
    else:
        raise ValueError(f"Unsupported VCS provider: {settings.vcs_provider}")

def get_ci_adapter():
    # If ci_provider is set, use that; otherwise fallback to vcs
    provider = settings.ci_provider or settings.vcs_provider
    if provider == "github":
        token = settings.ci_token or settings.vcs_token
        repo = settings.vcs_repo  # assumes same repo
        return GitHubAdapter(token, repo)
    # ... other adapters
    else:
        raise ValueError(f"Unsupported CI provider: {provider}")