import re
import html
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

class HTMLTableToMarkdown:
    """
    Converts HTML <table> elements into clean Markdown tables.
    Preserves exact quantitative pricing tariffs, benchmark metrics, and comparisons.
    """
    @staticmethod
    def convert_tables(html_content: str) -> str:
        def table_replacer(match):
            table_html = match.group(0)
            rows = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', table_html, re.IGNORECASE)
            if not rows:
                return ""

            parsed_matrix: List[List[str]] = []
            for row in rows:
                cells = re.findall(r'<(?:td|th)[^>]*>([\s\S]*?)</(?:td|th)>', row, re.IGNORECASE)
                clean_cells = []
                for cell in cells:
                    cell_text = re.sub(r'<[^>]+>', ' ', cell)
                    cell_clean = " ".join(html.unescape(cell_text).split()).replace("|", "\\|")
                    clean_cells.append(cell_clean)
                if any(c for c in clean_cells):
                    parsed_matrix.append(clean_cells)

            if not parsed_matrix:
                return ""

            # Ensure all rows have equal column length
            max_cols = max(len(row) for row in parsed_matrix)
            for row in parsed_matrix:
                while len(row) < max_cols:
                    row.append("")

            md_lines = []
            # Header row
            header = parsed_matrix[0]
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join([":---"] * max_cols) + " |")

            # Data rows
            for row in parsed_matrix[1:]:
                md_lines.append("| " + " | ".join(row) + " |")

            return "\n\n" + "\n".join(md_lines) + "\n\n"

        # Replace all HTML tables
        content_with_md_tables = re.sub(r'<table[^>]*>([\s\S]*?)</table>', table_replacer, html_content, flags=re.IGNORECASE)
        return content_with_md_tables

class DeepWebCrawler:
    """
    Autonomous Deep Web Link Crawler & Full Content Extractor Engine:
    - Pure HTTP stream fetching (zero DOM / headless browser JS overhead)
    - Dynamic requirement-driven sub-link discovery (zero hardcoded URL paths or keywords)
    - Unlimited page content length extraction (zero character length truncations)
    - Preserves HTML tables as Markdown tables
    """
    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def fetch_raw_html(self, url: str) -> Tuple[str, str]:
        """Fetches raw HTML string and final redirected URL via fast HTTP stream."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": self.user_agents[0],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    final_url = resp.geturl()
                    html_bytes = resp.read()
                    html_str = html_bytes.decode("utf-8", errors="ignore")
                    return html_str, final_url
        except Exception:
            pass
        return "", url

    def extract_full_page_markdown(self, html_str: str) -> str:
        """
        Extracts 100% full text content without character length truncations.
        Preserves HTML tables as Markdown tables.
        """
        if not html_str:
            return ""

        # 1. Convert HTML tables to Markdown tables
        text_with_tables = HTMLTableToMarkdown.convert_tables(html_str)

        # 2. Strip non-content script/style/nav/footer tags
        text_clean = re.sub(r'<script[\s\S]*?</script>', '', text_with_tables, flags=re.IGNORECASE)
        text_clean = re.sub(r'<style[\s\S]*?</style>', '', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'<svg[\s\S]*?</svg>', '', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'<nav[\s\S]*?</nav>', '', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'<footer[\s\S]*?</footer>', '', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'<header[\s\S]*?</header>', '', text_clean, flags=re.IGNORECASE)

        # 3. Strip remaining HTML tags while preserving linebreaks for paragraphs
        text_clean = re.sub(r'</?(?:p|h[1-6]|li|div|blockquote)[^>]*>', '\n', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'<[^>]+>', ' ', text_clean)

        # 4. Unescape HTML entities
        text_clean = html.unescape(text_clean)

        # 5. Clean excess whitespace but retain full paragraph structure
        lines = [line.strip() for line in text_clean.split("\n")]
        non_empty_lines = [l for l in lines if l]

        # 100% full content returned - ZERO character limit truncation
        return "\n\n".join(non_empty_lines)

    def discover_dynamic_child_links(
        self,
        base_url: str,
        html_str: str,
        requirement_terms: List[str],
        max_child_links: int = 3
    ) -> List[str]:
        """
        Extracts and scores child links from HTML dynamically based on requirement token overlap.
        Zero hardcoded URL paths or domain-specific keyword lists.
        """
        if not html_str or not requirement_terms:
            return []

        base_parsed = urllib.parse.urlparse(base_url)
        base_domain = base_parsed.netloc.lower()

        # Extract all <a href="..."> links
        raw_links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', html_str, re.IGNORECASE)
        candidate_links: List[Tuple[str, str, float]] = []
        seen_urls: Set[str] = {base_url.rstrip("/")}

        clean_req_tokens = set()
        for term in requirement_terms:
            tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', term.lower())
            clean_req_tokens.update(tokens)

        stop_words = {"what", "how", "why", "the", "and", "for", "with", "from", "about", "this", "that", "http", "https", "com", "org"}
        active_tokens = clean_req_tokens - stop_words
        if not active_tokens:
            return []

        for href, anchor_text in raw_links:
            # Resolve relative URLs
            full_url = urllib.parse.urljoin(base_url, href)
            parsed_u = urllib.parse.urlparse(full_url)
            
            # Stay on the same target domain
            if parsed_u.netloc.lower() != base_domain:
                continue

            # Skip fragment-only links or static assets
            clean_href_path = parsed_u.path.lower()
            if any(clean_href_path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".svg", ".zip"]):
                continue

            clean_full_url = full_url.split("#")[0].rstrip("/")
            if clean_full_url in seen_urls:
                continue
            seen_urls.add(clean_full_url)

            # Score link dynamically based on anchor text and URL path token match
            link_search_text = (anchor_text + " " + parsed_u.path).lower()
            score = sum(1.0 for token in active_tokens if token in link_search_text)

            if score > 0.0:
                candidate_links.append((clean_full_url, anchor_text.strip(), score))

        # Sort candidate links by dynamic score
        candidate_links.sort(key=lambda x: x[2], reverse=True)
        return [url for url, _, _ in candidate_links[:max_child_links]]

    def crawl_and_extract_deep_source(
        self,
        target_url: str,
        requirement_terms: Optional[List[str]] = None,
        max_child_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Crawls target URL, extracts full untruncated content, and dynamically traverses child links.
        Returns dict with primary_content, child_contents, full_combined_text, and child_urls.
        """
        html_main, final_url = self.fetch_raw_html(target_url)
        if not html_main:
            return {
                "target_url": target_url,
                "final_url": target_url,
                "primary_content": "",
                "child_urls": [],
                "combined_text": ""
            }

        primary_markdown = self.extract_full_page_markdown(html_main)
        child_urls: List[str] = []
        child_markdowns: List[str] = []

        if requirement_terms and max_child_depth > 1:
            child_urls = self.discover_dynamic_child_links(
                base_url=final_url,
                html_str=html_main,
                requirement_terms=requirement_terms,
                max_child_links=2
            )

            # Fetch child links concurrently
            if child_urls:
                with ThreadPoolExecutor(max_workers=len(child_urls)) as executor:
                    future_to_url = {executor.submit(self.fetch_raw_html, c_url): c_url for c_url in child_urls}
                    for future in as_completed(future_to_url):
                        try:
                            c_html, c_final = future.result()
                            if c_html:
                                c_md = self.extract_full_page_markdown(c_html)
                                if len(c_md) > 100:
                                    child_markdowns.append(f"\n--- Sub-Page Documentation [{c_final}] ---\n" + c_md)
                        except Exception:
                            pass

        combined_text_parts = [primary_markdown] + child_markdowns
        full_combined_text = "\n\n".join(combined_text_parts)

        return {
            "target_url": target_url,
            "final_url": final_url,
            "primary_content": primary_markdown,
            "child_urls": child_urls,
            "combined_text": full_combined_text
        }

# Global Deep Web Crawler Singleton
deep_web_crawler = DeepWebCrawler()
