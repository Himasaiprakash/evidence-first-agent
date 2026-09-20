import re
from typing import List, Dict, Optional
from backend.models.schemas import Claim, Source, Conflict, ConflictType, FactStatus

class ConflictAnalyzer:
    """
    Precision Empirical Conflict & Trade-Off Analyzer:
    - Strictly compares like-for-like empirical metrics (e.g., latency in ms vs ms, recall in % vs %)
    - Explicitly filters out false-positive numeric comparisons:
      * Software version numbers (v1.0, 3.1, 4.0)
      * Calendar years (2024, 2025, 2026)
      * Section / Step numbering (Step 1, Section 2)
      * Dimensionality (768-dim, 1536)
      * Count of unrelated entities
    - Only flags true empirical discrepancies or workload-conditioned trade-offs
    """

    VALID_METRIC_UNITS = {
        "latency": ["ms", "milliseconds", "s", "seconds", "us", "microseconds"],
        "accuracy_quality": ["%", "percent", "accuracy", "recall", "precision", "mrr", "ndcg", "f1", "bleu", "rouge", "hit@k", "recall@k"],
        "throughput": ["qps", "rps", "queries/sec", "tokens/s", "tokens/sec", "req/s", "samples/s"],
        "resource": ["gb", "mb", "kb", "tb", "vram", "ram", "cores", "gpus"],
        "efficiency": ["joules", "watts", "kwh", "flops", "gflops", "tflops"]
    }

    def analyze_conflicts(self, claims: List[Claim], sources: List[Source]) -> List[Conflict]:
        conflicts: List[Conflict] = []
        source_map: Dict[str, Source] = {s.id: s for s in sources}

        # Filter strictly for valid empirical metric claims
        metric_claims = [c for c in claims if self._is_valid_empirical_metric(c)]

        for i in range(len(metric_claims)):
            for j in range(i + 1, len(metric_claims)):
                c1 = metric_claims[i]
                c2 = metric_claims[j]

                # Must come from independent sources
                if c1.evidence.source_id == c2.evidence.source_id:
                    continue

                # Must share the same metric category
                cat1 = self._get_metric_category(c1)
                cat2 = self._get_metric_category(c2)
                if not cat1 or not cat2 or cat1 != cat2:
                    continue

                # Must share compatible units
                if not self._are_units_compatible(c1.unit, c2.unit):
                    continue

                # Check if numbers diverge significantly (> 15%)
                v1, v2 = c1.numeric_value, c2.numeric_value
                if v1 is not None and v2 is not None and v1 > 0 and v2 > 0:
                    diff_ratio = abs(v1 - v2) / max(v1, v2)

                    if diff_ratio > 0.15:
                        s1 = source_map.get(c1.evidence.source_id, sources[0])
                        s2 = source_map.get(c2.evidence.source_id, sources[-1])

                        c1.status = FactStatus.CONFLICTING
                        c2.status = FactStatus.CONFLICTING
                        if s2.id not in c1.contradicting_source_ids:
                            c1.contradicting_source_ids.append(s2.id)
                        if s1.id not in c2.contradicting_source_ids:
                            c2.contradicting_source_ids.append(s1.id)

                        conflicts.append(Conflict(
                            id=f"cfl-{len(conflicts)+1:03d}",
                            topic=f"Empirical Divergence in {cat1.replace('_', ' ').title()} ({c1.subject} vs {c2.subject})",
                            claim_a=c1,
                            claim_b=c2,
                            source_a=s1,
                            source_b=s2,
                            conflict_type=ConflictType.WORKLOAD_VARIATION,
                            difference_explanation=(
                                f"Source '{s1.title[:35]}' reports {v1} {c1.unit or ''} ({c1.conditions or 'standard benchmark'}), "
                                f"whereas source '{s2.title[:35]}' records {v2} {c2.unit or ''} ({c2.conditions or 'alternative evaluation'}). "
                                f"Variance of {diff_ratio*100:.1f}% stems from dataset distribution, hardware setup, or evaluation benchmark conditions."
                            ),
                            resolution_status="WORKLOAD_VARIATION"
                        ))

        return conflicts

    def _is_valid_empirical_metric(self, claim: Claim) -> bool:
        """Determines if a claim represents a genuine measurable metric rather than a version or year."""
        if claim.numeric_value is None:
            return False

        # Reject years (e.g. 1900-2099)
        if 1900 <= claim.numeric_value <= 2099 and claim.unit is None:
            return False

        # Reject common version / step patterns in subject or quote
        combined = f"{claim.subject} {claim.predicate} {claim.object_value} {claim.evidence.exact_quote}".lower()
        if re.search(r"\b(version|v\d|\bstep\b|\bchapter\b|\bsection\b|\bfigure\b|\btable\b)\b", combined):
            return False

        # Must have a recognized empirical unit
        unit = (claim.unit or "").lower().strip(" ,.")
        if not unit:
            # Check if quote contains explicit metric keyword (e.g. latency, recall, accuracy)
            if any(k in combined for k in ["latency of", "recall of", "accuracy of", "mrr of", "f1 score of", "ndcg@"]):
                return True
            return False

        return any(unit in unit_list for unit_list in self.VALID_METRIC_UNITS.values())

    def _get_metric_category(self, claim: Claim) -> Optional[str]:
        unit = (claim.unit or "").lower().strip(" ,.")
        for cat, unit_list in self.VALID_METRIC_UNITS.items():
            if unit in unit_list:
                return cat

        combined = f"{claim.subject} {claim.predicate} {claim.object_value} {claim.evidence.exact_quote}".lower()
        for cat, unit_list in self.VALID_METRIC_UNITS.items():
            if any(k in combined for k in unit_list):
                return cat
        return None

    def _are_units_compatible(self, u1: Optional[str], u2: Optional[str]) -> bool:
        u1_clean = (u1 or "").lower().strip(" ,.")
        u2_clean = (u2 or "").lower().strip(" ,.")

        if not u1_clean or not u2_clean:
            return False

        # Exact match or normalized equivalencies
        if u1_clean == u2_clean:
            return True
        if u1_clean in ["%", "percent"] and u2_clean in ["%", "percent"]:
            return True
        if u1_clean in ["ms", "milliseconds"] and u2_clean in ["ms", "milliseconds"]:
            return True
        if u1_clean in ["s", "seconds"] and u2_clean in ["s", "seconds"]:
            return True
        if u1_clean in ["qps", "queries/sec", "req/s"] and u2_clean in ["qps", "queries/sec", "req/s"]:
            return True
        return False
