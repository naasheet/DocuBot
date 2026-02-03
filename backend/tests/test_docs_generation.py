import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.models.documentation import Documentation, DocType


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
    email = "docgen@example.com"
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()
    user_in = UserCreate(email=email, password="password123", full_name="Doc Gen")
    return crud_user.create_user(db, user_in)


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def test_generate_readme_service(db: Session, test_user):
    repo = Repository(
        user_id=test_user.id,
        github_id=2222,
        name="docgen-repo",
        full_name="test/docgen-repo",
        description="Docgen repo",
        url="https://github.com/test/docgen-repo",
        is_active=True,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    cache = RepositoryCache(
        repository_id=repo.id,
        cache_type="analysis",
        payload={
            "file_tree": {"name": "root", "type": "dir", "children": []},
            "files": [
                {
                    "path": "app/main.py",
                    "language": "python",
                    "functions": [{"name": "main", "signature": "def main()"}],
                    "classes": [],
                }
            ],
        },
    )
    db.add(cache)
    db.commit()

    with patch("app.services.documentation.LLMService.generate_text", return_value="README CONTENT"):
        from app.services.documentation import generate_readme

        result = generate_readme(repo.id)
        assert result["status"] == "completed"

        doc = db.query(Documentation).filter(
            Documentation.repository_id == repo.id,
            Documentation.doc_type == DocType.README,
        ).first()
        assert doc is not None
        assert doc.content == "README CONTENT"


def test_docs_get_endpoint(client: TestClient, db: Session, test_user):
    repo = Repository(
        user_id=test_user.id,
        github_id=3333,
        name="docgen-repo-2",
        full_name="test/docgen-repo-2",
        description="Docgen repo 2",
        url="https://github.com/test/docgen-repo-2",
        is_active=True,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    doc = Documentation(
        repository_id=repo.id,
        doc_type=DocType.README,
        content="# Test README",
    )
    db.add(doc)
    db.commit()

    token = get_auth_token(client, "docgen@example.com", "password123")
    response = client.get(
        f"/api/v1/docs/{repo.id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"doc_type": "readme"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "# Test README"
