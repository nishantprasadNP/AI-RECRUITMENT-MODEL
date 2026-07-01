import pytest
from unittest.mock import MagicMock
from app.API.main import generate_recruiter_recommendation_data
from app.orchestrator import OrchestratorResult
from app.schemas.resume_schema import ResumeProfile, Experience
from app.hard_requirements.models import HardRequirementResult
from app.skill_gap.models import SkillGapResult
from app.candidate_scoring.models import CandidateScoreProfile
from app.role_classification.models import RoleProfile
from app.experience_analysis.models import SkillConfidenceProfile


def test_generate_recruiter_recommendation_data_passed_hard():
    # Setup mock OrchestratorResult
    resume = ResumeProfile(
        name="Alice Smith",
        skills=["Python", "FastAPI"],
        experience=[
            Experience(role="Software Engineer Intern", company="Google", duration="6 months", description="Python developer")
        ],
        projects=[],
        education=[],
        achievements=[]
    )
    
    hr_res = HardRequirementResult(
        passed=True,
        coverage_score=1.0,
        matched_required=["Python"],
        decision_reason="Passed all hard requirements"
    )
    
    sg_res = SkillGapResult(
        missing_required_skills=[],
        missing_preferred_skills=["Redis", "Kubernetes"],
        weak_skills=[],
        strong_skills=["Python"],
        improvement_areas=[],
        overall_gap_score=0.2,
        decision_summary="Missing some preferred skills"
    )
    
    score_profile = CandidateScoreProfile(
        candidate_name="Alice Smith",
        overall_score=87.5,
        component_scores={"projects": 85.0},
        weight_breakdown={"projects": 1.0},
        explanation=[]
    )
    
    role_profile = RoleProfile(
        role_family="software_engineering",
        specialization="backend_engineer",
        seniority="mid_level",
        evaluation_profile="mid_backend"
    )
    
    result = OrchestratorResult(
        candidate_name="Alice Smith",
        resume_profile=resume,
        hard_requirement_result=hr_res,
        skill_gap_result=sg_res,
        candidate_score=score_profile,
        role_profile=role_profile,
        semantic_score=0.85
    )
    
    confidence_profiles = {
        "Python": SkillConfidenceProfile(
            skill="Python",
            professional_signal=1.0,
            depth_signal=1.0,
            complexity_signal=1.0,
            confidence_score=95.0,
            confidence_level="Expert",
            skill_tier="Expert"
        )
    }
    
    rec = generate_recruiter_recommendation_data(result, confidence_profiles)
    
    assert rec["overall_score"] == 87.5
    assert "✓ Passed all hard requirements" in rec["why_score"]
    assert "✓ High semantic alignment with JD" in rec["why_score"]
    assert "✓ Strong Backend Engineer project experience" in rec["why_score"]
    assert "✓ Internship experience" in rec["why_score"]
    assert "✓ Strong Python confidence" in rec["why_score"]
    assert rec["recommendation"] == "Proceed to Technical Interview"
    assert "Redis" in rec["missing_skills"]
    assert "Kubernetes" in rec["missing_skills"]
    assert rec["confidence_summary"]["Python"] == 95.0


def test_generate_recruiter_recommendation_data_failed_hard():
    # Setup mock OrchestratorResult where hard requirements failed
    hr_res = HardRequirementResult(
        passed=False,
        coverage_score=0.0,
        matched_required=[],
        missing_required=["Python"],
        decision_reason="Missing Python skill"
    )
    
    score_profile = CandidateScoreProfile(
        candidate_name="Bob Jones",
        overall_score=92.0, # High score but failed hard reqs
        component_scores={},
        weight_breakdown={},
        explanation=[]
    )
    
    result = OrchestratorResult(
        candidate_name="Bob Jones",
        hard_requirement_result=hr_res,
        candidate_score=score_profile,
        semantic_score=0.9
    )
    
    rec = generate_recruiter_recommendation_data(result, {})
    
    assert rec["recommendation"] == "Reject"
    assert "✗ Failed hard requirements: Missing Python skill" in rec["why_score"]
