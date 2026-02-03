from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, AnyHttpUrl, field_validator
from sqlalchemy.orm import Session

from app.api import deps
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.models.user import User
from app.services.github import GitHubService
from app.services.cache import CacheService
from app.config import settings
from app.workers.celery_app import celery_app
from app.workers.tasks import analyze_repository
from app.core.rate_limit import limiter

router = APIRouter()

class RepositoryCreate(BaseModel):
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        url = str(value)
        if "github.com/" not in url:
            raise ValueError("URL must be a GitHub repository")
        return value

class RepositoryResponse(BaseModel):
    id: int
    github_id: int
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    user_id: int

    class Config:
        from_attributes = True

@router.get("/", response_model=List[Any])
@limiter.limit("30/minute")
async def list_repos(
    request: Request,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Fetch repos from GitHub
    """
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected"
        )
    cache = CacheService()
    cache_key = f"user:{current_user.id}:repos:list"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached

    service = GitHubService(current_user.github_access_token)
    repos = await service.get_user_repos()
    cache.set_json(cache_key, repos)
    return repos

@router.post("/", response_model=RepositoryResponse)
@limiter.limit("10/minute")
async def create_repo(
    request: Request,
    repo_in: RepositoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Add a repository from GitHub URL
    """
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected"
        )

    # Parse URL to get owner and repo name
    url = str(repo_in.url).strip()
    if url.endswith(".git"):
        url = url[:-4]
    
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].split("/")
    else:
        parts = url.split("/")
    
    parts = [p for p in parts if p]
    
    if len(parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL"
        )
        
    owner, repo_name = parts[0], parts[1]

    service = GitHubService(current_user.github_access_token)
    repo_data = await service.get_repo_details(owner, repo_name)

    # Check if repo already exists
    repo = db.query(Repository).filter(
        Repository.user_id == current_user.id,
        Repository.github_id == repo_data["id"]
    ).first()

    if not repo:
        repo = Repository(
            user_id=current_user.id,
            github_id=repo_data["id"],
            name=repo_data["name"],
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            url=repo_data["html_url"],
            is_active=True
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        CacheService().delete(f"user:{current_user.id}:repos:list")

    webhook_base = (settings.WEBHOOK_BASE_URL or "").rstrip("/")
    if webhook_base:
        webhook_url = f"{webhook_base}/api/v1/webhooks/github"
        await service.create_webhook(owner, repo_name, webhook_url)
    
    return repo

@router.get("/{repo_id}", response_model=RepositoryResponse)
@limiter.limit("60/minute")
async def get_repo(
    request: Request,
    repo_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific repository by ID
    """
    cache = CacheService()
    cache_key = f"user:{current_user.id}:repos:{repo_id}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return cached

    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    payload = RepositoryResponse.model_validate(repo).model_dump()
    cache.set_json(cache_key, payload)
    return payload


@router.get("/{repo_id}/tree")
@limiter.limit("60/minute")
async def get_repo_tree(
    request: Request,
    repo_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a cached, filtered file tree for quick UI display.
    """
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    cache = db.query(RepositoryCache).filter(
        RepositoryCache.repository_id == repo.id,
        RepositoryCache.cache_type == "file_tree",
    ).first()

    if cache and _is_cache_fresh(cache):
        payload = cache.payload or {}
        children = payload.get("children") if isinstance(payload, dict) else None
        if children:
            return payload

    if not current_user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub account not connected"
        )

    owner, repo_name = repo.full_name.split("/", 1)
    service = GitHubService(current_user.github_access_token)
    tree = await service.get_repo_file_tree(owner, repo_name)

    if cache is None:
        cache = RepositoryCache(
            repository_id=repo.id,
            cache_type="file_tree",
            payload=tree,
        )
        db.add(cache)
    else:
        cache.payload = tree

    db.commit()
    db.refresh(cache)
    return cache.payload


def _is_cache_fresh(cache: RepositoryCache) -> bool:
    timestamp = cache.updated_at or cache.created_at
    if timestamp is None:
        return False
    if timestamp.tzinfo is None:
        now = datetime.utcnow()
    else:
        now = datetime.now(timezone.utc)
    return now - timestamp <= timedelta(hours=1)

@router.delete("/{repo_id}")
async def delete_repo(repo_id: int):
    return {"message": f"Delete repository {repo_id}"}


@router.post("/{repo_id}/analyze")
@limiter.limit("60/minute")
async def analyze_repo(
    request: Request,
    repo_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Trigger repository analysis via Celery.
    """
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    task = analyze_repository.delay(repo.id)
    return {"task_id": task.id, "status": "queued"}


@router.get("/{repo_id}/analyze/{task_id}")
@limiter.limit("600/minute")
async def analyze_status(
    request: Request,
    repo_id: int,
    task_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Check analysis task status.
    """
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

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
