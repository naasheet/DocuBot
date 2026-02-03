import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal, engine, Base
from app.crud import user as crud_user
from app.schemas.user import UserCreate
from app.models.repository import Repository
from app.models.chat import ChatMessage, ChatSession


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
    email = "chatuser@example.com"
    existing = crud_user.get_user_by_email(db, email)
    if existing:
        db.delete(existing)
        db.commit()
    user_in = UserCreate(email=email, password="password123", full_name="Chat User")
    return crud_user.create_user(db, user_in)


def get_auth_token(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


def test_chat_endpoint_creates_messages(client: TestClient, db: Session, test_user):
    repo = Repository(
        user_id=test_user.id,
        github_id=4444,
        name="chat-repo",
        full_name="test/chat-repo",
        description="Chat repo",
        url="https://github.com/test/chat-repo",
        is_active=True,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    token = get_auth_token(client, "chatuser@example.com", "password123")

    with patch("app.api.v1.endpoints.chat.VectorDBService.search_code", return_value=[]), patch(
        "app.api.v1.endpoints.chat.LLMService.generate_text", return_value="Test answer"
    ):
        response = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"repo_id": repo.id, "query": "What is this repo?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test answer"
    assert data["session_id"]

    session_id = data["session_id"]
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    assert session is not None

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


def test_chat_history_endpoint(client: TestClient, db: Session, test_user):
    repo = Repository(
        user_id=test_user.id,
        github_id=5555,
        name="chat-repo-2",
        full_name="test/chat-repo-2",
        description="Chat repo 2",
        url="https://github.com/test/chat-repo-2",
        is_active=True,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    session = ChatSession(user_id=test_user.id, repository_id=repo.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    db.add(ChatMessage(session_id=session.id, role="user", content="Hi"))
    db.add(ChatMessage(session_id=session.id, role="assistant", content="Hello"))
    db.commit()

    token = get_auth_token(client, "chatuser@example.com", "password123")
    response = client.get(
        f"/api/v1/chat/history/{session.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session.id
    assert len(data["messages"]) == 2
