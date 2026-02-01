from fastapi import APIRouter

router = APIRouter()

@router.post("/github")
async def github_webhook():
    return {"message": "GitHub webhook handler"}
