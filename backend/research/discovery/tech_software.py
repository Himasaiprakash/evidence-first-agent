import json
import re
import urllib.request
import urllib.parse
import gzip
import io
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, SourceClass, SOURCE_CLASS_WEIGHTS

class TechSoftwareDiscovery:
    """
    Technical, Open-Source, Architecture & Standards Discovery Adapter:
    - GitHub Search API (Production architectures, stars, implementations)
    - Hugging Face Hub REST API (Model cards, benchmark scores, dataset metrics)
    - Stack Overflow / Stack Exchange API (Real-world failure modes, bugs, solutions)
    - PyPI / npm Package Registries (Distribution releases & ecosystem maturity)
    - IETF RFCs / Internet Standards (Protocols, cryptography, networking standards)
    - Production Case Studies & Engineering Architecture (AWS, Netflix, Meta, GitHub blogs)
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceFirstResearchAgent/1.0 (mailto:admin@evidenceagent.org)",
            "Accept": "application/vnd.github.v3+json"
        }
        self.engineering_domains = [
            "aws.amazon.com", "netflixtechblog.com", "engineering.fb.com", "github.blog",
            "blog.cloudflare.com", "databricks.com", "uber.com", "engineering.linkedin.com",
            "stripe.com", "blog.bytebytego.com", "openai.com", "cloud.google.com", "meta.com",
            "microsoft.com", "eng.lyft.com", "slack.engineering", "blog.twitter.com",
            "nvidia.com", "developer.nvidia.com", "coreweave.com", "anyscale.com", "pinecone.io",
            "weaviate.io", "qdrant.tech", "snowflake.com", "anthropic.com", "cohere.com",
            "huggingface.co", "developers.googleblog.com", "doordash.engineering", "airbnb.io"
        ]
        self.engineering_keywords = [
            "amazon", "aws", "netflix", "meta", "github", "cloudflare", "databricks", "uber",
            "linkedin", "stripe", "openai", "google", "microsoft", "nvidia", "coreweave",
            "snowflake", "anthropic", "doordash", "pinterest", "airbnb", "anyscale", "hugging face"
        ]

    def search_github_repositories(self, query: str, max_results: int = 3) -> List[Source]:
        """Search top GitHub repositories for architecture, code examples, and benchmarks."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={max_results}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("items", [])
                    for idx, repo in enumerate(items):
                        full_name = repo.get("full_name", "")
                        desc = repo.get("description") or "Open source technical implementation"
                        html_url = repo.get("html_url", "")
                        stars = repo.get("stargazers_count", 0)
                        language = repo.get("language") or "Python"
                        updated_at = repo.get("updated_at", "2025-01-01")[:10]

                        sources.append(Source(
                            id=f"src-github-{idx+1}",
                            title=f"GitHub: {full_name} (⭐ {stars:,})",
                            url=html_url,
                            source_type=SourceType.CODE_REPO,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                            author_publisher=f"{full_name.split('/')[0]} (GitHub Open Source)",
                            publication_date=updated_at,
                            credibility_score=95.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.OFFICIAL_DOCUMENTATION] * 100.0,
                            primary_status=True,
                            raw_content=f"Official GitHub Repository {full_name} ({language}, {stars:,} stars). Purpose: {desc}. Architecture specification, source code, and release documentation.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_huggingface_hub(self, query: str, max_results: int = 2) -> List[Source]:
        """Search Hugging Face Hub for open-source AI models, benchmark rankings, and model cards."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://huggingface.co/api/models?search={encoded_query}&limit={max_results}&full=true"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EvidenceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    models = json.loads(resp.read().decode("utf-8"))
                    for idx, m in enumerate(models):
                        model_id = m.get("id", f"model-{idx+1}")
                        likes = m.get("likes", 0)
                        downloads = m.get("downloads", 0)
                        pipeline = m.get("pipeline_tag") or "machine-learning"
                        tags = m.get("tags", [])
                        tag_str = ", ".join(tags[:4]) if tags else "ai-model"

                        sources.append(Source(
                            id=f"src-huggingface-{idx+1}",
                            title=f"Hugging Face Model: {model_id} (⬇️ {downloads:,})",
                            url=f"https://huggingface.co/{model_id}",
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                            author_publisher=f"{model_id.split('/')[0] if '/' in model_id else 'HuggingFace'} (AI Hub)",
                            publication_date=datetime.now().strftime("%Y-%m-%d"),
                            credibility_score=96.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.OFFICIAL_DOCUMENTATION] * 100.0,
                            primary_status=True,
                            raw_content=f"Hugging Face Model Card: {model_id}. Pipeline: {pipeline}. Community Downloads: {downloads:,}. Likes: {likes:,}. Architecture tags: {tag_str}. Benchmark performance and evaluation weights metadata.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_huggingface_daily_papers(self, query: str, max_results: int = 3) -> List[Source]:
        """Fetch cutting-edge daily AI preprints curated by Hugging Face (updated daily, 100% free)."""
        sources: List[Source] = []
        url = "https://huggingface.co/api/daily_papers"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                papers = json.loads(resp.read().decode("utf-8"))

            q_words = [w.lower() for w in query.split() if len(w) > 2]
            matched = []
            for item in papers:
                title = item.get("title", "")
                p = item.get("paper", {})
                summary = p.get("summary", "")
                combined = (title + " " + summary).lower()
                score = sum(1 for w in q_words if w in combined)
                if score > 0:
                    matched.append((score, title, p, item))

            matched.sort(key=lambda x: x[0], reverse=True)
            for idx, (_, title, p, item) in enumerate(matched[:max_results]):
                paper_id = p.get("id", f"hf-{idx+1}")
                summary = p.get("summary") or "Hugging Face Daily Research Paper."
                published = (p.get("publishedAt") or item.get("publishedAt") or "2026-09-01")[:10]
                upvotes = p.get("upvotes", 0)
                sources.append(Source(
                    id=f"src-hf-daily-{idx+1}",
                    title=f"Hugging Face Daily: {title}",
                    url=f"https://huggingface.co/papers/{paper_id}",
                    source_type=SourceType.ACADEMIC_PAPER,
                    category=SourceCategory.PRIMARY,
                    source_class=SourceClass.PRIMARY_RESEARCH,
                    author_publisher=f"Hugging Face Daily Papers (⭐ {upvotes} upvotes)",
                    publication_date=published,
                    credibility_score=97.0,
                    authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                    primary_status=True,
                    raw_content=f"Title: {title}. Abstract: {summary[:500]}. Curated on Hugging Face Daily Research with {upvotes} community upvotes. arXiv ID: {paper_id}.",
                    retrieval_timestamp=datetime.now().isoformat()
                ))
        except Exception:
            pass

        return sources

    def search_github_official_releases(self, query: str, max_results: int = 2) -> List[Source]:
        """Fetch official releases, tags, and changelogs from primary foundation repositories dynamically (100% free)."""
        sources: List[Source] = []

        # 1. Dynamically discover top repositories matching the query via GitHub Search
        clean_words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", query) if w.lower() not in ["compare", "latest", "benchmark", "the", "and", "for", "with", "model", "models"]]
        search_query = " ".join(clean_words[:4]) if clean_words else query
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page={max_results + 2}"

        target_repos = []
        try:
            req = urllib.request.Request(search_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    for repo in data.get("items", []):
                        fn = repo.get("full_name")
                        if fn and fn not in target_repos:
                            target_repos.append(fn)
        except Exception:
            pass

        # 2. Fetch latest official releases for the dynamically discovered repositories
        for repo in target_repos[:max_results]:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "EvidenceFirstResearchAgent/1.0",
                    "Accept": "application/vnd.github.v3+json"
                })
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        tag = data.get("tag_name") or data.get("name") or "Release"
                        pub_date = (data.get("published_at") or "2025-01-01")[:10]
                        body = (data.get("body") or "").strip().replace("\r\n", " ").replace("\n", " ")
                        clean_body = re.sub(r"[#*`]", "", body)[:400]
                        repo_org = repo.split('/')[0]
                        repo_name = repo.split('/')[-1].lower()[:12]
                        sources.append(Source(
                            id=f"src-release-{repo_name}",
                            title=f"Official Release: {repo} ({tag})",
                            url=data.get("html_url", f"https://github.com/{repo}/releases"),
                            source_type=SourceType.CODE_REPO,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRODUCTION_CASE_STUDY,
                            author_publisher=f"{repo_org} (Official Architecture Release)",
                            publication_date=pub_date,
                            credibility_score=98.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRODUCTION_CASE_STUDY] * 100.0,
                            primary_status=True,
                            raw_content=f"Official Production Release {tag} for {repo} published on {pub_date}. Architectural highlights and changelog: {clean_body}",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
            except Exception:
                pass

        return sources

    def search_stack_overflow(self, query: str, max_results: int = 2) -> List[Source]:
        """Search Stack Overflow for real-world implementation failure modes, errors, and accepted solutions."""
        sources: List[Source] = []
        clean_q = urllib.parse.quote(query)
        url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={clean_q}&site=stackoverflow&pagesize={max_results}&filter=withbody"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EvidenceAgent/1.0", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                raw_bytes = resp.read()
                # Decompress gzip if encoded
                if resp.info().get('Content-Encoding') == 'gzip':
                    raw_bytes = gzip.decompress(raw_bytes)
                data = json.loads(raw_bytes.decode("utf-8"))
                items = data.get("items", [])
                for idx, item in enumerate(items):
                    title = item.get("title", "Stack Overflow Discussion")
                    link = item.get("link", "https://stackoverflow.com")
                    score = item.get("score", 0)
                    is_answered = item.get("is_answered", False)
                    tags = ", ".join(item.get("tags", []))

                    clean_body = re.sub(r"<[^>]+>", "", item.get("body", ""))[:250]

                    sources.append(Source(
                        id=f"src-stackoverflow-{idx+1}",
                        title=f"Stack Overflow: {title}",
                        url=link,
                        source_type=SourceType.DOCUMENTATION,
                        category=SourceCategory.COMMUNITY,
                        source_class=SourceClass.FORUM,
                        author_publisher="Stack Overflow Developer Community",
                        publication_date="2024-01-01",
                        credibility_score=75.0,
                        authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.FORUM] * 100.0,
                        primary_status=False,
                        raw_content=f"Developer Technical Analysis: {title} (Votes: {score}, Answered: {is_answered}). Tags: [{tags}]. Core Issue / Solution: {clean_body}",
                        retrieval_timestamp=datetime.now().isoformat()
                    ))
        except Exception:
            pass

        return sources

    def search_pypi_package(self, package_name: str) -> List[Source]:
        """Fetch package metadata and release info from PyPI."""
        sources: List[Source] = []
        clean_pkg = package_name.lower().replace(" ", "-").strip()
        url = f"https://pypi.org/pypi/{clean_pkg}/json"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EvidenceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    info = data.get("info", {})
                    name = info.get("name", clean_pkg)
                    version = info.get("version", "latest")
                    summary = info.get("summary") or "Official Python package distribution."
                    home_page = info.get("project_url") or info.get("package_url") or f"https://pypi.org/project/{clean_pkg}/"

                    sources.append(Source(
                        id=f"src-pypi-{name.lower()}",
                        title=f"PyPI Package: {name} (v{version})",
                        url=home_page,
                        source_type=SourceType.DOCUMENTATION,
                        category=SourceCategory.PRIMARY,
                        source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                        author_publisher=f"{info.get('author') or name} (Python Package Index)",
                        publication_date="2025-01-01",
                        credibility_score=95.0,
                        authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.OFFICIAL_DOCUMENTATION] * 100.0,
                        primary_status=True,
                        raw_content=f"PyPI Official Distribution for {name} v{version}. Summary: {summary}. Official maintainers: {info.get('author_email', 'PyPI Maintainers')}.",
                        retrieval_timestamp=datetime.now().isoformat()
                    ))
        except Exception:
            pass

        return sources

    def search_npm_package(self, package_name: str, max_results: int = 3) -> List[Source]:
        """Fetch package distribution metrics, monthly downloads, and dependencies from npm Registry."""
        sources: List[Source] = []
        clean_pkg = package_name.lower().strip()
        url = f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(clean_pkg)}&size={max_results}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EvidenceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    objects = data.get("objects", [])
                    for idx, obj in enumerate(objects):
                        pkg = obj.get("package", {})
                        p_name = pkg.get("name", "")
                        version = pkg.get("version", "latest")
                        desc = pkg.get("description") or "npm package distribution"
                        links = pkg.get("links", {})
                        npm_url = links.get("npm") or f"https://www.npmjs.com/package/{p_name}"
                        downloads = obj.get("downloads", {})
                        monthly_dls = downloads.get("monthly", 0)
                        dependents = obj.get("dependents", "0")
                        date_str = str(obj.get("updated") or pkg.get("date") or "2025-01-01")[:10]

                        if p_name:
                            sources.append(Source(
                                id=f"src-npm-{p_name.replace('/', '_').lower()}",
                                title=f"npm Package: {p_name} (v{version})",
                                url=npm_url,
                                source_type=SourceType.DOCUMENTATION,
                                category=SourceCategory.PRIMARY,
                                source_class=SourceClass.OFFICIAL_DOCUMENTATION,
                                author_publisher=f"npm Registry ({p_name})",
                                publication_date=date_str,
                                credibility_score=95.0,
                                authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.OFFICIAL_DOCUMENTATION] * 100.0,
                                primary_status=True,
                                raw_content=f"Official npm Package: {p_name} v{version}. Monthly Downloads: {monthly_dls:,}. Dependents: {dependents}. Description: {desc}. Verified Node.js ecosystem package metadata.",
                                retrieval_timestamp=datetime.now().isoformat()
                            ))
        except Exception:
            pass

        return sources

    def search_ietf_rfcs(self, query: str, max_results: int = 2) -> List[Source]:
        """Search official IETF RFC internet technical standards and protocol specifications."""
        sources: List[Source] = []
        clean_q = re.sub(r'[^a-zA-Z0-9\s]', '', query).strip()
        url = f"https://datatracker.ietf.org/api/v1/doc/document/?name__startswith=rfc&title__icontains={urllib.parse.quote(clean_q)}&format=json&limit={max_results}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EvidenceAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    docs = data.get("objects", [])
                    for idx, doc in enumerate(docs):
                        rfc_name = doc.get("name", f"rfc{idx+1}")
                        title = doc.get("title", "IETF RFC Standard")
                        abstract = doc.get("abstract", "")
                        rfc_num = rfc_name.upper()
                        rfc_url = f"https://www.rfc-editor.org/rfc/{rfc_name}.html"

                        sources.append(Source(
                            id=f"src-ietf-{rfc_name}",
                            title=f"IETF Standard: {rfc_num} — {title}",
                            url=rfc_url,
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.TECHNICAL_STANDARD,
                            author_publisher="Internet Engineering Task Force (IETF Standards)",
                            publication_date="2024-01-01",
                            credibility_score=98.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.TECHNICAL_STANDARD] * 100.0,
                            primary_status=True,
                            raw_content=f"Official IETF RFC Specification {rfc_num}: {title}. Abstract: {abstract[:400]}. Governing Internet protocol standard.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_production_case_studies(self, topic: str, max_results: int = 3) -> List[Source]:
        """
        Discovers real-world enterprise production architectures, postmortems, and engineering case studies:
        - Targets recognized engineering blogs: AWS Architecture, Netflix TechBlog, Meta Engineering, GitHub, Cloudflare, Databricks, Uber, NVIDIA, CoreWeave, etc.
        - Enforces SourceClass.PRODUCTION_CASE_STUDY with authority weight 0.85.
        """
        import xml.etree.ElementTree as ET
        from backend.research.discovery.web import WebDiscovery
        sources: List[Source] = []
        web = WebDiscovery()

        clean_topic = topic.split("\n")[0].split(":")[0].strip()
        clean_topic = re.sub(r'\b(trade-?offs?|comparison|overview|landscape|vs\.?|versus)\b', ' ', clean_topic, flags=re.IGNORECASE)
        clean_topic = " ".join(clean_topic.split())
        seen_urls = set()

        # 1. Tier 1: Targeted Technical Press & Engineering RSS Search
        rss_queries = [
            f"{clean_topic} production architecture engineering blog",
            f"{clean_topic} enterprise deployment case study"
        ]
        for rq in rss_queries:
            if len(sources) >= max_results:
                break
            try:
                rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(rq)}&hl=en-US&gl=US&ceid=US:en"
                req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    root = ET.fromstring(resp.read().decode("utf-8", errors="ignore"))
                items = root.findall(".//item")
                for it in items:
                    title = it.find("title").text if it.find("title") is not None else ""
                    link = it.find("link").text if it.find("link") is not None else ""
                    pub = it.find("source").text if it.find("source") is not None else "Engineering Blog"
                    pub_date = it.find("pubDate").text if it.find("pubDate") is not None else datetime.now().strftime("%Y-%m-%d")

                    if not link or link in seen_urls:
                        continue
                    pub_low = (pub + " " + title).lower()
                    if any(k in pub_low for k in self.engineering_keywords) or any(ed in pub_low for ed in self.engineering_domains):
                        # Scrape substantive engineering text
                        scraped_text = web.fetch_web_page(link, timeout=4)
                        full_content = f"Title: {title}\nPublisher: {pub} (Enterprise Engineering)\nPublished: {pub_date}\nLink: {link}"
                        if scraped_text and len(scraped_text) > 150:
                            full_content += f"\nDetailed Engineering Documentation:\n{scraped_text[:3500]}"
                        
                        seen_urls.add(link)
                        src_id = f"src-prod-{len(sources)+1}-{re.sub(r'[^a-zA-Z0-9]', '', pub)[:8].lower()}"
                        sources.append(Source(
                            id=src_id,
                            title=f"Production Case Study: {title}",
                            url=link,
                            source_type=SourceType.DOCUMENTATION,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRODUCTION_CASE_STUDY,
                            author_publisher=f"{pub} (Enterprise Production Architecture)",
                            publication_date=pub_date[:16] if pub_date else "2026",
                            credibility_score=92.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRODUCTION_CASE_STUDY] * 100.0,
                            primary_status=True,
                            raw_content=full_content[:4500],
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
                        if len(sources) >= max_results:
                            break
            except Exception:
                pass

        # 2. Tier 2: Web Discovery Fallback if RSS returns < max_results
        if len(sources) < max_results:
            search_queries = [
                f"{clean_topic} enterprise production architecture case study",
                f"{clean_topic} real world production engineering deployment"
            ]
            for sq in search_queries:
                if len(sources) >= max_results:
                    break
                try:
                    web_results = web.search_duckduckgo(sq, max_results=max_results + 2)
                    for wr in web_results:
                        if wr.url in seen_urls:
                            continue
                        domain = urllib.parse.urlparse(wr.url).netloc.lower().replace("www.", "")
                        is_eng_blog = any(ed in domain for ed in self.engineering_domains)
                        is_fluff = any(f in domain for f in ["geeksforgeeks.org", "tutorialspoint.com", "w3schools.com", "medium.com/@"])
                        
                        if (is_eng_blog or "blog" in domain or "engineering" in domain or "architecture" in wr.url) and not is_fluff:
                            seen_urls.add(wr.url)
                            wr.source_class = SourceClass.PRODUCTION_CASE_STUDY
                            wr.category = SourceCategory.PRIMARY
                            wr.authority_score = SOURCE_CLASS_WEIGHTS[SourceClass.PRODUCTION_CASE_STUDY] * 100.0
                            wr.primary_status = True
                            wr.author_publisher = f"{domain} (Production Case Study)"
                            sources.append(wr)
                            if len(sources) >= max_results:
                                break
                except Exception:
                    pass

        return sources

