"""
Unit tests for Phase 5.3B HardRequirementEngine.
"""

import os
import pytest
from pydantic import ValidationError

from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.role_classification.models import RoleProfile
from app.hard_requirements import (
    CapabilityResolver,
    CapabilityResolutionResult,
    HardRequirementResult,
    HardRequirementEngine,
)
from app.hard_requirements.exceptions import RequirementMatchingError
from app.schemas.resume_schema import ResumeProfile
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine


TAXONOMY_PATH = os.path.join("data", "skill_graph", "skills_taxonomy.json")


@pytest.fixture
def basic_job_profile():
    """Fixture returning a JobProfile with minimum attributes."""
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


@pytest.fixture
def basic_role_profile():
    """Fixture returning a classified RoleProfile."""
    return RoleProfile(
        role_family="software_engineering",
        specialization="backend_engineer",
        seniority="mid",
        evaluation_profile="mid_backend"
    )


@pytest.fixture
def real_capability_resolver():
    """Fixture returning a CapabilityResolver linked to the real taxonomy."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    service = SkillGraphService(repo)
    inference = SkillInferenceEngine(service)
    return CapabilityResolver(inference)


def test_hard_requirement_engine_input_validation(basic_job_profile, basic_role_profile):
    """Verify that all three inputs are validated and raise RequirementMatchingError if None."""
    engine = HardRequirementEngine()
    caps = CapabilityResolutionResult(candidate_capabilities=[])

    # job_profile is None
    with pytest.raises(RequirementMatchingError) as exc_info:
        engine.evaluate_compliance(None, basic_role_profile, caps)
    assert "job_profile cannot be None" in str(exc_info.value)

    # role_profile is None
    with pytest.raises(RequirementMatchingError) as exc_info:
        engine.evaluate_compliance(basic_job_profile, None, caps)
    assert "role_profile cannot be None" in str(exc_info.value)

    # capabilities is None
    with pytest.raises(RequirementMatchingError) as exc_info:
        engine.evaluate_compliance(basic_job_profile, basic_role_profile, None)
    assert "capabilities cannot be None" in str(exc_info.value)


def test_hard_requirement_engine_successful_pass(basic_job_profile, basic_role_profile):
    """Verify compliant result when candidate meets all required skills."""
    engine = HardRequirementEngine()
    job = basic_job_profile.model_copy(update={
        "required_skills": ["Python", "Docker"]
    })
    caps = CapabilityResolutionResult(candidate_capabilities=["Python", "Docker"])

    result = engine.evaluate_compliance(job, basic_role_profile, caps)

    assert result.passed is True
    assert result.coverage_score == 1.0
    assert result.matched_required == ["Python", "Docker"]
    assert result.missing_required == []
    assert result.decision_reason == "All required skills satisfied."


def test_hard_requirement_engine_missing_required_skill(basic_job_profile, basic_role_profile):
    """Verify failed result with details when a required skill is missing."""
    engine = HardRequirementEngine()
    job = basic_job_profile.model_copy(update={
        "required_skills": ["Python", "Kafka"]
    })
    caps = CapabilityResolutionResult(candidate_capabilities=["Python"])

    result = engine.evaluate_compliance(job, basic_role_profile, caps)

    assert result.passed is False
    assert result.coverage_score == 0.5
    assert result.matched_required == ["Python"]
    assert result.missing_required == ["Kafka"]
    assert result.decision_reason == "Missing required skills: Kafka"


def test_hard_requirement_engine_coverage_score_calculation(basic_job_profile, basic_role_profile):
    """Verify coverage score calculation for partial matches."""
    engine = HardRequirementEngine()
    job = basic_job_profile.model_copy(update={
        "required_skills": ["Python", "Kafka", "Docker", "AWS"]
    })
    # candidate has 2 out of 4 skills -> coverage = 0.5
    caps = CapabilityResolutionResult(candidate_capabilities=["Python", "Docker"])

    result = engine.evaluate_compliance(job, basic_role_profile, caps)

    assert result.passed is False
    assert result.coverage_score == 0.5
    assert result.matched_required == ["Python", "Docker"]
    assert result.missing_required == ["Kafka", "AWS"]
    assert result.decision_reason == "Missing required skills: Kafka, AWS"


def test_capability_resolution_linkage(basic_job_profile, basic_role_profile, real_capability_resolver):
    """
    Linkage Test: Verify that when a candidate has ['FastAPI', 'Docker']
    and the job requires ['Python', 'Docker'], the candidate passes because
    Python is inferred from FastAPI via the taxonomy graph.
    """
    engine = HardRequirementEngine()
    
    # 1. Candidate resume has FastAPI and Docker
    resume = ResumeProfile(skills=["FastAPI", "Docker"])
    
    # 2. Resolve capabilities through the resolver using the taxonomy graph
    resolved_caps = real_capability_resolver.resolve_capabilities(resume)
    
    # Verify Python was indeed inferred
    assert "Python" in resolved_caps.candidate_capabilities

    # 3. Job requires Python and Docker
    job = basic_job_profile.model_copy(update={
        "required_skills": ["Python", "Docker"]
    })

    # 4. Evaluate compliance
    result = engine.evaluate_compliance(job, basic_role_profile, resolved_caps)

    # 5. Check outcome (should PASS)
    assert result.passed is True
    assert result.coverage_score == 1.0
    assert "Python" in result.matched_required
    assert "Docker" in result.matched_required
    assert result.decision_reason == "All required skills satisfied."
