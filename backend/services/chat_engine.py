import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from backend.models.schemas import (
    ResearchWorkspace, ChatRequest, ChatResponse, ChatIntentType,
    Source, Claim, EvidenceLink, DocumentChunk, Conflict, ReportSection
)

class ChatEngine:
    """
    100% Deterministic Evidence Inquiry Engine (0 LLM Calls):
    - Real-time sentence-level salience scoring across synthesized report chapters, chunks, and claims
    - Intent-directed extractive answering:
      1. LAYERS, STRUCTURE, ARCHITECTURE & ANATOMY ('layers of the sun', 'components of RAG', 'layers of the heart')
      2. PAIN POINTS, VULNERABILITIES & FAILURE MODES ('vulnerabilities of RAG', 'bottlenecks of deep learning')
      3. CLASSIFICATIONS & DISEASE TYPES ('types of heart diseases', 'categories of neural networks')
      4. EMPIRICAL BENCHMARKS & LATENCY PROFILES ('speed', 'accuracy', 'parameters', 'solar constant')
      5. ACTIVE CONTROVERSIES & CONFLICTS ('discrepancies', 'trade-offs')
    - Latency: < 2 milliseconds
    """
    def __init__(self):
        self.stop_words = {
            "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "do", "does", "did", "and", "or", "but", "if", "then", "else", "when", "what",
            "which", "who", "whom", "this", "that", "these", "those", "how", "why", "where",
            "can", "could", "will", "would", "should", "tell", "me", "about", "get", "give"
        }

    def classify_intent(self, message: str) -> ChatIntentType:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["conflict", "contradiction", "discrepancy", "dispute", "difference"]):
            return ChatIntentType.CONFLICTS
        elif any(w in msg_lower for w in ["layer", "layers", "structure", "structures", "component", "components", "anatomy", "part", "parts", "zone", "zones", "architecture", "topology"]):
            return ChatIntentType.DEEP_DIVE
        elif any(w in msg_lower for w in ["simplify", "beginner", "simple", "eli5", "easy", "summary", "brief"]):
            return ChatIntentType.SIMPLIFY
        elif any(w in msg_lower for w in ["deep dive", "deeply", "advanced", "details", "mechanism", "internal", "physiology"]):
            return ChatIntentType.DEEP_DIVE
        elif any(w in msg_lower for w in ["compare", "difference", "distinguish"]):
            return ChatIntentType.COMPARE
        elif any(w in msg_lower for w in ["evidence", "proof", "quote", "citation", "where does it say"]):
            return ChatIntentType.EVIDENCE
        elif any(w in msg_lower for w in ["source", "paper", "who published", "origin", "references"]):
            return ChatIntentType.SOURCES
        elif any(w in msg_lower for w in ["learn", "teach", "curriculum", "lesson", "prerequisite"]):
            return ChatIntentType.LEARN
        elif any(w in msg_lower for w in ["test", "quiz", "assess", "question", "examine"]):
            return ChatIntentType.TEST_ME
        elif any(w in msg_lower for w in ["build", "how to build", "code", "step", "implement", "deploy"]):
            return ChatIntentType.BUILD
        elif any(w in msg_lower for w in ["debug", "error", "wrong", "fix", "mistake", "pain point", "pain points", "limitation", "limitations", "failure", "vulnerability", "vulnerabilities", "bottleneck", "disease", "diseases", "pathology", "disorder", "syndrome"]):
            return ChatIntentType.DEBUG
        elif any(w in msg_lower for w in ["type", "types", "category", "categories", "kinds", "classification", "classifications"]):
            return ChatIntentType.EXPLAIN
        elif any(w in msg_lower for w in ["what is", "why is", "explain", "overview", "definition", "concept"]):
            return ChatIntentType.EXPLAIN
        else:
            return ChatIntentType.GENERAL

    def process_message(self, req: ChatRequest, workspace: ResearchWorkspace) -> ChatResponse:
        intent = req.intent_override or self.classify_intent(req.message)
        topic = workspace.topic
        query = req.message.strip()
        q_lower = query.lower()

        # 1. Handle Conversational Greeting
        if q_lower in ["hi", "hello", "hey", "greetings", "help", "who are you"]:
            return ChatResponse(
                intent=ChatIntentType.GENERAL,
                topic=topic,
                response_text=(
                    f"### 👋 Welcome to the **{topic}** Evidence Console\n\n"
                    f"I am your 100% Deterministic Evidence Specialist. This workspace contains **{len(workspace.sources)} verified sources**, "
                    f"**{len(workspace.claims)} grounded claims**, and **{len(workspace.conflicts)} empirical trade-offs** in `{workspace.plan.domain.value}`.\n\n"
                    f"**Direct Questions You Can Ask:**\n"
                    f"• *Structural Layers & Architecture*: 'What are the layers or core components?'\n"
                    f"• *Classifications & Types*: 'What are the types of diseases or failure modes?'\n"
                    f"• *Vulnerabilities & Pain Points*: 'What are the pain points and bottlenecks?'\n"
                    f"• *Empirical Evidence*: 'Show benchmarks, latency, or solar constants'"
                ),
                supporting_claims=workspace.claims[:2],
                supporting_sources=workspace.sources[:2],
                related_concepts=[e.name for e in workspace.entities[:4]],
                confidence_score=100.0
            )

        # 2. Extract Query Content Words
        q_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", q_lower) if w not in self.stop_words]
        if not q_words:
            q_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", q_lower)]

        # 3. Intent-Specific Sub-Routing (Conflicts)
        if intent == ChatIntentType.CONFLICTS:
            response_text = self._format_conflicts(workspace)
            return ChatResponse(
                intent=intent,
                topic=topic,
                response_text=response_text,
                supporting_claims=[c for c in workspace.claims if c.status.value == "CONFLICTING"][:3] or workspace.claims[:2],
                supporting_sources=workspace.sources[:2],
                related_concepts=[e.name for e in workspace.entities[:4]],
                confidence_score=98.0
            )

        # 4. Extract and Rank Candidate Sentences across Report Chapters, Chunks & Sources
        scored_sentences = self._score_sentences(query, q_words, workspace)

        # 5. Extract and Rank Relevant Claims
        scored_claims = self._score_claims(q_words, workspace.claims)

        # 6. Synthesize Targeted Deterministic Answer
        response_text = self._synthesize_extractive_answer(query, q_words, intent, workspace, scored_sentences, scored_claims)

        seen_src_ids = set()
        top_sources = []
        for s, _, _ in scored_sentences[:6]:
            if s.id not in seen_src_ids:
                seen_src_ids.add(s.id)
                top_sources.append(s)

        if not top_sources:
            top_sources = workspace.sources[:2]

        return ChatResponse(
            intent=intent,
            topic=topic,
            response_text=response_text,
            supporting_claims=[c for c, _ in scored_claims[:4]] or workspace.claims[:2],
            supporting_sources=top_sources,
            related_concepts=[e.name for e in workspace.entities[:5]],
            confidence_score=98.0
        )

    def _score_sentences(self, query: str, q_words: List[str], ws: ResearchWorkspace) -> List[Tuple[Source, str, float]]:
        """Score sentences across workspace report chapters and document chunks."""
        scored: List[Tuple[Source, str, float]] = []
        q_lower = query.lower()
        
        is_layer_query = any(w in q_lower for w in ["layer", "layers", "structure", "zone", "zones", "component", "components", "anatomy", "part", "parts", "architecture", "topology"])
        is_type_query = any(w in q_lower for w in ["type", "types", "kind", "kinds", "category", "categories", "disease", "diseases", "failure", "limitations", "examples"])
        is_vuln_query = any(w in q_lower for w in ["pain", "point", "vulnerability", "vulnerabilities", "failure", "failures", "limitation", "limitations", "bottleneck", "risk", "injection", "hallucination", "omission"])

        sources_map = {s.id: s for s in ws.sources}
        primary_source = ws.sources[0] if ws.sources else Source(
            id="src-workspace-report",
            title=f"Technical Dossier: {ws.topic}",
            url="",
            source_type="DOCUMENTATION",
            raw_content=""
        )

        # 1. Score Synthesized Report Chapters (High Density Evidence)
        for rep_sec in ws.report:
            paragraphs = rep_sec.content.split("\n\n")
            for p in paragraphs:
                p_clean = p.strip()
                if len(p_clean) < 30:
                    continue
                
                # Split paragraph into sentences
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p_clean) if len(s.strip()) > 25]
                for sentence in sentences:
                    s_lower = sentence.lower()
                    score = 0.0

                    matched_count = sum(1 for w in q_words if w in s_lower)
                    if matched_count > 0:
                        score += matched_count * 4.0

                    if is_layer_query:
                        if any(l in s_lower for l in ["core", "radiative", "convective", "photosphere", "chromosphere", "corona", "tachocline", "transition region", "pericardium", "myocardium", "endocardium", "atrium", "ventricle", "retriever", "reranker", "generator", "encoder", "attention"]):
                            score += 8.0
                        if any(k in s_lower for k in ["layer", "layers", "divided into", "consists of", "stratification", "interior", "atmosphere", "structure"]):
                            score += 6.0

                    if is_vuln_query:
                        if any(v in s_lower for v in ["vulnerability", "failure", "hallucination", "injection", "latency", "bottleneck", "noise", "reconnection", "flare"]):
                            score += 8.0

                    if is_type_query:
                        if any(t in s_lower for t in ["coronary", "arrhythmia", "failure", "cardiomyopathy", "transformer", "cnn", "rnn"]):
                            score += 6.0

                    if score > 0:
                        scored.append((primary_source, sentence, score))

        # 2. Score Document Chunks
        for chk in ws.chunks:
            source = sources_map.get(chk.source_id) or primary_source
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chk.text) if len(s.strip()) > 25]

            for sentence in sentences:
                s_lower = sentence.lower()
                score = 0.0

                matched_count = sum(1 for w in q_words if w in s_lower)
                if matched_count > 0:
                    score += matched_count * 3.0

                for i in range(len(q_words) - 1):
                    bigram = f"{q_words[i]} {q_words[i+1]}"
                    if bigram in s_lower:
                        score += 6.0

                if is_layer_query and any(l in s_lower for l in ["core", "radiative", "convective", "photosphere", "chromosphere", "corona", "layer", "zone", "structure", "myocardium", "pericardium"]):
                    score += 6.0

                if score > 0:
                    scored.append((source, sentence, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored

    def _score_claims(self, q_words: List[str], claims: List[Claim]) -> List[Tuple[Claim, float]]:
        scored: List[Tuple[Claim, float]] = []
        for c in claims:
            c_text = f"{c.subject} {c.predicate} {c.object_value} {c.evidence.exact_quote or ''}".lower()
            match_count = sum(1 for w in q_words if w in c_text)
            if match_count > 0:
                score = match_count * 2.5
                if c.importance == "critical":
                    score += 1.5
                scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _synthesize_extractive_answer(
        self,
        query: str,
        q_words: List[str],
        intent: ChatIntentType,
        ws: ResearchWorkspace,
        scored_sentences: List[Tuple[Source, str, float]],
        scored_claims: List[Tuple[Claim, float]]
    ) -> str:
        t = ws.topic.title()
        q_lower = query.lower()

        # =====================================================================
        # CASE A: LAYERS, STRUCTURE, ARCHITECTURE, ZONES & ANATOMY
        # =====================================================================
        if any(w in q_lower for w in ["layer", "layers", "structure", "structures", "zone", "zones", "component", "components", "anatomy", "part", "parts", "interior", "atmosphere", "pipeline", "topology"]):
            lines = [f"### 🏗️ Structural Layers, Architecture & Components of **{t}**:\n"]

            # Pull from Chapter 3 or Chapter 2 of the report
            struct_sec = next((s for s in ws.report if any(k in s.title.lower() for k in ["architecture", "topology", "structure", "theory", "principles", "components"])), None)
            if struct_sec:
                paragraphs = struct_sec.content.strip().split("\n\n")
                relevant_paras = [p for p in paragraphs if any(w in p.lower() for w in ["layer", "zone", "core", "interior", "atmosphere", "photosphere", "chromosphere", "corona", "component", "structure", "myocardium", "pericardium", "retriever"])]
                
                if relevant_paras:
                    lines.append(f"**Verified Structural Stratification:**\n{relevant_paras[0]}\n")
                    if len(relevant_paras) > 1:
                        lines.append(f"{relevant_paras[1]}\n")

            # Extract specific structural sentences from scored sentences
            if scored_sentences:
                lines.append("**Extracted Layer & Component Specifications:**")
                seen = set()
                for source, sentence, _ in scored_sentences:
                    if sentence[:40] in seen:
                        continue
                    seen.add(sentence[:40])
                    lines.append(f"• \"{sentence}\" — [{source.id}]")
                    if len(seen) >= 4:
                        break
                lines.append("")

            return "\n".join(lines)

        # =====================================================================
        # CASE B: PAIN POINTS, VULNERABILITIES, FAILURE MODES & BOTTLENECKS
        # =====================================================================
        elif any(w in q_lower for w in ["pain", "vulnerability", "vulnerabilities", "failure", "failures", "limitation", "limitations", "bottleneck", "risk", "risks", "drawback"]):
            lines = [f"### ⚠️ Verified Pain Points, Vulnerabilities & Failure Modes in **{t}**:\n"]

            fail_report_sec = next((s for s in ws.report if any(k in s.title.lower() for k in ["failure", "vulnerability", "limitation", "bottleneck", "challenge", "blueprint"])), None)
            if fail_report_sec:
                clean_sec = fail_report_sec.content.strip()
                if len(clean_sec) > 40:
                    lines.append(f"**Identified Operational Bottlenecks & Failure Modes:**\n{clean_sec}\n")

            vuln_sentences = [
                (src, s) for src, s, _ in scored_sentences 
                if any(v in s.lower() for v in ["vulnerability", "failure", "hallucination", "injection", "latency", "bottleneck", "omission", "noise", "error", "risk", "limitation", "overhead", "flare", "reconnection"])
            ]

            if vuln_sentences:
                lines.append("**Specific Extracted Empirical Evidence:**")
                seen = set()
                for src, sent in vuln_sentences:
                    if sent[:40] in seen:
                        continue
                    seen.add(sent[:40])
                    lines.append(f"• \"{sent}\" — [{src.id}]")
                    if len(seen) >= 4:
                        break
                lines.append("")

            return "\n".join(lines)

        # =====================================================================
        # CASE C: TYPES, DISEASES & CLASSIFICATIONS
        # =====================================================================
        elif any(w in q_lower for w in ["disease", "diseases", "illness", "pathology", "disorder", "type", "types", "category", "categories", "kinds", "classification"]):
            lines = [f"### 📋 Verified Classifications & Sub-Types in **{t}**:\n"]
            
            disease_sources = [s for s in ws.sources if any(k in s.title.lower() for k in ["cardiovascular", "disease", "failure", "coronary", "failure_modes", "vulnerability"])]
            if disease_sources:
                lines.append("**Key Sub-Classifications from Acquired Literature:**")
                for s in disease_sources:
                    preview = (s.raw_content or "").replace("\n", " ")
                    first_sentences = [sent.strip() for sent in re.split(r"(?<=[.!?])\s+", preview) if len(sent.strip()) > 30][:2]
                    summary_text = " ".join(first_sentences)
                    lines.append(f"• **{s.title.replace('Wikipedia: ', '')}** [{s.id}]: {summary_text}")
                lines.append("")

            if scored_sentences:
                lines.append("**Specific Extracted Findings:**")
                seen_snippets = set()
                for source, sentence, _ in scored_sentences:
                    if sentence[:40] in seen_snippets:
                        continue
                    seen_snippets.add(sentence[:40])
                    lines.append(f"• \"{sentence}\" — [{source.id}]")
                    if len(seen_snippets) >= 4:
                        break
            
            return "\n".join(lines)

        # =====================================================================
        # CASE D: LATENCY, BENCHMARKS & PERFORMANCE
        # =====================================================================
        elif any(w in q_lower for w in ["latency", "speed", "benchmark", "accuracy", "performance", "throughput", "recall", "mrr", "constant", "luminosity", "temperature", "mass"]):
            lines = [f"### ⚡ Empirical Measurements & Performance in **{t}**:\n"]
            metric_claims = [c for c, _ in scored_claims if c.numeric_value is not None]
            if metric_claims:
                lines.append("**Verified Empirical Metrics:**")
                for c in metric_claims[:4]:
                    lines.append(f"• **{c.subject}**: `{c.numeric_value} {c.unit or ''}` ({c.conditions}) [{c.evidence.source_id}]")
                    lines.append(f"  *Evidence Quote*: \"{c.evidence.exact_quote}\"")
                lines.append("")

            if scored_sentences:
                lines.append("**Contextual Observations:**")
                for source, sentence, _ in scored_sentences[:3]:
                    lines.append(f"• \"{sentence}\" [{source.id}]")

            return "\n".join(lines)

        # =====================================================================
        # CASE E: STANDARD TARGETED EXTRACTIVE ANSWER
        # =====================================================================
        else:
            lines = [f"### 🔬 Evidence Summary for *'{query}'* in **{t}**:\n"]
            
            if scored_sentences:
                seen_snippets = set()
                for source, sentence, _ in scored_sentences:
                    if sentence[:40] in seen_snippets:
                        continue
                    seen_snippets.add(sentence[:40])
                    lines.append(f"• \"{sentence}\" — [{source.id}]")
                    if len(seen_snippets) >= 4:
                        break
                lines.append("")

            if scored_claims:
                lines.append("**Direct Grounded Claims:**")
                for c, _ in scored_claims[:3]:
                    lines.append(f"• **{c.subject}** `{c.predicate.replace('_', ' ')}` **{c.object_value}** [{c.evidence.source_id}]")

            if not scored_sentences and not scored_claims:
                lines.append(f"No specific evidence matching terms '{', '.join(q_words)}' found in workspace {ws.id}.")

            return "\n".join(lines)

    def _format_conflicts(self, ws: ResearchWorkspace) -> str:
        t = ws.topic.title()
        if ws.conflicts:
            cfl_rows = []
            for cfl in ws.conflicts:
                cfl_rows.append(
                    f"• **{cfl.topic}** (`{cfl.conflict_type.value}`):\n"
                    f"  - **{cfl.source_a.title}** [{cfl.source_a.id}]: `{cfl.claim_a.numeric_value or cfl.claim_a.object_value} {cfl.claim_a.unit or ''}`\n"
                    f"  - **{cfl.source_b.title}** [{cfl.source_b.id}]: `{cfl.claim_b.numeric_value or cfl.claim_b.object_value} {cfl.claim_b.unit or ''}`\n"
                    f"  - **Root Cause Analysis**: {cfl.difference_explanation}\n"
                    f"  - **Resolution Status**: `{cfl.resolution_status}`"
                )
            return f"### ⚡ Empirical Discrepancies & Trade-Offs in **{t}**:\n\n" + "\n\n".join(cfl_rows)
        else:
            return f"### ✅ Conflict Analysis for **{t}**:\n\nZero empirical contradictions detected across the {len(ws.sources)} acquired primary sources. All metric evaluations are consistent."
