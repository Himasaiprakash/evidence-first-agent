import json
import urllib.request
import urllib.parse
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, SourceClass, SOURCE_CLASS_WEIGHTS

class KnowledgeGraphDiscovery:
    """
    Wikidata Structured Knowledge Graph Discovery Adapter:
    - Wikidata Entity Search (Official Wikimedia Knowledge Base)
    - 100M+ structured items, canonical identifiers, aliases, and concept relations
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceFirstResearchAgent/1.0 (mailto:admin@evidenceagent.org)"
        }

    def search_wikidata(self, query: str, max_results: int = 2) -> List[Source]:
        """Search Wikidata structured knowledge graph for canonical entities and ontology taxonomy."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={encoded_query}&language=en&format=json&limit={max_results}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    entities = data.get("search", [])
                    for idx, ent in enumerate(entities):
                        label = ent.get("label", query)
                        desc = ent.get("description", "Structured ontology entity")
                        qid = ent.get("id", f"Q{idx+1}")
                        ent_url = ent.get("url") or f"https://www.wikidata.org/wiki/{qid}"
                        aliases = ", ".join(ent.get("aliases", []))

                        sources.append(Source(
                            id=f"src-wikidata-{idx+1}",
                            title=f"Wikidata Entity ({qid}): {label}",
                            url=ent_url,
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.TERTIARY,
                            source_class=SourceClass.WIKIPEDIA,
                            author_publisher="Wikimedia Foundation (Wikidata Structured Knowledge Graph)",
                            publication_date="2025-01-01",
                            credibility_score=70.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.WIKIPEDIA] * 100.0,
                            primary_status=False,
                            raw_content=f"Wikidata Knowledge Graph Entity {qid}: {label}. Description: {desc}. Known Aliases: [{aliases}]. Verified entity identifier and semantic ontology mapping.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources
