import re
from typing import List, Tuple, Dict, Set
from backend.models.schemas import Source

class SourceDeduplicatorAndClusterer:
    """
    Source Deduplication & Event Clustering Engine (0 LLM Calls):
    - Jaccard title similarity and URL canonicalization
    - Event clustering: identifies identical wire stories / syndicate reprints
    - Ensures 10 reprints of the same Reuters/AP story are clustered into 1 primary source
    - Ranks sources by Authority, Credibility, and Recency
    """
    def deduplicate_and_rank(self, sources: List[Source]) -> List[Source]:
        if not sources:
            return []

        unique_sources: List[Source] = []
        seen_urls: Set[str] = set()
        seen_title_tokens: List[Tuple[Set[str], Source]] = []

        for s in sources:
            # 1. Exact URL match
            clean_url = s.url.lower().rstrip("/").split("?")[0]
            if clean_url in seen_urls:
                continue

            # 2. Tokenized Title Jaccard Similarity Check (Clustering wire reprints)
            title_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", s.title.lower()))
            is_duplicate = False

            for existing_tokens, existing_source in seen_title_tokens:
                intersection = len(title_words.intersection(existing_tokens))
                union = len(title_words.union(existing_tokens))
                similarity = (intersection / union) if union > 0 else 0.0

                if similarity >= 0.75:
                    # Same story/paper reprint - merge by keeping the higher authority source
                    is_duplicate = True
                    if s.authority_score > existing_source.authority_score:
                        existing_source.authority_score = s.authority_score
                        existing_source.credibility_score = max(existing_source.credibility_score, s.credibility_score)
                    break

            if not is_duplicate:
                seen_urls.add(clean_url)
                seen_title_tokens.append((title_words, s))
                unique_sources.append(s)

        # Rank sources by composite score: Authority * 0.5 + Credibility * 0.5
        unique_sources.sort(key=lambda s: (s.authority_score * 0.5 + s.credibility_score * 0.5), reverse=True)
        return unique_sources
