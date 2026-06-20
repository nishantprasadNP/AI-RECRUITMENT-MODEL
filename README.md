# AI Recruitment Intelligence System (ARIS)

ARIS is a production-ready, modular, and extensible AI-driven recruitment intelligence system built in Python. The platform transforms unstructured PDF resumes and raw job descriptions into structured intelligence assets, classifies roles into predefined industry taxonomies, generates dynamic evaluation strategies, constructs semantic evidence profiles, computes candidate experience signals, checks strict hard requirement compliance, detects exceptional standout achievements, and scores vector matches.

All components are wired into a central pipeline orchestrator or accessible through modular standalone engine APIs.

---

## Table of Contents
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Platform Core Engines](#platform-core-engines)
-   - [1. Dual-Engine PDF Ingestion](#1-dual-engine-pdf-ingestion)
-   - [2. Pydantic-Schema LLM Extraction](#2-pydantic-schema-llm-extraction)
-   - [3. Role Classification Engine](#3-role-classification-engine)
-   - [4. Evaluation Strategy Engine](#4-evaluation-strategy-engine)
-   - [5. Skill Knowledge Graph & Inference](#5-skill-knowledge-graph--inference)
-   - [6. Skill Evidence Engine](#6-skill-evidence-engine)
-   - [7. Experience Analysis & Skill Confidence Engine](#7-experience-analysis--skill-confidence-engine)
-   - [8. Hard Requirements Compliance Engine](#8-hard-requirements-compliance-engine)
-   - [9. Achievement Analyzer](#9-achievement-analyzer)
-   - [10. Semantic Matching & Embeddings](#10-semantic-matching--embeddings)
-   - [11. Candidate Scoring Engine](#11-candidate-scoring-engine)
-   - [12. Candidate Ranking Engine](#12-candidate-ranking-engine)
- [System Architecture](#system-architecture)
- [Pipeline Stages](#pipeline-stages)
- [Project Directory Structure](#project-directory-structure)
- [Setup & Installation](#setup--installation)
- [Usage Instructions](#usage-instructions)
-   - [Full Pipeline via Orchestrator](#full-pipeline-via-orchestrator)
-   - [Standalone Evaluation Strategy Engine](#standalone-evaluation-strategy-engine)
-   - [Standalone Achievement Analyzer](#standalone-achievement-analyzer)
-   - [Individual Stage Run Scripts](#individual-stage-run-scripts)
-   - [Phase 3 Validation Suite](#phase-3-validation-suite)
-   - [Programmatic API](#programmatic-api)
- [Data Schemas](#data-schemas)
-   - [Resume Profile](#resume-profile)
-   - [Job Profile](#job-profile)
-   - [Role Profile](#role-profile)
-   - [Evaluation Strategy](#evaluation-strategy)
-   - [Achievement Profile](#achievement-profile)
-   - [Hard Requirements Compliance Result](#hard-requirements-compliance-result)
-   - [Capability Resolution Result](#capability-resolution-result)
-   - [Candidate Score Profile](#candidate-score-profile)
-   - [Ranked Candidate List](#ranked-candidate-list)
- [Extraction Quality & Prevention Rules](#extraction-quality--prevention-rules)
- [Custom Exception Hierarchy](#custom-exception-hierarchy)
- [Running Tests](#running-tests)
- [Project Roadmap](#project-roadmap)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

Run all commands from the **project root** (`AI-RECRUITMENT-MODEL/`).

```bash
# 1. Activate the workspace virtual environment
source .venv/bin/activate             # macOS / Linux
# .venv\Scripts\activate              # Windows

# 2. Configure your environment variables (.env file)
# Create a .env file containing: GEMINI_API_KEY=your_key_here

# 3. Run the orchestrator with sample inputs
python scripts/run_full_pipeline.py
```

On first run, the local embedding model (`sentence-transformers/all-mpnet-base-v2`) is downloaded automatically. Subsequent runs are fully cached and take under 10 seconds.

---

## Prerequisites

| Requirement | Details |
|:---|:---|
| **Python** | 3.10 or newer recommended. (Python 3.12 is fully supported). |
| **Gemini API Key** | Required for structured profile extraction. Obtain one from the [Google AI Studio](https://aistudio.google.com/apikey). |
| **Dependencies** | Listed in [requirements.txt](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/requirements.txt) including `pdfplumber`, `PyMuPDF (fitz)`, `pydantic`, `sentence-transformers`, `scikit-learn`, `networkx`, and `pytest`. |

---

## Platform Core Engines

### 1. Dual-Engine PDF Ingestion
Located in [resume_parser.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/ingestion/resume_parser.py). It executes two parsers (`pdfplumber` and `PyMuPDF / fitz`) concurrently. It computes an alphanumeric-to-character density score for each output and retains the cleaner document structure. It handles corrupted, password-protected, and blank documents gracefully with tailored exceptions.

### 2. Pydantic-Schema LLM Extraction
Located in the [extraction](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/extraction) folder. Using Google Gemini (`gemini-2.5-flash`), it parses unstructured text into structured, typed payloads. The outputs are validated against strict contracts in [schemas](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/schemas) ensuring fields match explicit facts or supported inferences.

### 3. Role Classification Engine
Located in the [role_classification](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/role_classification) folder. It evaluates job description requirements against heuristic matrices in [role_rules.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/role_classification/role_rules.py). It classifies roles into standard Role Families (e.g. `software_engineering`, `data_ai`), specializations (e.g. `backend_engineer`, `ml_engineer`), and seniority levels (`junior`, `mid_level`, `senior`, `staff`).

### 4. Evaluation Strategy Engine
Located in the [evaluation_strategy](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/evaluation_strategy) folder. Generates role-aware evaluation weights, strictness levels, minimum skill confidence thresholds, and requirement tolerance values matching the classified `RoleProfile`. Predefined configurations exist for roles like `intern_backend`, `new_grad_backend`, `mid_backend`, `senior_backend`, `intern_ml`, `mid_ml`, and `senior_ml`. It handles unknown profiles through dynamic seniority and specialization fallback logic.

### 5. Skill Knowledge Graph & Inference
Located in the [knowledge_graph](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/knowledge_graph) folder. Loads a skills taxonomy from `data/skill_graph/skills_taxonomy.json` into a `NetworkX` directed graph. It maps relationships (e.g. `FastAPI` -> `requires` -> `Python`). The [skill_inference_engine.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/knowledge_graph/inference/skill_inference_engine.py) performs ancestral traversal to infer implicit skills.

### 6. Skill Evidence Engine
Located in the [skill_evidence](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/skill_evidence) folder. Collects direct mentions, mapped project usages, role references, and graph dependencies for candidate skills. It assigns weighted attributions (Direct: 1.0, Project: 0.8, Dependency: 0.5, Inherited: 0.3) to construct trace chains and qualitative evidence levels (`Expert`, `Strong`, `Moderate`, `Limited`).

### 7. Experience Analysis & Skill Confidence Engine
Located in the [experience_analysis](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/experience_analysis) folder. Calculates job complexity scores based on duration and projects. It combines direct evidence, role descriptions, and project tenures to compute numerical confidence scores (0-100) and confidence tiers.

### 8. Hard Requirements Compliance Engine
Located in the [hard_requirements](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/hard_requirements) folder. Resolves raw candidate skills to canonical definitions. It expands candidate capabilities with inferred ancestors from the Skill Knowledge Graph while tracking exact graph origins. It strictly matches resolved capabilities against job criteria to return pass status, coverage score, matched/missing requirements, and granular decision reasons.

### 9. Achievement Analyzer
Located in the [achievement_analysis](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/achievement_analysis) folder. Scans the candidate's `ResumeProfile` using sentence-level regex patterns to identify standout signals across 5 core dimensions: Academic (e.g., JEE AIR ranks, top universities, scholarships), Technical (e.g., hackathon wins, CP ratings, open-source), Research (e.g., papers, patents), Leadership (e.g., club leaders, mentors, EM/lead roles), and Entrepreneurship (e.g., founders, YC experience, product ownership). It scores categories, compiles a consolidated overall score (using a max-biased formula favoring standout spikes), and provides explanation traces.

### 10. Semantic Matching & Embeddings
Located in the [matching](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/matching) and [embeddings](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/embeddings) folders. Resolves parsed candidate profiles and job criteria into cohesive text structures. It generates vector embeddings locally using `SentenceTransformer` (`all-mpnet-base-v2`) and computes cosine similarity match scores.

### 11. Candidate Scoring Engine
Located in the [candidate_scoring](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_scoring) folder. Combines all candidate evaluation signals (semantic similarity score, skills confidence, experience duration vs. required, standout achievements, project relevance, and leadership) into a unified role-aware candidate score. It consumes weights defined by the `EvaluationStrategy` for the target role, ensuring a dynamically parameterized scoring system without hardcoded constants.

### 12. Candidate Ranking Engine
Located in the [candidate_ranking](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_ranking) folder. Ranks multiple candidate results deterministically. It sorts candidates by their overall score (descending) and breaks ties using a strict 4-tier hierarchy: Hard Requirement Coverage, Semantic Match Score, Skill Confidence Score, Achievement Score, and an ascending alphabetical name fallback. It also auto-extracts bulleted strengths and concerns for recruiter review based on component score thresholds.

---

## System Architecture

```mermaid
graph TD
    %% Inputs
    Resume[Resume PDF] --> Ingestion[Dual-Engine Parser\napp/ingestion/resume_parser.py]
    Ingestion --> RawResumeText[Raw Resume Text]
    
    JD[Job Description Text] --> JobExtractor[Job LLM Extractor\napp/extraction/job_extractor.py]
    RawResumeText --> ResumeExtractor[Resume LLM Extractor\napp/extraction/resume_extractor.py]
    
    %% Outputs of Extractor
    ResumeExtractor --> ResumeProfile[ResumeProfile\napp/schemas/resume_schema.py]
    JobExtractor --> JobProfile[JobProfile\napp/schemas/job_schema.py]
    
    %% Classification & Evaluation Strategy
    JobProfile --> RoleClassifier[Role Classifier\napp/role_classification/]
    RoleClassifier --> RoleProfile[RoleProfile\napp/role_classification/models.py]
    RoleProfile --> EvalStrategyEngine[Evaluation Strategy Engine\napp/evaluation_strategy/]
    EvalStrategyEngine --> EvaluationStrategy[EvaluationStrategy\napp/evaluation_strategy/models.py]
    
    %% Knowledge Graph & Inference
    Taxonomy[skills_taxonomy.json] --> Graph[Skill Knowledge Graph\napp/knowledge_graph/]
    Graph --> Inference[Skill Inference Engine]
    
    %% Hard Requirements Matching (Phase 8)
    ResumeProfile --> CapResolver[Capability Resolver\napp/hard_requirements/capability_resolver.py]
    Inference --> CapResolver
    CapResolver --> CapResult[CapabilityResolutionResult\napp/hard_requirements/models.py]
    CapResult --> HardReqEngine[Hard Requirement Engine\napp/hard_requirements/hard_requirement_engine.py]
    JobProfile --> HardReqEngine
    HardReqEngine --> HardReqResult[HardRequirementResult\napp/hard_requirements/models.py]
    
    %% Skill Evidence Engine
    ResumeProfile --> EvidenceEngine[Skill Evidence Engine\napp/skill_evidence/]
    Inference --> EvidenceEngine
    EvidenceEngine --> ExplainableProfile[ExplainableSkillProfile\napp/skill_evidence/models/]
    
    %% Experience Analysis & Skill Confidence Engine
    ResumeProfile --> ConfidenceEngine[Skill Confidence Engine\napp/experience_analysis/]
    ConfidenceEngine --> ConfidenceProfile[SkillConfidenceProfile\napp/experience_analysis/models.py]
    
    %% Achievement Analyzer (Phase 9)
    ResumeProfile --> AchievementAnalyzer[Achievement Analyzer\napp/achievement_analysis/]
    AchievementAnalyzer --> AchievementProfile[AchievementProfile\napp/achievement_analysis/models.py]
    
    %% Semantic Matching
    ResumeProfile --> TextBuilder[Text Builder\napp/embeddings/text_builder.py]
    JobProfile --> TextBuilder
    TextBuilder --> SemanticText[Semantic Text Representations]
    SemanticText --> Embedder[Embedding Generator\napp/embeddings/embedding_generator.py]
    Embedder --> Matcher[Semantic Matcher\napp/matching/semantic_matcher.py]
    Matcher --> SemanticScore[Semantic Match Score]

    %% Candidate Scoring Engine (Phase 10)
    ResumeProfile --> ScoringEngine[Candidate Scoring Engine\napp/candidate_scoring/]
    JobProfile --> ScoringEngine
    EvaluationStrategy --> ScoringEngine
    HardReqResult --> ScoringEngine
    SemanticScore --> ScoringEngine
    ConfidenceProfile --> ScoringEngine
    AchievementProfile --> ScoringEngine
    ScoringEngine --> CandidateScore[CandidateScoreProfile\napp/candidate_scoring/models.py]

    %% Candidate Ranking Engine (Phase 11)
    CandidateScore --> RankingEngine[Candidate Ranking Engine\napp/candidate_ranking/]
    RankingEngine --> RankedList[RankedCandidateList\napp/candidate_ranking/models.py]
    
    %% Persistence
    ResumeProfile --> Storage[Storage Layer\napp/storage/]
    JobProfile --> Storage
    RoleProfile --> Storage
    EvaluationStrategy --> Storage
    AchievementProfile --> Storage
    SemanticScore --> Storage
    CandidateScore --> Storage
    
    %% Formatting
    classDef main fill:#6c63ff,color:#fff,stroke:#333,stroke-width:2px;
    classDef module fill:#3b82f6,color:#fff,stroke:#333,stroke-width:1px;
    classDef data fill:#10b981,color:#fff,stroke:#333,stroke-width:1px;
    
    class Ingestion,RoleClassifier,EvalStrategyEngine,EvidenceEngine,ConfidenceEngine,CapResolver,HardReqEngine,AchievementAnalyzer,Matcher,ScoringEngine,RankingEngine main;
    class ResumeExtractor,JobExtractor,Embedder module;
    class ResumeProfile,JobProfile,RoleProfile,EvaluationStrategy,ExplainableProfile,ConfidenceProfile,AchievementProfile,CapResult,HardReqResult,CandidateScore,RankedList data;
```

---

## Pipeline Stages

The central orchestrator in [orchestrator.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/orchestrator.py) executes the pipeline in sequential stages:

| Stage | Name | Description | Responsible Module |
|:---:|:---|:---|:---|
| **1** | **PDF Ingestion** | Extracts text from PDFs using concurrent dual engines (`pdfplumber` + `PyMuPDF`). | [resume_parser.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/ingestion/resume_parser.py) |
| **2** | **Resume LLM Extraction** | Extracts structured fields via Gemini and compiles them into a verified Pydantic model. | [resume_extractor.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/extraction/resume_extractor.py) |
| **3** | **Job LLM Extraction** | Extracts explicit requirements, hidden signals, and complexity metrics from Job Descriptions. | [job_extractor.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/extraction/job_extractor.py) |
| **4** | **Role Classification** | Evaluates the job profile heuristics to detect role family, specialization, and seniority. | [role_classifier.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/role_classification/role_classifier.py) |
| **4A** | **Evaluation Strategy** | Generates dynamic weighting strategies based on the classified role context. | [strategy_engine.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/evaluation_strategy/strategy_engine.py) |
| **5** | **Text Compilation** | Builds detailed, structured semantic text profiles from extracted candidate and job fields. | [text_builder.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/embeddings/text_builder.py) |
| **6** | **Vector Embedding** | Generates normalized dense vector embeddings using a local SentenceTransformer model. | [embedding_generator.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/embeddings/embedding_generator.py) |
| **7** | **Semantic Matching** | Computes the cosine similarity between candidate and job profile vector representations. | [semantic_matcher.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/matching/semantic_matcher.py) |
| **8** | **Hard Requirements** | Expanded compliance resolver checking candidate capabilities against job specifications. | [hard_requirements](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/hard_requirements) |
| **9** | **Achievement Analysis** | Scans candidate fields to detect, categorize, score, and justify standout achievements. | [achievement_detector.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/achievement_analysis/achievement_detector.py) |
| **10** | **Candidate Scoring** | Combines all evaluation signals dynamically using evaluation strategy role weights. | [scoring_engine.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_scoring/scoring_engine.py) |
| **11** | **Candidate Ranking** | Deterministically ranks multiple candidate results, extracting strengths and concerns. | [ranking_engine.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_ranking/ranking_engine.py) |
| **12** | **Persistence** | Saves parsed candidate/job profiles, strategies, achievement profiles, scores, and match reports. | [storage](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/storage) |

---

## Project Directory Structure

```
AI-RECRUITMENT-MODEL/
├── app/
│   ├── core/                                      # Shared foundation layer
│   │   ├── config.py                              # Environment configs & API keys
│   │   ├── logging_setup.py                       # Unified system logger setup
│   │   └── exceptions.py                          # Core domain base exceptions
│   │
│   ├── ingestion/                                 # Stage 1 — Ingestion parsing
│   │   └── resume_parser.py                       # Concurrent dual-engine PDF extractor
│   │
│   ├── extraction/                                # Stage 2 & 3 — LLM semantic extraction
│   │   ├── resume_extractor.py                    # Candidate resume extraction engine
│   │   └── job_extractor.py                       # Job description extraction engine
│   │
│   ├── schemas/                                   # Pydantic schema schemas
│   │   ├── resume_schema.py                       # Candidate profile structure contract
│   │   └── job_schema.py                          # Job profile structure contract
│   │
│   ├── prompts/                                   # Prompt template files
│   │   ├── extraction_prompt.py                   # Resume LLM extraction rules
│   │   └── job_prompt.py                          # Job description extraction rules
│   │
│   ├── role_classification/                       # Stage 4 — Domain classification
│   │   ├── models.py                              # RoleProfile definitions
│   │   ├── exceptions.py                          # Classifier exception classes
│   │   ├── role_rules.py                          # Mapping matrices & heuristics
│   │   └── role_classifier.py                     # Heuristics evaluation engine
│   │
│   ├── evaluation_strategy/                       # Stage 4A — Evaluation strategy weights
│   │   ├── models.py                              # EvaluationStrategy definition
│   │   ├── strategy_rules.py                      # Weight configurations & rule library
│   │   ├── strategy_engine.py                     # Heuristic rules evaluation engine
│   │   └── exceptions.py                          # Evaluation strategy exception classes
│   │
│   ├── knowledge_graph/                           # Stage 5 — Skills graph & inferences
│   │   ├── repositories/
│   │   │   └── networkx_repository.py             # NetworkX taxonomy layer
│   │   ├── services/
│   │   │   └── skill_graph_service.py             # Graph queries service
│   │   ├── inference/
│   │   │   └── skill_inference_engine.py          # Ancestor skill inference resolver
│   │   ├── models.py                              # SkillNode structures
│   │   └── exceptions.py                          # Graph specific exceptions
│   │
│   ├── skill_evidence/                            # Stage 6 — Evidence chains
│   │   ├── engines/                               # Sub-engines (dependency, aggregation)
│   │   ├── graph/                                 # Graph schema adapters
│   │   ├── models/
│   │   │   └── evidence_models.py                 # Trace source & ExplainableSkillProfile
│   │   ├── scoring/                               # EvidenceScorer, TierClassifier
│   │   └── services/                              # Orchestrator services & factories
│   │
│   ├── experience_analysis/                       # Experience heuristics engine
│   │   ├── complexity_calculator.py               # Evaluates role complexity
│   │   ├── confidence_calculator.py               # Generates skill confidence
│   │   ├── evidence_collector.py                  # Collects raw experience signals
│   │   ├── signal_calculator.py                   # Analyzes project/role duration
│   │   ├── skill_confidence_engine.py             # Confidence analysis orchestrator
│   │   └── models.py                              # SkillConfidenceProfile
│   │
│   ├── hard_requirements/                         # Strict compliance matching
│   │   ├── models.py                              # HardRequirementResult & CapabilityResolutionResult
│   │   ├── exceptions.py                          # Compliance exception classes
│   │   └── capability_resolver.py                 # Resolves explicit/inferred skill matches
│   │
│   ├── candidate_scoring/                         # Stage 10 — Dynamic candidate scoring
│   │   ├── models.py                              # CandidateScoreProfile definition
│   │   ├── score_calculators.py                   # Sub-score mathematical calculators
│   │   ├── scoring_engine.py                      # Scoring orchestration & weights coordinator
│   │   └── exceptions.py                          # Scoring exceptions
│   │
│   ├── candidate_ranking/                         # Stage 11 — Deterministic candidate ranking
│   │   ├── models.py                              # RankedCandidate, RankedCandidateList
│   │   ├── tie_breakers.py                        # cmp_to_key deterministic comparators
│   │   ├── ranking_engine.py                      # Ranking coordination & strengths/concerns
│   │   └── exceptions.py                          # Ranking exceptions
│   │
│   ├── achievement_analysis/                      # Stage 9 — Standout achievement signals
│   │   ├── models.py                              # AchievementProfile & details definitions
│   │   ├── achievement_detector.py                # Regex scanner & candidate detector
│   │   ├── scoring.py                             # Category scorer & trace generator
│   │   └── exceptions.py                          # Achievement analysis exceptions
│   │
│   ├── embeddings/                                # Embeddings generation
│   │   ├── embedding_generator.py                 # Local SentenceTransformer generator
│   │   ├── embedder.py                            # LLM API embedding generator wrapper
│   │   └── text_builder.py                        # Compiler for semantic matching text
│   │
│   ├── matching/                                  # Cosine similarities
│   │   └── semantic_matcher.py                    # Scikit-learn matcher engine
│   │
│   ├── storage/                                   # Persistence layer
│   │   ├── job_storage.py                         # Saves JobProfile structures to file
│   │   └── profile_storage.py                     # Saves ResumeProfile structures to file
│   │
│   ├── utils/                                     # Utility layer
│   │   └── file_utils.py                          # File validations and assertions
│   │
│   ├── orchestrator.py                            # Central pipeline orchestrator
│   └── main.py                                    # CLI execution entry point shim
│
├── scripts/                                       # Independent execution scripts
│   ├── run_full_pipeline.py                       # Orchestrated end-to-end pipeline script
│   ├── run_resume_pipeline.py                     # Parse + Extract resume pipeline script
│   ├── run_job_pipeline.py                        # Parse + Extract job description script
│   └── run_matching.py                            # Matches stored JSON assets
│
├── data/                                          # Output assets (runtime generated)
│   ├── extracted_profiles/                        # Saved candidate json profiles
│   ├── extracted_jobs/                            # Saved job description profiles
│   ├── skill_graph/                               # Taxonomy mapping definitions
│   │   └── skills_taxonomy.json                   # Master NetworkX taxonomy schema
│   └── match_reports/                             # Vector score report outputs
│
├── tests/                                         # Project-wide unit tests directory
│   ├── test_achievement_analyzer.py                # Verifies standout signals detection & scoring
│   ├── test_evaluation_strategy.py                # Verifies rule libraries & fallbacks
│   ├── test_capability_resolver.py                # Verifies skill graph compliance resolver
│   ├── test_complexity_calculator.py              # Verifies experience complexity math
│   ├── test_confidence_calculator.py              # Verifies confidence level thresholds
...
```

---

## Setup & Installation

```bash
# 1. Clone the repository and navigate to root
git clone <repository_url>
cd AI-RECRUITMENT-MODEL

# 2. Setup the virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install packages
pip install -r requirements.txt
```

---

## Usage Instructions

### Full Pipeline via Orchestrator
To run the full end-to-end evaluation:

```python
from app.orchestrator import RecruitmentOrchestrator

orchestrator = RecruitmentOrchestrator()
result = orchestrator.run(
    resume_pdf_path="sample_resumes/resume1.pdf",
    jd_text="Raw job description text looking for a Senior Backend Developer...",
    job_name="senior_backend"
)

print(f"Match Score: {result.semantic_score:.2f}")
print(f"Role Specialization: {result.role_profile.specialization}")
print(f"Strictness Level: {result.evaluation_strategy.strictness_level}")
print(f"Candidate Overall Score: {result.candidate_score.overall_score:.1f}")

# Rank multiple candidates
ranked_candidates = orchestrator.rank_candidates([result])
for rc in ranked_candidates.root:
    print(f"Rank {rc.rank}: {rc.candidate_name} | Score: {rc.overall_score:.1f}")
    print(f"Strengths: {rc.strengths}")
    print(f"Concerns: {rc.concerns}")
```

### Standalone Evaluation Strategy Engine
```python
from app.role_classification.models import RoleProfile
from app.evaluation_strategy.strategy_engine import EvaluationStrategyEngine

engine = EvaluationStrategyEngine()
role_profile = RoleProfile(
    role_family="software_engineering",
    specialization="backend_engineer",
    seniority="intern",
    evaluation_profile="intern_backend"
)

strategy = engine.generate_strategy(role_profile)
print(strategy.component_weights)
# Outputs: {'skills': 0.35, 'projects': 0.40, 'experience': 0.20, 'achievements': 0.05}
```

### Standalone Achievement Analyzer
```python
from app.schemas.resume_schema import ResumeProfile
from app.achievement_analysis.achievement_detector import AchievementAnalyzer

analyzer = AchievementAnalyzer()
resume_profile = ResumeProfile(
    name="Jane Doe",
    skills=["Python"],
    achievements=["AIR 500 in JEE Advanced"],
    education=[],
    experience=[],
    projects=[]
)

ach_profile = analyzer.analyze(resume_profile)
print(ach_profile.achievement_score)      # Numeric score (e.g. 3.5)
print(ach_profile.explanation_traces)     # Step-by-step scoring traces
```

### Standalone Candidate Scoring Engine
```python
from app.candidate_scoring.scoring_engine import CandidateScoringEngine
from app.hard_requirements.models import HardRequirementResult

scoring_engine = CandidateScoringEngine()
score_profile = scoring_engine.generate_score(
    resume_profile=resume_profile,
    job_profile=job_profile,
    evaluation_strategy=strategy,
    hard_requirement_result=HardRequirementResult(passed=True, coverage_score=1.0),
    semantic_score=0.85,
    confidence_profiles=confidence_profiles,
    achievement_profile=achievement_profile
)
print(f"Overall Score: {score_profile.overall_score}")
print(f"Breakdowns: {score_profile.component_scores}")
```

### Standalone Candidate Ranking Engine
```python
from app.candidate_ranking.ranking_engine import CandidateRankingEngine

ranking_engine = CandidateRankingEngine()
ranked_list = ranking_engine.rank([score_profile_a, score_profile_b])
for candidate in ranked_list.root:
    print(f"Rank {candidate.rank}: {candidate.candidate_name} ({candidate.overall_score})")
```

---

## Data Schemas

### Resume Profile
Defined in [resume_schema.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/schemas/resume_schema.py). Represents extracted candidate details:
* `name`: Full name of candidate.
* `skills`: List of explicit skills declarations.
* `experience`: List of professional records (role, company, duration, description).
* `projects`: List of completed projects (name, technologies used, descriptions).
* `education`: List of degrees (degree, institution, field, graduation year).
* `certifications`: Extracted certifications (name, issuer, year).
* `achievements`: List of string raw achievements.

### Job Profile
Defined in [job_schema.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/schemas/job_schema.py). Represents job specifications:
* `title`: Official role title.
* `required_skills`: List of mandatory core skills.
* `preferred_skills`: List of nice-to-have supplementary skills.
* `critical_skills`: Highest priority requirements list.
* `experience_required`: Numeric tenure requirements.
* `seniority_level`: Classified target seniority.
* `hidden_hiring_signals`: Boolean fields (e.g. `startup_environment`, `high_ownership`).

### Role Profile
Defined in [models.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/role_classification/models.py). Contains structural details inferred by classifier rules:
* `role_family`: Broad field (e.g. `software_engineering`).
* `specialization`: Detailed job title (e.g. `backend_engineer`).
* `seniority`: Qualitative seniority level (e.g. `mid_level`).
* `evaluation_profile`: Composite target identifier (e.g. `mid_backend`).

### Evaluation Strategy
Defined in [models.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/evaluation_strategy/models.py). Contains weights and strictness settings:
* `evaluation_profile`: Composite target profile (e.g., `intern_backend`).
* `strictness_level`: Evaluation strictness (`low`, `medium`, `high`).
* `component_weights`: Dictionary mapping candidate areas to weights (must sum to `1.0`).
* `minimum_skill_confidence`: Threshold for skill confidence ratings.
* `hard_requirement_tolerance`: Acceptable tolerance level for missing requirements.

### Achievement Profile
Defined in [models.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/achievement_analysis/models.py). Contains candidate achievement signals:
* `achievement_score`: Overall consolidated score between `0.0` and `10.0`.
* `academic`: List of detected academic `AchievementDetail` items.
* `technical`: List of detected technical `AchievementDetail` items.
* `research`: List of detected research `AchievementDetail` items.
* `leadership`: List of detected leadership `AchievementDetail` items.
* `entrepreneurship`: List of detected entrepreneurial `AchievementDetail` items.
* `category_scores`: Calculated numeric scores for each individual category.
* `explanation_traces`: Structured, transparent explanation statements detailing how scores were assigned.

### Candidate Score Profile
Defined in [models.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_scoring/models.py). Contains all scoring components and evidence:
* `candidate_name`: Name of the scored candidate.
* `overall_score`: Consolidated, dynamically weighted score (0.0 to 100.0).
* `component_scores`: Dictionary of individual scores per active category (semantic, skills, experience, achievements, projects, leadership).
* `weight_breakdown`: Evaluation weights applied.
* `explanation`: Step-by-step trace logs of how each component and final score was derived.
* `hard_requirements_coverage`: Candidate's requirement compliance score.
* `semantic_score`: Local dense vector match score.
* `skill_confidence_score`: Average candidate skill confidence.
* `achievement_score`: Max-biased standout achievement score.

### Ranked Candidate List
Defined in [models.py](file:///Users/nischayverma/Desktop/AI-RECRUITMENT-MODEL/app/candidate_ranking/models.py). Represents a sorted collection of ranked candidates:
* `rank`: Rank number (1-indexed).
* `candidate_name` (alias `candidate`): Full candidate name.
* `overall_score` (alias `score`): Candidate's overall weighted score.
* `strengths`: Bulleted list of candidate strengths based on category high scores.
* `concerns`: Bulleted list of candidate concerns based on compliance failures or low scores.

---

## Extraction Quality & Prevention Rules

To preserve accuracy, ARIS enforces strict guidelines across its parsing pipelines:
* **The Golden Rule**: Every extracted data point must represent an *Explicit Fact* or *Supported Inference*. Default to `null`, `[]`, or `false` when evidence is insufficient.
* **No Technology Hallucination**: Do not introduce unmentioned libraries.
* **No Achievement Hallucination**: Every reported achievement is matched with exact sentence evidence from the resume source.
* **Leadership Heuristics**: `leadership` is set to `true` only when the candidate has managed, supervised, or mentored people.

---

## Custom Exception Hierarchy

All system processes use a unified, descriptive hierarchy inheriting from `ARISError` for clean diagnostics:

```
Exception (Python Built-in)
 └── ARISError (app.core.exceptions)
      ├── MissingAPIKeyError (app.core.exceptions)
      ├── GeminiAPIError (app.core.exceptions)
      ├── InvalidJSONResponseError (app.core.exceptions)
      ├── ProfileValidationError (app.core.exceptions)
      │
      ├── ResumeParserError (app.ingestion.resume_parser)
      │    ├── CorruptedPDFError (app.utils.file_utils)
      │    ├── EmptyPDFError (app.utils.file_utils)
      │    └── EncryptedPDFError (app.utils.file_utils)
      │
      ├── ResumeExtractionError (app.extraction.resume_extractor)
      │    └── EmptyResumeTextError (app.extraction.resume_extractor)
      │
      ├── JobExtractionError (app.extraction.job_extractor)
      │    └── EmptyJobTextError (app.extraction.job_extractor)
      │
      ├── RoleClassificationError (app.role_classification.exceptions)
      │    ├── RoleFamilyDetectionError (app.role_classification.exceptions)
      │    ├── SpecializationDetectionError (app.role_classification.exceptions)
      │    └── SeniorityDetectionError (app.role_classification.exceptions)
      │
      ├── EvaluationStrategyError (app.evaluation_strategy.exceptions)
      │    ├── StrategyNotFoundError (app.evaluation_strategy.exceptions)
      │    └── InvalidStrategyConfigError (app.evaluation_strategy.exceptions)
      │
      ├── HardRequirementError (app.hard_requirements.exceptions)
      │    ├── CapabilityResolutionError (app.hard_requirements.exceptions)
      │    ├── RequirementMatchingError (app.hard_requirements.exceptions)
      │    └── CoverageEvaluationError (app.hard_requirements.exceptions)
      │
      ├── AchievementAnalysisError (app.achievement_analysis.exceptions)
      │    ├── DetectionError (app.achievement_analysis.exceptions)
      │    └── ScoringError (app.achievement_analysis.exceptions)
      │
      ├── CandidateScoringError (app.candidate_scoring.exceptions)
      │    └── EngineExecutionError (app.candidate_scoring.exceptions)
      │
      ├── CandidateRankingError (app.candidate_ranking.exceptions)
      │    └── RankingEngineError (app.candidate_ranking.exceptions)
      │
      ├── EmbeddingError (app.embeddings.embedder)
      │    └── EmbeddingGenerationError (app.embeddings.embedding_generator)
      │
      └── SemanticMatchingError (app.matching.semantic_matcher)
```

---

## Running Tests

Verify all components are working correctly using pytest. Use `PYTHONPATH` before executing to ensure module imports are resolved:

```bash
# Run all tests (260+ cases covered, including Phase 10 and Phase 11)
PYTHONPATH=. .venv/bin/pytest
```

---

## Project Roadmap

ARIS V2 consists of thirteen distinct phases, divided into **Implemented** and **Future Roadmap** phases:

### Implemented Phases
* **Phase 1: Dual-Engine PDF Ingestion**: Robust text extraction from raw PDFs.
* **Phase 2: Resume Understanding Engine**: LLM extraction of candidate attributes.
* **Phase 3: Job Understanding Engine**: LLM extraction of JD requirements.
* **Phase 4: Role Classification Engine**: Domain and seniority classification.
* **Phase 4A: Evaluation Strategy Engine**: Generating dynamic, role-aware criteria.
* **Phase 5: Skill Knowledge Graph & Inference**: Canonical skill mapping and parent inference.
* **Phase 6: Skill Evidence Engine**: Weighted direct and dependency evidence tracking.
* **Phase 7: Skill Confidence Engine**: Candidate tenure & project complexity math.
* **Phase 8: Hard Requirements Compliance Engine**: Strict checks of candidate capabilities.
* **Phase 9: Achievement Analyzer**: Standing signals discovery & trace scoring.
* **Phase 10: Candidate Scoring Engine**: Unified dynamic weighted score calculations.
* **Phase 11: Candidate Ranking Engine**: Deterministic candidate rank order sorting and sorting tie-breakers.

### Future Roadmap Phases
* **Phase 12: Explainability Rendering**: Dynamic visualization of evidence and reasons.
* **Phase 13: Recruiter Copilot**: Interactive dialogue interface for custom candidate searches.

---

## Troubleshooting

| Diagnostics Issue | Common Culprit | Suggested Resolution |
|:---|:---|:---|
| `ModuleNotFoundError: No module named 'app'` | Running pytest directly without setting the python import paths | Execute tests setting `PYTHONPATH=. .venv/bin/pytest`. |
| `MissingAPIKeyError` | `.env` variables cannot be read | Ensure the `.env` file is in the root directory and contains `GEMINI_API_KEY`. |
| `Slow execution on first run` | SentenceTransformer is downloading the local model | Wait for downloading to finish. Subsequent runs load from local cache. |
| `EmptyPDFError` | The resume PDF has no selectable text | Use OCR on scanned resume files. |
