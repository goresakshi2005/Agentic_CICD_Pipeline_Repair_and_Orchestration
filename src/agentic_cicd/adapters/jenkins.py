class JenkinsAdapter:
    def __init__(self, url: str = None):
        self.url = url

    def job_info(self, name: str):
        return {"job": name}
