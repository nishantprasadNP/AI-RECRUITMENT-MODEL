"""
Integration tests for Phase 10 (Scoring) and Phase 11 (Ranking) in RecruitmentOrchestrator.
"""

import os
import tempfile
import json
import pytest
from unittest.mock import MagicMock

from app.orchestrator import RecruitmentOrchestrator, OrchestratorResult
from app.schemas.resume_schema import ResumeProfile, Experience
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_ranking.models import RankedCandidateList


def test_orchestrator_scoring_and_ranking_integration():
    # 1. Setup mock profiles for Candidate A (Stronger)
    mock_resume_a = ResumeProfile(
        name="Alice Smith",
        skills=["Python", "FastAPI"],
        experience=[Experience(role="Lead developer", duration="5 years")],
        projects=[],
        education=[],
        certifications=[],
        achievements=["Winner of outstanding contributor award"],
    )

    # Candidate B (Weaker)
    mock_resume_b = ResumeProfile(
        name="Bob Jones",
        skills=["Python"],
        experience=[Experience(role="Junior Developer", duration="1 year")],
        projects=[],
        education=[],
        certifications=[],
        achievements=[],
    )

    mock_job_profile = JobProfile(
        title="Lead Python Developer",
        required_skills=["Python", "FastAPI"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=5,
        education=None,
        leadership=True,
        seniority_level="senior",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="Lead Python Developer role with leadership requirements",
    )

    # 2. Mock external components
    mock_parser = MagicMock()
    mock_parser.extract_text.return_value = "Mock raw resume text"

    # We will use side effects to return different profiles on consecutive calls
    mock_resume_extractor = MagicMock()
    mock_resume_extractor.extract.side_effect = [mock_resume_a, mock_resume_b]

    mock_job_extractor = MagicMock()
    mock_job_extractor.extract.return_value = mock_job_profile

    mock_embedder = MagicMock()
    mock_embedder.generate_embedding.return_value = MagicMock()

    mock_matcher = MagicMock()
    # Mock semantic similarity scores for A and B
    mock_matcher.compute_similarity.side_effect = [0.90, 0.60]

    with tempfile.TemporaryDirectory() as tmp_dir:
        orchestrator = RecruitmentOrchestrator(
            resume_parser=mock_parser,
            resume_extractor=mock_resume_extractor,
            job_extractor=mock_job_extractor,
            embedding_generator=mock_embedder,
            semantic_matcher=mock_matcher,
            match_report_dir=tmp_dir,
        )

        # Run pipeline for Candidate A
        result_a = orchestrator.run(
            resume_pdf_path="alice_resume.pdf",
            jd_text="Mock raw JD text",
            job_name="lead_dev_alice",
        )

        # Run pipeline for Candidate B
        result_b = orchestrator.run(
            resume_pdf_path="bob_resume.pdf",
            jd_text="Mock raw JD text",
            job_name="lead_dev_bob",
        )

        # 3. Verify Candidate Score Profiles
        assert isinstance(result_a.candidate_score, CandidateScoreProfile)
        assert result_a.candidate_score.candidate_name == "Alice Smith"
        # Since Alice has FastAPI and Python, 5 years experience (matches 5 required), and lead experience, she should score high.
        assert result_a.candidate_score.overall_score > 60.0

        assert isinstance(result_b.candidate_score, CandidateScoreProfile)
        assert result_b.candidate_score.candidate_name == "Bob Jones"
        # Bob has fewer skills and years of experience, so score should be lower
        assert result_b.candidate_score.overall_score < result_a.candidate_score.overall_score

        # Verify saved match report has the candidate score
        assert os.path.exists(result_a.match_report_path)
        with open(result_a.match_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert "candidate_score" in report_data
        assert report_data["candidate_score"]["candidate_name"] == "Alice Smith"
        assert "overall_score" in report_data["candidate_score"]

        # 4. Verify Ranking Engine via orchestrator
        ranked_list = orchestrator.rank_candidates([result_b, result_a])
        assert isinstance(ranked_list, RankedCandidateList)
        assert len(ranked_list.root) == 2

        # Candidate A (Alice) should be ranked 1st
        assert ranked_list.root[0].rank == 1
        assert ranked_list.root[0].candidate_name == "Alice Smith"
        
        # Candidate B (Bob) should be ranked 2nd
        assert ranked_list.root[1].rank == 2
        assert ranked_list.root[1].candidate_name == "Bob Jones"
