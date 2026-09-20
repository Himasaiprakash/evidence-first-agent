from typing import Dict, Any, Optional
from backend.models.schemas import ResearchWorkspace, Curriculum, BuildProject, ChatResponse, ChatRequest
from backend.services.research_engine import ResearchEngine
from backend.services.learn_engine import LearnEngine
from backend.services.build_engine import BuildEngine
from backend.services.chat_engine import ChatEngine
from backend.services.workspace_store import workspace_store

class Orchestrator:
    """
    Central Orchestrator coordinating the execution loop:
    Goal Understanding -> Research & Verification -> Graph Assembly -> Learn Curriculum -> Build Blueprint -> Validation.
    """
    def __init__(self):
        self.research_engine = ResearchEngine()
        self.learn_engine = LearnEngine()
        self.build_engine = BuildEngine()
        self.chat_engine = ChatEngine()

    def process_unified_request(self, topic: str, goal: str = "Understand and Build", depth: str = "Comprehensive") -> Dict[str, Any]:
        # 1. Execute Research & Knowledge Graph Assembly
        workspace = workspace_store.create(topic=topic, goal=goal, depth=depth)
        
        # 2. Compile Learn Curriculum
        curriculum = self.learn_engine.generate_curriculum(workspace)
        
        # 3. Compile Build Engineering Project
        build_project = self.build_engine.create_build_project(workspace)

        return {
            "workspace": workspace,
            "curriculum": curriculum,
            "build_project": build_project,
            "status": "READY"
        }

orchestrator = Orchestrator()
