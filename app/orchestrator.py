"""
RecruitmentOrchestrator — Central pipeline entry point for the AI Recruitment Intelligence System.

Takes a resume PDF path and a raw job description text, runs all pipeline stages in sequence,
and returns a fully structured OrchestratorResult containing both profiles, the semantic match
score, and the paths to all saved artefacts.

Pipeline stages (in execution order):
  1. Ingest       — Parse PDF to raw text          (app.ingestion.resume_parser)
  2. Extract      — Resume LLM extraction          (app.extraction.resume_extractor)
  3. Extract      — Job description LLM extraction (app.extraction.job_extractor)
  4. Build text   — Compile semantic text from profiles (app.embeddings.text_builder)
  5. Embed        — Generate vector embeddings     (app.embeddings.embedding_generator)
  6. Match        — Compute cosine similarity      (app.matching.semantic_matcher)
  7. Persist      — Save profiles + match report   (app.storage.*)

Usage:
    from app.orchestrator import RecruitmentOrchestrator

    orchestrator = RecruitmentOrchestrator()
    result = orchestrator.run(
        resume_pdf_path="sample_resumes/resume1.pdf",
        jd_text=open("sample_jds/senior_software_engineer.txt").read(),
    )
    print(f"Match Score: {result.semantic_score:.4f}")
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.embeddings.embedding_generator import EmbeddingGenerator
from app.embeddings.text_builder import build_job_text, build_resume_text
from app.extraction.job_extractor import JobExtractor
from app.extraction.resume_extractor import ResumeInformationExtractor
from app.ingestion.resume_parser import ResumeParser
from app.matching.semantic_matcher import SemanticMatcher
from app.schemas.job_schema import JobProfile, SkillRequirement
from app.schemas.resume_schema import ResumeProfile
from app.role_classification.role_classifier import RoleClassifier
from app.role_classification.models import RoleProfile
from app.evaluation_strategy.strategy_engine import EvaluationStrategyEngine
from app.evaluation_strategy.models import EvaluationStrategy
from app.achievement_analysis.achievement_detector import AchievementAnalyzer
from app.achievement_analysis.models import AchievementProfile
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine
from app.hard_requirements import CapabilityResolver, HardRequirementEngine, HardRequirementResult
from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.experience_analysis.complexity_calculator import ComplexityCalculator
from app.experience_analysis.signal_calculator import SignalCalculator
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator
from app.experience_analysis.skill_confidence_engine import SkillConfidenceEngine
from app.experience_analysis.propagation_engine import EvidencePropagationEngine
from app.candidate_scoring import CandidateScoringEngine, CandidateScoreProfile
from app.candidate_ranking import CandidateRankingEngine, RankedCandidateList
from app.skill_gap import SkillGapEngine, SkillGapResult
from app.skill_normalization import SkillNormalizer
from app.storage.job_storage import save_job_profile
from app.storage.profile_storage import save_profile

logger = logging.getLogger("aris.orchestrator")


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class OrchestratorResult:
    """
    Structured result returned by the RecruitmentOrchestrator after a full pipeline run.

    Attributes:
        candidate_name:      Extracted candidate full name (or 'Unknown Candidate').
        job_name:            Normalised job role label used for storage.
        resume_profile:      Validated ResumeProfile Pydantic object.
        job_profile:         Validated JobProfile Pydantic object.
        role_profile:        Classified RoleProfile object.
        semantic_score:      Cosine similarity score in [0.0, 1.0].
        resume_profile_path: Filesystem path to the saved candidate JSON file.
        job_profile_path:    Filesystem path to the saved job JSON file.
        match_report_path:   Filesystem path to the saved match report JSON file.
    """

    candidate_name: str = "Unknown Candidate"
    job_name: str = "Unknown Role"
    resume_profile: Optional[ResumeProfile] = None
    job_profile: Optional[JobProfile] = None
    role_profile: Optional[RoleProfile] = None
    evaluation_strategy: Optional[EvaluationStrategy] = None
    achievement_profile: Optional[AchievementProfile] = None
    candidate_score: Optional[CandidateScoreProfile] = None
    hard_requirement_result: Optional[HardRequirementResult] = None
    skill_gap_result: Optional[SkillGapResult] = None
    semantic_score: float = 0.0
    resume_profile_path: str = ""
    job_profile_path: str = ""
    match_report_path: str = ""
    # Propagated confidence profiles computed by SkillConfidenceEngine.
    # Stored here so API endpoints can consume them without a second evidence collection.
    confidence_profiles: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class RecruitmentOrchestrator:
    """
    Central pipeline orchestrator for the AI Recruitment Intelligence System.

    Wires all pipeline stages together — from raw PDF ingestion through LLM
    extraction, semantic embedding, cosine similarity matching, and persistent
    storage — into a single, clean API call.

    All sub-services are created with sensible defaults but can be injected for
    testing or customisation:

        orchestrator = RecruitmentOrchestrator(
            resume_parser=MyCustomParser(),
            embedding_generator=MyFastEmbedder(),
        )
    """

    def __init__(
        self,
        resume_parser: Optional[ResumeParser] = None,
        resume_extractor: Optional[ResumeInformationExtractor] = None,
        job_extractor: Optional[JobExtractor] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        semantic_matcher: Optional[SemanticMatcher] = None,
        role_classifier: Optional[RoleClassifier] = None,
        evaluation_strategy_engine: Optional[EvaluationStrategyEngine] = None,
        achievement_analyzer: Optional[AchievementAnalyzer] = None,
        candidate_scoring_engine: Optional[CandidateScoringEngine] = None,
        candidate_ranking_engine: Optional[CandidateRankingEngine] = None,
        skill_gap_engine: Optional[SkillGapEngine] = None,
        match_report_dir: str = "data/match_reports",
    ) -> None:
        self._parser = resume_parser or ResumeParser()
        self._resume_extractor = resume_extractor or ResumeInformationExtractor()
        self._job_extractor = job_extractor or JobExtractor()
        self._embedder = embedding_generator or EmbeddingGenerator()
        self._matcher = semantic_matcher or SemanticMatcher()
        self._role_classifier = role_classifier or RoleClassifier()
        self._evaluation_strategy_engine = evaluation_strategy_engine or EvaluationStrategyEngine()
        self._achievement_analyzer = achievement_analyzer or AchievementAnalyzer()
        self._candidate_scoring_engine = candidate_scoring_engine or CandidateScoringEngine()
        self._candidate_ranking_engine = candidate_ranking_engine or CandidateRankingEngine()
        self._skill_gap_engine = skill_gap_engine or SkillGapEngine()
        self._match_report_dir = match_report_dir

        # Initialize knowledge graph components for Hard Requirements and Skill Confidence
        skills_repo = NetworkXSkillGraphRepository()
        try:
            skills_repo.initialize("data/skill_graph/skills_taxonomy.json")
        except Exception:
            pass
        skills_service = SkillGraphService(skills_repo)
        self._skills_service = skills_service
        self._inference_engine = SkillInferenceEngine(skills_service)
        self._capability_resolver = CapabilityResolver(self._inference_engine)
        self._hard_requirement_engine = HardRequirementEngine()
        self._skill_confidence_engine = SkillConfidenceEngine(
            evidence_collector=SkillEvidenceCollector(),
            complexity_calculator=ComplexityCalculator(),
            signal_calculator=SignalCalculator(),
            confidence_calculator=SkillConfidenceCalculator()
        )
        self._evidence_propagation_engine = EvidencePropagationEngine()
        self._skill_normalizer = SkillNormalizer()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run(
        self,
        resume_pdf_path: str,
        jd_text: str,
        job_name: str = "role",
    ) -> OrchestratorResult:
        """
        Executes the full recruitment intelligence pipeline.

        Args:
            resume_pdf_path: Absolute or relative path to the candidate's resume PDF.
            jd_text:         Raw text of the job description.
            job_name:        Human-readable name for the role (used in file naming).

        Returns:
            OrchestratorResult containing profiles, match score, and saved file paths.

        Raises:
            Any exception from the underlying pipeline stages will propagate to the caller.
            Use the individual service modules directly for more granular error handling.
        """
        result = OrchestratorResult(job_name=job_name)

        # ------------------------------------------------------------------
        # Stage 1: Ingest — parse PDF to raw text
        # ------------------------------------------------------------------
        logger.info("[Stage 1/7] Ingesting resume PDF: %s", resume_pdf_path)
        resume_text = self._parser.extract_text(resume_pdf_path)
        logger.info("Resume text extracted (%d chars)", len(resume_text))

        # ------------------------------------------------------------------
        # Stage 2: Extract — resume profile via LLM
        # ------------------------------------------------------------------
        logger.info("[Stage 2/7] Extracting structured resume profile via LLM...")
        resume_profile = self._resume_extractor.extract(resume_text)

        # Skill Normalization for Resume Pipeline
        logger.info("Normalizing candidate skills...")
        normalized_skills, canonical_to_raw_map = self._skill_normalizer.normalize_list(resume_profile.skills)
        resume_profile.normalized_skills = normalized_skills
        resume_profile.canonical_to_raw_map = canonical_to_raw_map
        logger.info(
            "Candidate skills normalized. Raw: %d, Normalized: %d",
            len(resume_profile.skills),
            len(normalized_skills)
        )

        result.resume_profile = resume_profile
        result.candidate_name = resume_profile.name or "Unknown Candidate"
        logger.info("Resume profile extracted for: %s", result.candidate_name)

        # ------------------------------------------------------------------
        # Stage 3: Extract — job profile via LLM
        # ------------------------------------------------------------------
        logger.info("[Stage 3/7] Extracting structured job profile via LLM...")
        job_profile = self._job_extractor.extract(jd_text)

        # Skill Normalization for Job Description Pipeline
        logger.info("Normalizing job description required and preferred skills...")
        
        # 1. Normalize Required Skills
        normalized_req = []
        for req in job_profile.required_skills:
            normalized = self._skill_normalizer.normalize(str(req))
            for norm_skill in normalized:
                normalized_req.append(SkillRequirement(
                    skill=norm_skill.canonical,
                    importance=req.importance,
                    reason=req.reason
                ))
        # Deduplicate required skills by skill name
        seen_req = set()
        deduped_req = []
        for req in normalized_req:
            if req.skill not in seen_req:
                seen_req.add(req.skill)
                deduped_req.append(req)
        job_profile.normalized_required_skills = deduped_req

        # 2. Normalize Preferred Skills
        normalized_pref = []
        for req in job_profile.preferred_skills:
            normalized = self._skill_normalizer.normalize(str(req))
            for norm_skill in normalized:
                normalized_pref.append(SkillRequirement(
                    skill=norm_skill.canonical,
                    importance=req.importance,
                    reason=req.reason
                ))
        # Deduplicate preferred skills by skill name
        seen_pref = set()
        deduped_pref = []
        for req in normalized_pref:
            if req.skill not in seen_pref:
                seen_pref.add(req.skill)
                deduped_pref.append(req)
        job_profile.normalized_preferred_skills = deduped_pref

        # 3. Build Job Profile canonical_to_raw_map
        job_canonical_to_raw = {}
        for req in job_profile.required_skills:
            normalized = self._skill_normalizer.normalize(str(req))
            for norm_skill in normalized:
                if norm_skill.confidence == 100:
                    job_canonical_to_raw[norm_skill.canonical] = str(req)
                else:
                    job_canonical_to_raw[norm_skill.canonical] = (str(req), norm_skill.confidence)
        
        for req in job_profile.preferred_skills:
            normalized = self._skill_normalizer.normalize(str(req))
            for norm_skill in normalized:
                if norm_skill.canonical not in job_canonical_to_raw:
                    if norm_skill.confidence == 100:
                        job_canonical_to_raw[norm_skill.canonical] = str(req)
                    else:
                        job_canonical_to_raw[norm_skill.canonical] = (str(req), norm_skill.confidence)
        job_profile.canonical_to_raw_map = job_canonical_to_raw

        logger.info(
            "Job skills normalized. Required: %d -> %d, Preferred: %d -> %d, Mapped canonicals: %d",
            len(job_profile.required_skills),
            len(deduped_req),
            len(job_profile.preferred_skills),
            len(deduped_pref),
            len(job_canonical_to_raw)
        )

        result.job_profile = job_profile
        logger.info("Job profile extracted (seniority: %s)", job_profile.seniority_level)

        # ------------------------------------------------------------------
        # Stage 4: Role Classification — determine role context
        # ------------------------------------------------------------------
        logger.info("[Stage 4/7] Classifying role context...")
        role_profile = self._role_classifier.classify(job_profile)
        result.role_profile = role_profile
        logger.info("Role Family: %s", role_profile.role_family)
        logger.info("Specialization: %s", role_profile.specialization)
        logger.info("Seniority: %s", role_profile.seniority)
        logger.info("Evaluation Profile: %s", role_profile.evaluation_profile)

        # ------------------------------------------------------------------
        # Stage 4A: Evaluation Strategy — generate weights & parameters
        # ------------------------------------------------------------------
        logger.info("[Stage 4A/7] Generating evaluation strategy...")
        evaluation_strategy = self._evaluation_strategy_engine.generate_strategy(role_profile)
        result.evaluation_strategy = evaluation_strategy
        logger.info("Evaluation Profile: %s, Strictness: %s", evaluation_strategy.evaluation_profile, evaluation_strategy.strictness_level)

        # ------------------------------------------------------------------
        # Stage 5: Build semantic text representations
        # ------------------------------------------------------------------
        logger.info("[Stage 5/7] Building semantic text representations...")
        resume_semantic_text = build_resume_text(resume_profile)

        # build_job_text raises ValueError with a descriptive message if the
        # profile is empty — propagate it so the caller gets a clear explanation.
        job_semantic_text = build_job_text(job_profile)

        logger.info(
            "Semantic text built — resume: %d chars, job: %d chars",
            len(resume_semantic_text),
            len(job_semantic_text),
        )


        # ------------------------------------------------------------------
        # Stage 6: Embed — generate vector embeddings
        # ------------------------------------------------------------------
        logger.info("[Stage 6/7] Generating embeddings...")
        resume_embedding = self._embedder.generate_embedding(resume_semantic_text)
        jd_embedding = self._embedder.generate_embedding(job_semantic_text)
        logger.info(
            "Embeddings generated — resume: %s, jd: %s",
            resume_embedding.shape,
            jd_embedding.shape,
        )

        # ------------------------------------------------------------------
        # Stage 7: Match — compute cosine similarity
        # ------------------------------------------------------------------
        logger.info("[Stage 7/7] Computing semantic similarity score...")
        score = self._matcher.compute_similarity(resume_embedding, jd_embedding)
        result.semantic_score = score
        logger.info("Semantic match score: %.4f", score)

        # ------------------------------------------------------------------
        # Stage 9: Achievement Analyzer — detect exceptional signals
        # ------------------------------------------------------------------
        logger.info("[Stage 9] Analyzing candidate achievements...")
        achievement_profile = self._achievement_analyzer.analyze(resume_profile)
        result.achievement_profile = achievement_profile
        logger.info("Achievement score calculated: %.1f", achievement_profile.achievement_score)

        # ------------------------------------------------------------------
        # Stage 10: Candidate Scoring Engine — combine signals
        # ------------------------------------------------------------------
        logger.info("[Stage 10] Computing candidate score profile...")
        # Resolve capabilities
        resolved_caps = self._capability_resolver.resolve_capabilities(resume_profile)
        # Evaluate compliance
        hard_requirement_result = self._hard_requirement_engine.evaluate_compliance(job_profile, role_profile, resolved_caps)
        result.hard_requirement_result = hard_requirement_result
        # Calculate skills confidence with concepts-aware evidence propagation
        raw_evidence = self._skill_confidence_engine._evidence_collector.collect(resume_profile)
        propagated_evidence = self._evidence_propagation_engine.propagate(raw_evidence, self._skills_service)
        confidence_profiles = self._skill_confidence_engine.analyze(resume_profile, evidence_map=propagated_evidence)
        result.confidence_profiles = confidence_profiles
        # Stage 12: Skill Gap Engine — identify skill gaps
        logger.info("[Stage 12] Analyzing skill gaps...")
        skill_gap_result = self._skill_gap_engine.analyze_gaps(
            job_profile=job_profile,
            hard_requirement_result=hard_requirement_result,
            confidence_profiles=confidence_profiles
        )
        result.skill_gap_result = skill_gap_result
        # Generate final unified score profile
        candidate_score = self._candidate_scoring_engine.generate_score(
            resume_profile=resume_profile,
            job_profile=job_profile,
            evaluation_strategy=evaluation_strategy,
            hard_requirement_result=hard_requirement_result,
            semantic_score=score,
            confidence_profiles=confidence_profiles,
            achievement_profile=achievement_profile
        )
        result.candidate_score = candidate_score
        logger.info("Candidate score calculated: %.1f", candidate_score.overall_score)

        # ------------------------------------------------------------------
        # Stage 8: Persist — save profiles and match report
        # ------------------------------------------------------------------
        result.resume_profile_path = save_profile(resume_profile)
        result.job_profile_path = save_job_profile(job_profile, role_name=job_name)
        result.match_report_path = self._save_match_report(result)

        logger.info(
            "Pipeline complete. Score=%.4f | Resume=%s | Job=%s | Report=%s",
            score,
            result.resume_profile_path,
            result.job_profile_path,
            result.match_report_path,
        )

        return result

    def rank_candidates(self, results: List[OrchestratorResult]) -> RankedCandidateList:
        """
        Stage 11: Candidate Ranking Engine.
        Ranks multiple candidates based on their OrchestratorResult score profiles.
        """
        profiles = []
        for r in results:
            if r.candidate_score:
                profiles.append(r.candidate_score)
            else:
                logger.warning("Candidate %s has no score profile. Skipping in ranking.", r.candidate_name)
        
        return self._candidate_ranking_engine.rank(profiles)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _save_match_report(self, result: OrchestratorResult) -> str:
        """
        Saves a JSON match report to data/match_reports/ with a timestamped filename.

        Returns:
            Absolute path to the saved report file.
        """
        os.makedirs(self._match_report_dir, exist_ok=True)

        # Build a filesystem-safe filename
        safe_candidate = re.sub(r"[^a-z0-9]+", "_", result.candidate_name.lower()).strip("_") or "candidate"
        safe_role = re.sub(r"[^a-z0-9]+", "_", result.job_name.lower()).strip("_") or "role"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_candidate}__{safe_role}__{timestamp}.json"
        filepath = os.path.join(self._match_report_dir, filename)

        report = {
            "candidate_name": result.candidate_name,
            "job_name": result.job_name,
            "role_profile": result.role_profile.model_dump() if result.role_profile else None,
            "evaluation_strategy": result.evaluation_strategy.model_dump() if result.evaluation_strategy else None,
            "achievement_profile": result.achievement_profile.model_dump() if result.achievement_profile else None,
            "candidate_score": result.candidate_score.model_dump() if result.candidate_score else None,
            "hard_requirement_result": result.hard_requirement_result.model_dump() if result.hard_requirement_result else None,
            "skill_gap_result": result.skill_gap_result.model_dump() if result.skill_gap_result else None,
            "semantic_score": result.semantic_score,
            "semantic_score_pct": round(result.semantic_score * 100, 2),
            "resume_profile_path": result.resume_profile_path,
            "job_profile_path": result.job_profile_path,
            "generated_at": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info("Match report saved: %s", filepath)
        return filepath
