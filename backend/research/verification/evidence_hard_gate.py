import re
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from backend.models.schemas import Claim, Source, SourceCategory
from backend.research.extraction.canonical_entity_gate import CanonicalEntityProfile, CanonicalResolutionResult

class EvidenceAuditVerdict(BaseModel):
    is_valid: bool
    verdict_code: str  # "ACCEPTED" | "REJECT_ENTITY_MISMATCH" | "REJECT_METRIC_MISMATCH" | "REJECT_NUMERICAL_UNBOUND" | "REJECT_TIER3_AGGREGATOR" | "REJECT_SPECULATIVE_FILLER"
    reason: str
    retained_claim: Optional[Claim] = None

class UniversalEvidenceHardGate:
    """
    Phase 2: Universal Evidence Hard-Gate Auditor (All Domains)
    - Enforces strict deterministic verification rules before any claim is accepted into evidence
    - Tests for Entity Mismatch, Relative Metric Extrapolation, Numerical Unbound Hallucinations,
      and Tier-3 Aggregator Pollution
    - Prunes unrequested speculative filler
    """
    def __init__(self):
        pass

    def audit_claim(
        self,
        claim: Claim,
        sources_dict: Dict[str, Source],
        resolution: CanonicalResolutionResult
    ) -> EvidenceAuditVerdict:
        """
        Audits a single empirical claim against its supporting source and canonical resolution.
        """
        # 1. Source Availability Check
        src_id = claim.evidence.source_id
        source = sources_dict.get(src_id)
        if not source:
            return EvidenceAuditVerdict(
                is_valid=False,
                verdict_code="REJECT_SOURCE_NOT_FOUND",
                reason=f"Claim cites source {src_id} which does not exist in workspace."
            )

        src_text = (source.title + " " + (source.raw_content or "")).lower()

        # 2. Speculative Filler & Unrequested Entity Check
        claim_full_str = f"{claim.subject} {claim.predicate} {claim.object_value}".lower()
        for unreq in resolution.unrequested_speculative_topics:
            if re.search(rf"\b{re.escape(unreq.lower())}\b", claim_full_str):
                return EvidenceAuditVerdict(
                    is_valid=False,
                    verdict_code="REJECT_SPECULATIVE_FILLER",
                    reason=f"Claim discusses unrequested entity/topic: '{unreq}'"
                )

        # 3. Tier-3 Aggregator Check for Quantitative Claims
        has_numeric = bool(re.search(r'\d+(?:\.\d+)?%?|\$\d+', claim.object_value))
        if has_numeric and source.authority_score < 70.0:
            return EvidenceAuditVerdict(
                is_valid=False,
                verdict_code="REJECT_TIER3_AGGREGATOR",
                reason=f"Quantitative claim sourced from low-authority aggregator {source.author_publisher} (Auth: {source.authority_score:.1f})"
            )

        # 4. Universal Entity Mismatch Check
        # Check if the claim mentions an entity family (e.g. GPT, Claude, Gemini, PostgreSQL, Llama)
        # but specifies a variant/version that does NOT match the resolved canonical entity
        for entity in resolution.entities:
            family = entity.query_term.lower() if entity.query_term else entity.canonical_name.split()[0].lower()
            if family and family in claim_full_str:
                allowed_identifiers = [entity.canonical_name.lower()] + [i.lower() for i in entity.active_identifiers]
                clean_name = re.sub(r'^(OpenAI|Anthropic|Google|Meta|Microsoft|Alibaba)\s+', '', entity.canonical_name, flags=re.IGNORECASE).lower()
                allowed_identifiers.append(clean_name)

                has_allowed = any(ai in claim_full_str for ai in allowed_identifiers)
                if not has_allowed:
                    # Check if claim specifies another numbered/named version
                    other_version = re.search(rf"\b{re.escape(family)}[-_ ]*([0-9]+(?:\.[0-9]+)?|[a-z]+[-_ ]*[0-9]+(?:\.[0-9]+)?)\b", claim_full_str)
                    if other_version:
                        ver_str = other_version.group(0)
                        if not any(ai in ver_str for ai in allowed_identifiers):
                            return EvidenceAuditVerdict(
                                is_valid=False,
                                verdict_code="REJECT_ENTITY_MISMATCH",
                                reason=f"Claim cites variant '{ver_str}' which does not match resolved canonical entity '{entity.canonical_name}'."
                            )

        # 5. Metric Mismatch & Relative-to-Absolute Check
        if "% of top score" in src_text or "relative" in src_text:
            if claim.predicate in ["accuracy", "pass_rate", "score"] and "%" in claim.object_value and not any(k in claim.object_value.lower() for k in ["relative", "top score"]):
                return EvidenceAuditVerdict(
                    is_valid=False,
                    verdict_code="REJECT_METRIC_MISMATCH",
                    reason="Source provides relative leaderboard comparison; claim improperly asserts absolute percentage without formula/denominator."
                )

        # 6. Verbatim Numerical Binding Check
        if has_numeric:
            # Extract raw numbers from object_value
            nums = re.findall(r'\b\d+(?:\.\d+)?\b', claim.object_value)
            for n in nums:
                # Disregard single-digit integers (like 1, 2) that can appear anywhere
                if len(n) > 1 and n not in (source.raw_content or "") and n not in source.title:
                    return EvidenceAuditVerdict(
                        is_valid=False,
                        verdict_code="REJECT_NUMERICAL_UNBOUND",
                        reason=f"Numerical value '{n}' does not exist verbatim in primary source {src_id}."
                    )

        # Passed all hard gates
        return EvidenceAuditVerdict(
            is_valid=True,
            verdict_code="ACCEPTED",
            reason="Passed entity matching, metric integrity, verbatim numerical binding, and authority tier verification.",
            retained_claim=claim
        )

    def filter_claims_hard_gate(
        self,
        claims: List[Claim],
        sources: List[Source],
        resolution: CanonicalResolutionResult
    ) -> Tuple[List[Claim], List[Tuple[Claim, str]]]:
        """
        Filters all extracted claims through the universal hard gate.
        Returns (accepted_claims, list_of_rejected_tuples).
        """
        sources_dict = {s.id: s for s in sources}
        accepted: List[Claim] = []
        rejected: List[Tuple[Claim, str]] = []

        for c in claims:
            verdict = self.audit_claim(c, sources_dict, resolution)
            if verdict.is_valid and verdict.retained_claim:
                accepted.append(verdict.retained_claim)
            else:
                rejected.append((c, f"{verdict.verdict_code}: {verdict.reason}"))

        return accepted, rejected
