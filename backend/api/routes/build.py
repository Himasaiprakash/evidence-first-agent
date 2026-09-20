from fastapi import APIRouter, HTTPException
from backend.models.schemas import BuildProject, CodeExecutionValidation, ValidateCodeRequest
from backend.services.build_engine import BuildEngine
from backend.services.workspace_store import workspace_store

router = APIRouter(prefix="/api/build", tags=["Build Engine"])
build_engine = BuildEngine()

@router.get("/project/{workspace_id}", response_model=BuildProject)
def get_build_project(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return build_engine.create_build_project(ws)

@router.post("/validate", response_model=CodeExecutionValidation)
def validate_code(req: ValidateCodeRequest):
    return build_engine.validate_code_submission(req)
