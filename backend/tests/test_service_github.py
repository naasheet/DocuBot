import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from app.services.github import GitHubService

@pytest.mark.asyncio
async def test_get_user_repos_success():
    """Test fetching user repositories successfully."""
    mock_data = [{"id": 1, "name": "test-repo", "full_name": "test/test-repo"}]
    
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_client.get.return_value = mock_response
        
        service = GitHubService("fake_token")
        repos = await service.get_user_repos()
        
        assert repos == mock_data
        # Verify correct URL and headers were used
        mock_client.get.assert_called_once()
        args, kwargs = mock_client.get.call_args
        assert "/user/repos" in args[0]
        assert kwargs["headers"]["Authorization"] == "Bearer fake_token"

@pytest.mark.asyncio
async def test_get_repo_details_success():
    """Test fetching repository details successfully."""
    mock_data = {"id": 1, "name": "test-repo", "owner": {"login": "testuser"}}
    
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_client.get.return_value = mock_response
        
        service = GitHubService("fake_token")
        details = await service.get_repo_details("testuser", "test-repo")
        
        assert details == mock_data
        assert "/repos/testuser/test-repo" in mock_client.get.call_args[0][0]

@pytest.mark.asyncio
async def test_get_file_content_success():
    """Test fetching file content successfully."""
    content = "print('hello world')"
    
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = content
        mock_client.get.return_value = mock_response
        
        service = GitHubService("fake_token")
        result = await service.get_file_content("testuser", "test-repo", "main.py")
        
        assert result == content
        # Verify raw accept header
        assert mock_client.get.call_args[1]["headers"]["Accept"] == "application/vnd.github.v3.raw"

@pytest.mark.asyncio
async def test_github_service_401_error():
    """Test handling of 401 Unauthorized error."""
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        # Simulate raise_for_status behavior
        error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error
        
        mock_client.get.return_value = mock_response
        
        service = GitHubService("bad_token")
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_user_repos()
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired GitHub token" in exc_info.value.detail

@pytest.mark.asyncio
async def test_github_service_404_error():
    """Test handling of 404 Not Found error."""
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        mock_response.raise_for_status.side_effect = error
        
        mock_client.get.return_value = mock_response
        
        service = GitHubService("token")
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_repo_details("user", "unknown-repo")
        
        assert exc_info.value.status_code == 404
        assert "GitHub resource not found" in exc_info.value.detail

@pytest.mark.asyncio
async def test_github_service_connection_error():
    """Test handling of connection errors."""
    with patch("app.services.github.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        # Simulate connection error
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        
        service = GitHubService("token")
        
        with pytest.raises(HTTPException) as exc_info:
            await service.get_user_repos()
        
        assert exc_info.value.status_code == 503
        assert "GitHub API connection error" in exc_info.value.detail