"""
Unit tests for weighted candidate scoring engine logic.
"""

import pytest
from typing import Any
from app.schemas.resume_schema import ResumeProfile, Experience, Project
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.evaluation_strategy.models import EvaluationStrategy
from app.achievement_analysis.models import AchievementProfile
from app.candidate_scoring.scoring_engine import CandidateScoringEngine
from app.hard_requirements.models import HardRequirementResult


def test_hard_requirement_coverage_impact():
    """
    Assert Candidate A (coverage=1.0) gets a higher overall score than
    Candidate B (coverage=0.60), all other scoring inputs being identical.
    """
    engine = CandidateScoringEngine()

    resume_profile = ResumeProfile(
        name="Candidate A",
        skills=["Python"],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[]
    )

    job_profile = JobProfile(
        title="Test Role",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=0,
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Test JD"
    )

    strategy = EvaluationStrategy(
        evaluation_profile="mid_backend",
        strictness_level="medium",
        component_weights={
            "skills": 0.50,
            "hard_requirements": 0.50
        },
        minimum_skill_confidence=50.0,
        hard_requirement_tolerance=10.0
    )

    hard_result_a = HardRequirementResult(
        passed=True, coverage_score=1.0, matched_required=["Python"], missing_required=[],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="100% coverage"
    )

    hard_result_b = HardRequirementResult(
        passed=False, coverage_score=0.6, matched_required=["Python"], missing_required=["Go"],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="60% coverage"
    )

    score_profile_a = engine.generate_score(
        resume_profile=resume_profile,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result_a,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    resume_profile_b = resume_profile.model_copy(update={"name": "Candidate B"})

    score_profile_b = engine.generate_score(
        resume_profile=resume_profile_b,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result_b,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    assert score_profile_a.overall_score > score_profile_b.overall_score


def test_project_score_isolation():
    """
    Assert that changing project score alone affects only project contribution.
    """
    engine = CandidateScoringEngine()

    resume_profile_1 = ResumeProfile(
        name="Test Candidate",
        skills=["Python"],
        experience=[],
        projects=[Project(name="Proj1", technologies=["Python"])],
        education=[],
        certifications=[],
        achievements=[]
    )

    resume_profile_2 = ResumeProfile(
        name="Test Candidate",
        skills=["Python"],
        experience=[],
        projects=[
            Project(name="Proj1", technologies=["Python"]),
            Project(name="Proj2", technologies=["Python"])
        ],
        education=[],
        certifications=[],
        achievements=[]
    )

    job_profile = JobProfile(
        title="Test Role",
        required_skills=["Python"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=0,
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Test JD"
    )

    strategy = EvaluationStrategy(
        evaluation_profile="mid_backend",
        strictness_level="medium",
        component_weights={
            "projects": 0.50,
            "skills": 0.50
        },
        minimum_skill_confidence=50.0,
        hard_requirement_tolerance=10.0
    )

    hard_result = HardRequirementResult(
        passed=True, coverage_score=1.0, matched_required=["Python"], missing_required=[],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="100% coverage"
    )

    score_profile_1 = engine.generate_score(
        resume_profile=resume_profile_1,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    score_profile_2 = engine.generate_score(
        resume_profile=resume_profile_2,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    assert score_profile_1.component_scores["projects"] != score_profile_2.component_scores["projects"]
    assert score_profile_1.component_scores["skills"] == score_profile_2.component_scores["skills"]


def test_hard_requirements_in_component_scores():
    """
    Assert that hard_requirements appears in component_scores.
    """
    engine = CandidateScoringEngine()

    resume_profile = ResumeProfile(
        name="Test Candidate",
        skills=["Python"],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[]
    )

    job_profile = JobProfile(
        title="Test Role",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=0,
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Test JD"
    )

    strategy = EvaluationStrategy(
        evaluation_profile="mid_backend",
        strictness_level="medium",
        component_weights={
            "skills": 0.50,
            "hard_requirements": 0.50
        },
        minimum_skill_confidence=50.0,
        hard_requirement_tolerance=10.0
    )

    hard_result = HardRequirementResult(
        passed=True, coverage_score=0.75, matched_required=["Python"], missing_required=["Go"],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="75% coverage"
    )

    score_profile = engine.generate_score(
        resume_profile=resume_profile,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    assert "hard_requirements" in score_profile.component_scores
    assert score_profile.component_scores["hard_requirements"] == 75.0


def test_overall_score_equals_weighted_sum():
    """
    Assert that overall score matches the weighted sum of components.
    """
    engine = CandidateScoringEngine()

    resume_profile = ResumeProfile(
        name="Test Candidate",
        skills=["Python"],
        experience=[Experience(role="Developer", duration="2 years")],
        projects=[],
        education=[],
        certifications=[],
        achievements=[]
    )

    job_profile = JobProfile(
        title="Test Role",
        required_skills=["Python"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=2,
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Test JD"
    )

    strategy = EvaluationStrategy(
        evaluation_profile="mid_backend",
        strictness_level="medium",
        component_weights={
            "skills": 0.20,
            "experience": 0.30,
            "hard_requirements": 0.50
        },
        minimum_skill_confidence=50.0,
        hard_requirement_tolerance=10.0
    )

    hard_result = HardRequirementResult(
        passed=True, coverage_score=0.80, matched_required=["Python"], missing_required=["Go"],
        matched_preferred=[], missing_preferred=[], critical_failures=[], decision_reason="80% coverage"
    )

    score_profile = engine.generate_score(
        resume_profile=resume_profile,
        job_profile=job_profile,
        evaluation_strategy=strategy,
        hard_requirement_result=hard_result,
        semantic_score=0.90,
        confidence_profiles={},
        achievement_profile=AchievementProfile(
            achievement_score=0.0, academic=[], technical=[], research=[], leadership=[], entrepreneurship=[],
            category_scores={}, explanation_traces=[]
        )
    )

    expected_overall = round(
        score_profile.component_scores["skills"] * strategy.component_weights["skills"] +
        score_profile.component_scores["experience"] * strategy.component_weights["experience"] +
        score_profile.component_scores["hard_requirements"] * strategy.component_weights["hard_requirements"],
        1
    )

    assert score_profile.overall_score == pytest.approx(expected_overall)
