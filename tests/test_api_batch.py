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


@patch("app.API.main.RecruitmentOrchestrator")
def test_analyze_multiple_endpoint_success(mock_orchestrator_class):
    # 1. Setup mock orchestrator instance and run result
    mock_orchestrator = MagicMock()
    mock_orchestrator_class.return_value = mock_orchestrator

    mock_result_1 = OrchestratorResult(
        candidate_name="ALICE SMITH",
        job_name="Software Engineer",
        resume_profile=ResumeProfile(name="ALICE SMITH", skills=["Python"], experience=[], projects=[], education=[], achievements=[]),
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
        candidate_score=CandidateScoreProfile(candidate_name="ALICE SMITH", overall_score=85.0, component_scores={"skills": 85.0}, weight_breakdown={"skills": 1.0}, explanation=[]),
        semantic_score=0.85,
        resume_profile_path="data/extracted_profiles/alice_smith.json",
        job_profile_path="data/extracted_jobs/role.json",
        match_report_path="data/match_reports/report1.json"
    )

    mock_result_2 = OrchestratorResult(
        candidate_name="BOB JONES",
        job_name="Software Engineer",
        resume_profile=ResumeProfile(name="BOB JONES", skills=["Python"], experience=[], projects=[], education=[], achievements=[]),
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
        hard_requirement_result=HardRequirementResult(passed=False, coverage_score=0.0, matched_required=[], missing_required=["Python"], decision_reason="Missing Python skill"),
        skill_gap_result=SkillGapResult(missing_required_skills=["Python"], missing_preferred_skills=[], weak_skills=[], strong_skills=[], improvement_areas=[], overall_gap_score=1.0, decision_summary="Bad"),
        candidate_score=CandidateScoreProfile(candidate_name="BOB JONES", overall_score=40.0, component_scores={"skills": 40.0}, weight_breakdown={"skills": 1.0}, explanation=[]),
        semantic_score=0.5,
        resume_profile_path="data/extracted_profiles/bob_jones.json",
        job_profile_path="data/extracted_jobs/role.json",
        match_report_path="data/match_reports/report2.json"
    )

    # Mock rank method of CandidateRankingEngine
    from app.candidate_ranking.models import RankedCandidate, RankedCandidateList
    mock_ranked_list = RankedCandidateList([
        RankedCandidate(rank=1, candidate_name="ALICE SMITH", score=85.0, strengths=["Strong verified skill confidence"], concerns=[]),
        RankedCandidate(rank=2, candidate_name="BOB JONES", score=40.0, strengths=[], concerns=["Missing Python skill"])
    ])
    mock_orchestrator._candidate_ranking_engine.rank.return_value = mock_ranked_list
    mock_orchestrator._skill_confidence_engine.analyze.return_value = {}

    # Define return value for orchestrator.run sequence
    mock_orchestrator.run.side_effect = [mock_result_1, mock_result_2]

    # 2. Fire batch analyze request
    jd_data = b"Dummy JD content looking for Python developer"
    resume_1_data = b"Alice resume PDF"
    resume_2_data = b"Bob resume PDF"

    response = client.post(
        "/analyze/multiple",
        files=[
            ("resumes", ("resume1.pdf", resume_1_data, "application/pdf")),
            ("resumes", ("resume2.pdf", resume_2_data, "application/pdf")),
            ("jd", ("jd.txt", jd_data, "text/plain"))
        ]
    )

    # 3. Check response
    assert response.status_code == status.HTTP_200_OK
    json_resp = response.json()
    
    assert "job" in json_resp
    assert "ranked_candidates" in json_resp
    assert "recruiter_summary" in json_resp

    assert len(json_resp["ranked_candidates"]) == 2
    assert json_resp["ranked_candidates"][0]["candidate_name"] == "ALICE SMITH"
    assert json_resp["ranked_candidates"][0]["rank"] == 1
    assert json_resp["ranked_candidates"][0]["recommendation"] == "Proceed to Technical Interview"
    assert json_resp["ranked_candidates"][0]["hard_requirement_status"] == "Passed"

    assert json_resp["ranked_candidates"][1]["candidate_name"] == "BOB JONES"
    assert json_resp["ranked_candidates"][1]["rank"] == 2
    assert json_resp["ranked_candidates"][1]["recommendation"] == "Reject"
    assert json_resp["ranked_candidates"][1]["hard_requirement_status"] == "Failed"

    assert json_resp["recruiter_summary"]["total_evaluated"] == 2
    assert json_resp["recruiter_summary"]["passed_hard_requirements"] == 1
    assert json_resp["recruiter_summary"]["failed_hard_requirements"] == 1
    assert json_resp["recruiter_summary"]["recommendations_breakdown"]["Reject"] == 1
    assert json_resp["recruiter_summary"]["recommendations_breakdown"]["Proceed to Technical Interview"] == 1
