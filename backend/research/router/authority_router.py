import re
import urllib.parse
import urllib.request
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

from backend.models.schemas import Source, SourceType, SourceCategory, DomainType, SourceClass, SOURCE_CLASS_WEIGHTS
from backend.research.extraction.canonical_entity_gate import CanonicalResolutionResult, CanonicalEntityProfile
from backend.research.discovery.web import WebDiscovery
from backend.research.discovery.academic_universal import AcademicUniversalDiscovery

# Known Tier-3 aggregator and blog domains that are forbidden from verifying quantitative numbers
TIER_3_AGGREGATOR_PATTERNS = [
    "finout.io", "g2.com", "baeseokj", "benchlm.ai", "llm-stats.com", "platform.teamai.com",
    "edstellar.com", "aimodelbenchmarks.com", "medium.com", "towardsdatascience.com", "forbes.com",
    "analyticsvidhya.com", "geeksforgeeks.org", "simplilearn.com", "techtarget.com",
    "spiceworks.com", "datacamp.com", "coursera.org", "pecollective.com", "claudefa.st",
    "typingmind.com", "railwail.com", "openrouter.ai", "autobench.org", "klu.ai", "promptlayer.com",
    "dpboss", "satta", "matka", "kalyan", "lottery", "casino", "gambling", "betting"
]

class AuthorityClassification(BaseModel):
    source_id: str
    authority_tier: str  # "TIER_1_PRIMARY" | "TIER_2_SECONDARY" | "TIER_3_AGGREGATOR"
    is_primary_vendor_or_regulator: bool
    verified_domain: str
    penalty_reason: Optional[str] = None

class PrimaryAuthorityRouter:
    """
    Phase 1: Universal Authority-Tiered Evidence Harvester (All Domains)
    - Directly routes targeted queries to verified primary authority domains using site: domain scoping
    - Replaces broad aggregator queries with primary documentation search
    - Automatically classifies evidence into Tier 1 (Primary), Tier 2 (Academic), and Tier 3 (Aggregator)
    - Rejects or quarantines Tier 3 aggregators for quantitative assertions
    """
    def __init__(self):
        self.web = WebDiscovery()
        self.academic = AcademicUniversalDiscovery()

    def harvest_primary_evidence(
        self,
        resolution: CanonicalResolutionResult,
        domain: DomainType
    ) -> Tuple[List[Source], List[Dict[str, Any]]]:
        """
        Dispatches precision primary queries across all canonical entities and dimensions.
        Returns (deduped_sources, executed_queries).
        """
        sources: List[Source] = []
        executed_queries: List[Dict[str, Any]] = []
        queries: List[Tuple[str, str, str]] = []  # (query_string, target_domain, entity_name)

        for entity in resolution.entities:
            clean_name = re.sub(r'^(OpenAI|Anthropic|Google|Meta|Microsoft|Alibaba)\s+', '', entity.canonical_name, flags=re.IGNORECASE)
            dims_text = " ".join(resolution.requested_dimensions[:3]) if resolution.requested_dimensions else "official documentation specifications"

            # 1. Primary Vendor Domain Direct Query (Strict site: prefix for 100% primary authority yield)
            for prim_domain in entity.primary_authority_domains[:2]:
                if prim_domain:
                    queries.append((f"site:{prim_domain} {clean_name} API pricing documentation specifications", prim_domain, entity.canonical_name))

            # 2. General Primary Technical Specifications & Pricing Query
            if domain in [DomainType.AI_TECHNOLOGY, DomainType.SOFTWARE_ENGINEERING]:
                queries.append((f"{entity.canonical_name} official API pricing benchmarks 2026", "", entity.canonical_name))
            else:
                queries.append((f"{entity.canonical_name} official specifications 2026", "", entity.canonical_name))

            # 3. Authoritative Encyclopedic Overview (Executed SECONDARY as tertiary background)
            wiki_sources = self.web.search_wikipedia_multi(clean_name, domain)
            wiki_yield = 0
            for ws in wiki_sources[:2]:
                ws.retrieval_query = clean_name
                ws.discovery_engine = "Wikipedia REST API"
                ws.phase = "Phase 1: Authority Harvest"
                tagged = self._classify_and_tag_source(ws, resolution.entities)
                if tagged:
                    sources.append(tagged)
                    wiki_yield += 1

            executed_queries.append({
                "phase": "Phase 1: Authority Harvest",
                "query": clean_name,
                "engine": "Wikipedia REST API",
                "target": entity.canonical_name,
                "yield_count": wiki_yield,
                "timestamp": datetime.now().isoformat()
            })

        # 4. Domain-Specific Independent Primary Registry Queries
        if domain == DomainType.AI_TECHNOLOGY:
            q_low = resolution.query.lower()
            if any(k in q_low for k in ["rag", "retrieval", "fine-tuning", "finetuning", "lora"]):
                queries.append(("Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks Lewis", "arxiv.org", "RAG Seminal Paper"))
                queries.append(("Fine-Tuning or Retrieval? Comparing Large Language Model Knowledge Injection", "arxiv.org", "RAG vs FT Comparative Paper"))
                queries.append(("LoRA Low-Rank Adaptation of Large Language Models Hu", "arxiv.org", "LoRA Seminal Paper"))
            else:
                queries.append(("site:swebench.com SWE-bench Verified coding benchmark results", "swebench.com", "SWE-bench"))
                queries.append(("site:lmarena.ai LMSYS Chatbot Arena Leaderboard results", "lmarena.ai", "LMSYS Arena"))
                queries.append(("site:openai.com/api/pricing GPT-4o GPT-4o-mini o1 pricing context", "openai.com", "OpenAI Official Pricing"))
                queries.append(("site:anthropic.com/pricing Claude 3.5 Sonnet Haiku pricing context", "anthropic.com", "Anthropic Official Pricing"))
                queries.append(("site:ai.google.dev/pricing Gemini 1.5 Pro Flash pricing context", "ai.google.dev", "Google AI Official Pricing"))
        elif domain in [DomainType.MEDICINE_BIOLOGY, DomainType.ENVIRONMENTAL_TOXICOLOGY]:
            queries.append((f"site:clinicaltrials.gov {resolution.query[:40]}", "clinicaltrials.gov", "ClinicalTrials"))
            queries.append((f"site:fda.gov {resolution.query[:40]}", "fda.gov", "FDA"))
        elif domain == DomainType.FINANCE_COMMERCE:
            queries.append((f"site:sec.gov {resolution.query[:40]} 10-K 10-Q filing", "sec.gov", "SEC EDGAR"))
            queries.append((f"site:federalreserve.gov {resolution.query[:40]}", "federalreserve.gov", "FederalReserve"))
        elif domain == DomainType.SOFTWARE_ENGINEERING:
            queries.append((f"site:github.com {resolution.query[:40]} benchmark latency", "github.com", "GitHub"))

        # Concurrently execute targeted searches (max 8 queries)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_q = {}
            for q in queries[:8]:
                q_str, domain_target, target_name = q
                if domain_target == "arxiv.org":
                    f = executor.submit(self.academic.search_arxiv, q_str, 2)
                    future_to_q[f] = (q_str, "ArXiv API", target_name)
                else:
                    f = executor.submit(self.web.search_duckduckgo, q_str, 2)
                    future_to_q[f] = (q_str, "DuckDuckGo Lite", target_name)
            for future in concurrent.futures.as_completed(future_to_q):
                q_tuple = future_to_q[future]
                yield_count = 0
                try:
                    res = future.result()
                    if res and isinstance(res, list):
                        for s in res:
                            s.retrieval_query = q_tuple[0]
                            s.discovery_engine = "DuckDuckGo Lite"
                            s.phase = "Phase 1: Authority Harvest"
                            # Classify and tag source authority
                            classified_source = self._classify_and_tag_source(s, resolution.entities)
                            if classified_source:
                                sources.append(classified_source)
                                yield_count += 1
                except Exception as e:
                    print(f"  [PRIMARY HARVEST WARNING] Query '{q_tuple[0]}' failed: {e}")

                executed_queries.append({
                    "phase": "Phase 1: Authority Harvest",
                    "query": q_tuple[0],
                    "engine": "DuckDuckGo Lite",
                    "target": q_tuple[2],
                    "yield_count": yield_count,
                    "timestamp": datetime.now().isoformat()
                })

        # Deduplicate sources by URL
        seen_urls = set()
        deduped = []
        for s in sources:
            clean_u = s.url.split("?")[0].rstrip("/")
            if clean_u not in seen_urls:
                seen_urls.add(clean_u)
                deduped.append(s)

        return deduped, executed_queries

    def _classify_and_tag_source(self, source: Source, entities: List[CanonicalEntityProfile]) -> Optional[Source]:
        """Tags source with strict authority tier and assigns deterministic SourceClass."""
        domain_name = urllib.parse.urlparse(source.url).netloc.lower().replace("www.", "")

        # Check if source is a tertiary source (Wikipedia, Wikidata, overview)
        if (source.category == SourceCategory.TERTIARY or
            "wikipedia.org" in domain_name or
            "wikidata.org" in domain_name or
            source.id.startswith("src-wiki")):
            source.category = SourceCategory.TERTIARY
            source.source_class = SourceClass.WIKIPEDIA
            source.authority_score = SOURCE_CLASS_WEIGHTS[SourceClass.WIKIPEDIA] * 100.0
            source.credibility_score = 65.0
            source.primary_status = False
            return source

        # Check if domain matches any Tier 3 aggregator pattern
        if any(agg in domain_name for agg in TIER_3_AGGREGATOR_PATTERNS):
            source.category = SourceCategory.SECONDARY
            source.source_class = SourceClass.BLOG
            source.authority_score = SOURCE_CLASS_WEIGHTS[SourceClass.BLOG] * 100.0
            source.credibility_score = 45.0
            source.primary_status = False
            return source

        # Check if domain matches a primary authority for any resolved entity
        is_primary = False
        for e in entities:
            if any(pd in domain_name for pd in e.primary_authority_domains if pd):
                is_primary = True
                break

        # Authoritative domain whitelist (regulatory bodies, official standards, top registries)
        authority_whitelist = [
            "openai.com", "anthropic.com", "cloud.google.com", "google.com", "swebench.com",
            "berkeley.edu", "fda.gov", "epa.gov", "nih.gov", "clinicaltrials.gov",
            "federalreserve.gov", "sec.gov", "postgresql.org", "clickhouse.com", "nature.com",
            "sciencedirect.com", "arxiv.org", "github.com", "nist.gov"
        ]
        if any(aw in domain_name for aw in authority_whitelist):
            is_primary = True

        if is_primary:
            source.category = SourceCategory.PRIMARY
            if "arxiv.org" in domain_name or "nature.com" in domain_name or "sciencedirect.com" in domain_name:
                source.source_class = SourceClass.PRIMARY_RESEARCH
            elif "sec.gov" in domain_name:
                source.source_class = SourceClass.COMPANY_FILING
            elif any(g in domain_name for g in ["fda.gov", "epa.gov", "federalreserve.gov"]):
                source.source_class = SourceClass.REGULATOR
            elif "nist.gov" in domain_name or "w3.org" in domain_name or "ietf.org" in domain_name:
                source.source_class = SourceClass.TECHNICAL_STANDARD
            else:
                source.source_class = SourceClass.OFFICIAL_DOCUMENTATION

            source.authority_score = SOURCE_CLASS_WEIGHTS.get(source.source_class, 0.90) * 100.0
            source.credibility_score = 99.0
            source.primary_status = True
        else:
            source.category = SourceCategory.SECONDARY
            source.source_class = SourceClass.SECONDARY_RESEARCH
            source.authority_score = SOURCE_CLASS_WEIGHTS[SourceClass.SECONDARY_RESEARCH] * 100.0
            source.credibility_score = 80.0
            source.primary_status = False

        return source
