import os
import json
from typing import Dict, List, Optional
from backend.models.schemas import ResearchWorkspace
from backend.services.research_engine import ResearchEngine

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "workspaces")
os.makedirs(STORAGE_DIR, exist_ok=True)

class WorkspaceStore:
    """
    Persistent Workspace Store:
    - Persists every research workspace as a structured JSON file in `data/workspaces/`
    - Loads all saved workspaces automatically on startup
    - Workspaces survive server restarts and code reloads permanently
    """
    def __init__(self):
        self._workspaces: Dict[str, ResearchWorkspace] = {}
        self._engine = ResearchEngine()
        self._load_from_disk()

    def _load_from_disk(self):
        """Scans and deserializes all JSON workspace files from disk."""
        self._workspaces.clear()
        if not os.path.exists(STORAGE_DIR):
            return

        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(STORAGE_DIR, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        ws = ResearchWorkspace.model_validate(data)
                        self._workspaces[ws.id] = ws
                except Exception as e:
                    print(f"Error loading workspace from {filepath}: {e}")

    def save(self, workspace: ResearchWorkspace):
        """Persists workspace in memory and writes directly to disk."""
        self._workspaces[workspace.id] = workspace
        filepath = os.path.join(STORAGE_DIR, f"{workspace.id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(workspace.model_dump_json(indent=2))
        except Exception as e:
            print(f"Failed to persist workspace {workspace.id} to disk: {e}")

    def save_workspace(self, workspace: ResearchWorkspace):
        """Alias for save."""
        self.save(workspace)

    def get_all(self) -> List[ResearchWorkspace]:
        self._load_from_disk()
        return list(self._workspaces.values())

    def get_by_id(self, workspace_id: str) -> Optional[ResearchWorkspace]:
        if workspace_id in self._workspaces:
            return self._workspaces[workspace_id]
        filepath = os.path.join(STORAGE_DIR, f"{workspace_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ws = ResearchWorkspace.model_validate(data)
                    self._workspaces[ws.id] = ws
                    return ws
            except Exception:
                pass
        return None

    def create(self, topic: str, goal: str = "Understand and Build", depth: str = "Comprehensive") -> ResearchWorkspace:
        from backend.research.deep_research_agent import DeepResearchAgent
        agent = DeepResearchAgent()
        workspace = agent.run_deep_research(topic=topic, goal=goal)
        self.save(workspace)
        return workspace

    def delete_all(self):
        """Deletes all saved workspaces from memory and disk."""
        self._workspaces.clear()
        if os.path.exists(STORAGE_DIR):
            for filename in os.listdir(STORAGE_DIR):
                if filename.endswith(".json"):
                    try:
                        os.remove(os.path.join(STORAGE_DIR, filename))
                    except Exception as e:
                        print(f"Error removing {filename}: {e}")

    def delete_by_id(self, workspace_id: str) -> bool:
        """Deletes a single workspace by ID."""
        self._workspaces.pop(workspace_id, None)
        filepath = os.path.join(STORAGE_DIR, f"{workspace_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error removing {filepath}: {e}")
        return False

workspace_store = WorkspaceStore()
