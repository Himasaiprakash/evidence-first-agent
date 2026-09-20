import re
from typing import List, Tuple, Set
from backend.models.schemas import Source, RejectedSource, RelevanceLevel, DomainType, SourceCategory, SourceType, SourceClass

class SourceRelevanceGate:
    """
    Strict Multi-Tier Source Relevance Gate:
    - Filters out online course advertisements, promotional marketing, and spam
    - Enforces strict word-boundary matching and homonym disambiguation
    - Enforces Epistemic Source Classification: Tertiary sources (Wikipedia, Wikidata) are barred from formal evidence
    - Filters out unrelated name collisions (e.g. Rishi Sunak, Sunderland AFC, Sunni Islam when researching the Sun)
    - Enforces hard domain-boundary rules
    """
    def filter_sources(self, topic: str, domain: DomainType, sources: List[Source]) -> Tuple[List[Source], List[RejectedSource]]:
        accepted_sources: List[Source] = []
        rejected_sources: List[RejectedSource] = []

        GENERIC_STOP_NOUNS = {
            "comparison", "comparisons", "model", "models", "analysis", "study",
            "overview", "system", "systems", "approach", "evaluation", "framework",
            "review", "investigation", "methods", "methodology", "techniques",
            "determine", "when", "combination", "technically", "economically",
            "preferable", "benchmarks", "benchmark", "real", "production", "evidence",
            "rather", "than", "generic", "explanations", "explanation", "guide",
            "trade-offs", "tradeoffs", "tradeoff", "trade", "offs", "vs", "versus",
            "landscape", "foundations", "paradigm", "paradigms", "perspective"
        }

        # Isolate clean topic from user instructions or guidance after colon or newline
        topic_clean = topic.split("\n")[0].split(":")[0].strip().lower()
        topic_words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", topic_clean)]
        
        # Pick the most distinctive noun, avoiding generic words
        distinctive_words = [w for w in topic_words if w not in GENERIC_STOP_NOUNS]
        primary_noun = distinctive_words[-1] if distinctive_words else (topic_words[-1] if topic_words else topic_clean)

        for src in sources:
            score, level, reason = self.evaluate_source(topic_clean, topic_words, primary_noun, domain, src)
            
            src.relevance_score = score
            src.relevance_level = level

            if level in [RelevanceLevel.DIRECT, RelevanceLevel.RELATED] and score >= 0.60:
                accepted_sources.append(src)
            else:
                rejected_sources.append(RejectedSource(
                    id=src.id,
                    title=src.title,
                    url=src.url,
                    reason=reason,
                    relevance_score=score,
                    relevance_level=level,
                    retrieval_query=getattr(src, "retrieval_query", ""),
                    discovery_engine=getattr(src, "discovery_engine", ""),
                    phase=getattr(src, "phase", "")
                ))

        return accepted_sources, rejected_sources

    def evaluate_source(self, topic: str, topic_words: list, primary_noun: str, domain: DomainType, source: Source) -> Tuple[float, RelevanceLevel, str]:
        title_lower = source.title.lower()
        content_lower = (source.raw_content or "").lower()
        combined_text = f"{title_lower} {content_lower}"

        GENERIC_STOP_NOUNS = {
            "comparison", "comparisons", "model", "models", "analysis", "study",
            "overview", "system", "systems", "approach", "evaluation", "framework",
            "review", "investigation", "methods", "methodology", "techniques",
            "determine", "when", "combination", "technically", "economically",
            "preferable", "benchmarks", "benchmark", "real", "production", "evidence",
            "rather", "than", "generic", "explanations", "explanation", "guide",
            "trade-offs", "tradeoffs", "tradeoff", "trade", "offs", "vs", "versus",
            "landscape", "foundations", "paradigm", "paradigms", "perspective"
        }

        # 0. Strict Epistemic Hierarchy: Tertiary sources (Wikidata / generic encyclopedic tertiary) are discovery aids ONLY.
        if (source.category == SourceCategory.TERTIARY or 
            "wikidata.org" in (source.url or "").lower() or
            source.id.startswith("svgsrc-wiki") or 
            source.id.startswith("src-wiki") or
            source.id.startswith("src-kg-")):
            return 0.15, RelevanceLevel.CONTEXTUAL, "Rejected as Primary Evidence: Tertiary source (Wikidata/Overview) is restricted to orientation and barred from formal evidence dossiers."

        # 0b. Reject Disambiguation stubs immediately
        if source.title.lower().endswith("(disambiguation)") or "may refer to:" in (source.raw_content or "").lower()[:300]:
            return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: Disambiguation stub page barred from evidence."

        # 1. Reject Online Course Ads & Promotional Marketing
        ad_keywords = ["join over", "enroll now", "online course", "course certificate", "sign up free", "buy now", "special offer", "coursera.org", "deeplearning.ai | andrew"]
        if any(ad in combined_text for ad in ad_keywords):
            return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: Promotional course advertisement or commercial marketing page."

        # 2. Celestial Body "Sun" Disambiguation Guard
        if topic == "sun" or topic == "the sun":
            if re.search(r"\b(sunak|sunderland|sunni|sun yat-sen|scene recognition|sun database|skin type|sunscreen|tanning)\b", combined_text):
                return 0.05, RelevanceLevel.IRRELEVANT, f"Rejected: Homonym match ({source.title}) unrelated to astronomical star 'Sun'."
            astro_keywords = ["star", "solar", "photosphere", "corona", "chromosphere", "fusion", "plasma", "heliosphere", "luminosity", "sunspot", "astronomy", "astrophysics", "mass", "earth", "radiation", "chemical", "composition"]
            if not any(k in combined_text for k in astro_keywords):
                return 0.10, RelevanceLevel.IRRELEVANT, "Rejected: Source lacks astronomical solar physics terminology."

        # 3. Gaming Feature Collisions for Deep Learning
        if topic == "deep learning" or topic == "neural network":
            if any(g in title_lower for g in ["super sampling", "anti-aliasing", "photoacoustic"]):
                return 0.10, RelevanceLevel.TANGENTIAL, "Rejected: Specialized graphics/hardware feature rather than foundational deep learning."

        # 4a. Medical / Biological Domain Guard
        if domain == DomainType.MEDICINE_BIOLOGY:
            ai_cs_terms = ["artificial intelligence", "large language model", "neural network", "vqa", "data protection", "data controller", "software", "privacy control", "image retrieval"]
            has_cs_term = any(t in title_lower or t in content_lower for t in ai_cs_terms)
            has_bio_term = any(t in combined_text for t in ["organ", "cardiac", "myocardium", "ventricle", "atrium", "valve", "blood", "circulation", "artery", "cardiovascular", "anatomy", "tissue", "biology", "gene", "protein", "dna", "cell"])
            if has_cs_term and not has_bio_term:
                return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: CS/AI paper lacking physiological/medical context."

        # 4b. Environmental, Physical, History, and Finance Domain Guard
        if domain in [DomainType.ENVIRONMENTAL_TOXICOLOGY, DomainType.PHYSICAL_SCIENCE, DomainType.HISTORY_HUMANITIES, DomainType.FINANCE_COMMERCE]:
            is_ai_topic = any(k in topic.lower() for k in ["ai", "llm", "language model", "gpt", "neural", "deep learning", "transformer", "prompt"])
            if not is_ai_topic:
                if any(t in title_lower for t in ["language models", "large language model", "prompt engineering", "sft + grpo", "neural network", "llms", "language model"]):
                    return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: CS/AI NLP paper lacking domain context."
            if not re.search(r"\b" + re.escape(primary_noun) + r"\b", combined_text):
                return 0.05, RelevanceLevel.IRRELEVANT, f"Rejected: Source lacks domain terminology for '{topic}'."

        # 4c. AI & Computing Domain Guard
        if domain == DomainType.AI_TECHNOLOGY:
            # Reject clinical / medical multiple choice exams when researching general model comparison
            if not any(k in topic for k in ["med", "health", "clinic", "doctor", "patient", "bio", "nephro"]):
                clinical_exam_terms = ["nephrology", "medical licensing", "clinical examination", "hospital", "chemotherapy", "histopathology", "patient care", "in vivo", "diagnostic performance", "diagnosis please", "radiology", "clinical diagnosis", "medical specialty", "access examination", "dentistry", "gre physics"]
                if any(t in combined_text for t in clinical_exam_terms):
                    return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: Clinical/medical examination or niche test paper outside general model comparison scope."

            # Reject specialized 3D geometry / mesh papers when researching general LLMs
            if not any(k in topic for k in ["mesh", "3d", "robot", "video", "render", "vision"]):
                graphics_terms = ["3d mesh", "mesh correspondence", "curvature-guided", "point cloud"]
                if any(t in combined_text for t in graphics_terms):
                    return 0.05, RelevanceLevel.IRRELEVANT, "Rejected: Specialized 3D/graphics preprint outside LLM benchmark scope."

            # Reject cross-domain homonyms & off-topic niche preprints in AI
            cross_domain_noise = [
                "piece of old cloth", "tattered clothes", "wash rag",
                "fine-tuned universe", "anthropic principle", "standard model of particle physics",
                "silent film", "broadway musical", "hip hop group", "viking ruler", "javelin thrower",
                "leisure walk", "points of interest", "point of interest", "walking descriptions",
                "pedestrian", "walking tour", "cybersecurity ai agent selection", "nist cybersecurity",
                "metaverse interaction systems", "metaverse", "turkish language enhanced",
                "chirp spread spectrum", "lpwan", "semtech", "lorawan", "radio frequency modulation"
            ]
            if any(noise in combined_text for noise in cross_domain_noise):
                return 0.02, RelevanceLevel.IRRELEVANT, "Rejected: Off-topic preprint, leisure/tourism, radio/telecom homonym, or metaverse noise outside core research scope."

            off_domain_terms = [
                "patient", "clinical trial", "cardiovascular", "oncology", "chemotherapy",
                "surgical", "histopathology", "in vivo", "biomagnification", "ecotoxicology",
                "trophic transfer", "tga balance", "soma assets", "on rrp", "reserve balance"
            ]
            ai_terms = [
                "llm", "language model", "transformer", "neural", "deep learning", "machine learning",
                "benchmark", "reasoning", "coding", "inference", "prompt", "token", "agent",
                "weights", "nlp", "swe-bench", "gpt", "claude", "gemini", "llama", "foundation model",
                "deepseek", "retrieval", "fine-tuning", "rag", "lora"
            ]
            has_off_domain = any(t in combined_text for t in off_domain_terms)
            has_ai_term = any(t in combined_text for t in ai_terms)
            if has_off_domain and not has_ai_term:
                return 0.02, RelevanceLevel.IRRELEVANT, f"Rejected: Off-domain paper lacking AI/LLM relevance to '{topic}'."

        # 4c. Comparative Arm & Acronym Alignment
        candidate_arms = [a.strip() for a in re.split(r"\b(?:vs\.?|versus|and|or|compared to|between)\b", topic) if len(a.strip()) >= 2]
        arm_expansions = list(candidate_arms)
        for arm in candidate_arms:
            clean_arm_words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", arm.lower()) if w not in GENERIC_STOP_NOUNS]
            arm_l = " ".join(clean_arm_words) if clean_arm_words else arm.lower()
            arm_expansions.append(arm_l)
            if "rag" in arm_l:
                arm_expansions.extend(["retrieval-augmented generation", "retrieval augmented generation", "retrieval-augmented", "retriever"])
            if any(k in arm_l for k in ["fine-tuning", "finetuning", "fine tuning", "fine-tuned", "tuning"]):
                arm_expansions.extend(["fine-tuning", "finetuning", "fine-tuned", "lora", "peft"])

        matching_title_arm = [exp for exp in arm_expansions if re.search(r"\b" + re.escape(exp) + r"\b", title_lower)]
        if matching_title_arm:
            return 0.96, RelevanceLevel.DIRECT, f"Direct candidate subject match in title: '{matching_title_arm[0]}'"

        # Content match must also have general subject coherence
        matching_content_arm = [exp for exp in arm_expansions if re.search(r"\b" + re.escape(exp) + r"\b", combined_text)]
        if matching_content_arm and any(k in combined_text for k in ["language model", "llm", "transformer", "nlp", "prompt", "retrieval", "fine-tuning", "lora"]):
            return 0.88, RelevanceLevel.DIRECT, f"Direct candidate subject match in content: '{matching_content_arm[0]}'"

        # 4d. Direct Model / Architecture entity alignment in AI Technology domain
        if domain == DomainType.AI_TECHNOLOGY:
            title_topic_matches = [w for w in topic_words if len(w) > 2 and re.search(r"\b" + re.escape(w) + r"\b", title_lower)]
            if title_topic_matches:
                return 0.95, RelevanceLevel.DIRECT, f"Direct topic match in title: {title_topic_matches}"
            if source.source_type == SourceType.CODE_REPO and any(re.search(r"\b" + re.escape(w) + r"\b", combined_text) for w in topic_words if len(w) > 2):
                return 0.92, RelevanceLevel.DIRECT, "Official primary architecture repository release matching query."
            ai_eval_terms = ["pricing", "cost", "token", "tokens", "swe-bench", "benchmark", "leaderboard", "latency", "ttft", "gpt", "claude", "gemini", "openai", "anthropic"]
            matched_eval_terms = [t for t in ai_eval_terms if re.search(r"\b" + re.escape(t) + r"\b", combined_text)]
            # Evaluation match must also align with at least one topic word
            if len(matched_eval_terms) >= 2 and any(re.search(r"\b" + re.escape(w) + r"\b", combined_text) for w in topic_words if len(w) > 2):
                return 0.92, RelevanceLevel.DIRECT, f"Direct AI evaluation match: {matched_eval_terms[:4]}"

        # 5. Exact Whole-Word Match in Title
        if re.search(r"\b" + re.escape(topic) + r"\b", title_lower):
            return 0.98, RelevanceLevel.DIRECT, "Exact whole-word topic match in source title."

        # 6. Check Head Noun Presence with word boundaries (must NOT be a generic stop noun)
        if primary_noun not in GENERIC_STOP_NOUNS and re.search(r"\b" + re.escape(primary_noun) + r"\b", combined_text):
            return 0.85, RelevanceLevel.DIRECT, f"Direct conceptual alignment: contains primary subject '{primary_noun}'."

        # 7. Check Topic Word Overlap
        overlap_count = sum(1 for w in topic_words if re.search(r"\b" + re.escape(w) + r"\b", combined_text))
        if overlap_count >= max(1, len(topic_words) - 1):
            return 0.75, RelevanceLevel.RELATED, "High semantic topical overlap."

        # 8. Production Case Studies & Engineering Deployments
        if getattr(source, "source_class", None) == SourceClass.PRODUCTION_CASE_STUDY and any(t in combined_text for t in ["retrieval", "rag", "fine-tuning", "lora", "llm", "architecture", "deployment", "pipeline"]):
            return 0.90, RelevanceLevel.DIRECT, "Authentic enterprise production case study."

        # 9. AI Domain fallback for relevant AI papers
        if domain == DomainType.AI_TECHNOLOGY and any(t in combined_text for t in ["retrieval-augmented", "rag", "fine-tuning", "prompt engineering", "vector database"]):
            return 0.75, RelevanceLevel.RELATED, "Topical AI domain alignment."

        return 0.20, RelevanceLevel.IRRELEVANT, f"Source lacks primary concept '{primary_noun}' and domain terms."
