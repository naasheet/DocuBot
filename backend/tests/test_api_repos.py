import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.user import User
from app.models.repository import Repository
# Import chat model to ensure SQLAlchemy relationships (User.chat_sessions) are registered
from app.models import chat, documentation

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(db: Session):
    email = "repotest@example.com"
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()
    
    user_in = UserCreate(email=email, password="password123", full_name="Repo Test")
    user = crud_user.create_user(db, user_in)
    return user

def get_auth_token(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]

def test_list_repos_unauthorized(client: TestClient):
    """Test that endpoint requires authentication."""
    response = client.get("/api/v1/repos/")
    assert response.status_code == 401

def test_list_repos_no_github_token(client: TestClient, db: Session, test_user):
    """Test that user without GitHub token gets 400."""
    # Ensure user has no token
    test_user.github_access_token = None
    db.add(test_user)
    db.commit()
    
    token = get_auth_token(client, "repotest@example.com", "password123")
    
    response = client.get(
        "/api/v1/repos/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "GitHub account not connected"

def test_list_repos_success(client: TestClient, db: Session, test_user):
    """Test successful retrieval of repos."""
    # Set GitHub token for user
    test_user.github_access_token = "gh_fake_token"
    db.add(test_user)
    db.commit()
    
    token = get_auth_token(client, "repotest@example.com", "password123")
    
    mock_repos = [
        {"id": 1, "name": "docubot", "full_name": "test/docubot", "private": False},
        {"id": 2, "name": "backend", "full_name": "test/backend", "private": True}
    ]
    
    # Patch the GitHubService used in the endpoint
    with patch("app.api.v1.endpoints.repos.GitHubService") as MockService:
        service_instance = MockService.return_value
        service_instance.get_user_repos = AsyncMock(return_value=mock_repos)
        
        response = client.get(
            "/api/v1/repos/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "docubot"
        
        # Verify service was initialized with correct token
        MockService.assert_called_with("gh_fake_token")
        service_instance.get_user_repos.assert_called_once()

def test_create_repo_success(client: TestClient, db: Session, test_user):
    """Test adding a repository via POST."""
    # Set GitHub token
    test_user.github_access_token = "gh_fake_token"
    db.add(test_user)
    db.commit()
    
    token = get_auth_token(client, "repotest@example.com", "password123")
    
    mock_repo_details = {
        "id": 12345,
        "name": "new-repo",
        "full_name": "test/new-repo",
        "description": "A test repo",
        "html_url": "https://github.com/test/new-repo",
        "owner": {"login": "test"}
    }
    
    with patch("app.api.v1.endpoints.repos.GitHubService") as MockService:
        service_instance = MockService.return_value
        service_instance.get_repo_details = AsyncMock(return_value=mock_repo_details)
        
        response = client.post(
            "/api/v1/repos/",
            headers={"Authorization": f"Bearer {token}"},
            json={"url": "https://github.com/test/new-repo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-repo"
        assert data["github_id"] == 12345
        
        # Verify DB persistence
        repo = db.query(Repository).filter(Repository.github_id == 12345).first()
        assert repo is not None
        assert repo.full_name == "test/new-repo"
        assert repo.user_id == test_user.id

def test_create_repo_invalid_url(client: TestClient, db: Session, test_user):
    """Test that invalid URLs are rejected."""
    # Set GitHub token
    test_user.github_access_token = "gh_fake_token"
    db.add(test_user)
    db.commit()
    
    token = get_auth_token(client, "repotest@example.com", "password123")
    
    response = client.post(
        "/api/v1/repos/",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": "not-a-github-url"}
    )
    
    assert response.status_code == 400
    assert "Invalid GitHub repository URL" in response.json()["detail"]

def test_get_repo_success(client: TestClient, db: Session, test_user):
    """Test retrieving a specific repository."""
    # Create a repo manually in DB
    repo = Repository(
        user_id=test_user.id,
        github_id=98765,
        name="get-test-repo",
        full_name="test/get-test-repo",
        description="Repo for get test",
        url="https://github.com/test/get-test-repo",
        is_active=True
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    token = get_auth_token(client, "repotest@example.com", "password123")

    response = client.get(
        f"/api/v1/repos/{repo.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == repo.id
    assert data["name"] == "get-test-repo"
    assert data["full_name"] == "test/get-test-repo"

def test_get_repo_not_found(client: TestClient, db: Session, test_user):
    """Test retrieving a non-existent repository."""
    token = get_auth_token(client, "repotest@example.com", "password123")

    response = client.get(
        "/api/v1/repos/999999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"

def test_get_repo_forbidden_other_user(client: TestClient, db: Session, test_user):
    """Test that user cannot access another user's repository."""
    # Create another user
    other_user_in = UserCreate(email="other@example.com", password="password123", full_name="Other User")
    other_user = crud_user.create_user(db, other_user_in)
    
    # Create repo for other user
    repo = Repository(
        user_id=other_user.id,
        github_id=11111,
        name="other-repo",
        full_name="other/other-repo",
        url="https://github.com/other/other-repo",
        is_active=True
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    
    # Login as test_user (repotest@example.com)
    token = get_auth_token(client, "repotest@example.com", "password123")
    
    # Try to access other user's repo
    response = client.get(
        f"/api/v1/repos/{repo.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return 404 because the query filters by current_user.id
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"