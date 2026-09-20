# Evidence-First Research, Learning & Building Agent

An autonomous, verifiable knowledge platform designed to research subjects deeply, build structured concept/evidence graphs, teach users through adaptive prerequisite-based curricula, and guide real-world project builds with programmatic error validation.

---

## 🏛️ System Architecture

```
                    ┌────────────────────────────┐
                    │      USER / CLIENT UI      │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │     API GATEWAY (FastAPI)   │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │        ORCHESTRATOR        │
                    └─────────────┬──────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ RESEARCH SERVICE │    │ LEARNING SERVICE │    │  BUILD SERVICE   │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   KNOWLEDGE SERVICES  │
                     └───────────┬───────────┘
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
┌──────────────┐         ┌──────────────┐            ┌──────────────┐
│ SEARCH & VEC │         │  GRAPH DB    │            │ RELATIONAL DB│
│ OpenSearch + │         │   Neo4j      │            │  PostgreSQL  │
│   Qdrant     │         │              │            │              │
└──────────────┘         └──────────────┘            └──────────────┘
```

---

## 🚀 Core Features

### 1. Research Engine (Verifiable Knowledge & Evidence Graph)
* **Topic Expansion**: Hierarchically explores prerequisites, benchmarks, standards, and competing architectures.
* **Evidence Grounding**: Every claim stores exact source quotes, page numbers, character offsets, or video timestamps.
* **Conflict Engine**: Highlights discrepancies (e.g. vendor claims vs independent benchmarks) instead of silently resolving them.
* **Saturation Engine**: Quantifies marginal information gain per search iteration.

### 2. Learn Engine (Adaptive Prerequisite-Based Curriculum)
* **Prerequisite DAG**: Enforces foundational masteries before advancing to downstream topics.
* **Multi-Level Explanations**: Switches between Beginner, Intermediate, Advanced, and Expert depths.
* **Adaptive Assessment**: 10 question formats with evidence-backed misconception diagnosis.
* **User Mastery Graph**: Tracks concept-by-concept mastery scores.

### 3. Build Engine (Goal-to-Execution Sandbox)
* **Requirements Decomposition**: Breaks goals into functional, technical, security, and performance constraints.
* **Implementation Blueprint**: Phased steps with inputs, actions, code snippets, expected outputs, and validation tests.
* **Error Diagnostic Intelligence**: Classifies violations (Syntax, Dependency, Architectural Anti-patterns, Silent Failures) with evidence-backed remedies.

### 4. Evidence-Grounded Chat
* **NLU Intent Classifier**: Detects user intents (`EXPLAIN`, `SIMPLIFY`, `DEEP_DIVE`, `COMPARE`, `EVIDENCE`, `CONFLICTS`, `TEST_ME`, `BUILD`, `DEBUG`).
* **Deterministic Synthesis**: Assembles structured responses with clickable source references.

---

## 🛠️ Quick Start

### 1. Run with Docker Compose
```bash
docker compose up -d
```
This spins up PostgreSQL (`5432`), Neo4j (`7687`), Qdrant (`6333`), OpenSearch (`9200`), and Redis (`6379`).

### 2. Install Python Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Launch Backend API
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8010 --reload
```
Interactive Swagger API documentation will be available at [http://localhost:8010/docs](http://localhost:8010/docs).

### 4. Run Test Suite
```bash
pytest tests/test_agent.py -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/research/workspaces` | List all active research workspaces |
| `POST` | `/api/research/submit` | Launch a new evidence-grounded research job |
| `GET` | `/api/research/workspace/{id}/claims` | Retrieve verified and conflicting claims with evidence |
| `GET` | `/api/learn/curriculum/{id}` | Get structured modules, lessons, and quizzes |
| `POST` | `/api/learn/quiz/evaluate/{id}` | Submit and evaluate quiz answer with diagnostic feedback |
| `GET` | `/api/build/project/{id}` | Get phased engineering build steps and validation commands |
| `POST` | `/api/build/validate` | Validate code against architectural constraints |
| `POST` | `/api/chat/query` | Query the knowledge graph via evidence-grounded chat |
| `GET` | `/api/graph/{id}` | Export full nodes and edges for graph visualization |
| `GET` | `/api/graph/{id}/cypher` | Export Neo4j Cypher statements |
