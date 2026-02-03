import httpx
from typing import List, Dict, Any
from fastapi import HTTPException, status
from app.config import settings

class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get_user_repos(self) -> List[Dict[str, Any]]:
        """
        Fetch all repositories for the authenticated user.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/user/repos",
                    headers=self.headers,
                    params={"sort": "updated", "per_page": 100, "visibility": "all"}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                self._handle_error(e)
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"GitHub API connection error: {str(e)}"
                )

    async def get_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch details of a specific repository.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                self._handle_error(e)
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"GitHub API connection error: {str(e)}"
                )

    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """
        Fetch raw content of a file from the repository.
        """
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                    headers=headers
                )
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                self._handle_error(e)
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"GitHub API connection error: {str(e)}"
                )

    async def create_webhook(self, owner: str, repo: str, webhook_url: str) -> Dict[str, Any]:
        """
        Create a GitHub webhook for push and pull_request events.
        """
        payload = {
            "name": "web",
            "active": True,
            "events": ["push", "pull_request"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0",
            },
        }

        if settings.GITHUB_WEBHOOK_SECRET:
            payload["config"]["secret"] = settings.GITHUB_WEBHOOK_SECRET

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/hooks",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    return {"message": "Webhook already exists or is invalid", "status_code": 422}
                self._handle_error(e)
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"GitHub API connection error: {str(e)}"
                )

    async def get_repo_file_tree(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fetch a filtered file tree for quick UI display.
        """
        repo_details = await self.get_repo_details(owner, repo)
        ref = repo_details.get("default_branch", "main")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{ref}",
                    headers=self.headers,
                    params={"recursive": "1"},
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                self._handle_error(e)
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"GitHub API connection error: {str(e)}"
                )

        paths = []
        for item in data.get("tree", []):
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if not self._is_allowed_path(path):
                continue
            paths.append(path)

        return self._build_tree_from_paths(paths)

    def _is_allowed_path(self, path: str) -> bool:
        if not path:
            return False
        ignore_dirs = {".git", "node_modules", "__pycache__"}
        parts = path.split("/")
        if any(part in ignore_dirs for part in parts):
            return False
        ext = f".{parts[-1].split('.')[-1]}" if "." in parts[-1] else ""
        return ext in {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".html",
            ".css",
            ".md",
            ".json",
            ".yml",
            ".yaml",
        }

    def _build_tree_from_paths(self, paths: List[str]) -> Dict[str, Any]:
        root = {"name": "", "path": "", "type": "dir", "children": []}
        index = {"": root}

        for path in paths:
            parts = path.split("/")
            filename = parts[-1]
            dir_part = "/".join(parts[:-1])

            parent = root
            if dir_part:
                parent = self._ensure_dir(index, dir_part)

            parent["children"].append({"name": filename, "path": path, "type": "file"})

        self._sort_tree(root)
        return root

    def _ensure_dir(self, index: Dict[str, Dict[str, Any]], dir_part: str) -> Dict[str, Any]:
        current_path = ""
        parent = index[""]
        for part in dir_part.split("/"):
            current_path = f"{current_path}/{part}" if current_path else part
            node = index.get(current_path)
            if node is None:
                node = {"name": part, "path": current_path, "type": "dir", "children": []}
                parent["children"].append(node)
                index[current_path] = node
            parent = node
        return parent

    def _sort_tree(self, node: Dict[str, Any]) -> None:
        children = node.get("children", [])
        if not children:
            return
        children.sort(key=lambda item: (item.get("type") != "dir", item.get("name", "")))
        for child in children:
            if child.get("type") == "dir":
                self._sort_tree(child)

    def _handle_error(self, e: httpx.HTTPStatusError):
        """
        Handle HTTP errors from GitHub API.
        """
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired GitHub token",
            )
        elif e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub resource not found",
            )
        else:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"GitHub API error: {e.response.text}",
            )
