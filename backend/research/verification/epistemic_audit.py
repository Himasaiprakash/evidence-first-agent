from typing import List
from backend.models.schemas import ResearchWorkspace, BoundClaim, EpistemicReport, FactStatus
from backend.research.authority_gating import authority_gate


class ProgrammaticEpistemicAuditor:
    """
    Programmatic Epistemic Auditor (Anti-Metadata Theater):
    - Calculates mathematical verification scores (0.0 to 10.0) from actual empirical test results.
    - Eliminates LLM-generated fake metadata labels (e.g. "PRODUCTION EVIDENCE: VERIFIED").
    - Assigns hard, non-deceptive verdicts ("VALID" vs "INVALID / UNVERIFIED").
    """

    def audit(self, workspace: ResearchWorkspace, bound_claims: List[BoundClaim], research_id: str) -> EpistemicReport:
        total_reqs = len(workspace.plan.objectives) if workspace.plan and workspace.plan.objectives else 6
        verified_bound_claims = [c for c in bound_claims if c.verification_status == FactStatus.VERIFIED]
        
        tier1_primary_claims = [c for c in verified_bound_claims if c.source_tier >= 0.90]

        # 1. Calculate Coverage Score (0.0 to 1.0)
        reqs_covered = min(total_reqs, len(verified_bound_claims))
        coverage_rate = reqs_covered / max(1, total_reqs)

        # 2. Calculate Tier 1 Primary Authority Ratio
        primary_ratio = len(tier1_primary_claims) / max(1, len(verified_bound_claims))

        # 3. Calculate Mean Entailment Score
        mean_entailment = (sum(c.entailment_score for c in verified_bound_claims) / len(verified_bound_claims)) if verified_bound_claims else 0.0

        # 4. Calculate Final Composite Epistemic Score (0.0 to 10.0)
        composite_score = (coverage_rate * 4.0) + (primary_ratio * 4.0) + (mean_entailment * 2.0)
        final_score = round(min(10.0, composite_score), 1)

        # 5. Strict Hard Verdict Rules
        # To get a VALID verdict:
        # - Final score must be >= 6.5
        # - Primary ratio must be >= 0.40 (At least 40% Tier 1/2 sources)
        # - Must have at least 3 verified bound claims
        if final_score >= 6.5 and primary_ratio >= 0.40 and len(verified_bound_claims) >= 3:
            verdict = "VALID (Empirically Bound & Verified)"
        else:
            verdict = "INVALID / UNVERIFIED (Insufficient Primary Evidence)"

        return EpistemicReport(
            final_score=final_score,
            verdict=verdict,
            coverage_rate=f"{coverage_rate * 100:.1f}%",
            tier1_primary_ratio=f"{primary_ratio * 100:.1f}%",
            verified_claims_count=len(verified_bound_claims),
            unbound_claims_count=len(workspace.claims) - len(verified_bound_claims),
            unresolved_conflicts_count=len(workspace.conflicts),
            research_id=research_id
        )


# Global Epistemic Auditor Singleton
epistemic_auditor = ProgrammaticEpistemicAuditor()
