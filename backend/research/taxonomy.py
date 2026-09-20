import os
import json
import re
from typing import Dict, List, Any, Union
from backend.models.schemas import DomainType

TAXONOMY_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "domain_taxonomy.json"
)

DEFAULT_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "AI_TECHNOLOGY": {
        "name": "AI & Modern Computing Technologies",
        "regex_patterns": [
            r"\b(rag|retrieval|augmented|generation|llm|llms|agent|agents|ai|transformer|transformers|neural|embedding|embeddings|vector|reranking|cross-encoder|prompt|nlp|deep learning|machine learning|computer vision|reinforcement learning|backprop|backpropagation|convolutional|cnn|rnn|lstm|diffusion|serving|inference|pagedattention|vllm|kv[- ]?cache|roofline|tensor parallel|pipeline parallel|gpt|gpt-4o|claude|gemini|llama|mistral|deepseek|swe-bench|humaneval|bfcl|mmlu|frontier model|model comparison|foundation model|prompt caching)\b"
        ],
        "anchor_terms": [
            "language model", "llm", "transformer", "neural", "deep learning", "inference", "fine-tuning", "retrieval", "rag", "lora"
        ],
        "search_hints": [
            "machine learning", "large language model", "neural network", "artificial intelligence"
        ],
        "ai_keywords": [
            "ai", "llm", "language model", "gpt", "neural", "deep learning", "transformer", "prompt"
        ]
    },
    "ENVIRONMENTAL_TOXICOLOGY": {
        "name": "Environmental Toxicology, Ecotoxicology & Chemical Fate",
        "regex_patterns": [
            r"\b(biomagnif\w*|bioaccumul\w*|bioconcentrat\w*|trophic|toxicolog\w*|ecotoxicolog\w*|pollut\w*|pesticides?|ddt|dde|mercury|methylmercury|pcbs?|pfas|heavy metals?|food web|food chain|environmental fate|contaminants?|endocrine disrupt\w*|pops?|persistent organic|microplastics?)\b"
        ],
        "anchor_terms": [
            "ecotoxicity", "contamination", "bioaccumulation", "exposure", "pollutant", "effluent", "pfas"
        ],
        "search_hints": [
            "toxicology", "environmental", "ecology"
        ]
    },
    "MEDICINE_BIOLOGY": {
        "name": "Medicine & Biology",
        "regex_patterns": [
            r"\b(heart|cardiac|cardiovascular|anatomy|genes?|genetics|crispr|cas9|sgrna|off-target|base edit|prime edit|lnp|lipid nanoparticle|medical|diseases?|drugs?|clinical|biology|cancer|proteins?|brain|liver|organs?|pulmonary|valve|ventricle|pathology)\b"
        ],
        "anchor_terms": [
            "clinical", "trial", "efficacy", "patient", "therapy", "fda", "pharmacology", "drug", "receptor"
        ],
        "search_hints": [
            "biology", "medicine", "cardiac", "physiology"
        ]
    },
    "PHYSICAL_SCIENCE": {
        "name": "Physical Sciences, Materials & Energy Storage",
        "regex_patterns": [
            r"\b(battery|batteries|solid-state|solid electrolyte|lithium metal|dendrite|ionic conductiv\w*|llzo|lgps|argyrodite|quantum|physics|semiconductor|thermodynamics|optics|relativity|teleportation|entanglement|sun|solar|stars?|astronomy|astrophysics|cosmology|galaxy|planets?|gravity|nuclear fusion|fusion|photosphere|corona|plasma|heliosphere)\b"
        ],
        "anchor_terms": [
            "quantum", "semiconductor", "thermodynamics", "optics", "relativity", "lithium", "battery", "photosphere", "fusion"
        ],
        "search_hints": [
            "physics", "chemistry", "quantum"
        ]
    },
    "FINANCE_COMMERCE": {
        "name": "Finance, Central Banking & Macro Plumbing",
        "regex_patterns": [
            r"\b(quantitative tightening|qt|balance sheet|soma|reverse repo|on rrp|sofr|iorb|repo market|treasury|tga|bank reserves|lclor|stocks?|markets?|revenue|crypto|finance|financial|economy|banking|valuation|earnings)\b"
        ],
        "anchor_terms": [
            "central bank", "monetary policy", "balance sheet", "interest rate", "treasury", "yield", "liquidity", "fomc", "fred", "reverse repurchase", "on rrp"
        ],
        "search_hints": [
            "finance", "economics", "market"
        ]
    },
    "SOFTWARE_ENGINEERING": {
        "name": "Software Engineering & Infrastructure",
        "regex_patterns": [
            r"\b(database|databases|compiler|compilers|operating system|kubernetes|linux|webrtc|cache|caching|backend|school management|api|microservices|distributed systems)\b"
        ],
        "anchor_terms": [
            "software", "architecture", "database", "api", "microservices", "distributed systems", "compiler", "operating system"
        ],
        "search_hints": [
            "software", "database", "computer science", "programming"
        ]
    },
    "HISTORY_HUMANITIES": {
        "name": "History & Humanities",
        "regex_patterns": [
            r"\b(roman|empire|wars?|history|historical|ancient|dynasty|revolution|centur(?:y|ies))\b"
        ],
        "anchor_terms": [
            "historical", "empire", "dynasty", "ancient", "revolution", "century", "historiography"
        ],
        "search_hints": [
            "history", "humanities", "ancient history"
        ]
    }
}


class DomainTaxonomyRegistry:
    """
    Central, Configurable Domain Taxonomy Registry:
    - Decouples hardcoded domain classification rules, regex patterns, anchor terms, and search hints.
    - Loads dynamic rules from `data/domain_taxonomy.json` with robust fallback to default taxonomy.
    """

    def __init__(self, filepath: str = TAXONOMY_FILE_PATH):
        self.filepath = filepath
        self.taxonomy: Dict[str, Dict[str, Any]] = self._load_taxonomy()

    def _load_taxonomy(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and len(data) > 0:
                        return data
            except Exception as e:
                print(f"[TAXONOMY WARNING] Failed to load taxonomy from {self.filepath}: {e}. Using default taxonomy.")
        return DEFAULT_TAXONOMY

    def reload(self):
        """Reloads taxonomy from disk."""
        self.taxonomy = self._load_taxonomy()

    def classify_domain(self, topic: str) -> DomainType:
        """Dynamically classifies a research topic into a DomainType based on taxonomy regex patterns."""
        t = topic.lower()

        # Check each domain in taxonomy order
        domain_order = [
            DomainType.AI_TECHNOLOGY,
            DomainType.ENVIRONMENTAL_TOXICOLOGY,
            DomainType.MEDICINE_BIOLOGY,
            DomainType.PHYSICAL_SCIENCE,
            DomainType.FINANCE_COMMERCE,
            DomainType.SOFTWARE_ENGINEERING,
            DomainType.HISTORY_HUMANITIES
        ]

        for dom in domain_order:
            dom_key = dom.value if isinstance(dom, DomainType) else str(dom)
            dom_config = self.taxonomy.get(dom_key, {})
            patterns = dom_config.get("regex_patterns", [])
            for pattern in patterns:
                if re.search(pattern, t):
                    return dom

        return DomainType.GENERAL

    def get_domain_anchors(self, domain: Union[DomainType, str]) -> List[str]:
        """Retrieves anchor terms for a specific domain."""
        dom_key = domain.value if isinstance(domain, DomainType) else str(domain)
        dom_config = self.taxonomy.get(dom_key, {})
        return dom_config.get("anchor_terms", [])

    def get_domain_hints(self, domain: Union[DomainType, str]) -> List[str]:
        """Retrieves search hints for a specific domain."""
        dom_key = domain.value if isinstance(domain, DomainType) else str(domain)
        dom_config = self.taxonomy.get(dom_key, {})
        return dom_config.get("search_hints", [])

    def is_ai_topic(self, topic: str, domain: Union[DomainType, str]) -> bool:
        """Determines if a topic is AI-related based on configured AI keywords or domain."""
        dom = domain if isinstance(domain, DomainType) else DomainType(domain) if domain in DomainType.__members__ else None
        if dom in [DomainType.AI_TECHNOLOGY, DomainType.SOFTWARE_ENGINEERING]:
            return True

        ai_config = self.taxonomy.get(DomainType.AI_TECHNOLOGY.value, {})
        ai_keywords = ai_config.get("ai_keywords", ["ai", "llm", "language model", "gpt", "neural", "deep learning", "transformer", "prompt"])

        t_lower = topic.lower()
        return any(kw in t_lower for kw in ai_keywords)


# Global singleton instance
domain_taxonomy = DomainTaxonomyRegistry()
