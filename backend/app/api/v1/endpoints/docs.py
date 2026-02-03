from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session

from app.api import deps
from app.models.repository import Repository
from app.models.documentation import Documentation
from app.models.user import User
from app.workers.celery_app import celery_app
from app.workers.tasks import generate_docs
from app.services.cache import CacheService
from app.core.rate_limit import limiter

router = APIRouter()

class DocsGenerateRequest(BaseModel):
    repo_id: int
    doc_type: Literal["readme", "api"] = "readme"


@router.post("/generate")
@limiter.limit("10/minute")
async def generate_docs_endpoint(
    request: Request,
    payload: DocsGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    repo = db.query(Repository).filter(
        Repository.id == payload.repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    task = generate_docs.delay(payload.repo_id, payload.doc_type)
    return {"task_id": task.id, "status": "queued"}


@router.get("/generate/{task_id}")
@limiter.limit("60/minute")
async def generate_docs_status(request: Request, task_id: str) -> Any:
    result = celery_app.AsyncResult(task_id)
    response: Dict[str, Any] = {
        "task_id": task_id,
        "state": result.state,
    }

    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = str(result.result)

    return response

@router.get("/{repo_id}")
@limiter.limit("60/minute")
async def get_docs(
    request: Request,
    repo_id: int,
    doc_type: Literal["readme", "api"] = "readme",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    cache = CacheService()
    cache_key = f"repo:{repo.id}:docs:{doc_type}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached

    doc = db.query(Documentation).filter(
        Documentation.repository_id == repo.id,
        Documentation.doc_type == doc_type,
    ).order_by(Documentation.updated_at.desc().nullslast(), Documentation.created_at.desc()).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation not found"
        )

    updated_at = doc.updated_at or doc.created_at
    payload = {
        "repo_id": repo.id,
        "doc_type": doc_type,
        "content": doc.content or "",
        "updated_at": updated_at.isoformat() if updated_at else None,
    }
    cache.set_json(cache_key, payload)
    return payload
