from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

# ==========================================
# 1. CORE TYPES & ENUMS
# ==========================================

class SourceType(str, Enum):
    WEB = "WEB"
    PDF = "PDF"
    YOUTUBE = "YOUTUBE"
    ACADEMIC_PAPER = "ACADEMIC_PAPER"
    GOVERNMENT_DOC = "GOVERNMENT_DOC"
    CODE_REPO = "CODE_REPO"
    STANDARDS_DOC = "STANDARDS_DOC"
    DOCUMENTATION = "DOCUMENTATION"
    NEWS = "NEWS"
    PATENT = "PATENT"
    CLINICAL_TRIAL = "CLINICAL_TRIAL"
    DATASET = "DATASET"
    FINANCIAL_FILING = "FINANCIAL_FILING"
    USER_NOTE = "USER_NOTE"

class SourceCategory(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"
    COMMUNITY = "COMMUNITY"
    UNKNOWN = "UNKNOWN"

class SourceClass(str, Enum):
    PRIMARY_RESEARCH = "PRIMARY_RESEARCH"            # 1.00 - Controlled experiments, peer-reviewed primary papers (arXiv, PubMed, Europe PMC)
    SYSTEMATIC_REVIEW = "SYSTEMATIC_REVIEW"          # 0.95 - Cochrane, PRISMA systematic literature evaluations
    META_ANALYSIS = "META_ANALYSIS"                  # 0.95 - Quantitative multi-study pooling
    OFFICIAL_STATISTICS = "OFFICIAL_STATISTICS"      # 0.95 - World Bank, FRED, OECD, BLS, Eurostat statistical releases
    GOVERNMENT = "GOVERNMENT"                        # 0.95 - Federal government agencies, Data.gov, legislative acts
    REGULATOR = "REGULATOR"                          # 0.95 - Statutory regulators: FDA, EPA, SEC, FTC, EMA, FCC
    COURT_DOCUMENT = "COURT_DOCUMENT"                # 0.95 - Judicial opinions, court dockets, statutory case law
    COMPANY_FILING = "COMPANY_FILING"                # 0.95 - SEC EDGAR 10-K, 10-Q, 8-K audited corporate filings
    OFFICIAL_DOCUMENTATION = "OFFICIAL_DOCUMENTATION"# 0.90 - Vendor technical documentation, official API specs, architecture manuals
    TECHNICAL_STANDARD = "TECHNICAL_STANDARD"        # 0.90 - Official standards bodies: NIST, IEEE, ISO, W3C, IETF RFCs
    PRODUCTION_CASE_STUDY = "PRODUCTION_CASE_STUDY"  # 0.85 - Real-world enterprise production postmortems & engineering architectures
    SECONDARY_RESEARCH = "SECONDARY_RESEARCH"        # 0.75 - Academic surveys, textbook syntheses, literature overviews
    NEWS = "NEWS"                                    # 0.60 - Reuters, AP, Bloomberg, FT, GDELT global event monitoring
    INDUSTRY_REPORT = "INDUSTRY_REPORT"              # 0.55 - Gartner, IDC, Forrester market analysis reports
    WIKIPEDIA = "WIKIPEDIA"                          # 0.35 - Tertiary encyclopedic overviews (Wikimedia Foundation)
    BLOG = "BLOG"                                    # 0.20 - Unverified personal blogs, medium articles, web tutorials
    FORUM = "FORUM"                                  # 0.10 - Stack Overflow, Reddit, community discussion threads

SOURCE_CLASS_WEIGHTS: Dict[SourceClass, float] = {
    SourceClass.PRIMARY_RESEARCH: 1.00,
    SourceClass.SYSTEMATIC_REVIEW: 0.95,
    SourceClass.META_ANALYSIS: 0.95,
    SourceClass.OFFICIAL_STATISTICS: 0.95,
    SourceClass.GOVERNMENT: 0.95,
    SourceClass.REGULATOR: 0.95,
    SourceClass.COURT_DOCUMENT: 0.95,
    SourceClass.COMPANY_FILING: 0.95,
    SourceClass.OFFICIAL_DOCUMENTATION: 0.90,
    SourceClass.TECHNICAL_STANDARD: 0.90,
    SourceClass.PRODUCTION_CASE_STUDY: 0.85,
    SourceClass.SECONDARY_RESEARCH: 0.75,
    SourceClass.NEWS: 0.60,
    SourceClass.INDUSTRY_REPORT: 0.55,
    SourceClass.WIKIPEDIA: 0.35,
    SourceClass.BLOG: 0.20,
    SourceClass.FORUM: 0.10,
}

class RelevanceLevel(str, Enum):
    DIRECT = "DIRECT"
    RELATED = "RELATED"
    CONTEXTUAL = "CONTEXTUAL"
    TANGENTIAL = "TANGENTIAL"
    IRRELEVANT = "IRRELEVANT"

class FactStatus(str, Enum):
    DIRECTLY_SUPPORTED = "DIRECTLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    VERIFIED = "VERIFIED"
    CONFLICTING = "CONFLICTING"
    UNSUPPORTED = "UNSUPPORTED"
    NO_EVIDENCE_FOUND = "NO_EVIDENCE_FOUND"
    OUTDATED = "OUTDATED"

class ConflictType(str, Enum):
    TRUE_CONTRADICTION = "TRUE_CONTRADICTION"
    WORKLOAD_VARIATION = "WORKLOAD_VARIATION"
    METHODOLOGY_DIFFERENCE = "METHODOLOGY_DIFFERENCE"
    TEMPORAL_DIFFERENCE = "TEMPORAL_DIFFERENCE"
    DEFINITION_DIFFERENCE = "DEFINITION_DIFFERENCE"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"

class DomainType(str, Enum):
    AI_TECHNOLOGY = "AI_TECHNOLOGY"
    MEDICINE_BIOLOGY = "MEDICINE_BIOLOGY"
    ENVIRONMENTAL_TOXICOLOGY = "ENVIRONMENTAL_TOXICOLOGY"
    PHYSICAL_SCIENCE = "PHYSICAL_SCIENCE"
    FINANCE_COMMERCE = "FINANCE_COMMERCE"
    HISTORY_HUMANITIES = "HISTORY_HUMANITIES"
    SOFTWARE_ENGINEERING = "SOFTWARE_ENGINEERING"
    GENERAL = "GENERAL"

# ==========================================
# 2. PLANNING & OBJECTIVES
# ==========================================

class ObjectiveStatus(str, Enum):
    COMPLETE = "Complete"
    WEAK = "Weak"
    GAP = "Gap"

class ResearchObjective(BaseModel):
    id: str
    name: str
    description: str
    required: bool = True
    evidence_count: int = 0
    status: ObjectiveStatus = ObjectiveStatus.GAP

class ResearchPlan(BaseModel):
    topic: str
    domain: DomainType = DomainType.GENERAL
    strategy_summary: str = ""
    objectives: List[ResearchObjective] = Field(default_factory=list)
    stopping_saturation_threshold: int = 2

# ==========================================
# 3. EVIDENCE & PROVENANCE MODELS
# ==========================================

class SourceLineage(BaseModel):
    source_id: str
    derived_from_id: Optional[str] = None
    relationship: str = "INDEPENDENT"

class Source(BaseModel):
    id: str
    title: str
    url: str
    source_type: SourceType
    category: SourceCategory = SourceCategory.SECONDARY
    source_class: SourceClass = SourceClass.SECONDARY_RESEARCH
    author_publisher: Optional[str] = None
    publication_date: Optional[str] = None
    credibility_score: float = 85.0
    authority_score: float = 80.0
    relevance_score: float = 1.0
    relevance_level: RelevanceLevel = RelevanceLevel.DIRECT
    primary_status: bool = False
    raw_content: Optional[str] = None
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    content_hash: Optional[str] = None
    lineage_group: Optional[str] = None
    retrieval_query: str = ""
    discovery_engine: str = ""
    matched_requirement: str = ""
    phase: str = ""

class RejectedSource(BaseModel):
    id: str
    title: str
    url: str
    reason: str
    relevance_score: float = 0.0
    relevance_level: RelevanceLevel = RelevanceLevel.IRRELEVANT
    retrieval_query: str = ""
    discovery_engine: str = ""
    phase: str = ""

class DocumentChunk(BaseModel):
    id: str
    source_id: str
    text: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    timestamp_start: Optional[str] = None
    timestamp_end: Optional[str] = None
    speaker: Optional[str] = None
    start_offset: int = 0
    end_offset: int = 0
    content_hash: str = ""
    retrieved_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class EvidenceLink(BaseModel):
    source_id: str
    chunk_id: str
    exact_quote: str
    section: Optional[str] = None
    page_number: Optional[int] = None
    timestamp: Optional[str] = None
    confidence: float = 0.9
    entailment_status: str = "DIRECT"

class ResearchScope(BaseModel):
    research_id: str
    workspace_id: str
    requirement_id: Optional[str] = None
    claim_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class QuantitativeEvidence(BaseModel):
    metric_name: str
    raw_value: float
    unit: str = "count"
    denominated_currency: Optional[str] = None
    reporting_period_start: Optional[str] = None
    reporting_period_end: Optional[str] = None
    reporting_entity: str = ""
    source_url: str = ""
    reproducibility_chain: List[str] = Field(default_factory=list)

class ParameterizedEconomicClaim(BaseModel):
    stakeholder: str
    transaction_type: str
    regime_period: str
    fee_structure: str
    subsidy_mechanism: Optional[str] = None
    regulatory_circular_id: Optional[str] = None

class BoundClaim(BaseModel):
    id: str
    research_id: str
    subject: str
    predicate: str
    object_value: str
    source_id: str
    source_type: SourceType
    source_tier: float = 0.50
    exact_passage_quote: str
    passage_character_offset: Tuple[int, int] = (0, 0)
    page_or_section: Optional[str] = None
    document_version_or_date: Optional[str] = None
    entailment_score: float = 1.0
    verification_status: FactStatus = FactStatus.VERIFIED
    quant_evidence: Optional[QuantitativeEvidence] = None
    economic_params: Optional[ParameterizedEconomicClaim] = None

class EpistemicReport(BaseModel):
    final_score: float = 0.0
    verdict: str = "INVALID / UNVERIFIED"
    coverage_rate: str = "0.0%"
    tier1_primary_ratio: str = "0.0%"
    verified_claims_count: int = 0
    unbound_claims_count: int = 0
    unresolved_conflicts_count: int = 0
    research_id: str = ""
    audited_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class Claim(BaseModel):
    id: str
    subject: str
    predicate: str
    object_value: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    date_context: Optional[str] = None
    conditions: Optional[str] = None
    importance: str = "normal"
    relevance_score: float = 1.0
    relevance_level: RelevanceLevel = RelevanceLevel.DIRECT
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    last_verified_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    evidence: EvidenceLink
    status: FactStatus = FactStatus.VERIFIED
    supporting_source_ids: List[str] = Field(default_factory=list)
    contradicting_source_ids: List[str] = Field(default_factory=list)
    independent_source_count: int = 1

class RejectedClaim(BaseModel):
    id: str
    subject: str
    predicate: str
    object_value: str
    source_id: str
    reason: str
    relevance_score: float = 0.0

class Entity(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    first_seen_source_id: Optional[str] = None

class Conflict(BaseModel):
    id: str
    topic: str
    claim_a: Claim
    claim_b: Claim
    source_a: Source
    source_b: Source
    conflict_type: ConflictType = ConflictType.WORKLOAD_VARIATION
    difference_explanation: str
    resolution_status: str = "UNRESOLVED"

# ==========================================
# 4. KNOWLEDGE GRAPH & REPORT
# ==========================================

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeGraphData(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)

class ReportSection(BaseModel):
    id: str
    title: str
    content: str
    subsections: List['ReportSection'] = Field(default_factory=list)
    cited_claim_ids: List[str] = Field(default_factory=list)
    cited_source_ids: List[str] = Field(default_factory=list)

class ResearchChallenge(BaseModel):
    single_source_claims_count: int = 0
    weak_evidence_claims_count: int = 0
    potential_overgeneralizations: List[str] = Field(default_factory=list)
    missing_dimensions: List[str] = Field(default_factory=list)
    adversarial_verdict: str = "SOUND"

class QualityScore(BaseModel):
    overall: float = 0.0
    coverage: float = 0.0
    evidence_completeness: float = 0.0
    evidence_entailment: float = 0.0
    topic_relevance_rate: float = 100.0
    claim_relevance_rate: float = 100.0
    source_authority: float = 0.0
    source_diversity: float = 0.0
    source_independence: float = 0.0
    verification_rate: float = 0.0
    recency: float = 0.0
    conflict_resolution: float = 0.0
    methodology_completeness: float = 0.0
    saturation: float = 0.0
    critical_gaps_count: int = 0
    unresolved_conflicts_count: int = 0
    confidence_rating: str = "MEDIUM"

class ResearchWorkspace(BaseModel):
    id: str
    topic: str
    goal: Optional[str] = "Comprehensive Analysis & Building Guide"
    status: str = "COMPLETED"
    depth: str = "Comprehensive"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    plan: Optional[ResearchPlan] = None
    quality: QualityScore = Field(default_factory=QualityScore)
    sources: List[Source] = Field(default_factory=list)
    rejected_sources: List[RejectedSource] = Field(default_factory=list)
    source_lineage: List[SourceLineage] = Field(default_factory=list)
    chunks: List[DocumentChunk] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    rejected_claims: List[RejectedClaim] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    conflicts: List[Conflict] = Field(default_factory=list)
    graph: KnowledgeGraphData = Field(default_factory=KnowledgeGraphData)
    report: List[ReportSection] = Field(default_factory=list)
    open_gaps: List[str] = Field(default_factory=list)
    saturation_history: List[int] = Field(default_factory=list)
    saturation_score: float = 0.0
    challenge: Optional[ResearchChallenge] = None
    executed_queries: List[Dict[str, Any]] = Field(default_factory=list)

class CreateResearchRequest(BaseModel):
    topic: str
    goal: Optional[str] = "Understand and Build"
    depth: Optional[str] = "Comprehensive"
    user_sources: Optional[List[Dict[str, Any]]] = None

# ==========================================
# 5. LEARN ENGINE MODELS
# ==========================================

class QuestionType(str, Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    CONCEPT_EXPLANATION = "CONCEPT_EXPLANATION"
    SCENARIO = "SCENARIO"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"
    CODE_DEBUGGING = "CODE_DEBUGGING"
    ARCHITECTURE = "ARCHITECTURE"
    CASE_STUDY = "CASE_STUDY"
    CALCULATION = "CALCULATION"

class QuizQuestion(BaseModel):
    id: str
    concept_id: str
    concept_name: str
    question: str
    question_type: QuestionType = QuestionType.MCQ
    difficulty: str = "Intermediate"
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str
    evidence_quote: str
    source_id: str

class Lesson(BaseModel):
    id: str
    title: str
    difficulty: str
    explanation: str
    key_takeaways: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    common_pitfalls: List[str] = Field(default_factory=list)
    evidence_claims: List[str] = Field(default_factory=list)
    questions: List[QuizQuestion] = Field(default_factory=list)

class LearningModule(BaseModel):
    id: str
    title: str
    description: str
    order: int
    prerequisites: List[str] = Field(default_factory=list)
    lessons: List[Lesson] = Field(default_factory=list)
    mastery_percentage: float = 0.0
    is_unlocked: bool = True

class Curriculum(BaseModel):
    workspace_id: str
    topic: str
    modules: List[LearningModule] = Field(default_factory=list)
    overall_mastery: float = 0.0

class UserMasteryProfile(BaseModel):
    user_id: str = "default_user"
    concept_scores: Dict[str, float] = Field(default_factory=dict)
    weak_areas: List[str] = Field(default_factory=list)
    mastered_areas: List[str] = Field(default_factory=list)
    remediation_recommendations: List[str] = Field(default_factory=list)

class QuizSubmission(BaseModel):
    question_id: str
    selected_answer: str

class QuizEvaluation(BaseModel):
    question_id: str
    is_correct: bool
    correct_answer: str
    explanation: str
    misconception_analysis: Optional[str] = None
    prerequisite_remediation: Optional[str] = None
    evidence_link: Optional[EvidenceLink] = None

# ==========================================
# 6. BUILD ENGINE MODELS
# ==========================================

class BuildPhaseStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BuildStep(BaseModel):
    step_number: int
    title: str
    objective: str
    prerequisites: List[str] = Field(default_factory=list)
    input_files: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    code_snippet: Optional[str] = None
    expected_output: str
    validation_command: str
    common_errors: List[str] = Field(default_factory=list)
    evidence_reference: str
    status: BuildPhaseStatus = BuildPhaseStatus.PENDING

class BuildRequirement(BaseModel):
    category: str
    description: str
    justification: str
    evidence_source_id: Optional[str] = None

class BuildProject(BaseModel):
    id: str
    workspace_id: str
    goal: str
    target_technology: str
    architecture_overview: str
    requirements: List[BuildRequirement] = Field(default_factory=list)
    steps: List[BuildStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "READY"

class CodeExecutionValidation(BaseModel):
    step_number: int
    executed_code: str
    console_output: str
    exit_code: int
    is_valid: bool
    detected_errors: List[str] = Field(default_factory=list)
    suggested_correction: Optional[str] = None
    evidence_explanation: Optional[str] = None

class ValidateCodeRequest(BaseModel):
    workspace_id: str
    step_number: int
    code_content: str

# ==========================================
# 7. CHAT ENGINE MODELS
# ==========================================

class ChatIntentType(str, Enum):
    EXPLAIN = "EXPLAIN"
    SIMPLIFY = "SIMPLIFY"
    DEEP_DIVE = "DEEP_DIVE"
    COMPARE = "COMPARE"
    EVIDENCE = "EVIDENCE"
    SOURCES = "SOURCES"
    CONFLICTS = "CONFLICTS"
    LEARN = "LEARN"
    TEST_ME = "TEST_ME"
    BUILD = "BUILD"
    DEBUG = "DEBUG"
    GENERAL = "GENERAL"

class ChatRequest(BaseModel):
    workspace_id: str
    message: str
    intent_override: Optional[ChatIntentType] = None

class ChatResponse(BaseModel):
    intent: ChatIntentType
    topic: str
    response_text: str
    supporting_claims: List[Claim] = Field(default_factory=list)
    supporting_sources: List[Source] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    confidence_score: float = 95.0
