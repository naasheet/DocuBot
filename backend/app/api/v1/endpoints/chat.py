from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def chat():
    return {"message": "Chat endpoint"}

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    return {"message": f"Get chat history {session_id}"}
