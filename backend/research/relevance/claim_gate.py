from typing import List, Tuple
from backend.models.schemas import Claim, RejectedClaim, RelevanceLevel, DomainType

class ClaimRelevanceGate:
    """
    Strict Claim Relevance Gate:
    - Ensures extracted claims are genuinely about the target subject
    - Filters out peripheral sentences or cross-domain noise
    """
    def filter_claims(self, topic: str, domain: DomainType, claims: List[Claim]) -> Tuple[List[Claim], List[RejectedClaim]]:
        accepted_claims: List[Claim] = []
        rejected_claims: List[RejectedClaim] = []

        topic_clean = topic.strip().lower()
        topic_words = [w for w in topic_clean.split() if len(w) > 2]
        stems = [w.rstrip("s").rstrip("ing") for w in topic_words if len(w) > 2]

        GENERIC_STOP_WORDS = {"model", "models", "comparison", "comparisons", "system", "systems", "approach", "study", "analysis", "framework"}
        distinctive_topic_words = [w for w in topic_words if w not in GENERIC_STOP_WORDS]

        for c in claims:
            claim_text = (c.subject + " " + c.predicate + " " + c.object_value + " " + (c.evidence.exact_quote or "")).lower()

            # 1. Biological cross-contamination filter
            if domain == DomainType.MEDICINE_BIOLOGY:
                ai_terms = ["data protection", "data controller", "vqa", "neural network", "privacy control", "artificial intelligence", "visual question", "critical thinking", "image retrieval", "exag"]
                if any(t in claim_text for t in ai_terms) and not any(w in claim_text for w in topic_words):
                    rejected_claims.append(RejectedClaim(
                        id=c.id,
                        subject=c.subject,
                        predicate=c.predicate,
                        object_value=c.object_value,
                        source_id=c.evidence.source_id,
                        reason=f"Cross-domain topic mismatch: claim discusses software/AI concepts instead of biological topic '{topic}'.",
                        relevance_score=0.02
                    ))
                    continue

            # 2. AI domain cross-contamination filter
            if domain == DomainType.AI_TECHNOLOGY:
                off_domain_ai = ["chemotherapy", "oncology", "surgical", "histopathology", "psychological safety", "cardiac", "patient survival"]
                ai_terms = ["llm", "language model", "transformer", "neural", "benchmark", "reasoning", "coding", "inference", "prompt", "token", "agent", "gpt", "claude", "gemini", "swe-bench", "bfcl", "latency", "cost", "throughput"]
                if any(t in claim_text for t in off_domain_ai) and not any(t in claim_text for t in ai_terms):
                    rejected_claims.append(RejectedClaim(
                        id=c.id,
                        subject=c.subject,
                        predicate=c.predicate,
                        object_value=c.object_value,
                        source_id=c.evidence.source_id,
                        reason=f"Off-domain claim lacking AI/LLM relevance: mentions clinical or unrelated workplace terms.",
                        relevance_score=0.02
                    ))
                    continue

            # 3. Match distinctive topic words or recognized domain terms
            if distinctive_topic_words:
                has_topic_match = any(w in claim_text for w in distinctive_topic_words)
            else:
                has_topic_match = any(w in claim_text for w in topic_words)

            has_domain_term = any(t in claim_text for t in [
                "gpt-4", "gpt-4o", "claude", "gemini", "llama", "swe-bench", "bfcl", "gpqa", "mmlu",
                "tokens/s", "token", "latency", "ttft", "prompt caching", "context window",
                "transformer", "attention", "cardiac", "valve", "qubit", "quantum"
            ])

            if has_topic_match or has_domain_term:
                c.relevance_score = 0.95 if has_topic_match else 0.85
                c.relevance_level = RelevanceLevel.DIRECT if has_topic_match else RelevanceLevel.RELATED
                accepted_claims.append(c)
            else:
                rejected_claims.append(RejectedClaim(
                    id=c.id,
                    subject=c.subject,
                    predicate=c.predicate,
                    object_value=c.object_value,
                    source_id=c.evidence.source_id,
                    reason=f"Claim does not mention core topic keywords or recognized domain terms.",
                    relevance_score=0.15
                ))

        return accepted_claims, rejected_claims
