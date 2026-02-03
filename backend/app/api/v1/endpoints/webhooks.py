from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.services.webhook_service import WebhookService
from app.workers.tasks import analyze_repository, analyze_changed_files
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/github")
@limiter.limit("30/minute")
async def github_webhook(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    body = await request.body()
    signature_256 = request.headers.get("X-Hub-Signature-256")
    signature_1 = request.headers.get("X-Hub-Signature")
    event_type = request.headers.get("X-GitHub-Event", "unknown")

    if not WebhookService().verify_signature(body, signature_256, signature_1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    payload = await request.json()
    repo_info = payload.get("repository") or {}
    full_name = repo_info.get("full_name")

    if not full_name:
        return {"message": "Webhook received: no repository info"}

    repo = db.query(Repository).filter(Repository.full_name == full_name).first()
    if not repo:
        return {"message": "Webhook received: repository not tracked"}

    deleted = db.query(RepositoryCache).filter(
        RepositoryCache.repository_id == repo.id
    ).delete()
    db.commit()

    action = "cache_invalidated"
    if event_type == "push":
        changed = _extract_changed_files(payload)
        analyze_changed_files.delay(
            repo.id,
            changed["added"],
            changed["modified"],
            changed["removed"],
        )
        action = "incremental_analysis_triggered"
    elif event_type == "pull_request":
        action = "pull_request_received"

    return {"message": "Webhook processed", "event": event_type, "action": action, "deleted": deleted}


def _extract_changed_files(payload: dict) -> dict:
    added = set()
    modified = set()
    removed = set()

    for commit in payload.get("commits", []):
        added.update(commit.get("added", []) or [])
        modified.update(commit.get("modified", []) or [])
        removed.update(commit.get("removed", []) or [])

    return {
        "added": sorted(added),
        "modified": sorted(modified),
        "removed": sorted(removed),
    }
