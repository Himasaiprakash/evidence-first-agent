import json
import urllib.request
import urllib.parse
import re
import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, DomainType, SourceClass, SOURCE_CLASS_WEIGHTS
from backend.research.taxonomy import domain_taxonomy
from backend.research.discovery.deep_web_crawler import deep_web_crawler

class WebDiscovery:
    """
    Real Web Discovery Adapter:
    - Automatically discovers canonical and sub-topic articles via Wikipedia OpenSearch & REST API
    - Fetches rich, comprehensive multi-paragraph content across anatomy, pathology, benchmarks, and architecture
    - Queries DuckDuckGo for live domain articles, educational docs, and reference guides
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceResearchBot/2.0 (contact@evidence-research.org)"
        }

    def _classify_web_domain(self, url: str) -> tuple:
        """Classifies arbitrary web URLs into deterministic SourceClass and authority score."""
        domain = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        if "wikipedia.org" in domain or "wikimedia.org" in domain:
            return SourceClass.WIKIPEDIA, SOURCE_CLASS_WEIGHTS[SourceClass.WIKIPEDIA] * 100.0, SourceCategory.TERTIARY, False
        if any(f in domain for f in ["stackoverflow.com", "reddit.com", "stackexchange.com", "quora.com"]):
            return SourceClass.FORUM, SOURCE_CLASS_WEIGHTS[SourceClass.FORUM] * 100.0, SourceCategory.COMMUNITY, False
        # Tutorial & aggregator blogs: explicit downgrade to BLOG (20.0)
        if any(t in domain for t in [
            "geeksforgeeks.org", "tutorialspoint.com", "javatpoint.com", "simplilearn.com",
            "w3schools.com", "towardsdatascience.com", "analyticsvidhya.com", "baeldung.com",
            "freecodecamp.org", "guru99.com"
        ]):
            return SourceClass.BLOG, SOURCE_CLASS_WEIGHTS[SourceClass.BLOG] * 100.0, SourceCategory.COMMUNITY, False
        if any(b in domain for b in ["medium.com", "blogspot.com", "wordpress.com", "substack.com"]):
            return SourceClass.BLOG, SOURCE_CLASS_WEIGHTS[SourceClass.BLOG] * 100.0, SourceCategory.COMMUNITY, False
        if any(n in domain for n in ["reuters.com", "bloomberg.com", "apnews.com", "ft.com", "wsj.com", "bbc.com", "theguardian.com"]):
            return SourceClass.NEWS, SOURCE_CLASS_WEIGHTS[SourceClass.NEWS] * 100.0, SourceCategory.SECONDARY, False
        if any(d in domain for d in ["docs.", "documentation", "github.io", "developer.", "ietf.org", "w3.org", "nist.gov", "python.org", "kubernetes.io"]):
            return SourceClass.OFFICIAL_DOCUMENTATION, SOURCE_CLASS_WEIGHTS[SourceClass.OFFICIAL_DOCUMENTATION] * 100.0, SourceCategory.PRIMARY, True
        return SourceClass.SECONDARY_RESEARCH, SOURCE_CLASS_WEIGHTS[SourceClass.SECONDARY_RESEARCH] * 100.0, SourceCategory.SECONDARY, False

    def search_wikipedia_multi(self, topic: str, domain: DomainType) -> List[Source]:
        """Fetch canonical entry plus domain-specific sub-articles from Wikipedia."""
        import time
        sources: List[Source] = []
        clean_topic = topic.strip()
        t_low = clean_topic.lower()

        slug_candidates = [
            clean_topic.replace(" ", "_"),
            clean_topic.title().replace(" ", "_")
        ]


        hints = domain_taxonomy.get_domain_hints(domain)

        clean_base = clean_topic.split("\n")[0].split(":")[0].strip()
        sub_terms = re.split(r"\b(?:vs\.?|versus|compared to|comparison|between|and|or|for|with)\b|,", clean_base, flags=re.IGNORECASE)
        capitalized_entities = [w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_-]+\b", clean_base) if len(w) >= 3]
        search_terms = [clean_base] + [p.strip() for p in sub_terms if len(p.strip()) >= 2] + capitalized_entities

        for term in search_terms[:6]:
            clean_term = re.sub(r"^(what (is|are)|how (does|to)|compare|benchmark)\s+", "", term, flags=re.IGNORECASE).strip()
            if len(clean_term) < 2:
                continue
            slug_candidates.append(clean_term.replace(" ", "_"))
            slug_candidates.append(clean_term.title().replace(" ", "_"))

            # 1. OpenSearch prefix search
            try:
                opensearch_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_term)}&limit=4&namespace=0&format=json"
                req = urllib.request.Request(opensearch_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if len(data) > 1 and isinstance(data[1], list):
                            for title in data[1]:
                                slug_candidates.append(title.replace(" ", "_"))
            except Exception:
                pass

            # 2. Semantic full-text search with domain hint for acronyms/short terms
            if hints and len(clean_term.split()) <= 2:
                try:
                    search_q = f"{clean_term} {hints[0]}"
                    sr_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(search_q)}&format=json&srlimit=3"
                    req2 = urllib.request.Request(sr_url, headers=self.headers)
                    with urllib.request.urlopen(req2, timeout=4) as resp2:
                        if resp2.status == 200:
                            s_data = json.loads(resp2.read().decode("utf-8"))
                            for hit in s_data.get("query", {}).get("search", []):
                                slug_candidates.append(hit.get("title", "").replace(" ", "_"))
                except Exception:
                    pass

        seen_slugs = set()
        clean_slugs = []
        for slug in slug_candidates:
            s_clean = slug.strip().replace(" ", "_")
            if s_clean.lower() not in seen_slugs and len(s_clean) > 1:
                seen_slugs.add(s_clean.lower())
                clean_slugs.append(s_clean)

        # Query Wikipedia API for full text extracts with redirects=1 and pageprops for disambiguation
        idx = 0
        while idx < len(clean_slugs) and len(sources) < 6 and idx < 12:
            slug = clean_slugs[idx]
            idx += 1
            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts|pageprops|links&pllimit=50&explaintext=1&redirects=1&titles={urllib.parse.quote(slug)}&format=json"
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        pages = data.get("query", {}).get("pages", {})
                        for pid, p in pages.items():
                            if pid == "-1":
                                continue
                            title = p.get("title", "")
                            extract = p.get("extract", "").strip()
                            t_lower = title.lower()
                            ext_lower = extract[:400].lower()

                            # Disambiguation Check: NEVER ingest disambiguation pages as documentation!
                            is_disambig = (
                                "disambiguation" in p.get("pageprops", {}) or
                                "may refer to:" in ext_lower or
                                "(disambiguation)" in t_lower
                            )
                            if is_disambig:
                                # Resolve links on disambiguation page that align with domain or match acronyms
                                links = [l.get("title", "") for l in p.get("links", [])]
                                for l in links:
                                    l_lower = l.lower()
                                    l_acronym = "".join([w[0].upper() for w in re.findall(r"\b[a-zA-Z]", l)])
                                    is_match = (
                                        any(h in l_lower for h in hints) or
                                        any(w in l_lower for w in clean_base.lower().split() if len(w) > 2) or
                                        any(st.upper() == l_acronym for st in search_terms if len(st) >= 2)
                                    )
                                    if is_match:
                                        l_slug = l.replace(" ", "_")
                                        if l_slug.lower() not in seen_slugs:
                                            seen_slugs.add(l_slug.lower())
                                            clean_slugs.append(l_slug)
                                continue

                            # Universal Entertainment / Homonym Collision Filter
                            if any(disq in t_lower for disq in ["(film)", "(album)", "(song)", "(river)", "(novel)", "(video game)", "(play)", "(tv series)", "(cricket)", "(football)", "(athlete)", "(musician)"]):
                                continue

                            # Cross-Domain Collision Filter
                            if domain == DomainType.AI_TECHNOLOGY:
                                if any(disq in t_lower for disq in ["(physics)", "(astronomy)", "(music)"]):
                                    continue
                                if any(disq in ext_lower for disq in ["piece of old cloth", "tattered clothes", "fine-tuned universe", "anthropic principle", "hip hop group", "silent film", "viking ruler", "javelin thrower"]):
                                    continue
                                ai_kw = ["neural", "language model", "deep learning", "machine learning", "transformer", "artificial intelligence", "nlp", "training", "weights", "fine-tuning", "retrieval", "augmented", "generation", "vector", "prompt", "parameters", "algorithm", "inference", "computing", "software"]
                                if not any(k in (t_lower + " " + ext_lower) for k in ai_kw):
                                    continue
                            elif domain == DomainType.FINANCE_COMMERCE:
                                fin_kw = ["finance", "economy", "economic", "market", "banking", "bank", "monetary", "fiscal", "reserve", "treasury", "interest", "capital", "debt", "bond", "liquidity", "inflation", "asset", "securities", "trade", "investment", "currency", "central bank", "tightening", "easing", "repo", "repurchase"]
                                if not any(k in (t_lower + " " + ext_lower) for k in fin_kw):
                                    continue

                            if len(extract) > 120:
                                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                                if not any(s.url == page_url for s in sources):
                                    src_id = f"src-wiki-{re.sub(r'[^a-zA-Z0-9]', '_', title.lower())[:16]}"
                                    sources.append(Source(
                                        id=src_id,
                                        title=f"Wikipedia: {title}",
                                        url=page_url,
                                        source_type=SourceType.DOCUMENTATION,
                                        category=SourceCategory.TERTIARY,
                                        source_class=SourceClass.WIKIPEDIA,
                                        author_publisher="Wikimedia Foundation (Wikipedia Tertiary Overview)",
                                        publication_date="2025-01-01",
                                        credibility_score=65.0,
                                        authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.WIKIPEDIA] * 100.0,
                                        primary_status=False,
                                        raw_content=extract[:3500],
                                        retrieval_timestamp=datetime.now().isoformat()
                                    ))
            except Exception:
                pass
            time.sleep(0.10)

        return sources

    def fetch_web_page(self, url: str, requirement_terms: Optional[List[str]] = None) -> str:
        """Fetch and extract 100% full readable markdown text from a live web page with dynamic child link crawling."""
        res = deep_web_crawler.crawl_and_extract_deep_source(url, requirement_terms=requirement_terms)
        return res.get("combined_text", "")

    def search_duckduckgo(self, query: str, max_results: int = 3) -> List[Source]:
        """Search DuckDuckGo Lite for live web documentation and scrape authoritative pages with robust fallback."""
        sources: List[Source] = []
        clean_q = re.sub(r'["\']', '', query).strip()
        if not clean_q:
            return sources

        try:
            url = "https://lite.duckduckgo.com/lite/"
            data = urllib.parse.urlencode({"q": clean_q}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                titles = re.findall(r'<a rel=[\'"]nofollow[\'"] href=[\'"]([^\'"]+)[\'"][^>]*class=[\'"]result-link[\'"]>([\s\S]*?)</a>', html)
                snippets = re.findall(r'<td class=[\'"]result-snippet[\'"]>([\s\S]*?)</td>', html)

                parsed_items = []
                for idx in range(min(max_results, len(titles))):
                    raw_url = titles[idx][0]
                    title = re.sub(r"<[^>]+>", "", titles[idx][1]).strip()
                    snippet = re.sub(r"<[^>]+>", "", snippets[idx]).strip() if idx < len(snippets) else ""

                    actual_url = raw_url
                    if "/uddg=" in raw_url:
                        m = re.search(r"/uddg=([^&]+)", raw_url)
                        if m:
                            actual_url = urllib.parse.unquote(m.group(1))
                    elif "duckduckgo.com/l/?uddg=" in raw_url:
                        m = re.search(r"uddg=([^&]+)", raw_url)
                        if m:
                            actual_url = urllib.parse.unquote(m.group(1))

                    if actual_url.startswith("http"):
                        parsed_items.append((idx, title, snippet, actual_url))

                if parsed_items:
                    import concurrent.futures
                    req_terms = clean_q.split()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(parsed_items)) as executor:
                        future_to_item = {
                            executor.submit(deep_web_crawler.crawl_and_extract_deep_source, item[3], req_terms): item
                            for item in parsed_items
                        }
                        for future in concurrent.futures.as_completed(future_to_item):
                            idx, title, snippet, actual_url = future_to_item[future]
                            try:
                                crawl_res = future.result()
                                page_text = crawl_res.get("combined_text", "")
                            except Exception:
                                page_text = ""

                            full_content = f"Title: {title}. URL: {actual_url}\nSummary: {snippet}"
                            if page_text and len(page_text) > 100:
                                full_content += f"\nDetailed Content:\n{page_text}"

                            domain_name = urllib.parse.urlparse(actual_url).netloc or "Live Web"
                            src_id = f"src-web-{idx+1}-{re.sub(r'[^a-zA-Z0-9]', '', domain_name)[:8]}"
                            s_class, s_auth, s_cat, s_primary = self._classify_web_domain(actual_url)
                            sources.append(Source(
                                id=src_id,
                                title=f"{title} ({domain_name})",
                                url=actual_url,
                                source_type=SourceType.DOCUMENTATION,
                                category=s_cat,
                                source_class=s_class,
                                author_publisher=f"{domain_name} (Live Web Documentation)",
                                publication_date=datetime.now().strftime("%Y-%m-%d"),
                                credibility_score=75.0,
                                authority_score=s_auth,
                                primary_status=s_primary,
                                raw_content=full_content,
                                retrieval_timestamp=datetime.now().isoformat()
                            ))
        except Exception as e:
            print(f"  [DISCOVERY WARNING] DuckDuckGo Lite live search failed for '{clean_q}': {e}")

        # Resilient Multi-Tier Fallback: If DuckDuckGo returned 0 results (due to bot challenge)
        if not sources:
            # 1. Live Web Search via Bing Search Engine (extracts real pages with live content)
            sources = self.search_bing(clean_q, max_results=max_results)

        if not sources:
            # 2. Google News RSS Live Ingestion
            try:
                rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_q)}&hl=en-US&gl=US&ceid=US:en"
                rss_req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(rss_req, timeout=5) as resp:
                    root = ET.fromstring(resp.read().decode("utf-8", errors="ignore"))
                    items = root.findall(".//item")
                    for idx, item in enumerate(items[:max_results]):
                        t = item.find("title").text if item.find("title") is not None else clean_q
                        l = item.find("link").text if item.find("link") is not None else ""
                        pub = item.find("source").text if item.find("source") is not None else "Google News"
                        pub_date = item.find("pubDate").text if item.find("pubDate") is not None else datetime.now().strftime("%Y-%m-%d")
                        sources.append(Source(
                            id=f"src-news-rss-{idx+1}",
                            title=f"Press: {t}",
                            url=l,
                            source_type=SourceType.NEWS,
                            category=SourceCategory.SECONDARY,
                            source_class=SourceClass.NEWS,
                            author_publisher=pub,
                            publication_date=pub_date[:16] if pub_date else "2026",
                            credibility_score=70.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.NEWS] * 100.0,
                            primary_status=False,
                            raw_content=f"Headline: {t}\nPublisher: {pub}\nPublished: {pub_date}\nLink: {l}",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
            except Exception as ne:
                print(f"  [DISCOVERY WARNING] Google News RSS fallback failed: {ne}")

            # 2. Autonomous Live Web & Documentation Discovery via Wikipedia Full-Text Search & External Documentation
            try:
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&utf8=&format=json&srlimit=4"
                s_req = urllib.request.Request(search_url, headers=self.headers)
                with urllib.request.urlopen(s_req, timeout=5) as s_resp:
                    if s_resp.status == 200:
                        s_data = json.loads(s_resp.read().decode("utf-8"))
                        search_hits = s_data.get("query", {}).get("search", [])
                        candidate_titles = [hit.get("title", "") for hit in search_hits if hit.get("title")]

                        for c_title in candidate_titles[:3]:
                            # Query external links for primary documentation and technical release sites
                            el_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extlinks&titles={urllib.parse.quote(c_title)}&ellimit=8&format=json"
                            el_req = urllib.request.Request(el_url, headers=self.headers)
                            try:
                                with urllib.request.urlopen(el_req, timeout=4) as el_resp:
                                    if el_resp.status == 200:
                                        el_data = json.loads(el_resp.read().decode("utf-8"))
                                        pages = el_data.get("query", {}).get("pages", {})
                                        for _, p_val in pages.items():
                                            extlinks = p_val.get("extlinks", [])
                                            for el in extlinks[:3]:
                                                raw_ext_url = el.get("*", "")
                                                if not raw_ext_url.startswith("http") or any(skip in raw_ext_url.lower() for skip in ["twitter.com", "facebook.com", "instagram.com", "youtube.com", "archive.org", "w3.org"]):
                                                    continue
                                                if any(s.url == raw_ext_url for s in sources):
                                                    continue

                                                scraped_text = self.fetch_web_page(raw_ext_url, timeout=5)
                                                if scraped_text and len(scraped_text) > 250:
                                                    domain_name = urllib.parse.urlparse(raw_ext_url).netloc
                                                    src_id = f"src-web-doc-{re.sub(r'[^a-zA-Z0-9]', '', domain_name)[:12]}"
                                                    s_class, s_auth, s_cat, s_primary = self._classify_web_domain(raw_ext_url)
                                                    sources.append(Source(
                                                        id=src_id,
                                                        title=f"Documentation: {c_title} ({domain_name})",
                                                        url=raw_ext_url,
                                                        source_type=SourceType.DOCUMENTATION,
                                                        category=s_cat,
                                                        source_class=s_class,
                                                        author_publisher=domain_name,
                                                        publication_date=datetime.now().strftime("%Y-%m-%d"),
                                                        credibility_score=80.0,
                                                        authority_score=s_auth,
                                                        primary_status=s_primary,
                                                        raw_content=f"Title: {c_title}\nURL: {raw_ext_url}\nScraped Live Content:\n{scraped_text[:4500]}",
                                                        retrieval_timestamp=datetime.now().isoformat()
                                                    ))
                                                    if len(sources) >= max_results + 3:
                                                        break
                            except Exception:
                                pass
            except Exception as we:
                print(f"  [DISCOVERY WARNING] Autonomous web documentation discovery failed: {we}")

        return sources

    def search_bing(self, query: str, max_results: int = 3) -> List[Source]:
        """Search Bing for live authoritative web pages and scrape content."""
        sources: List[Source] = []
        clean_q = re.sub(r'["\']', '', query).strip()
        if not clean_q:
            return sources

        try:
            import html as html_module
            import base64
            url = f"https://www.bing.com/search?q={urllib.parse.quote(clean_q)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                page_html = resp.read().decode("utf-8", errors="ignore")

            algo_blocks = re.findall(r'<li class="b_algo"[^>]*>([\s\S]*?)</li>', page_html)
            parsed_items = []
            for block in algo_blocks[:max_results]:
                title_m = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', block)
                if not title_m:
                    continue
                raw_href, raw_title = title_m.group(1), title_m.group(2)
                clean_title = re.sub('<[^>]+>', '', raw_title).strip()
                clean_href = html_module.unescape(raw_href)
                dest_url = clean_href
                u_m = re.search(r'[?&]u=a1([a-zA-Z0-9_-]+)', clean_href)
                if u_m:
                    b64 = u_m.group(1)
                    padded = b64 + '=' * (-len(b64) % 4)
                    try:
                        dest_url = base64.b64decode(padded.replace('-', '+').replace('_', '/')).decode('utf-8', errors='ignore')
                    except Exception:
                        pass

                snippet_m = re.search(r'<p[^>]*class="[^"]*b_lineclamp[^"]*"[^>]*>([\s\S]*?)</p>', block) or re.search(r'<p[^>]*>([\s\S]*?)</p>', block)
                clean_snippet = re.sub('<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ''

                if dest_url.startswith("http"):
                    parsed_items.append((len(parsed_items), clean_title, clean_snippet, dest_url))

            if parsed_items:
                import concurrent.futures
                req_terms = clean_q.split()
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(parsed_items)) as executor:
                    future_to_item = {
                        executor.submit(deep_web_crawler.crawl_and_extract_deep_source, item[3], req_terms): item
                        for item in parsed_items
                    }
                    for future in concurrent.futures.as_completed(future_to_item):
                        idx, title, snippet, actual_url = future_to_item[future]
                        try:
                            crawl_res = future.result()
                            page_text = crawl_res.get("combined_text", "")
                        except Exception:
                            page_text = ""

                        full_content = f"Title: {title}. URL: {actual_url}\nSummary: {snippet}"
                        if page_text and len(page_text) > 100:
                            full_content += f"\nDetailed Content:\n{page_text}"

                        domain_name = urllib.parse.urlparse(actual_url).netloc or "Live Web"
                        src_id = f"src-web-{idx+1}-{re.sub(r'[^a-zA-Z0-9]', '', domain_name)[:8]}"
                        s_class, s_auth, s_cat, s_primary = self._classify_web_domain(actual_url)
                        sources.append(Source(
                            id=src_id,
                            title=f"{title} ({domain_name})",
                            url=actual_url,
                            source_type=SourceType.DOCUMENTATION,
                            category=s_cat,
                            source_class=s_class,
                            author_publisher=f"{domain_name} (Live Web)",
                            publication_date=datetime.now().strftime("%Y-%m-%d"),
                            credibility_score=75.0,
                            authority_score=s_auth,
                            primary_status=s_primary,
                            raw_content=full_content,
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception as e:
            print(f"  [DISCOVERY WARNING] Bing live search failed for '{clean_q}': {e}")

        return sources

