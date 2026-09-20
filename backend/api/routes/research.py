from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import ResearchWorkspace, CreateResearchRequest, Source, Claim, Conflict
from backend.services.workspace_store import workspace_store

router = APIRouter(prefix="/api/research", tags=["Research"])

@router.get("/workspaces", response_model=List[ResearchWorkspace])
def list_workspaces():
    return workspace_store.get_all()

@router.delete("/workspaces")
def delete_all_workspaces():
    workspace_store.delete_all()
    return {"status": "success", "message": "All workspaces deleted successfully"}

@router.delete("/workspace/{workspace_id}")
def delete_workspace(workspace_id: str):
    success = workspace_store.delete_by_id(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found or already deleted")
    return {"status": "success", "message": f"Workspace {workspace_id} deleted"}

@router.get("/workspace/{workspace_id}", response_model=ResearchWorkspace)
def get_workspace(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Research workspace not found")
    return ws

@router.post("/submit", response_model=ResearchWorkspace)
def create_research(req: CreateResearchRequest):
    if not req.topic or len(req.topic.strip()) < 2:
        raise HTTPException(status_code=400, detail="Topic must be at least 2 characters long")
    goal_str = req.goal or "Understand and Build"
    print(f"\n{'='*70}\n[API REQUEST] POST /api/research/submit | Topic: '{req.topic}' | Goal: '{goal_str}'\n{'='*70}")
    try:
        ws = workspace_store.create(
            topic=req.topic,
            goal=req.goal or "Understand and Build",
            depth=req.depth or "Comprehensive"
        )
        print(f"[API RESPONSE] Successfully returned Workspace {ws.id} ({len(ws.report)} chapters, Quality: {ws.quality.overall:.1f}/100, Sources: {len(ws.sources)})\n{'='*70}\n")
        return ws
    except Exception as e:
        import traceback
        print(f"\n[API ERROR] Research pipeline failed for topic '{req.topic}': {type(e).__name__}: {e}")
        traceback.print_exc()
        print(f"{'='*70}\n")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspace/{workspace_id}/sources", response_model=List[Source])
def get_sources(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Research workspace not found")
    return ws.sources

@router.get("/workspace/{workspace_id}/claims", response_model=List[Claim])
def get_claims(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Research workspace not found")
    return ws.claims

@router.get("/workspace/{workspace_id}/conflicts", response_model=List[Conflict])
def get_conflicts(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Research workspace not found")
    return ws.conflicts
