from ..core.interfaces import VCSProvider, CIProvider
import httpx
import base64
import io
import zipfile
from junitparser import JUnitXml
from typing import Optional, Dict, Any, List

class GitHubAdapter(VCSProvider, CIProvider):
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def _get(self, url: str) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
        return None

    async def _post(self, url: str, data: dict) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=self.headers)
            return resp.status_code in (200, 201)

    async def _put(self, url: str, data: dict) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, json=data, headers=self.headers)
            return resp.status_code in (200, 201)

    # VCS methods
    async def get_commit(self, sha: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{self.repo}/commits/{sha}"
        return await self._get(url) or {}

    async def create_branch(self, branch_name: str, base_branch: str) -> bool:
        # Get base branch SHA
        base_url = f"{self.base_url}/repos/{self.repo}/git/ref/heads/{base_branch}"
        base_data = await self._get(base_url)
        if not base_data:
            return False
        sha = base_data["object"]["sha"]
        # Create new branch
        url = f"{self.base_url}/repos/{self.repo}/git/refs"
        data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        return await self._post(url, data)

    async def create_pr(self, title: str, body: str, head: str, base: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{self.repo}/pulls"
        data = {"title": title, "body": body, "head": head, "base": base}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=self.headers)
            if resp.status_code == 201:
                return resp.json()["html_url"]
        return None

    async def get_file_content(self, path: str, ref: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{self.repo}/contents/{path}?ref={ref}"
        data = await self._get(url)
        if data and "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8")
        return None

    async def update_file(self, path: str, content: str, message: str, branch: str) -> bool:
        # Get current SHA if exists
        url = f"{self.base_url}/repos/{self.repo}/contents/{path}?ref={branch}"
        current = await self._get(url)
        sha = current.get("sha") if current else None

        content_b64 = base64.b64encode(content.encode()).decode()
        data = {"message": message, "content": content_b64, "branch": branch}
        if sha:
            data["sha"] = sha

        put_url = f"{self.base_url}/repos/{self.repo}/contents/{path}"
        return await self._put(put_url, data)

    # CI methods
    async def get_run(self, run_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}"
        return await self._get(url) or {}

    async def get_logs(self, run_id: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}/logs"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
        return None

    async def get_test_results(self, run_id: str) -> str:
        artifacts_url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}/artifacts"
        artifacts = await self._get(artifacts_url)
        artifacts = artifacts.get("artifacts", []) if artifacts else []
        test_artifact = None
        for art in artifacts:
            name = art["name"].lower()
            if "test" in name or "junit" in name or "report" in name:
                test_artifact = art
                break
        if not test_artifact:
            return "No test artifact found."

        # Download zip
        async with httpx.AsyncClient() as client:
            resp = await client.get(test_artifact["archive_download_url"], headers=self.headers, follow_redirects=True)
            if resp.status_code != 200:
                return "Failed to download artifact."

        try:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                xml_files = [f for f in z.namelist() if f.endswith(".xml")]
                if not xml_files:
                    return "No XML file in artifact."
                with z.open(xml_files[0]) as f:
                    content = f.read().decode("utf-8")
                    xml = JUnitXml.fromstring(content)
                    failures = []
                    for suite in xml:
                        for case in suite:
                            if case.result and case.result.type == "failure":
                                failures.append(f"{case.name}: {case.result.message}")
                    if failures:
                        return "Test failures:\n" + "\n".join(failures)
                    else:
                        return "Test report found, but no failures."
        except Exception as e:
            return f"Error parsing test artifact: {e}"

    async def list_runs(self, status: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/repos/{self.repo}/actions/runs?per_page={limit}"
        if status:
            url += f"&status={status}"
        data = await self._get(url)
        return data.get("workflow_runs", []) if data else []

    async def trigger_workflow(self, workflow_id: str, ref: str, inputs: dict) -> bool:
        url = f"{self.base_url}/repos/{self.repo}/actions/workflows/{workflow_id}/dispatches"
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=self.headers)
            return resp.status_code == 204