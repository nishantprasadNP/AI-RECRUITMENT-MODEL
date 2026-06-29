import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.API.main import app
from app.orchestrator import OrchestratorResult
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.role_classification.models import RoleProfile
from app.hard_requirements.models import HardRequirementResult
from app.skill_gap.models import SkillGapResult
from app.candidate_scoring.models import CandidateScoreProfile

client = TestClient(app)


def test_analyze_endpoint_invalid_resume_type():
    """Verify that an invalid resume file type raises an HTTP 400 Bad Request."""
    resume_data = b"Dummy PDF content"
    jd_data = b"Dummy JD content"

    response = client.post(
        "/analyze",
        files={
            "resume": ("resume.txt", resume_data, "text/plain"),
            "jd": ("jd.txt", jd_data, "text/plain")
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Resume must be a PDF file" in response.json()["detail"]


def test_analyze_endpoint_invalid_jd_type():
    """Verify that an invalid job description file type raises an HTTP 400 Bad Request."""
    resume_data = b"Dummy PDF content"
    jd_data = b"Dummy JD content"

    response = client.post(
        "/analyze",
        files={
            "resume": ("resume.pdf", resume_data, "application/pdf"),
            "jd": ("jd.png", jd_data, "image/png")
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Job Description must be a text (.txt) or PDF" in response.json()["detail"]


@patch("app.API.main.RecruitmentOrchestrator")
def test_analyze_endpoint_success(mock_orchestrator_class):
    """Verify successful fit analysis returns structured backend metrics and deletes temp files."""
    # 1. Setup mock orchestrator instance and run result
    mock_orchestrator = MagicMock()
    mock_orchestrator_class.return_value = mock_orchestrator

    mock_result = OrchestratorResult(
        candidate_name="JOHN DOE",
        job_name="Software Engineer",
        resume_profile=ResumeProfile(name="JOHN DOE", skills=["Python"], experience=[], projects=[], education=[], achievements=[]),
        job_profile=JobProfile(
            title="Software Engineer",
            required_skills=["Python"],
            preferred_skills=[],
            critical_skills=[],
            experience_required=2,
            seniority_level="junior",
            hidden_hiring_signals=HiddenHiringSignals(),
            role_complexity_score=5,
            job_summary=""
        ),
        role_profile=RoleProfile(role_family="software_engineering", specialization="backend_engineer", seniority="junior", evaluation_profile="junior_backend"),
        hard_requirement_result=HardRequirementResult(passed=True, coverage_score=1.0, matched_required=["Python"], decision_reason="All required skills satisfied"),
        skill_gap_result=SkillGapResult(missing_required_skills=[], missing_preferred_skills=[], weak_skills=[], strong_skills=["Python"], improvement_areas=[], overall_gap_score=0.0, decision_summary="Good"),
        candidate_score=CandidateScoreProfile(candidate_name="JOHN DOE", overall_score=85.0, component_scores={"skills": 85.0}, weight_breakdown={"skills": 1.0}, explanation=[]),
        semantic_score=0.85,
        resume_profile_path="data/extracted_profiles/john_doe.json",
        job_profile_path="data/extracted_jobs/role.json",
        match_report_path="data/match_reports/report.json"
    )
    mock_orchestrator.run.return_value = mock_result
    mock_orchestrator._skill_confidence_engine.analyze.return_value = {}

    # 2. Fire analyze request
    resume_data = b"Dummy PDF content"
    jd_data = b"Dummy JD content"

    response = client.post(
        "/analyze",
        files={
            "resume": ("resume.pdf", resume_data, "application/pdf"),
            "jd": ("jd.txt", jd_data, "text/plain")
        }
    )

    # 3. Check response
    assert response.status_code == status.HTTP_200_OK
    json_resp = response.json()
    assert json_resp["candidate_name"] == "JOHN DOE"
    assert json_resp["semantic_score"] == 0.85
    assert json_resp["role_profile"]["evaluation_profile"] == "junior_backend"
    assert json_resp["hard_requirement_result"]["passed"] is True
    assert json_resp["skill_gap"]["overall_gap_score"] == 0.0
    assert json_resp["candidate_score"]["overall_score"] == 85.0

    # 4. Verify temporary files are deleted
    # The temp directory should be empty (or at least the generated request files should be removed)
    assert len(os.listdir("temp")) == 0
