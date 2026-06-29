"""
Unit tests for Phase 12 Skill Gap Analysis Engine models, exceptions, and engine.
"""

import pytest
from pydantic import ValidationError
from app.core.exceptions import ARISError
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.hard_requirements.models import HardRequirementResult
from app.experience_analysis.models import SkillConfidenceProfile
from app.skill_gap.models import SkillGapResult
from app.skill_gap.exceptions import (
    SkillGapError,
    GapAnalysisError,
    RecommendationGenerationError,
)
from app.skill_gap.skill_gap_engine import SkillGapEngine


def test_skill_gap_result_success():
    """
    Test successful validation of SkillGapResult model with complete valid data.
    """
    valid_data = {
        "missing_required_skills": ["Kafka"],
        "missing_preferred_skills": ["Docker"],
        "weak_skills": ["AWS"],
        "strong_skills": ["Python", "FastAPI"],
        "improvement_areas": [
            "Gain experience with Kafka",
            "Build cloud deployment projects"
        ],
        "overall_gap_score": 0.35,
        "decision_summary": "Candidate satisfies most requirements but lacks Kafka experience."
    }

    result = SkillGapResult(**valid_data)

    assert result.missing_required_skills == ["Kafka"]
    assert result.missing_preferred_skills == ["Docker"]
    assert result.weak_skills == ["AWS"]
    assert result.strong_skills == ["Python", "FastAPI"]
    assert result.improvement_areas == [
        "Gain experience with Kafka",
        "Build cloud deployment projects"
    ]
    assert result.overall_gap_score == 0.35
    assert result.decision_summary == "Candidate satisfies most requirements but lacks Kafka experience."


def test_skill_gap_result_defaults():
    """
    Test that default lists are instantiated when not provided.
    """
    result = SkillGapResult(
        overall_gap_score=0.0,
        decision_summary="Perfect match"
    )

    assert result.missing_required_skills == []
    assert result.missing_preferred_skills == []
    assert result.weak_skills == []
    assert result.strong_skills == []
    assert result.improvement_areas == []
    assert result.overall_gap_score == 0.0
    assert result.decision_summary == "Perfect match"


def test_skill_gap_result_strict_validation():
    """
    Test that strict mode prevents type coercion (e.g. string to float).
    """
    # In strict mode, providing a string "0.35" for a float field overall_gap_score should fail.
    with pytest.raises(ValidationError) as exc_info:
        SkillGapResult(
            overall_gap_score="0.35",
            decision_summary="Coercion test"
        )
    assert "Input should be a valid number" in str(exc_info.value)


def test_skill_gap_result_missing_required_fields():
    """
    Test that missing required fields raises a ValidationError.
    """
    with pytest.raises(ValidationError) as exc_info:
        SkillGapResult(
            overall_gap_score=0.5
            # decision_summary is missing
        )
    assert "Field required" in str(exc_info.value)


def test_skill_gap_result_score_boundaries():
    """
    Test that overall_gap_score is validated to be between 0.0 and 1.0.
    """
    # Score less than 0.0
    with pytest.raises(ValidationError) as exc_info:
        SkillGapResult(
            overall_gap_score=-0.1,
            decision_summary="Negative score test"
        )
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # Score greater than 1.0
    with pytest.raises(ValidationError) as exc_info:
        SkillGapResult(
            overall_gap_score=1.1,
            decision_summary="Score too large test"
        )
    assert "Input should be less than or equal to 1" in str(exc_info.value)


def test_exception_hierarchy():
    """
    Test the custom exception hierarchy for the skill gap module.
    """
    # SkillGapError inherits from ARISError
    assert issubclass(SkillGapError, ARISError)

    # GapAnalysisError and RecommendationGenerationError inherit from SkillGapError
    assert issubclass(GapAnalysisError, SkillGapError)
    assert issubclass(RecommendationGenerationError, SkillGapError)


# --- SkillGapEngine Tests ---

@pytest.fixture
def empty_job_profile():
    """Fixture returning a basic JobProfile with minimum required attributes."""
    return JobProfile(
        title="Software Engineer",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(
            autonomy_required=False,
            client_facing=False,
            research_oriented=False,
            innovation_focused=False,
            startup_environment=False,
            high_ownership=False
        ),
        role_complexity_score=5,
        job_summary="A job summary"
    )


def test_skill_gap_engine_validation(empty_job_profile):
    """
    Test that the engine validates None inputs and raises GapAnalysisError.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult()

    # job_profile is None
    with pytest.raises(GapAnalysisError) as exc_info:
        engine.analyze_gaps(None, hard_req, {})
    assert "job_profile cannot be None" in str(exc_info.value)

    # hard_requirement_result is None
    with pytest.raises(GapAnalysisError) as exc_info:
        engine.analyze_gaps(empty_job_profile, None, {})
    assert "hard_requirement_result cannot be None" in str(exc_info.value)

    # confidence_profiles is None
    with pytest.raises(GapAnalysisError) as exc_info:
        engine.analyze_gaps(empty_job_profile, hard_req, None)
    assert "confidence_profiles cannot be None" in str(exc_info.value)


def test_skill_gap_engine_no_gaps(empty_job_profile):
    """
    Test scenario: Candidate satisfies all requirements and demonstrates strong skill evidence.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult(
        passed=True,
        coverage_score=1.0,
        matched_required=["Python"],
        missing_required=[],
        matched_preferred=[],
        missing_preferred=[]
    )
    confidence = {
        "Python": SkillConfidenceProfile(
            skill="Python",
            professional_signal=0.8,
            depth_signal=0.9,
            complexity_signal=0.8,
            confidence_score=85.0,
            confidence_level="High"
        )
    }

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)

    assert result.missing_required_skills == []
    assert result.missing_preferred_skills == []
    assert result.weak_skills == []
    assert result.strong_skills == ["Python"]
    assert result.overall_gap_score == 0.0
    assert result.decision_summary == (
        "Candidate satisfies all identified requirements and demonstrates strong skill evidence."
    )
    assert result.improvement_areas == []


def test_skill_gap_engine_required_gaps_only(empty_job_profile):
    """
    Test scenario: Candidate has missing required skills, but no weak skills.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult(
        passed=False,
        coverage_score=0.33,
        matched_required=[],
        missing_required=["Kafka", "Docker"],
        matched_preferred=[],
        missing_preferred=[]
    )
    confidence = {}

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)

    assert result.missing_required_skills == ["Kafka", "Docker"]
    assert result.weak_skills == []
    assert result.overall_gap_score == 1.0  # (2 * 0.5)
    assert result.decision_summary == "Candidate is missing required skills: Kafka, Docker."
    assert result.improvement_areas == [
        "Gain experience with Kafka",
        "Build deployment projects using Docker"
    ]


def test_skill_gap_engine_weak_skills_only(empty_job_profile):
    """
    Test scenario: Candidate meets requirements but has weak evidence in certain skills.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult(
        passed=True,
        coverage_score=1.0,
        matched_required=["AWS"],
        missing_required=[],
        matched_preferred=[],
        missing_preferred=[]
    )
    confidence = {
        "AWS": SkillConfidenceProfile(
            skill="AWS",
            professional_signal=0.2,
            depth_signal=0.3,
            complexity_signal=0.2,
            confidence_score=40.0,
            confidence_level="Low"
        )
    }

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)

    assert result.missing_required_skills == []
    assert result.weak_skills == ["AWS"]
    assert result.overall_gap_score == 0.1  # (1 * 0.1)
    assert result.decision_summary == "Candidate meets requirements but has weak evidence in AWS."
    assert result.improvement_areas == ["Gain cloud deployment experience"]


def test_skill_gap_engine_mixed_gaps(empty_job_profile):
    """
    Test scenario: Candidate lacks required skills AND has weak evidence in others.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult(
        passed=False,
        coverage_score=0.5,
        matched_required=[],
        missing_required=["Kafka"],
        matched_preferred=[],
        missing_preferred=["Docker"]
    )
    confidence = {
        "AWS": SkillConfidenceProfile(
            skill="AWS",
            professional_signal=0.2,
            depth_signal=0.3,
            complexity_signal=0.2,
            confidence_score=45.0,
            confidence_level="Low"
        ),
        "Python": SkillConfidenceProfile(
            skill="Python",
            professional_signal=0.8,
            depth_signal=0.9,
            complexity_signal=0.8,
            confidence_score=85.0,
            confidence_level="High"
        )
    }

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)

    assert result.missing_required_skills == ["Kafka"]
    assert result.missing_preferred_skills == ["Docker"]
    assert result.weak_skills == ["AWS"]
    assert result.strong_skills == ["Python"]
    assert result.overall_gap_score == 0.8  # (1 * 0.5) + (1 * 0.2) + (1 * 0.1) = 0.8
    assert result.decision_summary == (
        "Candidate satisfies most requirements but lacks Kafka and has weak AWS evidence."
    )
    assert result.improvement_areas == [
        "Gain experience with Kafka",
        "Build deployment projects using Docker",
        "Gain cloud deployment experience"
    ]


def test_skill_gap_engine_score_capping(empty_job_profile):
    """
    Test that the overall gap score is capped at 1.0.
    """
    engine = SkillGapEngine()
    hard_req = HardRequirementResult(
        missing_required=["Kafka", "Docker", "AWS"],  # 3 * 0.5 = 1.5
        missing_preferred=["Kubernetes"],             # 1 * 0.2 = 0.2
    )
    confidence = {
        "Terraform": SkillConfidenceProfile(
            skill="Terraform",
            professional_signal=0.1,
            depth_signal=0.1,
            complexity_signal=0.1,
            confidence_score=30.0,
            confidence_level="Low"
        )
    }                                                 # 1 * 0.1 = 0.1

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)
    # Total raw score = 1.5 + 0.2 + 0.1 = 1.8, should be capped at 1.0
    assert result.overall_gap_score == 1.0


def test_skill_gap_engine_generic_skill_and_deduplication(empty_job_profile):
    """
    Test generic skill formatting, case-insensitivity in rules, and deduplication of recommendations.
    """
    engine = SkillGapEngine()
    # "kafka" in lowercase to test case-insensitive matching
    hard_req = HardRequirementResult(
        missing_required=["kafka", "python", "docker"],
        missing_preferred=["Docker"]  # Duplicate check
    )
    confidence = {
        "Python": SkillConfidenceProfile(
            skill="Python",
            professional_signal=0.2,
            depth_signal=0.2,
            complexity_signal=0.2,
            confidence_score=40.0,
            confidence_level="Low"
        )  # Duplicate check for "python" recommendation
    }

    result = engine.analyze_gaps(empty_job_profile, hard_req, confidence)

    # Recommendations:
    # 1. kafka -> "Gain experience with Kafka" (matched case-insensitively)
    # 2. python -> "Improve proficiency in python"
    # 3. docker -> "Build deployment projects using Docker"
    # 4. Docker (missing_preferred) -> "Build deployment projects using Docker" (duplicate, skipped)
    # 5. Python (weak) -> "Improve proficiency in Python" (duplicate/case check? Actually, "Improve proficiency in Python" vs "Improve proficiency in python". Let's verify. They are different strings, so both might appear if case is different. Let's see. Yes, they would be distinct due to casing. Let's make sure our deduplication/casing behaves correctly.)

    assert "Gain experience with Kafka" in result.improvement_areas
    assert "Build deployment projects using Docker" in result.improvement_areas
    assert "Improve proficiency in python" in result.improvement_areas
    assert "Improve proficiency in Python" in result.improvement_areas

    # Verify no duplicates in the final list
    assert len(result.improvement_areas) == len(set(result.improvement_areas))
