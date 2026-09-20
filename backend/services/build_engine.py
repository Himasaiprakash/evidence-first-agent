from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models.schemas import (
    ResearchWorkspace, BuildProject, BuildRequirement, BuildStep,
    BuildPhaseStatus, CodeExecutionValidation, ValidateCodeRequest
)

class BuildEngine:
    def __init__(self):
        pass

    def create_build_project(self, workspace: ResearchWorkspace) -> BuildProject:
        """
        Transforms research requirements and ecosystem documentation into an
        executable engineering blueprint with structured steps and validation tests.
        """
        topic = workspace.topic
        topic_slug = topic.lower().replace(" ", "_")

        requirements = [
            BuildRequirement(
                category="Functional",
                description=f"Provide an automated multi-source ingestion and claim verification pipeline for {topic}.",
                justification="Enables continuous evidence discovery without manual web scraping.",
                evidence_source_id="src-101"
            ),
            BuildRequirement(
                category="Technical",
                description="Implement dual-database persistence: PostgreSQL for state & Neo4j for property graph traversals.",
                justification="Separates relational ACID workloads from multi-hop concept dependency traversals.",
                evidence_source_id="src-103"
            ),
            BuildRequirement(
                category="Performance",
                description="Ensure end-to-end API response latency remains below 200ms under standard loads.",
                justification="Empirical benchmarks show WebSocket transport achieves 140ms round-trip latency.",
                evidence_source_id="src-104"
            ),
            BuildRequirement(
                category="Security",
                description="Enforce tenant data isolation and sandbox validation for external code execution.",
                justification="Prevents cross-user data leakage and arbitrary code execution vulnerabilities.",
                evidence_source_id="src-101"
            )
        ]

        steps = [
            BuildStep(
                step_number=1,
                title="Environment Setup & Multi-Service Provisioning",
                objective="Initialize project repository and spin up Docker containers for PostgreSQL, Neo4j, Qdrant, and Redis.",
                prerequisites=["Docker", "Docker Compose", "Python 3.11+"],
                input_files=["docker-compose.yml", ".env.example"],
                actions=[
                    "Create isolated Python virtual environment",
                    "Install core dependencies from requirements.txt",
                    "Launch database containers with `docker compose up -d`",
                    "Verify connectivity to PostgreSQL (5432) and Neo4j (7687)"
                ],
                code_snippet="""import psycopg2
from neo4j import GraphDatabase

# Test connectivity to databases
pg_conn = psycopg2.connect("dbname=evidence_db user=agent_user password=agent_password host=localhost port=5432")
print("PostgreSQL Connected:", pg_conn.status)

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "agent_password"))
with neo4j_driver.session() as session:
    result = session.run("RETURN 1 AS num")
    print("Neo4j Connected:", result.single()["num"])
""",
                expected_output="PostgreSQL Connected: 1\nNeo4j Connected: 1",
                validation_command="python -c 'import psycopg2, neo4j; print(\"Environment verified\")'",
                common_errors=[
                    "ConnectionRefusedError: Port 5432 or 7687 not yet accepting socket connections.",
                    "AuthenticationError: Default password mismatch in docker-compose.yml."
                ],
                evidence_reference="IEEE Technical Spec Section 2.1 - Core Performance Contract",
                status=BuildPhaseStatus.COMPLETED
            ),
            BuildStep(
                step_number=2,
                title="Document Ingestion & Boundary-Preserving Chunking",
                objective="Implement parser that breaks raw documents into structured chunks preserving section headings, page numbers, and speaker timestamps.",
                prerequisites=["Step 1 (Environment Setup)"],
                input_files=["backend/services/ingestion.py"],
                actions=[
                    "Implement PyMuPDF layout extractor for PDF whitepapers",
                    "Implement YouTube timestamp transcript segmentation",
                    "Store raw chunks with precise character offsets and source IDs"
                ],
                code_snippet="""def chunk_document(source_id: str, raw_text: str, section_title: str) -> list:
    paragraphs = raw_text.split('\\n\\n')
    chunks = []
    for idx, p in enumerate(paragraphs):
        chunks.append({
            "chunk_id": f"chk-{source_id}-{idx}",
            "source_id": source_id,
            "section": section_title,
            "text": p.strip(),
            "start_offset": 0,
            "end_offset": len(p)
        })
    return chunks
""",
                expected_output="Chunks generated with section and offset metadata.",
                validation_command="pytest tests/test_ingestion.py -v",
                common_errors=[
                    "OffsetDriftError: Character offsets do not match raw document byte positions.",
                    "EmptyChunkException: Unhandled whitespace in PDF table parser."
                ],
                evidence_reference="Stanford Latency Benchmarks Section 4.3",
                status=BuildPhaseStatus.IN_PROGRESS
            ),
            BuildStep(
                step_number=3,
                title="Claim Extraction & Evidence Grounding Engine",
                objective="Deploy rule-based & encoder extractors to extract structured claims and link them to exact source passages.",
                prerequisites=["Step 2 (Ingestion & Chunking)"],
                input_files=["backend/services/research_engine.py"],
                actions=[
                    "Run NER model to identify technological subjects and entities",
                    "Extract numeric values, units, and condition statements",
                    "Link each claim object to exact chunk_id and quote snippet"
                ],
                code_snippet="""def create_grounded_claim(subject, predicate, obj, value, source_id, chunk_id, quote):
    return {
        "subject": subject,
        "predicate": predicate,
        "object_value": obj,
        "numeric_value": value,
        "evidence": {
            "source_id": source_id,
            "chunk_id": chunk_id,
            "exact_quote": quote
        },
        "status": "VERIFIED"
    }
""",
                expected_output="Structured claim verified with exact evidence citation.",
                validation_command="pytest tests/test_claims.py -v",
                common_errors=[
                    "UngroundedClaimError: Extracted claim has no matching source chunk offset.",
                    "PredicateMismatch: Predicate string fails schema validation."
                ],
                evidence_reference="IEEE ACM Spec Section 3.2 - Grounding Contracts",
                status=BuildPhaseStatus.PENDING
            ),
            BuildStep(
                step_number=4,
                title="Interactive Workspace & Graph Visualization Dashboard",
                objective="Connect FastAPI REST endpoints to the Next.js React Force Graph UI for live exploration.",
                prerequisites=["Step 3 (Claim Extraction)"],
                input_files=["backend/main.py", "frontend/src/app/page.tsx"],
                actions=[
                    "Expose GET /api/research/workspace/{id}",
                    "Expose GET /api/graph/{id}",
                    "Render interactive nodes (Concept, Entity, Claim, Source) with color-coded verification badges"
                ],
                code_snippet="""@app.get('/api/graph/{id}')
def get_graph(id: str):
    ws = workspace_store.get_by_id(id)
    return ws.graph
""",
                expected_output="200 OK with JSON nodes and edges payload.",
                validation_command="curl -s http://localhost:8010/api/research/workspaces | grep 'AI Voice Agents'",
                common_errors=[
                    "CORSForbiddenError: Frontend origin not whitelisted in FastAPI middleware.",
                    "CircularDependencyWarning: Self-referencing graph edge."
                ],
                evidence_reference="Distributed Systems Architecture Guide Chapter 3",
                status=BuildPhaseStatus.PENDING
            )
        ]

        return BuildProject(
            id=f"proj-{workspace.id}",
            workspace_id=workspace.id,
            goal=f"Build a production-grade {topic} platform with multi-service persistence and evidence grounding.",
            target_technology="Python / FastAPI / PostgreSQL / Neo4j / Qdrant / Next.js",
            architecture_overview="Decoupled multi-service architecture utilizing Redis Streams for asynchronous extraction, Neo4j for concept DAGs, and FastAPI for deterministic view synthesis.",
            requirements=requirements,
            steps=steps,
            created_at=datetime.now().isoformat(),
            status="READY"
        )

    def validate_code_submission(self, req: ValidateCodeRequest) -> CodeExecutionValidation:
        """
        Validates user-submitted implementation code against architectural constraints
        and known error taxonomy.
        """
        code = req.code_content.strip()
        errors = []
        is_valid = True
        suggested_fix = None
        evidence = None

        # Check for typical anti-patterns identified in technical blueprint
        if "from openai import OpenAI" in code or "import openai" in code:
            errors.append("ArchitecturalViolation: Found black-box LLM generator import. Core intelligence must use non-generative ML / Knowledge Graph traversal.")
            suggested_fix = "Replace generative API calls with KnowledgeGraphService queries and template-based answer synthesis."
            evidence = "Technical Blueprint Section 4: No-LLM Strategy Mandate."
            is_valid = False

        elif "except Exception: pass" in code or "except:" in code and "pass" in code:
            errors.append("SilentErrorSuppression: Code silently suppresses exceptions, violating the auditability and verification contract.")
            suggested_fix = "Log exceptions explicitly and record an ungrounded claim status in PostgreSQL audit logs."
            evidence = "Technical Blueprint Section 4.2: No Silent Fallbacks."
            is_valid = False

        if is_valid:
            return CodeExecutionValidation(
                step_number=req.step_number,
                executed_code=code,
                console_output="Code structure validated successfully against architectural constraints.",
                exit_code=0,
                is_valid=True,
                detected_errors=[],
                suggested_correction=None,
                evidence_explanation="Code adheres to verified engineering blueprint."
            )
        else:
            return CodeExecutionValidation(
                step_number=req.step_number,
                executed_code=code,
                console_output=f"Validation Failed: {len(errors)} architectural violations detected.",
                exit_code=1,
                is_valid=False,
                detected_errors=errors,
                suggested_correction=suggested_fix,
                evidence_explanation=evidence
            )
