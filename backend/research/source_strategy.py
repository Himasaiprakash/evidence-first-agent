from typing import List, Dict
from backend.models.schemas import DomainType, SourceType

class SourceStrategy:
    """
    Determines appropriate source categories and targeted search queries based on domain and research objectives.
    """
    def get_queries(self, topic: str, domain: DomainType) -> List[Dict[str, str]]:
        t = topic.strip()
        
        queries = [
            {"type": "canonical", "query": t, "source_type": "WEB"},
            {"type": "academic", "query": f"{t} principles architecture survey", "source_type": "ACADEMIC_PAPER"},
            {"type": "benchmarks", "query": f"{t} empirical benchmarks performance latency recall", "source_type": "WEB"},
            {"type": "controversies", "query": f"{t} limitations trade-offs conflicts disadvantages", "source_type": "WEB"},
            {"type": "implementation", "query": f"{t} implementation guide architecture production", "source_type": "WEB"}
        ]

        if domain == DomainType.AI_TECHNOLOGY:
            queries.append({"type": "academic_recent", "query": f"{t} state of the art evaluation", "source_type": "ACADEMIC_PAPER"})
        elif domain == DomainType.MEDICINE_BIOLOGY:
            queries.append({"type": "clinical", "query": f"{t} clinical trial efficacy meta-analysis", "source_type": "ACADEMIC_PAPER"})
        elif domain == DomainType.PHYSICAL_SCIENCE:
            queries.append({"type": "physics", "query": f"{t} experimental validation measurement", "source_type": "ACADEMIC_PAPER"})

        return queries
