from fastapi import APIRouter

router = APIRouter()

@router.post("/generate")
async def generate_docs():
    return {"message": "Generate documentation"}

@router.get("/{repo_id}")
async def get_docs(repo_id: int):
    return {"message": f"Get documentation for repo {repo_id}"}
