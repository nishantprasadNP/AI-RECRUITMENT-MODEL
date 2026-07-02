"""
Candidate Scoring Engine for Phase 10 in ARIS V2.
"""

import logging
from typing import Dict, List, Any, Optional
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import JobProfile
from app.evaluation_strategy.models import EvaluationStrategy
from app.achievement_analysis.models import AchievementProfile
from app.experience_analysis.models import SkillConfidenceProfile
from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_scoring.score_calculators import ComponentScoreCalculators
from app.candidate_scoring.exceptions import EngineExecutionError

logger = logging.getLogger("aris.candidate_scoring.engine")


class CandidateScoringEngine:
    """
    Combines all candidate evaluation signals into a single, unified, role-weighted score
    using weights defined by the EvaluationStrategy.
    """
    def __init__(self) -> None:
        pass

    def generate_score(
        self,
        resume_profile: ResumeProfile,
        job_profile: JobProfile,
        evaluation_strategy: EvaluationStrategy,
        hard_requirement_result: Any,
        semantic_score: float,
        confidence_profiles: Dict[str, SkillConfidenceProfile],
        achievement_profile: AchievementProfile
    ) -> CandidateScoreProfile:
        """
        Consumes all candidate evaluation signals and produces a unified CandidateScoreProfile.

        Args:
            resume_profile: Candidate's structured ResumeProfile.
            job_profile: The job requirements JobProfile.
            evaluation_strategy: The role-aware criteria EvaluationStrategy weights.
            hard_requirement_result: HardRequirementsResult indicating compliance check results.
            semantic_score: Float cosine similarity matching score.
            confidence_profiles: Dictionary of candidate skills mapping to SkillConfidenceProfile.
            achievement_profile: AchievementProfile containing candidate achievement signals.

        Returns:
            A CandidateScoreProfile containing overall score, breakdowns, and trace logs.

        Raises:
            EngineExecutionError: If scoring pipeline execution fails.
        """
        if not resume_profile:
            raise EngineExecutionError("ResumeProfile cannot be None.")
        if not evaluation_strategy:
            raise EngineExecutionError("EvaluationStrategy cannot be None.")

        try:
            weights = evaluation_strategy.component_weights
            component_scores: Dict[str, float] = {}
            explanation: List[str] = []

            candidate_name = resume_profile.name or "Unknown Candidate"
            logger.info("Scoring candidate: %s", candidate_name)

            # Use normalized (canonical) required skills so matching aligns with the
            # HardRequirementEngine and with the canonical keys in confidence_profiles.
            # Example: JD "React" + Resume "ReactJS" both normalize to "React.js" —
            # only canonical matching finds the confidence entry.
            # Falls back to raw required_skills if normalization was not run
            # (e.g. in unit tests that bypass the orchestrator).
            normalized = job_profile.normalized_required_skills if job_profile else []
            req_skills = normalized if normalized else (job_profile.required_skills if job_profile else [])
            exp_req = job_profile.experience_required if job_profile else 0


            # 2. Skill Strength
            if "skills" in weights:
                score = ComponentScoreCalculators.calculate_skills_score(confidence_profiles, req_skills)
                component_scores["skills"] = score
                explanation.append(f"Skill Strength: {score}/100.0 (Weight: {weights['skills']:.2f})")

            # 3. Experience Quality
            if "experience" in weights:
                score = ComponentScoreCalculators.calculate_experience_score(resume_profile, exp_req)
                component_scores["experience"] = score
                explanation.append(f"Experience Quality: {score}/100.0 (Weight: {weights['experience']:.2f})")

            # 4. Achievement Impact
            if "achievements" in weights:
                score = ComponentScoreCalculators.calculate_achievements_score(achievement_profile)
                component_scores["achievements"] = score
                explanation.append(f"Achievement Impact: {score}/100.0 (Weight: {weights['achievements']:.2f})")

            # 5. Projects Strength
            if "projects" in weights:
                score = ComponentScoreCalculators.calculate_projects_score(resume_profile, req_skills)
                component_scores["projects"] = score
                explanation.append(f"Projects Strength: {score}/100.0 (Weight: {weights['projects']:.2f})")

            # 6. Leadership Strength
            if "leadership" in weights:
                score = ComponentScoreCalculators.calculate_leadership_score(resume_profile, achievement_profile)
                component_scores["leadership"] = score
                explanation.append(f"Leadership Strength: {score}/100.0 (Weight: {weights['leadership']:.2f})")

            # Calculate compliance score derived from coverage score
            hard_coverage = 0.0
            missing_skills = []
            if hard_requirement_result:
                hard_coverage = getattr(hard_requirement_result, "coverage_score", 0.0)
                missing_skills = getattr(hard_requirement_result, "missing_required", [])

            compliance_score = round(hard_coverage * 100.0, 1)
            component_scores["hard_requirements"] = compliance_score

            # Calculate overall weighted score
            total_weight = sum(weights[k] for k in weights if k in component_scores)
            if total_weight > 0:
                weighted_score = sum(component_scores[k] * weights[k] for k in component_scores if k in weights) / total_weight
                overall_score = round(weighted_score, 1)
            else:
                overall_score = 0.0

            explanation.insert(0, f"Overall candidate score calculated as {overall_score} using evaluation profile '{evaluation_strategy.evaluation_profile}'.")

            # Append hard requirements check details to explanation
            if hard_requirement_result:
                if not missing_skills:
                    explanation.append("Hard Requirements: Passed critical compliance requirements check.")
                else:
                    explanation.append(f"Hard Requirements: Failed compliance check. Missing required skills: {missing_skills}")

            # Compute skill confidence score tie-breaker metric (average of candidate's actual confidence scores)
            avg_skill_confidence = 0.0
            if confidence_profiles:
                scores = [p.confidence_score for p in confidence_profiles.values()]
                avg_skill_confidence = sum(scores) / len(scores) if scores else 0.0

            ach_score_val = achievement_profile.achievement_score if achievement_profile else 0.0

            return CandidateScoreProfile(
                candidate_name=candidate_name,
                overall_score=overall_score,
                component_scores=component_scores,
                weight_breakdown=weights,
                explanation=explanation,
                hard_requirements_coverage=hard_coverage,
                semantic_score=semantic_score,
                skill_confidence_score=round(avg_skill_confidence, 2),
                achievement_score=ach_score_val
            )

        except Exception as e:
            raise EngineExecutionError(f"Scoring pipeline execution failed: {e}") from e
