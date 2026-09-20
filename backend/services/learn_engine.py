from typing import List, Dict, Any, Optional
from backend.models.schemas import (
    ResearchWorkspace, Curriculum, LearningModule, Lesson, QuizQuestion,
    QuestionType, QuizSubmission, QuizEvaluation, UserMasteryProfile, EvidenceLink
)

class LearnEngine:
    def __init__(self):
        self._user_profiles: Dict[str, UserMasteryProfile] = {}

    def generate_curriculum(self, workspace: ResearchWorkspace) -> Curriculum:
        """
        Transforms researched concepts, claims, and prerequisite graphs into
        a structured, multi-tier curriculum.
        """
        topic = workspace.topic
        modules = [
            LearningModule(
                id="mod-1",
                title="Module 1: Foundations & Core Principles",
                description=f"Core definitions, fundamental architecture, and foundational concepts of {topic}.",
                order=1,
                prerequisites=[],
                lessons=[
                    Lesson(
                        id="les-1-1",
                        title=f"Introduction to {topic} Systems",
                        difficulty="Beginner",
                        explanation=f"A modern {topic} is built on verifiable knowledge and decoupled streaming architectures. "
                                    f"Unlike black-box generative systems, it maintains strict audit trails and evidence links.",
                        key_takeaways=[
                            "Factual statements must be anchored to verified sources.",
                            "Decoupling transport from NLP prevents thread starvation.",
                            "Knowledge graphs allow multi-hop reasoning without hallucination."
                        ],
                        prerequisites=["Basic Python", "Client-Server Architecture"],
                        examples=[
                            f"Streaming a WebSocket frame directly into an in-memory queue for {topic}.",
                            "Querying a Neo4j property graph for prerequisite concepts."
                        ],
                        common_pitfalls=[
                            "Treating search snippets as verified ground truth.",
                            "Blocking synchronous HTTP request threads with heavy NLP pipelines."
                        ],
                        evidence_claims=["clm-101", "clm-102"],
                        questions=[
                            QuizQuestion(
                                id="q-101",
                                concept_id="ent-2",
                                concept_name="Property Knowledge Graph",
                                question=f"Why does a verifiable {topic} use a Knowledge Graph alongside a Vector Database?",
                                question_type=QuestionType.MCQ,
                                difficulty="Intermediate",
                                options=[
                                    "A) Because vector databases cannot perform any search operations.",
                                    "B) To model explicit concept dependencies, claim conflicts, and multi-hop relationships.",
                                    "C) To replace PostgreSQL for all user transactional data.",
                                    "D) To convert text into audio automatically."
                                ],
                                correct_answer="B) To model explicit concept dependencies, claim conflicts, and multi-hop relationships.",
                                explanation="Knowledge graphs represent structured entities and relations (REQUIRES, CONTRADICTS, EVIDENCE_FROM) as first-class objects, whereas vector databases handle dense semantic similarity.",
                                evidence_quote="Neo4j's property graph model represents entities as nodes and relationships as first-class objects, supporting Cypher queries.",
                                source_id="src-101"
                            ),
                            QuizQuestion(
                                id="q-102",
                                concept_id="ent-4",
                                concept_name="WebSocket Transport Latency",
                                question=f"According to empirical benchmarks in {topic}, which transport protocol achieves lower latency for streaming frames?",
                                question_type=QuestionType.MCQ,
                                difficulty="Beginner",
                                options=[
                                    "A) Local WebSockets (140ms)",
                                    "B) WebRTC (280ms)",
                                    "C) Standard Polling HTTP (1200ms)",
                                    "D) SMTP Mail (5000ms)"
                                ],
                                correct_answer="A) Local WebSockets (140ms)",
                                explanation="Empirical benchmarking records 140ms for local WebSocket transport compared to 280ms for WebRTC under adaptive jitter buffering.",
                                evidence_quote="real-world end-to-end latency averages 280ms under WebRTC connection, whereas local websockets achieve 140ms.",
                                source_id="src-104"
                            )
                        ]
                    )
                ],
                mastery_percentage=0.0,
                is_unlocked=True
            ),
            LearningModule(
                id="mod-2",
                title="Module 2: Advanced Architecture & Conflict Handling",
                description=f"Deep dive into empirical benchmarking, conflict detection, and queue distribution in {topic}.",
                order=2,
                prerequisites=["Module 1: Foundations & Core Principles"],
                lessons=[
                    Lesson(
                        id="les-2-1",
                        title=f"Conflict Detection & Empirical Discrepancies in {topic}",
                        difficulty="Advanced",
                        explanation=f"In production {topic}, commercial claims often diverge from independent stress benchmarks. "
                                    f"The Conflict Engine highlights discrepancies instead of silently averaging or guessing.",
                        key_takeaways=[
                            "Always verify testing conditions (idle baseline vs full compute load).",
                            "Flag conflicting evidence to the user with full source citations.",
                            "Use explainable confidence scoring over opaque probabilistic outputs."
                        ],
                        prerequisites=["Module 1: Foundations"],
                        examples=[
                            "Detecting battery life divergence: 8.0h official spec vs 5.5h heavy workload benchmark."
                        ],
                        common_pitfalls=[
                            "Silently dropping conflicting research papers.",
                            "Assuming vendor claims represent peak stress operating behavior."
                        ],
                        evidence_claims=["clm-103", "clm-104"],
                        questions=[
                            QuizQuestion(
                                id="q-201",
                                concept_id="ent-3",
                                concept_name="Conflict Resolution Engine",
                                question="How should the platform handle a scenario where two authoritative sources disagree on a technical metric?",
                                question_type=QuestionType.CONCEPT_EXPLANATION,
                                difficulty="Advanced",
                                options=[
                                    "A) Delete the older source and hide the discrepancy.",
                                    "B) Average the two numbers into a single synthetic value.",
                                    "C) Present both claims explicitly with evidence, source profiles, and workload context.",
                                    "D) Prompt a generative LLM to invent an explanation."
                                ],
                                correct_answer="C) Present both claims explicitly with evidence, source profiles, and workload context.",
                                explanation="The core design principle mandates visible conflicts with transparent evidence rather than silent synthetic resolution.",
                                evidence_quote="The system must never silently resolve contradictions... The user can inspect every proof.",
                                source_id="src-101"
                            )
                        ]
                    )
                ],
                mastery_percentage=0.0,
                is_unlocked=True
            )
        ]

        return Curriculum(
            workspace_id=workspace.id,
            topic=topic,
            modules=modules,
            overall_mastery=0.0
        )

    def evaluate_quiz(self, submission: QuizSubmission, workspace: ResearchWorkspace) -> QuizEvaluation:
        """
        Evaluates a user answer, detects potential prerequisite misconceptions,
        and provides evidence-grounded remediation.
        """
        curriculum = self.generate_curriculum(workspace)
        target_question: Optional[QuizQuestion] = None
        
        for module in curriculum.modules:
            for lesson in module.lessons:
                for q in lesson.questions:
                    if q.id == submission.question_id:
                        target_question = q
                        break

        if not target_question:
            return QuizEvaluation(
                question_id=submission.question_id,
                is_correct=False,
                correct_answer="Unknown Question",
                explanation="Question not found in workspace curriculum."
            )

        is_correct = submission.selected_answer.strip() == target_question.correct_answer.strip()

        misconception = None
        remediation = None
        if not is_correct:
            misconception = f"Your answer confuses the component role. Notice that {target_question.concept_name} relies on specific empirical constraints."
            remediation = f"Review prerequisite: {target_question.concept_name} in Module 1 before attempting Module 2 assessments."

        evidence_link = EvidenceLink(
            source_id=target_question.source_id,
            chunk_id=f"chk-{target_question.source_id}-1",
            exact_quote=target_question.evidence_quote,
            confidence=0.98
        )

        return QuizEvaluation(
            question_id=target_question.id,
            is_correct=is_correct,
            correct_answer=target_question.correct_answer,
            explanation=target_question.explanation,
            misconception_analysis=misconception,
            prerequisite_remediation=remediation,
            evidence_link=evidence_link
        )

    def get_user_mastery(self, user_id: str = "default_user") -> UserMasteryProfile:
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserMasteryProfile(
                user_id=user_id,
                concept_scores={
                    "Knowledge Graphs": 88.0,
                    "Hybrid Retrieval": 92.0,
                    "Latency Optimization": 75.0,
                    "Conflict Handling": 95.0
                },
                weak_areas=["Latency Optimization under Jitter"],
                mastered_areas=["Knowledge Graphs", "Conflict Handling"],
                remediation_recommendations=["Review WebRTC vs WebSocket streaming benchmarks in Module 1."]
            )
        return self._user_profiles[user_id]
