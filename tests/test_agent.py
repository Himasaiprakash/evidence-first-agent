import pytest
from backend.services.research_engine import ResearchEngine
from backend.services.knowledge_graph import KnowledgeGraphService
from backend.services.learn_engine import LearnEngine
from backend.services.build_engine import BuildEngine
from backend.services.chat_engine import ChatEngine
from backend.models.schemas import (
    QuizSubmission, ValidateCodeRequest, ChatRequest, ChatIntentType, FactStatus
)

def test_research_engine_claim_grounding():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents", goal="Understand and Build")
    
    assert ws.topic == "AI Voice Agents"
    assert len(ws.sources) >= 5
    assert len(ws.claims) >= 4
    assert len(ws.conflicts) >= 1
    
    # Check claim grounding
    for claim in ws.claims:
        assert claim.evidence.exact_quote is not None
        assert len(claim.evidence.exact_quote) > 0
        assert claim.evidence.source_id.startswith("src-")

def test_conflict_detection():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents")
    
    # Check that conflicting claims exist
    conflicting_claims = [c for c in ws.claims if c.status == FactStatus.CONFLICTING]
    assert len(conflicting_claims) >= 2
    assert len(ws.conflicts) >= 1
    assert ws.conflicts[0].resolution_status in ["UNRESOLVED", "WORKLOAD_VARIATION"]

def test_knowledge_graph_cypher_export():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents")
    kg_service = KnowledgeGraphService()
    kg_service.build_from_workspace(ws.topic, ws.entities, ws.claims, ws.sources)
    
    cypher_statements = kg_service.export_neo4j_cypher()
    assert len(cypher_statements) > 0
    assert any("MERGE" in s for s in cypher_statements)

def test_learn_engine_curriculum_and_quiz():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents")
    learn_engine = LearnEngine()
    
    curriculum = learn_engine.generate_curriculum(ws)
    assert len(curriculum.modules) >= 2
    assert len(curriculum.modules[0].lessons[0].questions) >= 1
    
    target_q = curriculum.modules[0].lessons[0].questions[0]
    # Correct answer submission
    eval_correct = learn_engine.evaluate_quiz(
        QuizSubmission(question_id=target_q.id, selected_answer=target_q.correct_answer),
        ws
    )
    assert eval_correct.is_correct is True
    
    # Incorrect answer submission
    eval_wrong = learn_engine.evaluate_quiz(
        QuizSubmission(question_id=target_q.id, selected_answer="Wrong Answer"),
        ws
    )
    assert eval_wrong.is_correct is False
    assert eval_wrong.misconception_analysis is not None

def test_build_engine_validation():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents")
    build_engine = BuildEngine()
    
    project = build_engine.create_build_project(ws)
    assert len(project.steps) >= 4
    assert len(project.requirements) >= 4
    
    # Validate forbidden LLM import
    val_fail = build_engine.validate_code_submission(ValidateCodeRequest(
        workspace_id=ws.id,
        step_number=1,
        code_content="import openai\nclient = openai.OpenAI()"
    ))
    assert val_fail.is_valid is False
    assert any("ArchitecturalViolation" in err for err in val_fail.detected_errors)

def test_chat_engine_intent_and_grounding():
    engine = ResearchEngine()
    ws = engine.run_research("AI Voice Agents")
    chat_engine = ChatEngine()
    
    resp_simplify = chat_engine.process_message(
        ChatRequest(workspace_id=ws.id, message="Please simplify this for a beginner"),
        ws
    )
    assert resp_simplify.intent == ChatIntentType.SIMPLIFY
    assert "Beginner Explanation" in resp_simplify.response_text
    
    resp_conflicts = chat_engine.process_message(
        ChatRequest(workspace_id=ws.id, message="Why do these sources disagree?"),
        ws
    )
    assert resp_conflicts.intent == ChatIntentType.CONFLICTS
    assert "Identified Conflicts" in resp_conflicts.response_text
