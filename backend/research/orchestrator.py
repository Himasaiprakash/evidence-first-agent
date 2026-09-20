import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from backend.models.schemas import (
    ResearchWorkspace, Source, RejectedSource, DocumentChunk, Claim, RejectedClaim, Entity, Conflict,
    ResearchPlan, QualityScore, ResearchChallenge, ObjectiveStatus
)
from backend.research.planner import ResearchPlanner
from backend.research.source_strategy import SourceStrategy
from backend.research.discovery.web import WebDiscovery
from backend.research.discovery.academic import AcademicDiscovery
from backend.research.relevance.source_gate import SourceRelevanceGate
from backend.research.relevance.claim_gate import ClaimRelevanceGate
from backend.research.ingestion.chunker import DocumentChunker
from backend.research.extraction.entities import EntityExtractor
from backend.research.extraction.claims import ClaimExtractor
from backend.research.verification.conflicts import ConflictAnalyzer
from backend.research.coverage.analyzer import CoverageAnalyzer
from backend.research.challenge.research_challenger import ResearchChallenger
from backend.research.reporting.compiler import ReportCompiler
from backend.services.knowledge_graph import KnowledgeGraphService

class AutonomousResearchOrchestrator:
    """
    Genuine Recursive Autonomous Research Orchestrator:
    - Multi-Pass Recursive Loop: Automatically researches its own detected gaps until evidence satisfies objectives
    - Strict Multi-Tier Relevance Gates for sources & claims
    - Precision Conflict Analyzer (eliminates version/year false conflicts)
    - Full Evidence Provenance & Measurable Quality Metrics
    """
    def __init__(self):
        self.planner = ResearchPlanner()
        self.strategy = SourceStrategy()
        self.web_discovery = WebDiscovery()
        self.academic_discovery = AcademicDiscovery()
        self.source_gate = SourceRelevanceGate()
        self.claim_gate = ClaimRelevanceGate()
        self.chunker = DocumentChunker()
        self.entity_extractor = EntityExtractor()
        self.claim_extractor = ClaimExtractor()
        self.conflict_analyzer = ConflictAnalyzer()
        self.coverage_analyzer = CoverageAnalyzer()
        self.challenger = ResearchChallenger()
        self.report_compiler = ReportCompiler()
        self.kg_service = KnowledgeGraphService()

    def run_research(self, topic: str, goal: str = "Understand and Build", depth: str = "Comprehensive", max_passes: int = 3) -> ResearchWorkspace:
        workspace_id = f"ws-{uuid.uuid4().hex[:8]}"
        clean_topic = topic.strip()

        # Step 1: Domain-Specific Research Planning
        plan = self.planner.plan(clean_topic, user_goal=goal)

        acquired_sources_map: Dict[str, Source] = {}
        all_rejected_sources: List[RejectedSource] = []
        all_chunks: List[DocumentChunk] = []
        all_claims: List[Claim] = []
        all_rejected_claims: List[RejectedClaim] = []
        saturation_history: List[int] = []

        seen_urls: Set[str] = set()

        # ===================================================================
        # RECURSIVE MULTI-PASS RESEARCH LOOP
        # ===================================================================
        for pass_num in range(1, max_passes + 1):
            # Formulate queries for this pass
            if pass_num == 1:
                queries = self.strategy.get_queries(clean_topic, plan.domain)
            else:
                # Targeted gap search queries for any weak or missing objectives
                gap_objs = [o for o in plan.objectives if o.status in [ObjectiveStatus.GAP, ObjectiveStatus.WEAK]]
                if not gap_objs:
                    # All objectives satisfied!
                    break
                queries = []
                for obj in gap_objs[:3]:
                    queries.append(f"{clean_topic} {obj.name} benchmark evaluation mechanism")
                    queries.append(f"{clean_topic} {obj.name} architecture failure modes")

            # Execute discovery
            raw_sources: List[Source] = []
            
            # Canonical & Subtopic Encyclopedia
            if pass_num == 1:
                wiki_sources = self.web_discovery.search_wikipedia_multi(clean_topic, plan.domain)
                raw_sources.extend(wiki_sources)

            # Academic arXiv discovery
            for q in queries[:2]:
                q_str = q.get("query", clean_topic) if isinstance(q, dict) else str(q)
                arxiv_sources = self.academic_discovery.search_arxiv(q_str, domain=plan.domain, max_results=3)
                raw_sources.extend(arxiv_sources)

            # Targeted web search
            for q in queries[:3]:
                q_str = q.get("query", clean_topic) if isinstance(q, dict) else str(q)
                web_sources = self.web_discovery.search_duckduckgo(q_str, max_results=3)
                raw_sources.extend(web_sources)

            # Deduplicate by URL
            unique_raw: List[Source] = []
            for s in raw_sources:
                if s.url not in seen_urls:
                    seen_urls.add(s.url)
                    unique_raw.append(s)

            # Source Relevance Gate (P0)
            accepted, rejected = self.source_gate.filter_sources(clean_topic, plan.domain, unique_raw)
            all_rejected_sources.extend(rejected)

            for s in accepted:
                acquired_sources_map[s.id] = s

            # Ingestion & Chunking
            new_chunks = self.chunker.chunk_sources(accepted)
            all_chunks.extend(new_chunks)

            # Dynamic Claim Extraction
            current_sources = list(acquired_sources_map.values())
            raw_claims = self.claim_extractor.extract_claims(clean_topic, current_sources, all_chunks)

            # Claim Relevance Gate (P0)
            accepted_claims, rejected_claims = self.claim_gate.filter_claims(clean_topic, plan.domain, raw_claims)
            all_rejected_claims.extend(rejected_claims)
            all_claims = accepted_claims

            saturation_history.append(len(all_claims))

            # Evaluate Coverage Matrix
            conflicts = self.conflict_analyzer.analyze_conflicts(all_claims, current_sources)
            plan, open_gaps, quality, saturation_score = self.coverage_analyzer.evaluate_coverage(
                plan=plan,
                claims=all_claims,
                sources=current_sources,
                conflicts_count=len(conflicts),
                saturation_history=saturation_history
            )

            # If required objectives are satisfied, exit recursive loop
            if quality.coverage >= 90.0 and len(open_gaps) == 0:
                break

        # Final Evaluation after Recursive Loop
        final_sources = list(acquired_sources_map.values())
        entities = self.entity_extractor.extract_entities(clean_topic, final_sources, all_chunks)
        conflicts = self.conflict_analyzer.analyze_conflicts(all_claims, final_sources)

        plan, open_gaps, quality, saturation_score = self.coverage_analyzer.evaluate_coverage(
            plan=plan,
            claims=all_claims,
            sources=final_sources,
            conflicts_count=len(conflicts),
            saturation_history=saturation_history
        )

        total_raw_count = len(final_sources) + len(all_rejected_sources)
        total_raw_claims = len(all_claims) + len(all_rejected_claims)
        
        quality.topic_relevance_rate = round((len(final_sources) / max(total_raw_count, 1)) * 100, 1)
        quality.claim_relevance_rate = round((len(all_claims) / max(total_raw_claims, 1)) * 100, 1)

        # Adversarial Research Challenger
        challenge = self.challenger.challenge(plan, all_claims, final_sources)

        # Lifecycle Status Determination
        if quality.coverage >= 85.0 and len(open_gaps) == 0:
            final_status = "COMPLETED"
        elif quality.coverage >= 60.0:
            final_status = "NEEDS_EXPANSION"
        else:
            final_status = "PARTIAL"

        # Property Knowledge Graph
        graph = self.kg_service.build_from_workspace(clean_topic, entities, all_claims, final_sources)

        # Report Compilation
        report = self.report_compiler.compile_report(
            topic=clean_topic,
            goal=goal,
            plan=plan,
            sources=final_sources,
            entities=entities,
            claims=all_claims,
            conflicts=conflicts,
            challenge=challenge,
            quality=quality,
            open_gaps=open_gaps
        )

        return ResearchWorkspace(
            id=workspace_id,
            topic=clean_topic,
            goal=goal,
            status=final_status,
            depth=depth,
            created_at=datetime.now().isoformat(),
            plan=plan,
            quality=quality,
            sources=final_sources,
            rejected_sources=all_rejected_sources,
            chunks=all_chunks,
            claims=all_claims,
            rejected_claims=all_rejected_claims,
            entities=entities,
            conflicts=conflicts,
            graph=graph,
            report=report,
            open_gaps=open_gaps,
            saturation_history=saturation_history,
            saturation_score=saturation_score,
            challenge=challenge
        )
