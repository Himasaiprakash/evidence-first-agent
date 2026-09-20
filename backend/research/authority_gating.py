from enum import Enum
from typing import Dict, List, Tuple, Optional
from backend.models.schemas import Source, SourceType, SourceClass, SOURCE_CLASS_WEIGHTS


class AuthorityTier(str, Enum):
    TIER_1_PRIMARY = "TIER_1_PRIMARY"              # 1.00 - Regulators, Acts, Official Stats, Peer-Reviewed Papers
    TIER_2_OFFICIAL_SPECS = "TIER_2_OFFICIAL_SPECS"  # 0.90 - Vendor Tech Specs, ISO/IETF Standards, SEC Filings
    TIER_3_SECONDARY = "TIER_3_SECONDARY"            # 0.75 - Enterprise Engineering Postmortems, Literature Surveys
    TIER_4_ENCYCLOPEDIC = "TIER_4_ENCYCLOPEDIC"      # 0.35 - Wikipedia (Discovery & Background ONLY)
    TIER_5_UNVERIFIED_WEB = "TIER_5_UNVERIFIED_WEB"  # 0.10 - Personal Blogs, Forums, YouTube Transcripts


AUTHORITY_TIER_WEIGHTS: Dict[AuthorityTier, float] = {
    AuthorityTier.TIER_1_PRIMARY: 1.00,
    AuthorityTier.TIER_2_OFFICIAL_SPECS: 0.90,
    AuthorityTier.TIER_3_SECONDARY: 0.75,
    AuthorityTier.TIER_4_ENCYCLOPEDIC: 0.35,
    AuthorityTier.TIER_5_UNVERIFIED_WEB: 0.10,
}


class PrimaryAuthorityGate:
    """
    5-Tier Primary Source Authority Router & Enforcement Gate:
    - Enforces authority thresholds based on claim type (Regulatory, Architectural, Economic, General).
    - Rejects Wikipedia / YouTube / Blog sources from supporting core regulatory or architectural claims.
    """

    def classify_source_tier(self, source: Source) -> AuthorityTier:
        """Classifies a source into its authority tier based on domain, source_type, and source_class."""
        url = (source.url or "").lower()
        title = (source.title or "").lower()

        # Tier 1: Regulatory Bodies & Official Statistics
        if any(reg in url or reg in title for reg in ["npci.org", "rbi.org", "sec.gov", "fda.gov", "who.int", "data.gov", "bls.gov", "worldbank.org", "arxiv.org", "ncbi.nlm.nih.gov", "pubmed"]):
            return AuthorityTier.TIER_1_PRIMARY
        if source.source_type == SourceType.GOVERNMENT_DOC or source.source_type == SourceType.ACADEMIC_PAPER:
            return AuthorityTier.TIER_1_PRIMARY

        # Tier 2: Official Standards & Corporate Filings
        if any(spec in url or spec in title for spec in ["ietf.org", "w3.org", "iso.org", "nist.gov", "ieee.org", "github.com"]):
            return AuthorityTier.TIER_2_OFFICIAL_SPECS
        if source.source_type == SourceType.STANDARDS_DOC or source.source_type == SourceType.DOCUMENTATION or source.source_type == SourceType.FINANCIAL_FILING:
            return AuthorityTier.TIER_2_OFFICIAL_SPECS

        # Tier 4: Wikipedia (Discovery ONLY)
        if "wikipedia.org" in url or "wikimedia" in url or source.source_class == SourceClass.WIKIPEDIA:
            return AuthorityTier.TIER_4_ENCYCLOPEDIC

        # Tier 5: Generic Forums & Personal Blogs
        if source.source_type == SourceType.YOUTUBE or "youtube.com" in url or "medium.com" in url or source.source_class in [SourceClass.BLOG, SourceClass.FORUM]:
            return AuthorityTier.TIER_5_UNVERIFIED_WEB

        # Default Tier 3 for general web articles
        return AuthorityTier.TIER_3_SECONDARY

    def get_source_authority_score(self, source: Source) -> float:
        """Returns numerical authority weight (0.10 to 1.00)."""
        tier = self.classify_source_tier(source)
        return AUTHORITY_TIER_WEIGHTS[tier]

    def validate_claim_authority(self, claim_category: str, source: Source) -> Tuple[bool, str]:
        """
        Validates if source has sufficient authority tier to support the claim category.
        - REGULATORY, ARCHITECTURAL, ECONOMIC_FEE requires Tier 1 or Tier 2 (>= 0.90).
        """
        tier = self.classify_source_tier(source)
        weight = AUTHORITY_TIER_WEIGHTS[tier]

        category = claim_category.upper()
        if category in ["REGULATORY", "ARCHITECTURAL", "ECONOMIC_FEE"]:
            if weight < 0.90:
                return False, f"Claim category '{category}' requires Tier-1/2 primary sources (>=0.90 authority). Provided source tier: {tier.value} ({weight:.2f})."

        if category in ["QUANTITATIVE", "BENCHMARK"]:
            if weight < 0.75:
                return False, f"Quantitative claim category '{category}' requires at least Tier-3 sources (>=0.75 authority). Provided tier: {tier.value}."

        return True, "Passed authority tier validation."


# Global Authority Gate Singleton
authority_gate = PrimaryAuthorityGate()
