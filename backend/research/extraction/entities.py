import re
from typing import List, Set
from backend.models.schemas import Entity, DocumentChunk, Source

class EntityExtractor:
    """
    Dynamic Entity Extractor:
    - Extracts real entities directly from retrieved document chunks and source metadata
    - Resolves duplicate names and aliases
    - Zero hardcoded domain entities
    """
    def extract_entities(self, topic: str, sources: List[Source], chunks: List[DocumentChunk]) -> List[Entity]:
        entities: List[Entity] = []
        seen_names: Set[str] = set()

        # 1. Main Topic Entity
        topic_title = topic.strip().title()
        entities.append(Entity(
            id="ent-1",
            name=topic_title,
            type="Core Topic",
            description=f"Primary research subject.",
            aliases=[topic.strip().lower(), topic_title]
        ))
        seen_names.add(topic_title.lower())

        # 2. Extract Author / Organization Entities from Sources
        for src in sources:
            if src.author_publisher and src.author_publisher != "Academic Researchers":
                name = src.author_publisher.split(" et al.")[0].strip()
                if name.lower() not in seen_names and len(name) > 3:
                    seen_names.add(name.lower())
                    ent_type = "Organization" if any(w in name.lower() for w in ["lab", "institute", "group", "foundation", "ieee", "acm", "wikipedia"]) else "Person"
                    entities.append(Entity(
                        id=f"ent-src-{len(entities)+1}",
                        name=name,
                        type=ent_type,
                        description=f"Source author/publisher for {src.title[:30]}.",
                        first_seen_source_id=src.id
                    ))

        # 3. Dynamic Technical Term & Acronym Extraction from text chunks
        for chk in chunks:
            text = chk.text
            # Match acronyms (e.g. RAG, AEC, VAD, LLM, BERT, GPU, CRISPR, DNA, Qdrant)
            acronyms = re.findall(r"\b[A-Z]{2,6}\b", text)
            for ac in set(acronyms):
                if ac.lower() not in seen_names and len(ac) >= 2:
                    seen_names.add(ac.lower())
                    entities.append(Entity(
                        id=f"ent-tech-{len(entities)+1}",
                        name=ac,
                        type="Technology / Concept",
                        description=f"Technical term discovered in {chk.section}.",
                        first_seen_source_id=chk.source_id
                    ))

            # Match capitalized key concepts (e.g., "Vector Database", "Quantum Circuit", "Dense Retrieval")
            key_phrases = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", text)
            for kp in set(key_phrases):
                kp_clean = kp.strip()
                if kp_clean.lower() not in seen_names and len(kp_clean) > 4 and kp_clean.lower() != topic_title.lower():
                    # Filter out common sentence starters
                    if kp_clean.lower() not in ["this paper", "we propose", "in this", "recent work", "the proposed"]:
                        seen_names.add(kp_clean.lower())
                        entities.append(Entity(
                            id=f"ent-term-{len(entities)+1}",
                            name=kp_clean,
                            type="Concept / Component",
                            description=f"Concept extracted from source text.",
                            first_seen_source_id=chk.source_id
                        ))

        return entities[:12]
