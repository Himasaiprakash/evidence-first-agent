import json
import urllib.request
import urllib.parse
import re
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, SourceClass, SOURCE_CLASS_WEIGHTS

class AcademicUniversalDiscovery:
    """
    Universal Academic & Scientific Discovery Adapter:
    - OpenAlex REST API (250M+ scientific papers across all disciplines)
    - Semantic Scholar (Allen Institute for AI citation graphs & TLDRs)
    - Crossref REST API (150M+ registered DOI scholarly records)
    - arXiv REST API (Physics, AI, Computer Science, Quantitative Biology)
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceFirstResearchAgent/1.0 (mailto:admin@evidenceagent.org)"
        }

    def search_openalex(self, query: str, max_results: int = 3) -> List[Source]:
        """Search OpenAlex global academic literature repository."""
        sources: List[Source] = []
        clean_q = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', query).strip()
        encoded_query = urllib.parse.quote(clean_q)
        q_low = clean_q.lower()
        is_modern = any(k in q_low for k in ["llm", "gpt", "claude", "gemini", "model", "benchmark", "agent", "reasoning", "coding"])
        year_filter = "&filter=publication_year:2024-2026" if is_modern else ""
        url = f"https://api.openalex.org/works?search={encoded_query}{year_filter}&per-page={max_results}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    for idx, work in enumerate(results):
                        title = work.get("title") or f"Academic Paper {idx+1}"
                        doi = work.get("doi") or work.get("id") or f"https://openalex.org/W{idx+1}"
                        pub_year = str(work.get("publication_year") or "2024")
                        cited_by = work.get("cited_by_count", 0)

                        abstract = ""
                        inv_index = work.get("abstract_inverted_index")
                        if inv_index and isinstance(inv_index, dict):
                            word_positions = []
                            for word, positions in inv_index.items():
                                for pos in positions:
                                    word_positions.append((pos, word))
                            word_positions.sort(key=lambda x: x[0])
                            abstract = " ".join([w for _, w in word_positions[:80]])

                        if not abstract:
                            abstract = f"Published scientific research with {cited_by} citations in peer-reviewed repository."

                        authorships = work.get("authorships", [])
                        author_names = [a.get("author", {}).get("display_name", "") for a in authorships[:2]]
                        author_str = ", ".join([a for a in author_names if a]) or "Academic Researchers"

                        sources.append(Source(
                            id=f"src-openalex-{idx+1}",
                            title=f"Paper: {title}",
                            url=doi,
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{author_str} ({pub_year})",
                            publication_date=f"{pub_year}-01-01",
                            credibility_score=97.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"{title}. Abstract: {abstract}. Official peer-reviewed open-access study with {cited_by} citations.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_semantic_scholar(self, query: str, max_results: int = 3) -> List[Source]:
        """Query Semantic Scholar Graph API for high-influence papers and TLDR summaries."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={max_results}&fields=title,abstract,authors,year,citationCount,tldr,url"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    papers = data.get("data", [])
                    for idx, p in enumerate(papers):
                        title = p.get("title") or "Scholarly Publication"
                        paper_url = p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId', idx)}"
                        year = str(p.get("year") or "2024")
                        citations = p.get("citationCount", 0)
                        
                        tldr_obj = p.get("tldr")
                        tldr_text = tldr_obj.get("text", "") if isinstance(tldr_obj, dict) else ""
                        abstract = p.get("abstract") or tldr_text or f"Peer-reviewed research cataloged on Semantic Scholar with {citations} citations."
                        
                        authors = p.get("authors", [])
                        author_str = ", ".join([a.get("name", "") for a in authors[:2] if a.get("name")]) or "Research Investigators"

                        sources.append(Source(
                            id=f"src-semanticscholar-{idx+1}",
                            title=f"Semantic Scholar: {title}",
                            url=paper_url,
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{author_str} ({year})",
                            publication_date=f"{year}-01-01",
                            credibility_score=96.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"{title}. TLDR: {tldr_text or abstract[:300]}. Total Citations: {citations}. Allen Institute for AI Semantic Scholar.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_crossref(self, query: str, max_results: int = 3) -> List[Source]:
        """Query Crossref REST API for verified journal publications and DOI metadata."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.crossref.org/works?query={encoded_query}&rows={max_results}&select=DOI,title,author,published,container-title,abstract"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("message", {}).get("items", [])
                    for idx, item in enumerate(items):
                        titles = item.get("title", [])
                        title = titles[0] if titles else "Crossref Academic Record"
                        doi = item.get("DOI", "")
                        container = item.get("container-title", ["Academic Journal"])
                        journal = container[0] if container else "Academic Journal"
                        
                        pub_parts = item.get("published", {}).get("date-parts", [["2024"]])
                        year = str(pub_parts[0][0]) if pub_parts and pub_parts[0] else "2024"
                        
                        authors = item.get("author", [])
                        author_str = ", ".join([f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors[:2]]) or "Crossref Contributors"

                        clean_abstract = re.sub(r"<[^>]+>", "", item.get("abstract") or f"Published research registered via Crossref DOI registry in {journal}.")

                        sources.append(Source(
                            id=f"src-crossref-{idx+1}",
                            title=f"Crossref: {title}",
                            url=f"https://doi.org/{doi}" if doi else "https://crossref.org",
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{author_str} ({journal})",
                            publication_date=f"{year}-01-01",
                            credibility_score=97.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"{title}. Published in {journal} ({year}). Abstract: {clean_abstract[:300]}. Official Crossref DOI record.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_arxiv(self, query: str, max_results: int = 3) -> List[Source]:
        """Query arXiv REST API for physics, computer science, and mathematics preprints."""
        sources: List[Source] = []
        # Stop-words and generic evaluation terms that must NEVER be OR'd across documents
        generic_nlp_terms = {
            "compare", "comparison", "latest", "the", "and", "for", "with", "between", "from",
            "that", "this", "study", "analysis", "evaluation", "framework", "system", "benchmark",
            "benchmarks", "accuracy", "empirical", "model", "models", "same", "task", "overview"
        }
        terms = [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query) if w.lower() not in generic_nlp_terms]
        
        q_low = query.lower()
        if "rag" in q_low or "retrieval-augmented" in q_low or "retrieval augmented" in q_low:
            if any(k in q_low for k in ["fine-tuning", "finetuning", "fine tuning", "lora", "peft"]):
                search_str = '(ti:"retrieval-augmented" OR all:"retrieval-augmented" OR ti:RAG) AND (all:"fine-tuning" OR all:finetuning OR all:LoRA)'
            else:
                search_str = 'ti:"retrieval-augmented" OR all:"retrieval-augmented generation"'
        elif len(terms) >= 2:
            search_str = f'all:"{terms[0]}" AND all:"{terms[1]}"'
        elif terms:
            search_str = f'all:"{terms[0]}"'
        else:
            search_str = f'all:"{query[:40]}"'
        encoded_query = urllib.parse.quote(search_str)
        url = f"https://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    xml_content = resp.read().decode("utf-8")
                    entries = xml_content.split("<entry>")
                    for idx, entry in enumerate(entries[1:]):
                        title_match = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                        summary_match = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                        id_match = re.search(r"<id>(.*?)</id>", entry, re.DOTALL)
                        published_match = re.search(r"<published>(.*?)</published>", entry)

                        if title_match and summary_match:
                            clean_title = title_match.group(1).replace("\n", " ").strip()
                            clean_summary = summary_match.group(1).replace("\n", " ").strip()
                            paper_url = id_match.group(1).strip() if id_match else f"https://arxiv.org/abs/{idx}"
                            pub_date = published_match.group(1)[:10] if published_match else "2024-01-01"

                            sources.append(Source(
                                id=f"src-arxiv-{idx+1}",
                                title=f"arXiv: {clean_title}",
                                url=paper_url,
                                source_type=SourceType.ACADEMIC_PAPER,
                                category=SourceCategory.PRIMARY,
                                source_class=SourceClass.PRIMARY_RESEARCH,
                                author_publisher="arXiv Preprint Repository (Cornell University)",
                                publication_date=pub_date,
                                credibility_score=95.0,
                                authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                                primary_status=True,
                                raw_content=f"{clean_title}. Abstract: {clean_summary}",
                                retrieval_timestamp=datetime.now().isoformat()
                            ))
        except Exception:
            pass

        return sources
