import os
from backend.models.schemas import ResearchWorkspace
from backend.research.orchestrator import AutonomousResearchOrchestrator
from backend.research.deep_research_agent import DeepResearchAgent
from backend.research.groq_client import GroqClient

class ResearchEngine:
    """
    Unified Research Engine:
    - Automatically activates Groq-powered Deep Research Agent when GROQ_API_KEY is available
    - Seamlessly falls back to deterministic multi-source orchestrator when running offline or without API keys
    """
    def __init__(self):
        self.groq_client = GroqClient()
        self.deterministic_orchestrator = AutonomousResearchOrchestrator()
        self.deep_research_agent = DeepResearchAgent(groq_client=self.groq_client)

    def run_research(self, topic: str, goal: str = "Understand and Build", depth: str = "Comprehensive") -> ResearchWorkspace:
        try:
            return self.deep_research_agent.run_deep_research(topic=topic, goal=goal)
        except Exception as e:
            import traceback
            print(f"\n[ENGINE ERROR] DeepResearchAgent failed with {type(e).__name__}: {e}")
            traceback.print_exc()
            print(f"[ENGINE FALLBACK] Switching to deterministic orchestrator...\n")
            return self.deterministic_orchestrator.run_research(topic=topic, goal=goal, depth=depth)
