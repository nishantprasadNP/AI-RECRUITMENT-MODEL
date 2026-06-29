"""
Unit tests for Phase 5.3A RequirementMatcher and RequirementMatchResult.
"""

import pytest
from pydantic import ValidationError

from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.hard_requirements.models import (
    CapabilityResolutionResult,
    RequirementMatchResult,
)
from app.hard_requirements.requirement_matcher import RequirementMatcher


@pytest.fixture
def empty_job_profile():
    """Fixture to create a basic JobProfile with minimum attributes."""
    return JobProfile(
        title="Software Engineer",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        seniority_level="mid",
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        job_summary="Job summary details"
    )


def test_requirement_match_result_validation():
    """Verify that RequirementMatchResult enforces strict validation rules."""
    # Successful instantiation
    result = RequirementMatchResult(
        matched_required=["Python"],
        missing_required=["Kafka"],
        matched_preferred=["Docker"],
        missing_preferred=["AWS"],
        coverage_score=0.5,
        critical_failures=["Kafka"]
    )
    assert result.coverage_score == 0.5

    # Strict type enforcement (e.g. passing a string "0.5" instead of float)
    with pytest.raises(ValidationError) as exc_info:
        RequirementMatchResult(
            matched_required=[],
            missing_required=[],
            matched_preferred=[],
            missing_preferred=[],
            coverage_score="0.5",
            critical_failures=[]
        )
    assert "Input should be a valid number" in str(exc_info.value)

    # Boundary check: coverage_score less than 0.0
    with pytest.raises(ValidationError) as exc_info:
        RequirementMatchResult(
            coverage_score=-0.1
        )
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

    # Boundary check: coverage_score greater than 1.0
    with pytest.raises(ValidationError) as exc_info:
        RequirementMatchResult(
            coverage_score=1.01
        )
    assert "Input should be less than or equal to 1" in str(exc_info.value)


def test_requirement_matcher_full_match(empty_job_profile):
    """Test full matching scenario where candidate meets all requirements."""
    matcher = RequirementMatcher()
    
    # Define required and preferred skills on job
    job = empty_job_profile.model_copy(update={
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker", "Git"]
    })

    # Candidate has all required and preferred skills
    capabilities = CapabilityResolutionResult(
        candidate_capabilities=["Python", "FastAPI", "Docker", "Git", "SQL"]
    )

    result = matcher.match_requirements(job, capabilities)

    assert result.matched_required == ["Python", "FastAPI"]
    assert result.missing_required == []
    assert result.matched_preferred == ["Docker", "Git"]
    assert result.missing_preferred == []
    assert result.coverage_score == 1.0
    assert result.critical_failures == []


def test_requirement_matcher_partial_match(empty_job_profile):
    """Test partial matching scenario where candidate has some but not all skills."""
    matcher = RequirementMatcher()

    job = empty_job_profile.model_copy(update={
        "required_skills": ["Python", "FastAPI", "Kubernetes"],
        "preferred_skills": ["Docker", "Terraform"]
    })

    # Candidate has Python (required) and Docker (preferred), misses FastAPI, Kubernetes, Terraform
    capabilities = CapabilityResolutionResult(
        candidate_capabilities=["Python", "Docker", "SQL"]
    )

    result = matcher.match_requirements(job, capabilities)

    assert result.matched_required == ["Python"]
    assert result.missing_required == ["FastAPI", "Kubernetes"]
    assert result.matched_preferred == ["Docker"]
    assert result.missing_preferred == ["Terraform"]
    assert result.coverage_score == pytest.approx(1 / 3)
    assert result.critical_failures == ["FastAPI", "Kubernetes"]


def test_requirement_matcher_no_required_skills(empty_job_profile):
    """Verify that a job description with no required skills returns coverage = 1.0."""
    matcher = RequirementMatcher()

    job = empty_job_profile.model_copy(update={
        "required_skills": [],
        "preferred_skills": ["Docker"]
    })

    capabilities = CapabilityResolutionResult(
        candidate_capabilities=["Docker"]
    )

    result = matcher.match_requirements(job, capabilities)

    assert result.matched_required == []
    assert result.missing_required == []
    assert result.matched_preferred == ["Docker"]
    assert result.missing_preferred == []
    assert result.coverage_score == 1.0
    assert result.critical_failures == []


def test_requirement_matcher_case_insensitive(empty_job_profile):
    """Test case-insensitive matching and preservation of original job skill names in outputs."""
    matcher = RequirementMatcher()

    job = empty_job_profile.model_copy(update={
        "required_skills": ["Kafka", "PyTorch", "AWS"],
        "preferred_skills": ["PostgreSQL"]
    })

    # Candidate capabilities with mixed/different casing
    capabilities = CapabilityResolutionResult(
        candidate_capabilities=["kafka", "pytorch", "Postgresql"]
    )

    result = matcher.match_requirements(job, capabilities)

    # Casing in result must match job profile required/preferred casing exactly
    assert result.matched_required == ["Kafka", "PyTorch"]
    assert result.missing_required == ["AWS"]
    assert result.matched_preferred == ["PostgreSQL"]
    assert result.missing_preferred == []
    assert result.coverage_score == pytest.approx(2 / 3)
    assert result.critical_failures == ["AWS"]


def test_requirement_matcher_preferred_skill_matching(empty_job_profile):
    """Verify detailed matching behavior of preferred skills."""
    matcher = RequirementMatcher()

    job = empty_job_profile.model_copy(update={
        "required_skills": ["Python"],
        "preferred_skills": ["Docker", "AWS", "Kubernetes"]
    })

    # Candidate has required (Python) and preferred (AWS, Docker)
    capabilities = CapabilityResolutionResult(
        candidate_capabilities=["python", "aws", "docker"]
    )

    result = matcher.match_requirements(job, capabilities)

    assert result.matched_required == ["Python"]
    assert result.missing_required == []
    assert result.matched_preferred == ["Docker", "AWS"]
    assert result.missing_preferred == ["Kubernetes"]
    assert result.coverage_score == 1.0
    assert result.critical_failures == []
