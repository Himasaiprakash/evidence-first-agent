import re
import json
from datetime import datetime
from typing import List, Optional, Tuple, Any
from backend.models.schemas import ResearchPlan, ResearchObjective, DomainType
from backend.research.planning.requirement_engine import ResearchRequirements, RequirementItem, ChapterOutlineItem, ResearchRequirementEngine
from backend.research.taxonomy import domain_taxonomy

class ResearchPlanner:
    """
    Intelligent Topic-Aware Research Planner:
    - LLM-Assisted Dynamic Planning: Decomposes arbitrary research topics into domain, objectives, testable requirements, and tailored chapter outline using Groq LPU inference.
    - Zero static lock-in: Evaluates current frontier state dynamically.
    - Robust Deterministic Fallback: Automatically falls back to rule-based heuristics if the LLM is offline or output fails schema validation.
    """
    def plan(self, topic: str, user_goal: str = "Understand architecture, benchmarks, and production build") -> ResearchPlan:
        domain = self._classify_domain(topic)
        objectives = self._generate_topic_specific_objectives(topic, domain)
        return ResearchPlan(
            topic=topic,
            domain=domain,
            strategy_summary=f"Multi-source empirical investigation targeting {len(objectives)} required dimensions in {domain.value}.",
            objectives=objectives,
            stopping_saturation_threshold=2
        )

    def plan_with_llm(
        self,
        topic: str,
        user_goal: str = "Understand architecture, benchmarks, and production build",
        groq_client: Optional[Any] = None,
        fallback_engine: Optional[ResearchRequirementEngine] = None,
        resolution: Optional[Any] = None
    ) -> Tuple[ResearchPlan, ResearchRequirements]:
        """
        LLM-Assisted Dynamic Research Planner:
        - Prompts Groq LLM to formulate domain, objectives, testable requirements, and tailored chapter outline
        - Detects false/adversarial premises and pivots to empirical refutation planning
        - Falls back gracefully to deterministic planning if LLM is unavailable or output fails schema validation
        """
        if groq_client and groq_client.is_available():
            try:
                today_str = datetime.now().strftime("%Y-%m-%d")
                premise_falsified = bool(getattr(resolution, "premise_falsified", False)) if resolution else False
                falsification_explanation = str(getattr(resolution, "falsification_explanation", "")) if resolution else ""

                system_prompt = (
                    "You are the Principal Research Strategist and Epistemic Planning Architect. "
                    "Your mission is to formulate an exhaustive, publication-grade research plan and testable requirement specification in JSON format. "
                    "You tailor every objective, requirement, targeted search query, and chapter outline to the exact subject. "
                    "Avoid generic filler, placeholder text, or canned historical introductions. "
                    f"TEMPORAL RECENCY MANDATE (Current Date: {today_str}): When researching fast-evolving domains (especially AI, machine learning, and software), "
                    f"focus strictly on the latest, currently active state-of-the-art developments, architectures, and benchmarks as of {today_str}. "
                    "Target contemporary active models, current preprints, and active software releases. Do NOT default to obsolete legacy systems."
                )

                falsification_instruction = ""
                if premise_falsified:
                    falsification_instruction = (
                        f"\n\nCRITICAL ADVERSARIAL REFUTATION MANDATE:\n"
                        f"The research query asserts a premise that is FACTUALLY FALSE: \"{falsification_explanation}\".\n"
                        f"You MUST NOT treat the false event as having occurred. Do NOT invent causes for a non-existent event.\n"
                        f"Instead, structure an EMPIRICAL REFUTATION PLAN:\n"
                        f"- Objective 1 & Chapter 1: Directly falsify the premise with official institutional timeline & status.\n"
                        f"- Objective 2 & Chapter 2: Document what ACTUALLY occurred during the specified period.\n"
                        f"- Objective 3 & Chapter 3: Trace the origin, political/economic context, and narrative spread of the false claim.\n"
                        f"- Objective 4 & Chapter 4: Analyze institutional continuity mechanisms, treaty safeguards, and operational reality.\n"
                        f"- Objective 5 & Chapter 5: Contrast real empirical challenges with fictitious collapse scenarios.\n"
                        f"- Objective 6 & Chapter 6: Authoritative Epistemic Refutation & Falsification Ledger.\n"
                    )

                user_prompt = f"""Generate an exhaustive research plan and testable requirements specification in JSON format for:
Topic: '{topic}'
Goal: '{user_goal}'{falsification_instruction}

Return ONLY a valid JSON object matching this exact schema:
{{
  "domain": "CLASSIFIED_DOMAIN",
  "core_subject": "Concise Core Subject Name based on the Topic",
  "strategy_summary": "Multi-dimensional empirical investigation...",
  "objectives": [
    {{"id": "obj-1", "name": "Objective Title", "description": "Specific analytical objective", "required": true}}
  ],
  "requirements": [
    {{
      "id": "req-1",
      "category": "DATA_SERIES",
      "name": "Requirement Name",
      "description": "Precise empirical requirement",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "targeted_queries": ["precision search query targeting primary source"]
    }}
  ],
  "core_mechanisms": ["Mechanism 1", "Mechanism 2"],
  "required_metrics": ["Metric 1 (units)", "Metric 2 (units)"],
  "historical_events": ["Event 1 (Year)", "Event 2 (Year)"],
  "authoritative_source_tiers": {{
    "Tier 1 Primary": ["Source 1", "Source 2"],
    "Tier 2 Independent Benchmarks": ["Source 3"]
  }},
  "epistemic_qualifications": ["Caveat or methodological distinction"],
  "chapter_outline": [
    {{"number": 1, "title": "Chapter Title", "focus": "Chapter analytical mandate"}}
  ]
}}

CRITICAL CONSTRAINTS:
1. 'domain' MUST be exactly one of: AI_TECHNOLOGY, MEDICINE_BIOLOGY, ENVIRONMENTAL_TOXICOLOGY, PHYSICAL_SCIENCE, FINANCE_COMMERCE, SOFTWARE_ENGINEERING, HISTORY_HUMANITIES, GENERAL.
2. Provide 6 to 9 specific 'objectives'.
3. Provide 5 to 8 discrete 'requirements' with 'category' in ["MECHANISM", "DATA_SERIES", "HISTORICAL_CASE", "REGULATORY_CONSTRAINT"].
4. For each requirement, provide 2-3 'targeted_queries' designed to retrieve primary academic papers, official specifications, or benchmark leaderboards.
5. Provide an 8-to-9 chapter outline tailored to the domain. Chapter 1 MUST start directly with the current active subject scope, empirical lineup, and operational definitions. Outline chapters covering core mechanisms/architecture, empirical data/benchmarks/trials, operational dynamics, economics/trade-offs, failure modes/limits, and institutional decision frameworks.
6. Target primary authoritative sources, peer-reviewed literature, official regulatory registries, or verified empirical benchmarks appropriate to the domain.
7. Ensure JSON is strictly valid with no trailing commas, unescaped quotes, or control characters.
"""

                resp = groq_client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=4000
                )

                raw_content = resp.choices[0].message.content.strip()

                # Extract JSON block
                json_str = raw_content
                if "```" in json_str:
                    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str)
                    if match:
                        json_str = match.group(1).strip()

                brace_start = json_str.find("{")
                brace_end = json_str.rfind("}")
                if brace_start != -1 and brace_end != -1:
                    json_str = json_str[brace_start:brace_end+1]

                # Robust JSON repair
                cleaned_json = re.sub(r"//[^\n]*", "", json_str)
                cleaned_json = re.sub(r'("[^"\n]*")\s*\n\s*("[a-zA-Z0-9_]+"\s*:)', r'\1,\n\2', cleaned_json)
                cleaned_json = re.sub(r'(\b\d+(?:\.\d+)?|\btrue|\bfalse|\bnull)\s*\n\s*("[a-zA-Z0-9_]+"\s*:)', r'\1,\n\2', cleaned_json, flags=re.IGNORECASE)
                cleaned_json = re.sub(r'([\]\}])\s*\n\s*("[a-zA-Z0-9_]+"\s*:|\{)', r'\1,\n\2', cleaned_json)
                cleaned_json = re.sub(r",\s*([\]}])", r"\1", cleaned_json)

                try:
                    data = json.loads(cleaned_json, strict=False)
                except Exception:
                    data = json.loads(json_str, strict=False)

                # Parse and validate domain
                domain_raw = str(data.get("domain", "GENERAL")).upper().strip()
                try:
                    domain = DomainType(domain_raw)
                except ValueError:
                    if any(k in domain_raw for k in ["AI", "LEARNING", "NEURAL", "MODEL", "TECH"]):
                        domain = DomainType.AI_TECHNOLOGY
                    elif any(k in domain_raw for k in ["MED", "BIO", "HEALTH", "CLINIC"]):
                        domain = DomainType.MEDICINE_BIOLOGY
                    elif any(k in domain_raw for k in ["TOXIC", "ENV", "POLLUT", "ECOL"]):
                        domain = DomainType.ENVIRONMENTAL_TOXICOLOGY
                    elif any(k in domain_raw for k in ["PHYS", "MATER", "BATTER", "QUANT", "CHEM"]):
                        domain = DomainType.PHYSICAL_SCIENCE
                    elif any(k in domain_raw for k in ["FIN", "ECON", "BANK", "COMM"]):
                        domain = DomainType.FINANCE_COMMERCE
                    elif any(k in domain_raw for k in ["SOFT", "ENG", "CODE", "COMP"]):
                        domain = DomainType.SOFTWARE_ENGINEERING
                    elif any(k in domain_raw for k in ["HIST", "HUMAN"]):
                        domain = DomainType.HISTORY_HUMANITIES
                    else:
                        domain = self._classify_domain(topic)

                core_subject = str(data.get("core_subject") or topic).strip()
                if ("frontier ai" in core_subject.lower() or "concise core subject" in core_subject.lower()) and ("ai" not in topic.lower() and "model" not in topic.lower()):
                    core_subject = topic
                strategy_summary = data.get("strategy_summary") or f"Dynamic LLM-assisted empirical research plan for '{topic}' in {domain.value}."

                # Objectives
                objectives: List[ResearchObjective] = []
                for idx, obj in enumerate(data.get("objectives", [])):
                    obj_id = str(obj.get("id") or f"obj-{idx+1}")
                    obj_name = str(obj.get("name") or f"Objective {idx+1}")
                    obj_desc = str(obj.get("description") or obj_name)
                    objectives.append(ResearchObjective(
                        id=obj_id,
                        name=obj_name,
                        description=obj_desc,
                        required=bool(obj.get("required", True))
                    ))

                # Requirements
                requirements: List[RequirementItem] = []
                for idx, req in enumerate(data.get("requirements", [])):
                    req_id = str(req.get("id") or f"req-{idx+1}")
                    category = str(req.get("category") or "DATA_SERIES").upper()
                    if category not in ["MECHANISM", "DATA_SERIES", "HISTORICAL_CASE", "REGULATORY_CONSTRAINT"]:
                        category = "DATA_SERIES"
                    req_name = str(req.get("name") or f"Requirement {idx+1}")
                    req_desc = str(req.get("description") or req_name)
                    keywords = [re.sub(r'["\';:,]', '', str(k)).strip().lower() for k in req.get("keywords", []) if k]
                    if not keywords:
                        keywords = [w.lower() for w in req_name.split() if len(w) > 3]
                    targeted_queries = [re.sub(r'["\']', '', str(q)).strip() for q in req.get("targeted_queries", []) if q]
                    if not targeted_queries:
                        targeted_queries = [f"{core_subject} {req_name}"]

                    requirements.append(RequirementItem(
                        id=req_id,
                        category=category,
                        name=req_name,
                        description=req_desc,
                        keywords=keywords,
                        targeted_queries=targeted_queries
                    ))

                # Chapter Outline
                chapter_outline: List[ChapterOutlineItem] = []
                for idx, ch in enumerate(data.get("chapter_outline", [])):
                    ch_num = int(ch.get("number") or idx+1)
                    ch_title = str(ch.get("title") or f"Chapter {ch_num}")
                    ch_focus = str(ch.get("focus") or ch_title)
                    chapter_outline.append(ChapterOutlineItem(
                        number=ch_num,
                        title=ch_title,
                        focus=ch_focus
                    ))

                # Validate non-triviality
                if len(objectives) >= 4 and len(requirements) >= 3 and len(chapter_outline) >= 5:
                    plan = ResearchPlan(
                        topic=topic,
                        domain=domain,
                        strategy_summary=strategy_summary,
                        objectives=objectives,
                        stopping_saturation_threshold=2
                    )

                    targeted_gap_queries = []
                    for r in requirements:
                        if r.targeted_queries:
                            targeted_gap_queries.append(r.targeted_queries[0])

                    reqs = ResearchRequirements(
                        topic=topic,
                        domain=domain,
                        core_subject=core_subject,
                        requirements=requirements,
                        core_mechanisms=[str(m) for m in data.get("core_mechanisms", [])],
                        required_metrics=[str(m) for m in data.get("required_metrics", [])],
                        historical_events=[str(e) for e in data.get("historical_events", [])],
                        authoritative_source_tiers={str(k): [str(x) for x in v] for k, v in data.get("authoritative_source_tiers", {}).items() if isinstance(v, list)},
                        targeted_gap_queries=targeted_gap_queries,
                        epistemic_qualifications=[str(q) for q in data.get("epistemic_qualifications", [])],
                        chapter_outline=chapter_outline
                    )

                    return plan, reqs

            except Exception as e:
                print(f"  [PLANNING WARNING] LLM planning failed: {type(e).__name__}: {e}. Engaging deterministic fallback...")

        # Fallback
        plan = self.plan(topic, user_goal=user_goal)
        if fallback_engine is None:
            fallback_engine = ResearchRequirementEngine()
        reqs = fallback_engine.generate_requirements(topic, user_goal, plan.domain)
        return plan, reqs

    def _classify_domain(self, topic: str) -> DomainType:
        """Dynamically classifies topic using configurable DomainTaxonomyRegistry."""
        return domain_taxonomy.classify_domain(topic)

    def _generate_topic_specific_objectives(self, topic: str, domain: DomainType) -> List[ResearchObjective]:
        """
        Universal Dynamic Objective Formulation:
        Dynamically extracts core technical entities and formulates 6 comprehensive empirical
        research objectives for ANY topic across all domains without hardcoded sector templates.
        """
        clean_topic = topic.strip()
        words = [w for w in clean_topic.split() if w.lower() not in ["the", "a", "an", "of", "in", "for", "and", "or", "to", "about", "compare", "vs", "versus"]]
        core_name = " ".join(words[:4]) if words else clean_topic

        return [
            ResearchObjective(
                id="obj-1",
                name=f"Scope, Lineup & Architecture ({core_name})",
                description=f"Technical specifications, architectural foundations, candidate lineups, and operational definitions for {clean_topic}.",
                required=True
            ),
            ResearchObjective(
                id="obj-2",
                name=f"Empirical Benchmarking & Quantitative Metrics ({core_name})",
                description=f"Standardized performance benchmarks, empirical pass rates, quantitative experimental data, and comparative statistics for {clean_topic}.",
                required=True
            ),
            ResearchObjective(
                id="obj-3",
                name=f"Operational Mechanics & Systemic Dynamics ({core_name})",
                description=f"Systemic dynamics, execution mechanics, throughput, integration patterns, and component coordination for {clean_topic}.",
                required=True
            ),
            ResearchObjective(
                id="obj-4",
                name=f"Tooling, Infrastructure & Integration ({core_name})",
                description=f"Hardware requirements, API interfaces, tooling integration, runtime overheads, and infrastructural constraints for {clean_topic}.",
                required=True
            ),
            ResearchObjective(
                id="obj-5",
                name=f"Economic Evaluation, Latency & Cost ({core_name})",
                description=f"Operating costs, resource budgets, latency profiling (TTFT/throughput), and economic trade-offs for {clean_topic}.",
                required=True
            ),
            ResearchObjective(
                id="obj-6",
                name=f"Failure Modes, Limitations & Decision Framework ({core_name})",
                description=f"Critical vulnerabilities, known bottlenecks, boundary conditions, and actionable deployment recommendations for {clean_topic}.",
                required=True
            )
        ]
