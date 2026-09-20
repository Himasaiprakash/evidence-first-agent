from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.chat_engine import ChatEngine
from backend.services.workspace_store import workspace_store

router = APIRouter(prefix="/api/chat", tags=["Evidence Chat"])
chat_engine = ChatEngine()

@router.post("/query", response_model=ChatResponse)
def handle_chat_query(req: ChatRequest):
    ws = workspace_store.get_by_id(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return chat_engine.process_message(req, ws)
