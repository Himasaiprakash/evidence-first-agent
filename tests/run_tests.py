import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.research_engine import ResearchEngine
from backend.services.knowledge_graph import KnowledgeGraphService
from backend.services.learn_engine import LearnEngine
from backend.services.build_engine import BuildEngine
from backend.services.chat_engine import ChatEngine
from backend.models.schemas import (
    QuizSubmission, ValidateCodeRequest, ChatRequest, ChatIntentType, FactStatus
)

class TestEvidenceFirstAgent(unittest.TestCase):

    def test_research_engine_claim_grounding_and_provenance(self):
        engine = ResearchEngine()
        ws = engine.run_research("Retrieval Augmented Generation", goal="Understand and Build RAG")
        
        self.assertEqual(ws.topic, "Retrieval Augmented Generation")
        self.assertGreaterEqual(len(ws.sources), 2)
        self.assertGreaterEqual(len(ws.chunks), 2)
        self.assertGreaterEqual(len(ws.claims), 2)
        self.assertIsNotNone(ws.plan)
        self.assertGreaterEqual(len(ws.plan.objectives), 5)
        self.assertIsNotNone(ws.challenge)
        self.assertIn(ws.challenge.adversarial_verdict, ["SOUND", "NEEDS_EXPANSION", "QUESTIONABLE"])
        
        # Verify strict claim grounding: all quotes must exist and have real source IDs
        for claim in ws.claims:
            self.assertTrue(bool(claim.evidence.exact_quote))
            self.assertTrue(claim.evidence.source_id.startswith("src-"))

    def test_measurable_quality_score(self):
        engine = ResearchEngine()
        ws = engine.run_research("Quantum Computing")
        
        self.assertGreater(ws.quality.overall, 0.0)
        self.assertGreater(ws.quality.coverage, 0.0)
        self.assertGreater(ws.quality.evidence_completeness, 0.0)
        self.assertIn(ws.quality.confidence_rating, ["HIGH", "MEDIUM-HIGH", "MEDIUM", "LOW"])

    def test_knowledge_graph_cypher_export(self):
        engine = ResearchEngine()
        ws = engine.run_research("Artificial Intelligence")
        kg_service = KnowledgeGraphService()
        kg_service.build_from_workspace(ws.topic, ws.entities, ws.claims, ws.sources)
        
        cypher_statements = kg_service.export_neo4j_cypher()
        self.assertGreater(len(cypher_statements), 0)
        self.assertTrue(any("MERGE" in s for s in cypher_statements))

    def test_learn_engine_curriculum_and_quiz(self):
        engine = ResearchEngine()
        ws = engine.run_research("Retrieval Augmented Generation")
        learn_engine = LearnEngine()
        
        curriculum = learn_engine.generate_curriculum(ws)
        self.assertGreaterEqual(len(curriculum.modules), 2)
        self.assertGreaterEqual(len(curriculum.modules[0].lessons[0].questions), 1)
        
        target_q = curriculum.modules[0].lessons[0].questions[0]
        eval_correct = learn_engine.evaluate_quiz(
            QuizSubmission(question_id=target_q.id, selected_answer=target_q.correct_answer),
            ws
        )
        self.assertTrue(eval_correct.is_correct)
        
        eval_wrong = learn_engine.evaluate_quiz(
            QuizSubmission(question_id=target_q.id, selected_answer="Wrong Answer"),
            ws
        )
        self.assertFalse(eval_wrong.is_correct)
        self.assertIsNotNone(eval_wrong.misconception_analysis)

    def test_build_engine_validation(self):
        engine = ResearchEngine()
        ws = engine.run_research("Retrieval Augmented Generation")
        build_engine = BuildEngine()
        
        project = build_engine.create_build_project(ws)
        self.assertGreaterEqual(len(project.steps), 4)
        self.assertGreaterEqual(len(project.requirements), 4)
        
        # Test detection of architectural violation (ungrounded generative LLM)
        val_fail = build_engine.validate_code_submission(ValidateCodeRequest(
            workspace_id=ws.id,
            step_number=1,
            code_content="import openai\nclient = openai.OpenAI()"
        ))
        self.assertFalse(val_fail.is_valid)
        self.assertTrue(any("ArchitecturalViolation" in err for err in val_fail.detected_errors))

    def test_chat_engine_intent_and_grounding(self):
        engine = ResearchEngine()
        ws = engine.run_research("Retrieval Augmented Generation")
        chat_engine = ChatEngine()
        
        resp_simplify = chat_engine.process_message(
            ChatRequest(workspace_id=ws.id, message="Please simplify this for a beginner"),
            ws
        )
        self.assertEqual(resp_simplify.intent, ChatIntentType.SIMPLIFY)
        self.assertGreater(len(resp_simplify.response_text), 50)
        
        resp_conflicts = chat_engine.process_message(
            ChatRequest(workspace_id=ws.id, message="Why do these sources disagree?"),
            ws
        )
        self.assertEqual(resp_conflicts.intent, ChatIntentType.CONFLICTS)
        self.assertGreater(len(resp_conflicts.response_text), 20)

if __name__ == "__main__":
    unittest.main()
