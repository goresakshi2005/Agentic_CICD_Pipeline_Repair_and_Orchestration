class GitLabAdapter:
    def __init__(self, token: str = None):
        self.token = token

    def project_info(self, project_id: str):
        return {"project_id": project_id}
