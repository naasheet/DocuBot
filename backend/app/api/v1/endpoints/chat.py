import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import SessionLocal
from app.models.chat import ChatMessage, ChatSession
from app.models.repository import Repository
from app.models.user import User
from app.services.llm import LLMService
from app.services.vector_db import VectorDBService
from app.services.cache import CacheService
from app.utils.prompts import RAG_PROMPT_TEMPLATE
from app.core.rate_limit import limiter

router = APIRouter()

class ChatRequest(BaseModel):
    repo_id: int
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[int] = None
    top_k: int = Field(5, ge=1, le=20)
    history_limit: int = Field(6, ge=0, le=20)


@router.post("/")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    repo = db.query(Repository).filter(
        Repository.id == payload.repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        db.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    session = None
    if payload.session_id is not None:
        session = db.query(ChatSession).filter(
            ChatSession.id == payload.session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.repository_id == repo.id,
        ).first()

    if session is None:
        session = ChatSession(
            user_id=current_user.id,
            repository_id=repo.id,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    vector_service = VectorDBService()
    collection_name = os.getenv("QDRANT_COLLECTION", "docubot_code")
    results = vector_service.search_code(
        query=payload.query,
        repo_id=repo.id,
        collection_name=collection_name,
        top_k=payload.top_k,
    )

    history = _load_history(db, session.id, payload.history_limit)
    context = _format_context(results, history)
    prompt = RAG_PROMPT_TEMPLATE.format(
        query=payload.query,
        context=context,
    )

    llm = LLMService()
    answer = llm.generate_text(prompt).strip()

    db.add(ChatMessage(session_id=session.id, role="user", content=payload.query))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer))
    db.commit()
    CacheService().delete(f"chat:session:{session.id}:history")

    return {
        "session_id": session.id,
        "answer": answer,
        "results": results,
    }


@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    db = SessionLocal()
    repo = db.query(Repository).filter(
        Repository.id == payload.repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    session = None
    if payload.session_id is not None:
        session = db.query(ChatSession).filter(
            ChatSession.id == payload.session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.repository_id == repo.id,
        ).first()

    if session is None:
        session = ChatSession(
            user_id=current_user.id,
            repository_id=repo.id,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    vector_service = VectorDBService()
    collection_name = os.getenv("QDRANT_COLLECTION", "docubot_code")
    results = vector_service.search_code(
        query=payload.query,
        repo_id=repo.id,
        collection_name=collection_name,
        top_k=payload.top_k,
    )

    history = _load_history(db, session.id, payload.history_limit)
    context = _format_context(results, history)
    prompt = RAG_PROMPT_TEMPLATE.format(
        query=payload.query,
        context=context,
    )

    llm = LLMService()
    db.add(ChatMessage(session_id=session.id, role="user", content=payload.query))
    db.commit()
    CacheService().delete(f"chat:session:{session.id}:history")

    def event_stream():
        answer_parts: List[str] = []
        try:
            yield _sse_event("meta", {"session_id": session.id})
            for chunk in llm.generate_text_stream(prompt):
                answer_parts.append(chunk)
                yield _sse_data(chunk)
            answer = "".join(answer_parts).strip()
            db.add(ChatMessage(session_id=session.id, role="assistant", content=answer))
            db.commit()
            CacheService().delete(f"chat:session:{session.id}:history")
            yield _sse_event("done", {"status": "completed"})
        except Exception as exc:
            db.rollback()
            yield _sse_event("error", {"message": str(exc)})
        finally:
            db.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/history/{session_id}")
@limiter.limit("60/minute")
async def get_history(
    request: Request,
    session_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    cache = CacheService()
    cache_key = f"chat:session:{session.id}:history"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    payload = {
        "session_id": session.id,
        "repo_id": session.repository_id,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }
    cache.set_json(cache_key, payload, ttl=60)
    return payload


def _format_context(results: List[Dict[str, Any]], history: List[ChatMessage]) -> str:
    sections: List[str] = []

    if history:
        history_lines = []
        for message in history:
            history_lines.append(f"{message.role}: {message.content}")
        sections.append("Conversation History\n" + "\n".join(history_lines))

    if not results:
        sections.append("Retrieved Context\nTBD")
        return "\n\n".join(sections)

    blocks: List[str] = []
    for item in results:
        payload = item.get("payload") or {}
        code = payload.get("content") or payload.get("code") or ""
        path = payload.get("path") or payload.get("file_path") or "unknown"
        symbol = payload.get("symbol") or payload.get("name") or ""
        score = item.get("score")

        header_parts = [f"path: {path}"]
        if symbol:
            header_parts.append(f"symbol: {symbol}")
        if score is not None:
            header_parts.append(f"score: {score:.4f}")

        header = " | ".join(header_parts)
        block = f"{header}\n{code}".strip()
        blocks.append(block)

    sections.append("Retrieved Context\n" + "\n\n---\n\n".join(blocks))
    return "\n\n".join(sections)


def _load_history(db: Session, session_id: int, limit: int) -> List[ChatMessage]:
    if limit <= 0:
        return []
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()[::-1]
    )


def _sse_data(content: str) -> str:
    safe = content.replace("\r", "")
    lines = safe.split("\n")
    return "data: " + "\ndata: ".join(lines) + "\n\n"


def _sse_event(event: str, payload: Dict[str, Any]) -> str:
    import json

    return f"event: {event}\n" + _sse_data(json.dumps(payload))
