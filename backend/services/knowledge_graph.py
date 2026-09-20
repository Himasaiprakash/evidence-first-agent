from typing import List, Dict, Any, Optional, Set, Tuple
from backend.models.schemas import (
    KnowledgeGraphData, GraphNode, GraphEdge, Claim, Source, Entity, FactStatus
)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

class KnowledgeGraphService:
    """
    Graph Service supporting in-memory graph operations, path traversal,
    prerequisite DAG analysis, and Neo4j Cypher generation.
    Includes built-in pure Python fallback when NetworkX is not installed.
    """
    def __init__(self):
        if HAS_NETWORKX:
            self._nx_graph = nx.DiGraph()
        else:
            self._nx_graph = None
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._adjacency: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}
        self._reverse_adjacency: Dict[str, List[str]] = {}

    def build_from_workspace(self, topic: str, entities: List[Entity], claims: List[Claim], sources: List[Source]) -> KnowledgeGraphData:
        self.clear()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # 1. Add Main Topic Node
        topic_node_id = f"node-topic-{topic.lower().replace(' ', '-')}"
        self._add_node(topic_node_id, topic, "Core Topic", {"status": "Mastered"})
        nodes.append(GraphNode(id=topic_node_id, label=topic, node_type="Core Topic", metadata={"status": "Mastered"}))

        # 2. Add Entity Nodes
        for ent in entities:
            node_id = f"node-ent-{ent.id}"
            self._add_node(node_id, ent.name, ent.type, {"description": ent.description, "aliases": ent.aliases})
            nodes.append(GraphNode(id=node_id, label=ent.name, node_type=ent.type, metadata={"description": ent.description}))
            
            # Connect to topic
            edge_id = f"e-topic-{ent.id}"
            self._add_edge(topic_node_id, node_id, "CONTAINS_CONCEPT", {})
            edges.append(GraphEdge(id=edge_id, source=topic_node_id, target=node_id, relation="CONTAINS_CONCEPT"))

        # 3. Add Source Nodes
        for src in sources:
            node_id = f"node-src-{src.id}"
            self._add_node(node_id, src.title, "Source", {
                "category": src.category,
                "credibility": src.credibility_score,
                "authority": src.authority_score,
                "url": src.url
            })
            nodes.append(GraphNode(id=node_id, label=src.title[:35] + "...", node_type="Source", metadata={
                "category": src.category,
                "credibility": src.credibility_score
            }))

        # 4. Add Claim & Evidence Nodes
        for clm in claims:
            clm_node_id = f"node-clm-{clm.id}"
            self._add_node(clm_node_id, f"{clm.subject}: {clm.predicate}", "Claim", {
                "status": clm.status,
                "object_value": clm.object_value,
                "conditions": clm.conditions
            })
            nodes.append(GraphNode(
                id=clm_node_id,
                label=f"{clm.subject}: {clm.predicate}",
                node_type="Claim",
                metadata={"status": clm.status, "value": clm.object_value}
            ))

            # Edge: Claim -> Source
            src_node_id = f"node-src-{clm.evidence.source_id}"
            if src_node_id in self._nodes:
                edge_id = f"e-clm-src-{clm.id}"
                self._add_edge(clm_node_id, src_node_id, "EVIDENCE_FROM", {
                    "quote": clm.evidence.exact_quote,
                    "confidence": clm.evidence.confidence
                })
                edges.append(GraphEdge(id=edge_id, source=clm_node_id, target=src_node_id, relation="EVIDENCE_FROM"))

            # Edge: Claim -> Contradicting Claims
            for cont_src_id in clm.contradicting_source_ids:
                cont_node_id = f"node-src-{cont_src_id}"
                if cont_node_id in self._nodes:
                    edge_id = f"e-clm-contra-{clm.id}-{cont_src_id}"
                    self._add_edge(clm_node_id, cont_node_id, "CONTRADICTS", {})
                    edges.append(GraphEdge(id=edge_id, source=clm_node_id, target=cont_node_id, relation="CONTRADICTS"))

        return KnowledgeGraphData(nodes=nodes, edges=edges)

    def clear(self):
        if HAS_NETWORKX and self._nx_graph is not None:
            self._nx_graph.clear()
        self._nodes.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()

    def _add_node(self, node_id: str, label: str, node_type: str, metadata: Dict[str, Any]):
        self._nodes[node_id] = {"label": label, "node_type": node_type, **metadata}
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
        if node_id not in self._reverse_adjacency:
            self._reverse_adjacency[node_id] = []
        if HAS_NETWORKX and self._nx_graph is not None:
            self._nx_graph.add_node(node_id, label=label, node_type=node_type, **metadata)

    def _add_edge(self, source: str, target: str, relation: str, metadata: Dict[str, Any]):
        if source not in self._adjacency:
            self._adjacency[source] = []
        self._adjacency[source].append((target, relation, metadata))
        if target not in self._reverse_adjacency:
            self._reverse_adjacency[target] = []
        self._reverse_adjacency[target].append(source)
        if HAS_NETWORKX and self._nx_graph is not None:
            self._nx_graph.add_edge(source, target, relation=relation, **metadata)

    def find_prerequisites(self, concept_node_id: str) -> List[str]:
        """Traverse upstream REQUIRES edges in the concept DAG."""
        if HAS_NETWORKX and self._nx_graph is not None and self._nx_graph.has_node(concept_node_id):
            return list(nx.ancestors(self._nx_graph, concept_node_id))
        visited: Set[str] = set()
        queue = [concept_node_id]
        while queue:
            curr = queue.pop(0)
            for parent in self._reverse_adjacency.get(curr, []):
                if parent not in visited:
                    visited.add(parent)
                    queue.append(parent)
        return list(visited)

    def export_neo4j_cypher(self) -> List[str]:
        """Generate equivalent Cypher statements for exporting into Neo4j."""
        cypher_statements = []
        for node_id, data in self._nodes.items():
            label = data.get("node_type", "Entity").replace(" ", "")
            cypher_statements.append(
                f"MERGE (n:{label} {{id: '{node_id}', label: '{data.get('label', '')}'}})"
            )
        for u, neighbors in self._adjacency.items():
            for v, rel, _ in neighbors:
                rel_clean = rel.replace(" ", "_").upper()
                cypher_statements.append(
                    f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) MERGE (a)-[:{rel_clean}]->(b)"
                )
        return cypher_statements
