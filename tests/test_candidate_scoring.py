"""
Unit tests for Phase 10 Candidate Scoring Engine.
"""

import pytest
from typing import Any
from app.schemas.resume_schema import ResumeProfile, Experience, Project
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.evaluation_strategy.models import EvaluationStrategy
from app.achievement_analysis.models import AchievementProfile, AchievementDetail
from app.experience_analysis.models import SkillConfidenceProfile
from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_scoring.score_calculators import ComponentScoreCalculators, parse_duration_to_years
from app.candidate_scoring.scoring_engine import CandidateScoringEngine
from app.candidate_scoring.exceptions import EngineExecutionError
from app.hard_requirements.models import HardRequirementResult


def test_parse_duration_to_years():
    assert parse_duration_to_years("2 years") == 2.0
    assert parse_duration_to_years("6 months") == 0.5
    assert parse_duration_to_years("1 year 6 months") == 1.5
    assert parse_duration_to_years("1.5 yrs") == 1.5
    assert parse_duration_to_years("3 mos") == 0.25
    assert parse_duration_to_years(None) == 0.0
    assert parse_duration_to_years("") == 0.0


def test_score_calculators():
    # 1. Semantic
    assert ComponentScoreCalculators.calculate_semantic_score(0.85) == 85.0
    assert ComponentScoreCalculators.calculate_semantic_score(1.1) == 100.0
    assert ComponentScoreCalculators.calculate_semantic_score(-0.5) == 0.0

    # 2. Skills
    confidence_profiles = {
        "Python": SkillConfidenceProfile(
            skill="Python", professional_signal=1.0, depth_signal=1.0, complexity_signal=1.0,
            confidence_score=90.0, confidence_level="Expert", skill_tier="Expert"
        ),
        "FastAPI": SkillConfidenceProfile(
            skill="FastAPI", professional_signal=0.5, depth_signal=0.5, complexity_signal=0.5,
            confidence_score=60.0, confidence_level="Moderate", skill_tier="Intermediate"
        )
    }
    # Both required skills possessed
    score = ComponentScoreCalculators.calculate_skills_score(confidence_profiles, ["Python", "FastAPI"])
    assert score == 75.0  # (90 + 60) / 2 = 75
    # One required skill missing
    score_missing = ComponentScoreCalculators.calculate_skills_score(confidence_profiles, ["Python", "Docker"])
    assert score_missing == 45.0  # (90 + 0) / 2 = 45
    # Empty requirements list fallback
    score_fallback = ComponentScoreCalculators.calculate_skills_score(confidence_profiles, [])
    assert score_fallback == 75.0

    # 3. Experience
    resume_profile = ResumeProfile(
        skills=["Python"],
        experience=[
            Experience(role="Backend Engineer", duration="2 years"),
            Experience(role="Lead Backend Engineer", duration="3 years")
        ],
        projects=[], education=[], certifications=[], achievements=[]
    )
    # Total parsed: 5 years, required: 5 years -> 100%
    assert ComponentScoreCalculators.calculate_experience_score(resume_profile, 5) == 100.0
    # Total parsed: 5 years, required: 10 years -> 50%
    assert ComponentScoreCalculators.calculate_experience_score(resume_profile, 10) == 50.0

    # 4. Achievements
    ach_profile = AchievementProfile(
        achievement_score=8.2, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
        category_scores={}, explanation_traces=[]
    )
    assert ComponentScoreCalculators.calculate_achievements_score(ach_profile) == 82.0

    # 5. Projects
    resume_proj = ResumeProfile(
        skills=["Python"],
        projects=[
            Project(name="Proj1", technologies=["Python", "FastAPI"]),
            Project(name="Proj2", technologies=["Docker"])
        ],
        experience=[], education=[], certifications=[], achievements=[]
    )
    # Match skills: Python, FastAPI
    assert ComponentScoreCalculators.calculate_projects_score(resume_proj, ["Python"]) == 60.0  # 2 projects (40) + 1 relevant (20) = 60.0
    assert ComponentScoreCalculators.calculate_projects_score(resume_proj, ["Docker"]) == 60.0  # 2 projects (40) + 1 relevant (20) = 60.0

    # 6. Leadership
    ach_profile_lead = AchievementProfile(
        achievement_score=0.0, academic=[], technical=[], research=[],
        leadership=[
            AchievementDetail(title="Club President", source_section="education", source_detail="...", score_contribution=2.5, explanation="...")
        ],
        entrepreneurship=[], category_scores={}, explanation_traces=[]
    )
    # Has lead role in experience
    assert ComponentScoreCalculators.calculate_leadership_score(resume_profile, ach_profile_lead) == 100.0
    
    # No lead role, has one leadership achievement
    resume_no_lead = ResumeProfile(
        skills=[], experience=[Experience(role="Engineer", duration="1 year")],
        projects=[], education=[], certifications=[], achievements=[]
    )
    assert ComponentScoreCalculators.calculate_leadership_score(resume_no_lead, ach_profile_lead) == 50.0


def test_candidate_scoring_engine():
    engine = CandidateScoringEngine()

    resume_profile = ResumeProfile(
        name="John Doe",
        skills=["Python", "FastAPI"],
        experience=[Experience(role="Developer", duration="3 years")],
        projects=[Project(name="P1", technologies=["Python"])],
        education=[], certifications=[], achievements=[]
    )

    job_profile = JobProfile(
        title="Python Dev",
        required_skills=["Python", "FastAPI"],
        preferred_skills=[], critical_skills=[],
        experience_required=3,
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Backend Developer"
    )

    strategy = EvaluationStrategy(
        evaluation_profile="mid_backend",
        strictness_level="medium",
        component_weights={
            "skills": 0.30,
            "projects": 0.30,
            "experience": 0.30,
            "achievements": 0.10
        },
        minimum_skill_confidence=50.0,
        hard_requirement_tolerance=10.0
    )

    hard_result = HardRequirementResult(
        passed=True, coverage_score=1.0, matched_required=["Python"], missing_required=[],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="Passed"
    )

    confidence_profiles = {
        "Python": SkillConfidenceProfile(
            skill="Python", professional_signal=1.0, depth_signal=1.0, complexity_signal=1.0,
            confidence_score=80.0, confidence_level="Strong", skill_tier="Advanced"
        )
    }

    ach_profile = AchievementProfile(
        achievement_score=5.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
        category_scores={}, explanation_traces=[]
    )

    score_profile = engine.generate_score(
        resume_profile=resume_profile,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result,
        semantic_score=0.80,
        confidence_profiles=confidence_profiles,
        achievement_profile=ach_profile
    )

    assert isinstance(score_profile, CandidateScoreProfile)
    assert score_profile.candidate_name == "John Doe"
    # Component calculations:
    # skills = 80 (Python) + 0 (FastAPI missing from confidence profiles) -> average = 40.0
    # projects = 1 project (20) + 1 relevant (20) = 40.0
    # experience = 3 years / 3 required -> 100.0
    # achievements = 5.0 * 10 = 50.0
    # Weighted: 40 * 0.3 + 40 * 0.3 + 100 * 0.3 + 50 * 0.1 = 12 + 12 + 30 + 5 = 59.0
    assert score_profile.overall_score == 59.0
    assert score_profile.component_scores["skills"] == 40.0
    assert score_profile.component_scores["experience"] == 100.0
    
    # Check tie breaker preserves
    assert score_profile.hard_requirements_coverage == 1.0
    assert score_profile.semantic_score == 0.80
    assert score_profile.skill_confidence_score == 80.0
    assert score_profile.achievement_score == 5.0

    # Ensure traces generated
    assert len(score_profile.explanation) > 0
    assert any("skill" in trace.lower() for trace in score_profile.explanation)


def test_scoring_engine_validation():
    engine = CandidateScoringEngine()
    with pytest.raises(EngineExecutionError):
        engine.generate_score(None, Any, Any, Any, Any, Any, Any)
