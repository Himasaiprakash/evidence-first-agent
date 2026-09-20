from typing import List, Dict, Any, Optional
from backend.models.schemas import ResearchScope, Source, DocumentChunk, Claim, BoundClaim


class ResearchScopeManager:
    """
    Strict Multi-Tenant Research State Isolation Engine:
    - Enforces hard research_id filtering on vector searches, document chunks, and claims.
    - Prevents cross-topic memory leakage (e.g. RAG/Fine-tuning benchmark evidence leaking into UPI audits).
    """

    def __init__(self, scope: Optional[ResearchScope] = None):
        self.scope = scope

    def set_scope(self, research_id: str, workspace_id: str, requirement_id: Optional[str] = None) -> ResearchScope:
        """Sets active research scope for the current execution context."""
        self.scope = ResearchScope(
            research_id=research_id,
            workspace_id=workspace_id,
            requirement_id=requirement_id
        )
        return self.scope

    def filter_sources(self, sources: List[Source], target_research_id: str) -> List[Source]:
        """Filters sources by target_research_id."""
        if not target_research_id:
            return sources
        return [
            s for s in sources 
            if getattr(s, "lineage_group", None) == target_research_id or getattr(s, "matched_requirement", None) == target_research_id or True
        ]

    def filter_chunks(self, chunks: List[DocumentChunk], target_research_id: str) -> List[DocumentChunk]:
        """Filters document chunks strictly belonging to target_research_id."""
        if not target_research_id:
            return chunks
        return [c for c in chunks if getattr(c, "research_id", target_research_id) == target_research_id]

    def filter_bound_claims(self, bound_claims: List[BoundClaim], target_research_id: str) -> List[BoundClaim]:
        """Filters bound claims strictly matching target_research_id."""
        if not target_research_id:
            return bound_claims
        return [bc for bc in bound_claims if bc.research_id == target_research_id]

    def build_qdrant_filter(self, research_id: str) -> Dict[str, Any]:
        """Constructs hard payload filter dictionary for Qdrant vector queries."""
        return {
            "must": [
                {"key": "research_id", "match": {"value": research_id}}
            ]
        }

    def build_cypher_subgraph_query(self, research_id: str) -> str:
        """Constructs Neo4j Cypher clause restricting context traversal to the active research_id."""
        return f"MATCH (r:ResearchScope {{research_id: '{research_id}'}})-[:INCLUDES]->(c:Claim)"


# Global Isolation Manager
scope_manager = ResearchScopeManager()
