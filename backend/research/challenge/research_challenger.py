from typing import List
from backend.models.schemas import Claim, Source, ResearchPlan, ResearchChallenge, ObjectiveStatus

class ResearchChallenger:
    """
    Adversarial Research Challenger:
    - Scrutinizes the knowledge base before finalizing
    - Flags claims that depend entirely on a single source
    - Detects ungrounded overgeneralizations
    - Issues an adversarial verdict on research soundness
    """
    def challenge(self, plan: ResearchPlan, claims: List[Claim], sources: List[Source]) -> ResearchChallenge:
        single_source_claims = sum(1 for c in claims if len(c.supporting_source_ids) <= 1)
        weak_evidence_claims = sum(1 for c in claims if c.evidence.confidence < 0.90)

        potential_overgeneralizations = []
        for c in claims:
            if any(w in (c.subject + " " + c.predicate + " " + c.object_value).lower() for w in ["always", "never", "all", "impossible", "optimal"]):
                potential_overgeneralizations.append(
                    f"Claim '{c.id}' makes an absolute assertion ('{c.subject} {c.predicate} {c.object_value}') that may overlook edge-case configurations."
                )

        missing_dimensions = [
            f"Dimension '{obj.name}' has status '{obj.status.value}'"
            for obj in plan.objectives if obj.status in [ObjectiveStatus.GAP, ObjectiveStatus.WEAK]
        ]

        if len(missing_dimensions) > 2 or (len(claims) < 3):
            verdict = "NEEDS_EXPANSION"
        elif single_source_claims > (len(claims) * 0.7):
            verdict = "QUESTIONABLE"
        else:
            verdict = "SOUND"

        return ResearchChallenge(
            single_source_claims_count=single_source_claims,
            weak_evidence_claims_count=weak_evidence_claims,
            potential_overgeneralizations=potential_overgeneralizations[:3],
            missing_dimensions=missing_dimensions[:3],
            adversarial_verdict=verdict
        )
