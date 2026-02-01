from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.repository import Repository
from app.models.user import User
from app.services.github import GitHubService

router = APIRouter()

class RepositoryCreate(BaseModel):
    url: str

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
async def list_repos(
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
    service = GitHubService(current_user.github_access_token)
    return await service.get_user_repos()

@router.post("/", response_model=RepositoryResponse)
async def create_repo(
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
    url = repo_in.url.strip()
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
    
    return repo

@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repo(
    repo_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific repository by ID
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
    return repo

@router.delete("/{repo_id}")
async def delete_repo(repo_id: int):
    return {"message": f"Delete repository {repo_id}"}
