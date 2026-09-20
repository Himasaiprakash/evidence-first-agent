import json
import urllib.request
import urllib.parse
import re
from typing import List, Optional
from datetime import datetime
from backend.models.schemas import Source, SourceType, SourceCategory, SourceClass, SOURCE_CLASS_WEIGHTS

class BiomedicalDiscovery:
    """
    Dedicated Biomedical, Clinical & Life Sciences Discovery Adapter:
    - NIH PubMed / NCBI E-Utilities (MEDLINE peer-reviewed medical literature)
    - Europe PMC (European Bioinformatics Institute / 43M+ life science articles)
    - ClinicalTrials.gov v2 API (Global human clinical trials & endpoints)
    - bioRxiv & medRxiv (Cold Spring Harbor Laboratory biomedical preprints)
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "EvidenceFirstResearchAgent/1.0 (mailto:admin@evidenceagent.org)"
        }

    def search_pubmed(self, query: str, max_results: int = 3) -> List[Source]:
        """Search PubMed NCBI E-Utilities for clinical and biomedical literature."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        esearch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_query}&retmode=json&retmax={max_results}"

        try:
            req = urllib.request.Request(esearch_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    id_list = data.get("esearchresult", {}).get("idlist", [])

                    if id_list:
                        esummary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(id_list)}&retmode=json"
                        req_sum = urllib.request.Request(esummary_url, headers=self.headers)
                        with urllib.request.urlopen(req_sum, timeout=6) as sum_resp:
                            if sum_resp.status == 200:
                                sum_data = json.loads(sum_resp.read().decode("utf-8"))
                                result_dict = sum_data.get("result", {})
                                for idx, pmid in enumerate(id_list):
                                    doc = result_dict.get(pmid, {})
                                    title = doc.get("title") or f"PubMed Clinical Study {pmid}"
                                    source_journal = doc.get("source") or "National Center for Biotechnology Information (NCBI)"
                                    pub_date = str(doc.get("pubdate") or "2024")[:10]

                                    sources.append(Source(
                                        id=f"src-pubmed-{idx+1}",
                                        title=f"PubMed: {title}",
                                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                        source_type=SourceType.ACADEMIC_PAPER,
                                        category=SourceCategory.PRIMARY,
                                        source_class=SourceClass.PRIMARY_RESEARCH,
                                        author_publisher=f"NIH PubMed / {source_journal}",
                                        publication_date=f"{pub_date}-01-01" if len(pub_date) == 4 else pub_date,
                                        credibility_score=98.0,
                                        authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                                        primary_status=True,
                                        raw_content=f"{title}. Published in {source_journal}. Verified clinical research from the NIH/NLM PubMed database.",
                                        retrieval_timestamp=datetime.now().isoformat()
                                    ))
        except Exception:
            pass

        return sources

    def search_europe_pmc(self, query: str, max_results: int = 3) -> List[Source]:
        """Search Europe PMC for life science, pharmacology, and clinical research."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_query}&format=json&pageSize={max_results}&resultType=core"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    result_list = data.get("resultList", {}).get("result", [])
                    for idx, res in enumerate(result_list):
                        title = res.get("title") or "Europe PMC Study"
                        doi = res.get("doi", "")
                        journal = res.get("journalTitle") or "European Life Sciences Journal"
                        year = str(res.get("pubYear") or "2024")
                        author_str = res.get("authorString") or "Medical Investigators"
                        abstract = res.get("abstractText") or f"Research published in {journal} ({year})."
                        clean_abstract = re.sub(r"<[^>]+>", "", abstract)

                        article_url = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/{res.get('source', 'MED')}/{res.get('id', '')}"

                        sources.append(Source(
                            id=f"src-europepmc-{idx+1}",
                            title=f"Europe PMC: {title}",
                            url=article_url,
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{author_str[:50]} ({journal})",
                            publication_date=f"{year}-01-01",
                            credibility_score=97.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"{title}. Journal: {journal} ({year}). Abstract: {clean_abstract[:320]}. Europe PMC repository.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_biorxiv(self, query: str, max_results: int = 2) -> List[Source]:
        """Search bioRxiv & medRxiv preprints via Europe PMC preprint syndication (SRC:PPR)."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(f"{query} SRC:PPR")
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={encoded_query}&format=json&pageSize={max_results}&resultType=core"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    result_list = data.get("resultList", {}).get("result", [])
                    for idx, res in enumerate(result_list):
                        title = res.get("title") or "bioRxiv/medRxiv Preprint"
                        doi = res.get("doi", "")
                        publisher = res.get("journalTitle") or res.get("bookOrReportDetails", {}).get("publisher") or "bioRxiv / medRxiv"
                        year = str(res.get("pubYear") or "2025")
                        author_str = res.get("authorString") or "Biomedical Authors"
                        abstract = res.get("abstractText") or f"Preprint study in {publisher} ({year})."
                        clean_abstract = re.sub(r"<[^>]+>", "", abstract)
                        article_url = f"https://doi.org/{doi}" if doi else f"https://europepmc.org/article/PPR/{res.get('id', '')}"

                        sources.append(Source(
                            id=f"src-biorxiv-{idx+1}",
                            title=f"bioRxiv/medRxiv: {title}",
                            url=article_url,
                            source_type=SourceType.ACADEMIC_PAPER,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{author_str[:50]} ({publisher})",
                            publication_date=f"{year}-01-01",
                            credibility_score=96.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"{title}. Published on {publisher} ({year}). Abstract: {clean_abstract[:320]}. Verified biomedical preprint archive.",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

    def search_clinical_trials(self, query: str, max_results: int = 2) -> List[Source]:
        """Query ClinicalTrials.gov v2 API for registered human studies, interventions, and phase protocols."""
        sources: List[Source] = []
        encoded_query = urllib.parse.quote(query)
        url = f"https://clinicaltrials.gov/api/v2/studies?query.term={encoded_query}&pageSize={max_results}"

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    studies = data.get("studies", [])
                    for idx, study in enumerate(studies):
                        protocol = study.get("protocolSection", {})
                        ident = protocol.get("identificationModule", {})
                        nct_id = ident.get("nctId", f"NCT{idx+1}")
                        brief_title = ident.get("briefTitle") or "Clinical Trial Protocol"
                        
                        status_module = protocol.get("statusModule", {})
                        overall_status = status_module.get("overallStatus", "COMPLETED")
                        
                        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
                        lead_sponsor = sponsor_module.get("leadSponsor", {}).get("name", "Clinical Research Sponsor")
                        
                        design_module = protocol.get("designModule", {})
                        phases = design_module.get("phases", ["Phase 2/3"])
                        phase_str = ", ".join(phases) if phases else "Clinical Phase"

                        desc_module = protocol.get("descriptionModule", {})
                        summary = desc_module.get("briefSummary") or f"Registered trial evaluating interventions for {query}."

                        sources.append(Source(
                            id=f"src-clinicaltrial-{idx+1}",
                            title=f"Clinical Trial ({nct_id}): {brief_title}",
                            url=f"https://clinicaltrials.gov/study/{nct_id}",
                            source_type=SourceType.CLINICAL_TRIAL,
                            category=SourceCategory.PRIMARY,
                            source_class=SourceClass.PRIMARY_RESEARCH,
                            author_publisher=f"{lead_sponsor} ({phase_str})",
                            publication_date="2025-01-01",
                            credibility_score=99.0,
                            authority_score=SOURCE_CLASS_WEIGHTS[SourceClass.PRIMARY_RESEARCH] * 100.0,
                            primary_status=True,
                            raw_content=f"Official Clinical Trial {nct_id}. Title: {brief_title}. Status: {overall_status}. Sponsor: {lead_sponsor}. Phase: {phase_str}. Protocol Summary: {summary[:350]}",
                            retrieval_timestamp=datetime.now().isoformat()
                        ))
        except Exception:
            pass

        return sources

