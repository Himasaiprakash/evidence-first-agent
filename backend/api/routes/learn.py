from fastapi import APIRouter, HTTPException
from backend.models.schemas import Curriculum, QuizSubmission, QuizEvaluation, UserMasteryProfile
from backend.services.learn_engine import LearnEngine
from backend.services.workspace_store import workspace_store

router = APIRouter(prefix="/api/learn", tags=["Learning Engine"])
learn_engine = LearnEngine()

@router.get("/curriculum/{workspace_id}", response_model=Curriculum)
def get_curriculum(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return learn_engine.generate_curriculum(ws)

@router.post("/quiz/evaluate/{workspace_id}", response_model=QuizEvaluation)
def evaluate_quiz_answer(workspace_id: str, submission: QuizSubmission):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return learn_engine.evaluate_quiz(submission, ws)

@router.get("/mastery/{user_id}", response_model=UserMasteryProfile)
def get_user_mastery(user_id: str = "default_user"):
    return learn_engine.get_user_mastery(user_id)
