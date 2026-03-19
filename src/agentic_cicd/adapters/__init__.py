from .github import GitHubAdapter
from ..config import settings

def get_vcs_adapter():
    if settings.vcs_provider == "github":
        return GitHubAdapter(settings.vcs_token, settings.vcs_repo)
    elif settings.vcs_provider == "gitlab":
        # Placeholder – implement GitLabAdapter similarly
        raise NotImplementedError("GitLab adapter not yet implemented")
    else:
        raise ValueError(f"Unsupported VCS provider: {settings.vcs_provider}")

def get_ci_adapter():
    provider = settings.ci_provider or settings.vcs_provider
    if provider == "github":
        token = settings.ci_token or settings.vcs_token
        return GitHubAdapter(token, settings.vcs_repo)
    elif provider == "gitlab":
        raise NotImplementedError("GitLab CI adapter not yet implemented")
    elif provider == "jenkins":
        raise NotImplementedError("Jenkins adapter not yet implemented")
    else:
        raise ValueError(f"Unsupported CI provider: {provider}")