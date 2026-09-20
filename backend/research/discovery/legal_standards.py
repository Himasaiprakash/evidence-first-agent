import json
import urllib.request
import urllib.parse
import re
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, SourceClass, SOURCE_CLASS_WEIGHTS

class LegalStandardsDiscovery:
    """
    Legal, Judicial & Statutory Technical Standards Discovery Adapter:
    - CourtListener / Free Law Project RECAP API (Federal judicial opinions, dockets, SCOTUS/Appellate case law)
    - NIST CSRC / SP 800 Standards (National Institute of Standards and Technology official publications)
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceFirstResearchAgent/1.0 (mailto:admin@evidenceagent.org)"
        }

    def search_courtlistener(self, query: str, max_results: int = 2) -> List[Source]:
        """Search CourtListener RECAP REST API for authoritative judicial opinions and case law."""
        sources: List[Source] = []
        # Filter to 1-2 prominent search terms for fast endpoint indexing response
        clean_words = [w for w in re.findall(r'[a-zA-Z]{4,}', query) if w.lower() not in ['what', 'about', 'versus', 'compare', 'difference', 'between', 'does', 'with']]
        search_term = " ".join(clean_words[:2]) if clean_words else query.strip()
        encoded_query = urllib.parse.quote_plus(search_term)
        url = f"https://www.courtlistener.com/api/rest/v4/search/?q={encoded_query}&type=o"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    for idx, res in enumerate(results[:max_results]):
                        case_name = res.get("caseName") or "Judicial Opinion"
                        court = res.get("court") or "Federal Judicial Court"
                        date_filed = str(res.get("dateFiled") or "2024-01-01")[:10]
                        cite_count = res.get("citeCount", 0)
                        citations = res.get("citation", [])
                        cite_str = citations[0] if citations else f"Cluster {res.get('cluster_id', idx)}"
                        abs_url = res.get("absolute_url", "")
                        opinion_url = f"https://www.courtlistener.com{abs_url}" if abs_url else f"https://www.courtlistener.com/opinion/{res.get('cluster_id', idx)}/"

                        sources.append(Source(
                            id=f"src-court-{idx+1}",
                            title=f"Court Opinion: {case_name} ({court})",
                            url=opinion_url,
                            source_type=SourceType.GOVERNMENT_DOC,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.COURT_DOCUMENT,
                            author_publisher=f"{court} (Statutory Case Law)",
                            publication_date=date_filed,
                            credibility_score=99.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.COURT_DOCUMENT] * 100.0,
                            primary_status=True,
                            raw_content=f"Authoritative Judicial Ruling: {case_name}. Jurisdiction: {court}. Date Filed: {date_filed}. Official Citation: {cite_str}. Cited in {cite_count} subsequent court opinions. Verified via CourtListener Free Law Project.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_nist_standards(self, query: str, max_results: int = 2) -> List[Source]:
        """Search NIST Computer Security Resource Center (CSRC) & Special Publications (SP 800 series)."""
        from backend.research.discovery.web import WebDiscovery
        sources: List[Source] = []
        web = WebDiscovery()

        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
        nist_query = f"site:csrc.nist.gov/publications/detail/sp OR site:nist.gov {clean_q} standard"

        try:
            results = web.search_duckduckgo(nist_query, max_results=max_results + 2)
            for wr in results:
                if "nist.gov" in wr.url.lower():
                    wr.source_class = SourceClass.TECHNICAL_STANDARD
                    wr.category = SourceCategory.PRIMARY
                    wr.authority_score = SOURCE_CLASS_WEIGHTS[SourceClass.TECHNICAL_STANDARD] * 100.0
                    wr.primary_status = True
                    wr.author_publisher = "National Institute of Standards and Technology (NIST Standards)"
                    sources.append(wr)
                    if len(sources) >= max_results:
                        break
        except Exception:
            pass

        return sources
