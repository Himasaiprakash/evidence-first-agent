from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.models.schemas import KnowledgeGraphData
from backend.services.workspace_store import workspace_store
from backend.services.knowledge_graph import KnowledgeGraphService

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

@router.get("/{workspace_id}", response_model=KnowledgeGraphData)
def get_graph_data(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws.graph

@router.get("/{workspace_id}/cypher")
def export_cypher(workspace_id: str):
    ws = workspace_store.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    kg_service = KnowledgeGraphService()
    kg_service.build_from_workspace(ws.topic, ws.entities, ws.claims, ws.sources)
    statements = kg_service.export_neo4j_cypher()
    return {"workspace_id": workspace_id, "cypher_statements": statements}
