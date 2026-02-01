import httpx
from typing import List, Dict, Any
from fastapi import HTTPException, status

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