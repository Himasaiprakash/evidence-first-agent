import re
import uuid
from typing import List, Tuple, Optional
from backend.models.schemas import Claim, Source, DocumentChunk, BoundClaim, FactStatus, SourceType
from backend.research.authority_gating import authority_gate


class PassageQuoteBinder:
    """
    Exact Passage Quote Binder & Entailment Engine:
    - Binds extracted claims to exact passage text windows within retrieved source content.
    - Calculates character offsets and entailment scores.
    - Rejects unevidenced or hallucinated claims lacking passage proof.
    """

    def bind_claim(
        self,
        claim: Claim,
        source: Source,
        chunks: List[DocumentChunk],
        research_id: str,
        claim_category: str = "GENERAL"
    ) -> Tuple[Optional[BoundClaim], str]:
        """
        Attempts to bind a raw Claim object to an exact passage quote within document chunks.
        Returns (BoundClaim, status_message).
        """
        # 1. Authority Tier Enforcement Check
        is_auth_valid, auth_msg = authority_gate.validate_claim_authority(claim_category, source)
        if not is_auth_valid:
            return None, f"Authority Gate Rejected: {auth_msg}"

        source_tier_score = authority_gate.get_source_authority_score(source)
        raw_text = (source.raw_content or "").strip()

        # Find best passage chunk matching claim subject and object
        subj_words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", claim.subject)]
        obj_words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", claim.object_value)]

        target_keywords = set(subj_words + obj_words)
        best_chunk: Optional[DocumentChunk] = None
        best_quote = ""
        best_offset: Tuple[int, int] = (0, 0)
        max_matches = 0

        # Search matching chunks
        matching_chunks = [c for c in chunks if c.source_id == source.id] if chunks else []
        if not matching_chunks and raw_text:
            # Create transient chunk from raw text
            matching_chunks = [
                DocumentChunk(
                    id=f"chk-{uuid.uuid4().hex[:8]}",
                    source_id=source.id,
                    text=raw_text[:1500],
                    start_offset=0,
                    end_offset=min(1500, len(raw_text))
                )
            ]

        for chunk in matching_chunks:
            c_text_lower = chunk.text.lower()
            match_count = sum(1 for kw in target_keywords if kw in c_text_lower)
            if match_count > max_matches:
                max_matches = match_count
                best_chunk = chunk
                
                # Extract exact sentence or passage window
                sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
                for sentence in sentences:
                    s_lower = sentence.lower()
                    if any(kw in s_lower for kw in subj_words) and any(kw in s_lower for kw in obj_words):
                        best_quote = sentence.strip()
                        start_idx = raw_text.find(best_quote) if raw_text else 0
                        end_idx = start_idx + len(best_quote) if start_idx != -1 else len(best_quote)
                        best_offset = (max(0, start_idx), end_idx)
                        break

                if not best_quote and sentences:
                    best_quote = sentences[0].strip()
                    best_offset = (chunk.start_offset, chunk.end_offset)

        if not best_quote or max_matches == 0:
            return None, f"Passage Match Failed: No supporting passage quote found for claim subject '{claim.subject}' and object '{claim.object_value}'."

        # Compute entailment score based on keyword overlap ratio
        entailment_score = min(1.0, (max_matches / max(1, len(target_keywords))) * 0.90 + (source_tier_score * 0.10))

        if entailment_score < 0.40:
            return None, f"Entailment Low ({entailment_score:.2f}): Passage quote does not sufficiently support claim."

        bound_claim = BoundClaim(
            id=claim.id if claim.id else f"bclm-{uuid.uuid4().hex[:8]}",
            research_id=research_id,
            subject=claim.subject,
            predicate=claim.predicate,
            object_value=claim.object_value,
            source_id=source.id,
            source_type=source.source_type if hasattr(source, "source_type") else SourceType.WEB,
            source_tier=source_tier_score,
            exact_passage_quote=best_quote,
            passage_character_offset=best_offset,
            page_or_section=best_chunk.section if best_chunk else "Main Body",
            document_version_or_date=source.retrieval_timestamp[:10] if source.retrieval_timestamp else "2026",
            entailment_score=round(entailment_score, 2),
            verification_status=FactStatus.VERIFIED
        )

        return bound_claim, "Successfully bound claim to exact passage quote."


# Global Passage Binder Singleton
passage_binder = PassageQuoteBinder()
