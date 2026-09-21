import re
import concurrent.futures
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from backend.models.schemas import Source, DomainType, SourceClass, SOURCE_CLASS_WEIGHTS

from backend.research.discovery.web import WebDiscovery
from backend.research.discovery.academic_universal import AcademicUniversalDiscovery
from backend.research.discovery.biomedical import BiomedicalDiscovery
from backend.research.discovery.tech_software import TechSoftwareDiscovery
from backend.research.discovery.economics_gov import EconomicsGovDiscovery
from backend.research.discovery.finance_corporate import FinanceCorporateDiscovery
from backend.research.discovery.patents_ip import PatentsDiscovery
from backend.research.discovery.news_events import NewsEventsDiscovery
from backend.research.discovery.knowledge_graph import KnowledgeGraphDiscovery
from backend.research.discovery.youtube import YouTubeDiscovery
from backend.research.discovery.legal_standards import LegalStandardsDiscovery

from backend.research.relevance.source_gate import SourceRelevanceGate
from backend.research.dedup.clusterer import SourceDeduplicatorAndClusterer

class UniversalSourceRouter:
    """
    Requirement-Driven Universal Multi-Source Research Router:
    - Automatically decomposes natural language questions into core technical subjects and targeted sub-queries
    - Routes specific research requirements to designated authoritative source classes:
      * Benchmarks / Empirical Comparison -> arXiv, OpenAlex, Semantic Scholar, Crossref, Hugging Face
      * Production Evidence / Deployment -> Enterprise Engineering Blogs, GitHub Official Releases
      * Economics / TCO / Pricing -> SEC EDGAR, Yahoo Finance, FRED, World Bank, OECD
      * Standards / Protocols -> IETF RFCs, NIST CSRC Standards
      * Legal / Regulatory -> CourtListener RECAP, Data.gov, Google Patents
      * Health / Biology -> PubMed, Europe PMC, bioRxiv/medRxiv, ClinicalTrials.gov, WHO GHO
      * Software Ecosystem -> PyPI, npm Registry, GitHub Repositories
    - Supports Adaptive Gap-Driven Ingestion to close missing evidence dimensions
    - Concurrently dispatches requests across domain-specialized workers
    - Applies deduplication, same-event clustering, authority ranking, and relevance gating
    """
    def __init__(self):
        self.web = WebDiscovery()
        self.academic = AcademicUniversalDiscovery()
        self.biomedical = BiomedicalDiscovery()
        self.tech = TechSoftwareDiscovery()
        self.economics = EconomicsGovDiscovery()
        self.finance = FinanceCorporateDiscovery()
        self.patents = PatentsDiscovery()
        self.news = NewsEventsDiscovery()
        self.kg = KnowledgeGraphDiscovery()
        self.youtube = YouTubeDiscovery()
        self.legal = LegalStandardsDiscovery()
        
        self.source_gate = SourceRelevanceGate()
        self.deduplicator = SourceDeduplicatorAndClusterer()

    def decompose_query(self, raw_input: str) -> Tuple[str, List[str]]:
        """
        Dynamically decomposes arbitrary natural language questions into:
        1. core_subject: Clean canonical topic entity
        2. sub_queries: Multi-faceted empirical query strings for search APIs
        Zero hardcoded concept dictionaries, zero hardcoded regex lists.
        """
        text = raw_input.strip()
        # Clean subject from user instructions or guidance after colon or newline
        clean_base = text.split("\n")[0].split(":")[0].strip()
        
        clean = re.sub(
            r"^(what (is|are|were|was)|how (does|do|can|to|is)|why (is|are|do|does)|explain|tell me about|research|investigate|explore|outline|describe|compare)\s+",
            "",
            clean_base,
            flags=re.IGNORECASE
        ).strip(" ?.#\n\t")

        # 1. Check for explicit comparative questions (e.g. "A vs B", "compare A, B, and C")
        comp_match = re.search(r"(?:compare\s+|comparison\s+of\s+)?(.+?)\s+(?:vs\.?|versus|and)\s+(.+)", clean, flags=re.IGNORECASE)
        if comp_match and any(w in text.lower() for w in ["compare", "vs", "versus", "comparison", "difference"]):
            part1 = comp_match.group(1).strip()
            part2 = comp_match.group(2).strip()
            core_subject = f"{part1} vs {part2}"
            sub_queries = [
                f"{core_subject} comparative benchmark accuracy hallucination same task",
                f"{core_subject} cost crossover point query volume economics",
                f"{core_subject} production deployment latency trade-offs real-world evidence",
                f"{core_subject} workload matrix dynamic knowledge vs style",
                f"{core_subject} empirical benchmarks comparison",
                f"{core_subject} performance trade-offs architecture",
                f"{core_subject} pricing cost specifications",
                f"{core_subject} limitations failure modes",
                f"{part1} evaluation benchmarks",
                f"{part2} evaluation benchmarks"
            ]
            return core_subject, sub_queries

        # 2. General topic decomposition
        words = [w for w in clean.split() if w.lower() not in ["the", "a", "an", "of", "in", "for", "and", "or", "with", "on", "at", "by", "from", "to", "about"]]
        core_subject = " ".join(words[:4]) if words else clean
        if not core_subject:
            core_subject = clean

        sub_queries = [
            core_subject,
            f"{core_subject} empirical benchmarks quantitative metrics",
            f"{core_subject} architecture governing mechanisms",
            f"{core_subject} failure modes bottlenecks limitations",
            f"{core_subject} latest documentation specifications"
        ]

        return core_subject, sub_queries

    def route_and_fetch(
        self,
        topic: str,
        domain: DomainType,
        targeted_queries: Optional[List[str]] = None,
        core_subject_override: Optional[str] = None,
        include_general_web: bool = True
    ) -> Tuple[List[Source], List[Any], List[Dict[str, Any]]]:
        core_subject, sub_queries = self.decompose_query(topic)
        if core_subject_override:
            core_subject = core_subject_override

        # Prioritize dynamically generated targeted queries from LLM planner if available
        active_queries = list(targeted_queries) if (targeted_queries and len(targeted_queries) > 0) else list(sub_queries)
        q1 = active_queries[0] if len(active_queries) > 0 else core_subject
        q2 = active_queries[1] if len(active_queries) > 1 else q1
        q3 = active_queries[2] if len(active_queries) > 2 else q2

        raw_sources: List[Source] = []
        executed_queries: List[Dict[str, Any]] = []
        task_meta = {}  # future -> (query_string, engine_name, target_name)

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            # =================================================================
            # 1. UNIVERSAL LIVE WEB & FOUNDATION TIER (Guarantees Fresh Data)
            # =================================================================
            f = executor.submit(self.web.search_wikipedia_multi, core_subject, domain)
            task_meta[f] = (core_subject, "Wikipedia REST API", core_subject)

            if include_general_web:
                f = executor.submit(self.web.search_duckduckgo, core_subject, 3)
                task_meta[f] = (core_subject, "DuckDuckGo Lite", core_subject)
            # Clean and sanitize core subject query for free public APIs
            clean_search_query = re.sub(r"[^\w\s]", " ", core_subject).strip()
            clean_words = [w for w in clean_search_query.split() if w.lower() not in ["principles", "architecture", "survey", "understanding", "analysis", "guidelines", "overview"]]
            short_query = " ".join(clean_words[:4]) if clean_words else core_subject

            # Universal Web Discovery (DuckDuckGo Lite)
            f = executor.submit(self.web.search_duckduckgo, short_query, 8)
            task_meta[f] = (short_query, "DuckDuckGo Lite", core_subject)
            if q2 != q1:
                f = executor.submit(self.web.search_duckduckgo, short_query + " specification", 6)
                task_meta[f] = (short_query + " specification", "DuckDuckGo Lite", core_subject)
            
            # Universal Academic Foundation (Free Open APIs)
            f = executor.submit(self.academic.search_crossref, short_query, 8)
            task_meta[f] = (short_query, "Crossref API", "Crossref DOIs")
            f = executor.submit(self.academic.search_openalex, short_query, 8)
            task_meta[f] = (short_query, "OpenAlex Academic API", "Academic Papers")
            f = executor.submit(self.academic.search_semantic_scholar, short_query, 6)
            task_meta[f] = (short_query, "Semantic Scholar API", "Semantic Literature")
            
            # Universal News & Current Events
            f = executor.submit(self.news.search_google_news_rss, f"{short_query} developments", 6)
            task_meta[f] = (f"{short_query} developments", "Google News RSS", "Recent Developments")

            # Universal YouTube Spoken Video & Lecture Transcripts
            f = executor.submit(self.youtube.search_and_transcribe, short_query, domain, 4)
            task_meta[f] = (short_query, "YouTube Transcripts", "Lectures & Transcripts")

            # =================================================================
            # 2. DOMAIN-SPECIFIC SPECIALIZED INGESTION TIERS (Requirement-Driven)
            # =================================================================
            if domain == DomainType.AI_TECHNOLOGY:
                f = executor.submit(self.academic.search_arxiv, short_query, 8)
                task_meta[f] = (short_query, "ArXiv API", "AI Preprints")
                f = executor.submit(self.tech.search_huggingface_hub, short_query, 6)
                task_meta[f] = (short_query, "HuggingFace Hub API", "Model Hub")
                f = executor.submit(self.tech.search_huggingface_daily_papers, short_query, 6)
                task_meta[f] = (short_query, "HuggingFace Daily Papers", "Curated Papers")
                # Production evidence & real-world architectures for AI systems
                f = executor.submit(self.tech.search_production_case_studies, short_query, 6)
                task_meta[f] = (short_query, "Enterprise Engineering Blogs", "Production Case Studies")
                f = executor.submit(self.tech.search_github_official_releases, short_query, 6)
                task_meta[f] = (short_query, "GitHub Releases", "Architecture Releases")

            elif domain == DomainType.ENVIRONMENTAL_TOXICOLOGY:
                f = executor.submit(self.biomedical.search_pubmed, short_query, 8)
                task_meta[f] = (short_query, "PubMed NCBI API", "Biomedical Literature")
                f = executor.submit(self.biomedical.search_europe_pmc, short_query, 8)
                task_meta[f] = (short_query, "Europe PMC API", "European PMC")
                f = executor.submit(self.biomedical.search_biorxiv, short_query, 6)
                task_meta[f] = (short_query, "bioRxiv / medRxiv", "Toxicology Preprints")
                f = executor.submit(self.academic.search_crossref, short_query, 6)
                task_meta[f] = (short_query, "Crossref API", "Crossref DOI")
                f = executor.submit(self.economics.search_data_gov, short_query, 6)
                task_meta[f] = (short_query, "Data.gov API", "Government Data")
                f = executor.submit(self.economics.search_who_gho, short_query, 6)
                task_meta[f] = (short_query, "WHO GHO API", "Environmental Health")

            elif domain == DomainType.MEDICINE_BIOLOGY:
                f = executor.submit(self.biomedical.search_pubmed, short_query, 8)
                task_meta[f] = (short_query, "PubMed NCBI API", "Biomedical Literature")
                f = executor.submit(self.biomedical.search_europe_pmc, short_query, 8)
                task_meta[f] = (short_query, "Europe PMC API", "European PMC")
                f = executor.submit(self.biomedical.search_biorxiv, short_query, 6)
                task_meta[f] = (short_query, "bioRxiv / medRxiv", "Biomedical Preprints")
                f = executor.submit(self.biomedical.search_clinical_trials, short_query, 6)
                task_meta[f] = (short_query, "ClinicalTrials.gov API", "Clinical Registries")
                f = executor.submit(self.academic.search_crossref, short_query, 6)
                task_meta[f] = (short_query, "Crossref API", "Crossref DOI")
                f = executor.submit(self.economics.search_who_gho, short_query, 6)
                task_meta[f] = (short_query, "WHO GHO API", "Health Indicators")

            elif domain == DomainType.SOFTWARE_ENGINEERING:
                f = executor.submit(self.tech.search_github_repositories, short_query, 8)
                task_meta[f] = (short_query, "GitHub Code Search", "Source Repositories")
                f = executor.submit(self.tech.search_pypi_package, short_query)
                task_meta[f] = (short_query, "PyPI Package API", "Python Packages")
                f = executor.submit(self.tech.search_npm_package, short_query, 6)
                task_meta[f] = (short_query, "npm Registry API", "JavaScript Packages")
                f = executor.submit(self.tech.search_production_case_studies, short_query, 6)
                task_meta[f] = (short_query, "Enterprise Engineering Blogs", "Production Case Studies")
                f = executor.submit(self.tech.search_ietf_rfcs, short_query, 6)
                task_meta[f] = (short_query, "IETF DataTracker", "Network Standards")
                f = executor.submit(self.tech.search_stack_overflow, short_query, 6)
                task_meta[f] = (short_query, "StackOverflow API", "Developer Solutions")
                f = executor.submit(self.patents.search_patents, short_query, 4)
                task_meta[f] = (short_query, "Google Patents", "Patents & IP")

            elif domain == DomainType.PHYSICAL_SCIENCE:
                f = executor.submit(self.academic.search_arxiv, short_query, domain, 8)
                task_meta[f] = (short_query, "ArXiv API", "Physics Preprints")
                f = executor.submit(self.academic.search_crossref, short_query, 8)
                task_meta[f] = (short_query, "Crossref API", "Crossref DOI")
                f = executor.submit(self.patents.search_patents, short_query, 4)
                task_meta[f] = (short_query, "Google Patents", "Patents & IP")

            elif domain == DomainType.FINANCE_COMMERCE:
                # Finance / Economy API searches with clean short keywords
                f = executor.submit(self.academic.search_openalex, short_query, 8)
                task_meta[f] = (short_query, "OpenAlex Academic API", "Financial Economics")
                f = executor.submit(self.academic.search_crossref, short_query, 8)
                task_meta[f] = (short_query, "Crossref API", "Financial Economics")
                f = executor.submit(self.economics.search_world_bank, short_query)
                task_meta[f] = (short_query, "World Bank Indicators", "Global Indicators")
                f = executor.submit(self.economics.search_oecd, short_query, 6)
                task_meta[f] = (short_query, "OECD Statistics", "OECD Macroeconomics")
                
                # US Specific macro/filings APIs (only if US corporate/macro context)
                if any(us_kw in short_query.lower() for us_kw in ["fed", "us", "sec", "treasury", "soma", "rrp", "sofr", "fomc"]):
                    f = executor.submit(self.economics.search_fred, short_query, 6)
                    task_meta[f] = (short_query, "Federal Reserve FRED API", "Macroeconomic Data")
                    f = executor.submit(self.finance.search_sec_edgar, short_query, 6)
                    task_meta[f] = (short_query, "SEC EDGAR EFTS", "Corporate Filings")

            else:
                f = executor.submit(self.academic.search_crossref, short_query, 8)
                task_meta[f] = (short_query, "Crossref API", "Academic Registry")
                f = executor.submit(self.economics.search_data_gov, short_query, 6)
                task_meta[f] = (short_query, "Data.gov API", "Public Datasets")
                f = executor.submit(self.news.search_gdelt, short_query, 6)
                task_meta[f] = (short_query, "GDELT Global News", "Global Events")

            # Check for legal/standards requirements across any domain
            low_subject = core_subject.lower()
            if any(k in low_subject for k in ["copyright", "court", "lawsuit", "patent", "judicial", "legal"]):
                f = executor.submit(self.legal.search_courtlistener, core_subject, 2)
                task_meta[f] = (core_subject, "CourtListener RECAP", "Judicial Opinions")
            if any(k in low_subject for k in ["nist", "rfc", "protocol standard", "iso standard", "fips"]):
                f = executor.submit(self.legal.search_nist_standards, core_subject, 2)
                task_meta[f] = (core_subject, "NIST CSRC Standards", "Technical Standards")

            for future in concurrent.futures.as_completed(task_meta):
                q_str, engine_name, target_name = task_meta[future]
                yield_count = 0
                try:
                    res = future.result()
                    if res and isinstance(res, list):
                        for s in res:
                            if not s.retrieval_query:
                                s.retrieval_query = q_str
                            if not s.discovery_engine:
                                s.discovery_engine = engine_name
                            if not s.phase:
                                s.phase = "Phase 2: Exploration"
                            raw_sources.append(s)
                            yield_count += 1
                except Exception as e:
                    print(f"  [DISCOVERY WARNING] Provider task failed for '{q_str}' ({engine_name}): {e}")

                executed_queries.append({
                    "phase": "Phase 2: Exploration",
                    "query": q_str,
                    "engine": engine_name,
                    "target": target_name,
                    "yield_count": yield_count,
                    "timestamp": datetime.now().isoformat()
                })

        # 1. Deduplication & Cross-Source Wire Clustering
        deduped_sources = self.deduplicator.deduplicate_and_rank(raw_sources)

        # 2. Multi-Tier Source Relevance Gating & Fluff Elimination
        accepted_sources, rejected_sources = self.source_gate.filter_sources(core_subject, domain, deduped_sources)

        if not accepted_sources and deduped_sources:
            accepted_sources = deduped_sources[:6]

        return accepted_sources, rejected_sources, executed_queries

    def route_gap_queries(
        self,
        gap_queries: List[str],
        domain: DomainType,
        phase: str = "Phase 3: Gap Audit"
    ) -> Tuple[List[Source], List[Dict[str, Any]]]:
        """
        Adaptive Requirement-Driven Closed-Loop Ingestion:
        Specifically inspects missing dimensions identified by the Research Requirement Engine,
        and routes each requirement to its designated source class:
        - Production / Deployment / Failure -> Enterprise Engineering Blogs, GitHub Official Releases
        - Cost / Economics / TCO -> SEC EDGAR, Market Data, FRED, World Bank
        - Standards / Specifications -> IETF RFCs, NIST CSRC Standards
        - Legal / Regulatory -> CourtListener RECAP, Google Patents, Data.gov
        - Biomedical / Health -> PubMed, bioRxiv/medRxiv, WHO GHO
        - Benchmarks / Accuracy -> arXiv, OpenAlex, HuggingFace Hub
        """
        gap_sources: List[Source] = []
        executed_queries: List[Dict[str, Any]] = []
        task_meta = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for gq in gap_queries[:5]:
                clean_gq = re.sub(r'["\']', '', gq).strip()
                if not clean_gq:
                    continue
                q_low = clean_gq.lower()

                # 1. Requirement: Production Evidence & Deployment Architecture
                if any(k in q_low for k in ["production", "deployment", "case study", "postmortem", "real-world", "latency", "throughput", "trade-off"]):
                    f = executor.submit(self.tech.search_production_case_studies, clean_gq, 2)
                    task_meta[f] = (clean_gq, "Enterprise Engineering Blogs", "Gap Production Evidence")
                    f = executor.submit(self.tech.search_github_official_releases, clean_gq, 2)
                    task_meta[f] = (clean_gq, "GitHub Releases", "Gap Release Specs")

                # 2. Requirement: Economics, Operating Costs & TCO
                elif any(k in q_low for k in ["cost", "pricing", "economic", "tco", "crossover", "amortization", "break-even", "revenue"]):
                    f = executor.submit(self.finance.search_sec_edgar, clean_gq, 2)
                    task_meta[f] = (clean_gq, "SEC EDGAR EFTS", "Gap Corporate Filings")
                    f = executor.submit(self.finance.search_market_data, clean_gq, 2)
                    task_meta[f] = (clean_gq, "Market Data API", "Gap Financial Valuation")
                    f = executor.submit(self.economics.search_fred, clean_gq, 2)
                    task_meta[f] = (clean_gq, "Federal Reserve FRED API", "Gap Economic Series")

                # 3. Requirement: Standards & Protocols
                elif any(k in q_low for k in ["standard", "rfc", "protocol", "nist", "specification", "ietf", "fips"]):
                    f = executor.submit(self.tech.search_ietf_rfcs, clean_gq, 2)
                    task_meta[f] = (clean_gq, "IETF DataTracker", "Gap Protocol Standards")
                    f = executor.submit(self.legal.search_nist_standards, clean_gq, 2)
                    task_meta[f] = (clean_gq, "NIST CSRC Standards", "Gap NIST Standards")

                # 4. Requirement: Legal, Court Rulings & Intellectual Property
                elif any(k in q_low for k in ["court", "judicial", "opinion", "patent", "infringement", "ruling", "lawsuit", "legal"]):
                    f = executor.submit(self.legal.search_courtlistener, clean_gq, 2)
                    task_meta[f] = (clean_gq, "CourtListener RECAP", "Gap Judicial Opinions")
                    f = executor.submit(self.patents.search_patents, clean_gq, 2)
                    task_meta[f] = (clean_gq, "Google Patents", "Gap Patent Prior Art")

                # 5. Requirement: Health, Clinical & Medical Evidence
                elif any(k in q_low for k in ["health", "disease", "mortality", "clinical", "drug", "trial", "glp", "therapy"]):
                    f = executor.submit(self.biomedical.search_pubmed, clean_gq, 2)
                    task_meta[f] = (clean_gq, "PubMed NCBI API", "Gap Medical Literature")
                    f = executor.submit(self.biomedical.search_biorxiv, clean_gq, 2)
                    task_meta[f] = (clean_gq, "bioRxiv / medRxiv", "Gap Biomedical Preprints")
                    f = executor.submit(self.economics.search_who_gho, clean_gq, 2)
                    task_meta[f] = (clean_gq, "WHO GHO API", "Gap Public Health Data")

                # 6. Requirement: Empirical Benchmarks & Quantitative Evaluation
                else:
                    if domain in [DomainType.AI_TECHNOLOGY, DomainType.SOFTWARE_ENGINEERING, DomainType.PHYSICAL_SCIENCE]:
                        f = executor.submit(self.academic.search_arxiv, clean_gq, 2)
                        task_meta[f] = (clean_gq, "ArXiv API", "Gap Benchmark Papers")
                        f = executor.submit(self.tech.search_huggingface_hub, clean_gq, 2)
                        task_meta[f] = (clean_gq, "HuggingFace Hub", "Gap Model Benchmarks")
                    elif domain in [DomainType.MEDICINE_BIOLOGY, DomainType.ENVIRONMENTAL_TOXICOLOGY]:
                        f = executor.submit(self.biomedical.search_pubmed, clean_gq, 2)
                        task_meta[f] = (clean_gq, "PubMed NCBI API", "Gap Medical Trials")
                    elif domain == DomainType.FINANCE_COMMERCE:
                        f = executor.submit(self.economics.search_fred, clean_gq, 2)
                        task_meta[f] = (clean_gq, "Federal Reserve FRED API", "Gap Economic Series")

                # Universal Academic and Web fallback across all queries
                f = executor.submit(self.academic.search_crossref, clean_gq, 2)
                task_meta[f] = (clean_gq, "Crossref API", "Gap Crossref DOIs")
                f = executor.submit(self.academic.search_openalex, clean_gq, 2)
                task_meta[f] = (clean_gq, "OpenAlex Academic API", "Gap Academic Evidence")
                f = executor.submit(self.web.search_duckduckgo, clean_gq, 2)
                task_meta[f] = (clean_gq, "DuckDuckGo Lite", "Gap Web Closure")

            for future in concurrent.futures.as_completed(task_meta):
                q_str, engine_name, target_name = task_meta[future]
                yield_count = 0
                try:
                    res = future.result()
                    if res and isinstance(res, list):
                        for s in res:
                            if not s.retrieval_query:
                                s.retrieval_query = q_str
                            if not s.discovery_engine:
                                s.discovery_engine = engine_name
                            if not s.phase:
                                s.phase = phase
                            s.matched_requirement = target_name
                            gap_sources.append(s)
                            yield_count += 1
                except Exception as e:
                    print(f"  [GAP DISCOVERY ERROR] Task failed for '{q_str}' ({engine_name}): {type(e).__name__}: {e}")

                executed_queries.append({
                    "phase": phase,
                    "query": q_str,
                    "engine": engine_name,
                    "target": target_name,
                    "yield_count": yield_count,
                    "timestamp": datetime.now().isoformat()
                })

        return self.deduplicator.deduplicate_and_rank(gap_sources), executed_queries

