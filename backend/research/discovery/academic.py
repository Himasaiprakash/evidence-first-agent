import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, DomainType, SourceClass, SOURCE_CLASS_WEIGHTS

class AcademicDiscovery:
    """
    Real Academic Discovery Adapter:
    - Queries arXiv Search API with domain-aware category filters
    - Supports quantitative biology, physics, computer science, and mathematics
    - Enforces hard rule: ZERO fabricated papers
    """
    def __init__(self):
        self.headers = {"User-Agent": "EvidenceFirstAgent/1.0 (AcademicResearchBot)"}

    def search_arxiv(self, query: str, domain: DomainType = DomainType.GENERAL, max_results: int = 8) -> List[Source]:
        """Query arXiv API with domain-specific category constraints."""
        # Sanitize query: strip special characters, parentheses, and extra prompt noise
        clean_q = re.sub(r"[^\w\s]", " ", query).strip()
        words = [w for w in clean_q.split() if w.lower() not in ["principles", "architecture", "survey", "understanding", "analysis", "guidelines", "overview"]]
        short_q = " ".join(words[:4]) if words else "computer science"
        
        # Add arXiv category filter if domain is biology/medicine or physics
        if domain == DomainType.MEDICINE_BIOLOGY:
            search_expr = f"all:{short_q} AND cat:q-bio*"
        elif domain == DomainType.PHYSICAL_SCIENCE:
            search_expr = f"all:{short_q} AND (cat:quant-ph OR cat:physics*)"
        elif domain == DomainType.AI_TECHNOLOGY or domain == DomainType.SOFTWARE_ENGINEERING:
            search_expr = f"all:{short_q} AND cat:cs*"
        else:
            search_expr = f"all:{short_q}"

        encoded_query = urllib.parse.quote(search_expr)
        url = f"https://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        sources = []

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                xml_data = resp.read().decode("utf-8")
                root = ET.fromstring(xml_data)
                
                for idx, entry in enumerate(root.findall("{http://www.w3.org/2005/Atom}entry")):
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                    published_elem = entry.find("{http://www.w3.org/2005/Atom}published")
                    id_elem = entry.find("{http://www.w3.org/2005/Atom}id")

                    if title_elem is not None and summary_elem is not None and id_elem is not None:
                        title = title_elem.text.strip().replace("\n", " ")
                        summary = summary_elem.text.strip().replace("\n", " ")
                        paper_url = id_elem.text.strip()
                        pub_date = published_elem.text[:10] if published_elem is not None else "2025-01-01"

                        authors = [a.find("{http://www.w3.org/2005/Atom}name").text for a in entry.findall("{http://www.w3.org/2005/Atom}author") if a.find("{http://www.w3.org/2005/Atom}name") is not None]
                        author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")

                        sources.append(Source(
                            id=f"src-arxiv-{idx+1}",
                            title=f"Paper: {title}",
                            url=paper_url,
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=author_str or "Academic Researchers",
                            publication_date=pub_date,
                            credibility_score=98.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=summary,
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources
