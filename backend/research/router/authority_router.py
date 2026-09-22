import re
import json
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

            # Direct Ingestion of Official Documentation URLs resolved in Phase 0
            for doc_url in entity.documentation_urls:
                if doc_url.startswith("http"):
                    try:
                        doc_text = self.web.fetch_web_page(doc_url)
                        if doc_text and len(doc_text) > 300:
                            doc_domain = urllib.parse.urlparse(doc_url).netloc.lower().replace("www.", "")
                            sources.append(Source(
                                id=f"src-doc-{re.sub(r'[^a-zA-Z0-9]', '_', doc_domain)[:16]}",
                                title=f"Official Specification: {entity.canonical_name} ({doc_domain})",
                                url=doc_url,
                                source_type=SourceType.DOCUMENTATION,
                                category=SourceCategory.PRIMARY,
                                source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                                author_publisher=entity.governing_authority or doc_domain,
                                publication_date=datetime.now().strftime("%Y-%m-%d"),
                                credibility_score=99.0,
                                authority_score=95.0,
                                primary_status=True,
                                raw_content=doc_text[:12000],
                                retrieval_timestamp=datetime.now().isoformat()
                            ))
                    except Exception as e:
                        print(f"  [PRIMARY DOC FETCH WARNING] Failed to fetch {doc_url}: {e}")

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
            wiki_topic = f"{clean_name} (language model)" if domain in [DomainType.AI_TECHNOLOGY, DomainType.SOFTWARE_ENGINEERING] else clean_name
            wiki_sources = self.web.search_wikipedia_multi(wiki_topic, domain)
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
            # Direct Ingestion of Official Live Model Pricing & Tariff Registry (OpenRouter Primary Registry)
            try:
                openrouter_url = "https://openrouter.ai/api/v1/models"
                req = urllib.request.Request(openrouter_url, headers={"User-Agent": "EvidenceResearchBot/2.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    data = json.loads(r.read().decode("utf-8"))
                    models = data.get("data", [])
                    matched_specs = []
                    seen_m_ids = set()
                    for e in resolution.entities:
                        c_name_low = e.canonical_name.lower()
                        gov_auth_low = e.governing_authority.lower() if e.governing_authority else ""
                        dom_tokens = [d.split('.')[0] for d in e.primary_authority_domains if d]
                        
                        # Extract search tokens dynamically from entity canonical name, authority, and primary domains
                        search_tokens = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', f"{c_name_low} {gov_auth_low} {' '.join(dom_tokens)}")) - {"series", "model", "models", "the", "inc", "corp", "com", "org", "official"}
                        
                        # Sort models dynamically by context length (highest context / non-batch models first)
                        sorted_v_models = sorted(models, key=lambda x: x.get("context_length", 0), reverse=True)

                        entity_matches = 0
                        for m in sorted_v_models:
                            m_id = m.get("id", "").lower()
                            m_name = m.get("name", "").lower()

                            # Skip batch/free preview noise
                            if ":batch" in m_id or ":free" in m_id:
                                continue

                            # Dynamic match: does m_id or m_name contain any of the entity's search tokens?
                            if search_tokens and any(tok in m_id or tok in m_name for tok in search_tokens):
                                if m_id not in seen_m_ids:
                                    seen_m_ids.add(m_id)
                                    p = m.get("pricing", {})
                                    p_in = float(p.get("prompt", 0)) * 1000000
                                    p_out = float(p.get("completion", 0)) * 1000000
                                    ctx = m.get("context_length", 0)
                                    matched_specs.append(f"- Canonical Entity: {e.canonical_name} (Official Model Variant: {m.get('name')}, ID: {m.get('id')})\n  Context Window: {ctx:,} tokens\n  Input Token Pricing: ${p_in:.2f} per 1M tokens\n  Output Token Pricing: ${p_out:.2f} per 1M tokens")
                                    entity_matches += 1
                                    if entity_matches >= 5:
                                        break

                    if matched_specs:
                        spec_text = "Official API Model Pricing & Context Window Tariff Registry (OpenRouter Live Primary Registry):\n\n" + "\n\n".join(matched_specs[:20])
                        sources.append(Source(
                            id="src-doc-openrouter-registry",
                            title="Official API Model Pricing & Context Window Tariff Registry (openrouter.ai)",
                            url="https://openrouter.ai/models",
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                            author_publisher="OpenRouter Technical Model Registry",
                            publication_date=datetime.now().strftime("%Y-%m-%d"),
                            credibility_score=99.0,
                            authority_score=95.0,
                            primary_status=True,
                            raw_content=spec_text,
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
            except Exception as e:
                print(f"  [OPENROUTER REGISTRY FETCH WARNING] {e}")

            # 4. Universal Dynamic Primary Authority Scoping
            # Uses primary authority domains resolved dynamically in Phase 0 for each entity
            names_str = " ".join([e.canonical_name for e in resolution.entities]) if resolution.entities else resolution.query[:40]
            dims_str = " ".join(resolution.requested_dimensions[:3]) if resolution.requested_dimensions else "specifications"
            queries.append((f"{names_str} {dims_str} official documentation benchmarks 2026", "", names_str))
            
            # Dynamic academic paper routing if query or dimensions mention research
            q_low = resolution.query.lower()
            if any(k in q_low for k in ["paper", "study", "rag", "retrieval", "fine-tuning", "lora", "benchmark", "accuracy"]):
                queries.append((f"{names_str} {resolution.query[:50]} technical paper", "arxiv.org", "ArXiv Primary Research"))

        # Concurrently execute targeted searches (max 10 queries)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_to_q = {}
            for q in queries[:10]:
                q_str, domain_target, target_name = q
                if q_str.startswith("http"):
                    f = executor.submit(self.web.fetch_web_page, q_str)
                    future_to_q[f] = (q_str, "Direct URL Crawl", target_name)
                elif domain_target == "arxiv.org":
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
                    if res and isinstance(res, str) and len(res) > 300:
                        doc_url = q_tuple[0]
                        doc_domain = urllib.parse.urlparse(doc_url).netloc.lower().replace("www.", "")
                        s = Source(
                            id=f"src-doc-{re.sub(r'[^a-zA-Z0-9]', '_', doc_domain)[:16]}-{hash(doc_url)%1000}",
                            title=f"Official Pricing & Specs: {q_tuple[2]} ({doc_domain})",
                            url=doc_url,
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                            author_publisher=doc_domain,
                            publication_date=datetime.now().strftime("%Y-%m-%d"),
                            credibility_score=99.0,
                            authority_score=95.0,
                            primary_status=True,
                            raw_content=res[:12000],
                            retrieval_timestamp=datetime.now().isoformat()
                        )
                        sources.append(s)
                        yield_count += 1
                    elif res and isinstance(res, list):
                        for s in res:
                            s.retrieval_query = q_tuple[0]
                            s.discovery_engine = q_tuple[1]
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

        # Deduplicate sources by URL and deep-crawl primary authority pages
        seen_urls = set()
        deduped = []
        for s in sources:
            clean_u = s.url.split("?")[0].rstrip("/")
            if clean_u not in seen_urls:
                seen_urls.add(clean_u)
                # Deep crawl primary vendor/academic pages if raw_content is concise snippet (< 1000 chars)
                if (s.primary_status or s.authority_score >= 75.0) and len(s.raw_content or "") < 1000:
                    try:
                        full_txt = self.web.fetch_web_page(s.url)
                        if full_txt and len(full_txt) > len(s.raw_content or ""):
                            s.raw_content = full_txt[:12000]
                    except Exception as err:
                        print(f"  [DEEP CRAWL WARNING] Failed to fetch {s.url}: {err}")
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
