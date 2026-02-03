import hashlib
import hmac
import json
import os
import time
import zlib
from typing import Dict, Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import SessionLocal
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud import user as crud_user
from app.services.embeddings import EmbeddingService


API_BASE = os.getenv("INTEGRATION_API_BASE", "http://localhost:8000")
QDRANT_BASE = os.getenv("INTEGRATION_QDRANT_BASE", "http://qdrant:6333")
COLLECTION = os.getenv("QDRANT_COLLECTION", "docubot_code")


def _register_and_login(email: str, password: str) -> str:
    with httpx.Client(base_url=API_BASE, timeout=120) as client:
        client.post("/api/v1/auth/register", json={"email": email, "password": password})
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]


def _create_repo(db: Session, user_id: int, full_name: str) -> Repository:
    github_id = time.time_ns() % 1_000_000_000
    repo = Repository(
        user_id=user_id,
        github_id=github_id,
        name=full_name.split("/")[-1],
        full_name=full_name,
        description="Integration test repo",
        url=f"https://github.com/{full_name}",
        is_active=True,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def _create_analysis_cache(db: Session, repo_id: int) -> None:
    cache = RepositoryCache(
        repository_id=repo_id,
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


def _create_qdrant_collection() -> None:
    with httpx.Client(timeout=30) as client:
        for _ in range(10):
            try:
                health = client.get(f"{QDRANT_BASE}/healthz")
                if health.status_code == 200:
                    break
            except httpx.RequestError:
                time.sleep(1)
        client.delete(f"{QDRANT_BASE}/collections/{COLLECTION}")
        response = client.put(
            f"{QDRANT_BASE}/collections/{COLLECTION}",
            json={"vectors": {"size": 384, "distance": "Cosine"}},
        )
        response.raise_for_status()


def _upsert_point(repo_id: int, path: str, content: str) -> None:
    embedder = EmbeddingService()
    vector = embedder.generate_embedding(content)
    checksum = zlib.crc32(f"{path}:0".encode("utf-8")) % 1_000_000
    point_id = repo_id * 1_000_000 + checksum
    payload = {
        "repo_id": repo_id,
        "path": path,
        "language": "python",
        "doc_type": "function",
        "symbol": "main",
        "chunk_index": 0,
        "content": content,
    }
    with httpx.Client(timeout=30) as client:
        response = client.put(
            f"{QDRANT_BASE}/collections/{COLLECTION}/points",
            params={"wait": "true"},
            json={"points": [{"id": point_id, "vector": vector, "payload": payload}]},
        )
        assert response.status_code == 200, response.text


def test_full_doc_generation_flow():
    email = f"docflow_{int(time.time())}@example.com"
    token = _register_and_login(email, "password123")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user_id = user.id
        repo = _create_repo(db, user_id, "test/docflow-repo")
        repo_id = repo.id
        _create_analysis_cache(db, repo_id)
    finally:
        db.close()

    with httpx.Client(base_url=API_BASE, timeout=60) as client:
        response = client.post(
            "/api/v1/docs/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"repo_id": repo_id, "doc_type": "readme"},
        )
        response.raise_for_status()
        task_id = response.json()["task_id"]

        final_state = None
        for _ in range(60):
            status = client.get(
                f"/api/v1/docs/generate/{task_id}",
                headers={"Authorization": f"Bearer {token}"},
            ).json()
            final_state = status.get("state")
            if final_state == "SUCCESS":
                break
            if final_state == "FAILURE":
                break
            time.sleep(2)

        assert final_state == "SUCCESS", status

        doc_resp = client.get(
            f"/api/v1/docs/{repo_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"doc_type": "readme"},
        )
        doc_resp.raise_for_status()
        content = doc_resp.json().get("content", "")
        assert content


def test_full_chat_flow():
    email = f"chatflow_{int(time.time())}@example.com"
    token = _register_and_login(email, "password123")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        user_id = user.id
        repo = _create_repo(db, user_id, "test/chatflow-repo")
        repo_id = repo.id
    finally:
        db.close()

    _create_qdrant_collection()
    _upsert_point(repo_id, "app/main.py", "def main():\n    return True\n")

    with httpx.Client(base_url=API_BASE, timeout=120) as client:
        response = client.post(
            "/api/v1/chat/",
            headers={"Authorization": f"Bearer {token}"},
            json={"repo_id": repo_id, "query": "What does main return?"},
        )
        response.raise_for_status()
        data = response.json()
        assert data.get("answer")
        assert data.get("session_id")


def test_webhook_flow():
    db = SessionLocal()
    try:
        email = f"webhook_{int(time.time())}@example.com"
        user_in = UserCreate(email=email, password="password123", full_name="Webhook User")
        user = crud_user.create_user(db, user_in)
        repo = _create_repo(db, user_id=user.id, full_name="test/webhook-repo")
    finally:
        db.close()

    payload: Dict[str, Any] = {
        "repository": {"full_name": repo.full_name},
        "commits": [
            {"added": ["app/new.py"], "modified": ["app/main.py"], "removed": ["app/old.py"]}
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    secret = settings.GITHUB_WEBHOOK_SECRET.encode("utf-8")
    signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    with httpx.Client(base_url=API_BASE, timeout=30) as client:
        response = client.post(
            "/api/v1/webhooks/github",
            headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "push"},
            content=body,
        )
        response.raise_for_status()
        data = response.json()
        assert data["event"] == "push"
        assert data["action"] == "incremental_analysis_triggered"
