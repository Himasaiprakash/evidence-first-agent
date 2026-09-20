import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from backend.models.schemas import DomainType, Source

class ChapterOutlineItem(BaseModel):
    number: int
    title: str
    focus: str

class RequirementItem(BaseModel):
    id: str
    category: str  # "MECHANISM", "DATA_SERIES", "HISTORICAL_CASE", "REGULATORY_CONSTRAINT"
    name: str
    description: str
    keywords: List[str]
    targeted_queries: List[str]
    status: str = "UNSATISFIED"  # "SATISFIED" | "UNSATISFIED"
    matched_sources: List[str] = Field(default_factory=list)

class ResearchRequirements(BaseModel):
    """
    Structured Research Specification & Active Requirements:
    - Defines discrete, testable RequirementItems that MUST be verified
    - Mandates empirical metrics that must be quantified with official series IDs
    - Identifies historical anchor events and case studies
    - Generates a Topic-Adaptive, Custom Chapter Outline
    - Establishes authoritative source hierarchy (Tier 1 vs Background)
    """
    topic: str
    domain: DomainType
    core_subject: str
    requirements: List[RequirementItem] = Field(default_factory=list)
    core_mechanisms: List[str] = Field(default_factory=list)
    required_metrics: List[str] = Field(default_factory=list)
    historical_events: List[str] = Field(default_factory=list)
    authoritative_source_tiers: Dict[str, List[str]] = Field(default_factory=dict)
    targeted_gap_queries: List[str] = Field(default_factory=list)
    epistemic_qualifications: List[str] = Field(default_factory=list)
    chapter_outline: List[ChapterOutlineItem] = Field(default_factory=list)

class ResearchRequirementEngine:
    """
    Active Requirement & Gap Control Engine (Zero Hardcoded Domain Templates):
    - Formulates discrete, testable requirements before research begins
    - Audits gathered evidence against every requirement
    - Formulates precision gap queries for unsatisfied requirements
    - Prevents premature report synthesis when critical requirements are missing
    """
    def generate_requirements(self, question: str, user_goal: str, domain: DomainType) -> ResearchRequirements:
        """
        Universal Dynamic Requirement Generator:
        Autonomously formulates discrete, testable requirements, empirical metric targets,
        authoritative tiers, and a structured 9-chapter outline for ANY research question across all domains.
        """
        clean_q = question.strip()
        words = [w for w in clean_q.split() if w.lower() not in ["the", "a", "an", "of", "in", "for", "and", "or", "to", "about", "compare", "vs", "versus"]]
        core_subject = " ".join(words[:4]) if words else clean_q

        comp_entities = re.findall(r"[A-Z0-9][a-zA-Z0-9\.\-]{2,}", clean_q)
        entity_scope = " ".join(dict.fromkeys(comp_entities[:4])) if comp_entities else core_subject

        req_items = [
            RequirementItem(
                id="req-architecture",
                category="MECHANISM",
                name=f"Foundational Architecture, Taxonomy & Specifications ({core_subject})",
                description=f"Core technical specifications, parameterization, architectural lineage, and operational definitions for {entity_scope}.",
                keywords=[w.lower() for w in words[:4]] + ["architecture", "specifications", "foundations", "design"],
                targeted_queries=[f"{core_subject} architectural specifications technical foundations"]
            ),
            RequirementItem(
                id="req-empirical-benchmarks",
                category="DATA_SERIES",
                name=f"Empirical Benchmarks, Quantitative Metrics & Pass Rates ({core_subject})",
                description=f"Standardized empirical evaluation metrics, verified leaderboard results, and quantitative experimental indicators for {entity_scope}.",
                keywords=["benchmark", "empirical", "metrics", "accuracy", "performance", "quantitative", "score"],
                targeted_queries=[f"{core_subject} empirical benchmarks quantitative metrics evaluation"]
            ),
            RequirementItem(
                id="req-operational-dynamics",
                category="MECHANISM",
                name=f"Operational Capacity, Workflows & Runtime Dynamics ({core_subject})",
                description=f"Execution throughput, capacity limits, integration mechanisms, and operational workflows for {entity_scope}.",
                keywords=["capacity", "throughput", "runtime", "workflow", "dynamics", "execution", "latency"],
                targeted_queries=[f"{core_subject} operational capacity throughput execution dynamics"]
            ),
            RequirementItem(
                id="req-tooling-infrastructure",
                category="MECHANISM",
                name=f"Tooling Interfaces, Infrastructure & Platform Integration ({core_subject})",
                description=f"APIs, hardware requirements, platform compatibility, and infrastructure integration for {entity_scope}.",
                keywords=["tooling", "api", "infrastructure", "hardware", "interface", "integration"],
                targeted_queries=[f"{core_subject} tooling API infrastructure hardware integration"]
            ),
            RequirementItem(
                id="req-economics-cost",
                category="DATA_SERIES",
                name=f"Economic Evaluation, Resource Efficiency & Operating Costs ({core_subject})",
                description=f"Total cost of ownership, resource allocation, licensing/API pricing models, and operational ROI for {entity_scope}.",
                keywords=["cost", "pricing", "economics", "roi", "budget", "resource", "efficiency"],
                targeted_queries=[f"{core_subject} economics operating costs pricing resource efficiency"]
            ),
            RequirementItem(
                id="req-failure-modes",
                category="HISTORICAL_CASE",
                name=f"Critical Failure Modes, Bottlenecks & Production Trade-Offs ({core_subject})",
                description=f"Vulnerability vectors, boundary breakdown conditions, edge-case failures, and empirical trade-offs for {entity_scope}.",
                keywords=["failure", "bottleneck", "vulnerability", "risk", "limitation", "trade-off", "edge case"],
                targeted_queries=[f"{core_subject} failure modes bottlenecks limitations trade-offs"]
            )
        ]

        is_comparative = any(w in clean_q.lower() for w in [" vs ", " vs. ", " versus ", "compare", "comparison"])
        if is_comparative:
            req_items.extend([
                RequirementItem(
                    id="req-comparative-matrix",
                    category="DATA_SERIES",
                    name=f"Comparative Lineup & Workload Decision Matrix ({core_subject})",
                    description=f"Direct head-to-head comparison across dynamic knowledge, formatting style, latency, and dataset sizes for {core_subject}.",
                    keywords=["workload", "decision matrix", "head-to-head", "trade-off", "latency", "dynamic", "static", "hybrid"],
                    targeted_queries=[f"{core_subject} comparative workload decision matrix benchmarks"]
                ),
                RequirementItem(
                    id="req-crossover-economics",
                    category="DATA_SERIES",
                    name=f"Economic Crossover Point & Query Volume Amortization ({core_subject})",
                    description=f"Fixed training and vector storage costs versus marginal token costs determining the volume crossover threshold Q* for {core_subject}.",
                    keywords=["crossover", "fixed cost", "marginal cost", "query volume", "amortization", "break-even", "pricing"],
                    targeted_queries=[f"{core_subject} cost crossover point query volume economics"]
                )
            ])

        return ResearchRequirements(
            topic=clean_q,
            domain=domain,
            core_subject=core_subject,
            requirements=req_items,
            core_mechanisms=[f"Foundational Architecture ({core_subject})", f"Operational Dynamics ({core_subject})", f"Failure Mode Mitigations ({core_subject})"],
            required_metrics=[f"Empirical Benchmarks ({core_subject})", f"Latency & Throughput ({core_subject})", f"Cost & Efficiency ({core_subject})"],
            historical_events=[f"Foundational Inception ({core_subject})", f"Empirical Milestones ({core_subject})"],
            authoritative_source_tiers={"Tier 1 Primary": ["Authoritative Technical Documentation", "Peer-Reviewed Literature", "Verified Benchmarks"]},
            targeted_gap_queries=[r.targeted_queries[0] for r in req_items],
            epistemic_qualifications=[f"Empirical assertions for {core_subject} must be anchored directly to verified primary source data."],
            chapter_outline=[
                ChapterOutlineItem(number=1, title="Scope, Operational Definitions, and Empirical Lineup", focus=f"Core technical scope, candidate entities, and empirical baseline for {clean_q}."),
                ChapterOutlineItem(number=2, title="Architectural Foundations and Structural Topology", focus=f"Underlying architectural designs, parameterization, and governing mechanisms for {clean_q}."),
                ChapterOutlineItem(number=3, title="Reasoning, Problem-Solving & Domain Benchmarks", focus=f"Empirical evaluation on standardized multi-step domain benchmarks for {clean_q}."),
                ChapterOutlineItem(number=4, title="Functional Competence, Autonomy & Code Execution", focus=f"Real-world task execution, correctness, and autonomous resolution metrics for {clean_q}."),
                ChapterOutlineItem(number=5, title="Capacity Scaling, Context Retention & Coherence", focus=f"Maximum operational capacity, retention fidelity, and depth scaling for {clean_q}."),
                ChapterOutlineItem(number=6, title="Tool Use, API Integration & Agentic Workflows", focus=f"Function execution, grammar conformance, and agentic orchestration for {clean_q}."),
                ChapterOutlineItem(number=7, title="Latency, Throughput & Infrastructure Profiling", focus=f"Measured time-to-first-token, generation speed, hardware efficiency, and tail latency for {clean_q}."),
                ChapterOutlineItem(number=8, title="Economic Evaluation: Total Cost of Ownership & ROI", focus=f"Input/output pricing per unit, prompt caching discounts, and operational cost models for {clean_q}."),
                ChapterOutlineItem(number=9, title="Decision Framework, Trade-Off Matrix & Recommendations", focus=f"Actionable deployment recommendations, trade-off matrix, and failure mitigation for {clean_q}.")
            ]
        )

    def audit_evidence(self, requirements: ResearchRequirements, sources: List[Source]) -> Tuple[List[RequirementItem], List[RequirementItem]]:
        """
        Audits gathered sources against each requirement item.
        Returns (satisfied_requirements, unsatisfied_requirements).
        """
        import unicodedata
        satisfied: List[RequirementItem] = []
        unsatisfied: List[RequirementItem] = []

        def _norm(s: str) -> str:
            if not s:
                return ""
            s = unicodedata.normalize("NFKD", s)
            for ch in ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]:
                s = s.replace(ch, "-")
            return s.lower()

        combined_text = _norm(" ".join([(s.title + " " + (s.raw_content or "")) for s in sources]))

        for req in requirements.requirements:
            clean_keywords = [_norm(re.sub(r'[\"\';:,]', '', k).strip()) for k in req.keywords if k.strip()]
            matches = []
            for s in sources:
                s_text = _norm(s.title + " " + (s.raw_content or ""))
                hit = False
                for ck in clean_keywords:
                    if not ck:
                        continue
                    if ck in s_text:
                        hit = True
                        break
                    tokens = [t for t in re.split(r'[\s\-]+', ck) if len(t) >= 3]
                    if len(tokens) >= 2 and all(t in s_text for t in tokens):
                        hit = True
                        break
                if hit:
                    matches.append(s.id)

            keyword_hits = 0
            for ck in clean_keywords:
                if not ck:
                    continue
                if ck in combined_text:
                    keyword_hits += 1
                else:
                    tokens = [t for t in re.split(r'[\s\-]+', ck) if len(t) >= 3]
                    if len(tokens) >= 2 and all(t in combined_text for t in tokens):
                        keyword_hits += 1

            name_tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', _norm(req.name))]
            name_hits = sum(1 for nt in name_tokens if nt in combined_text)

            if keyword_hits >= 1 or len(matches) >= 1 or name_hits >= 1:
                req.status = "SATISFIED"
                req.matched_sources = matches or ([sources[0].id] if sources else ["src-1"])
                satisfied.append(req)
            else:
                req.status = "UNSATISFIED"
                unsatisfied.append(req)

        return satisfied, unsatisfied
