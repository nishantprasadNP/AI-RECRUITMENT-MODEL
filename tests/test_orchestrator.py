import os
import tempfile
import pytest
from unittest.mock import MagicMock

from app.orchestrator import RecruitmentOrchestrator, OrchestratorResult
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import JobProfile, HiddenHiringSignals
from app.role_classification.models import RoleProfile


def test_orchestrator_full_pipeline_run():
    # 1. Setup mock profiles
    mock_resume_profile = ResumeProfile(
        name="John Doe",
        skills=["Python", "React"],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[],
    )

    mock_job_profile = JobProfile(
        title="Senior Backend Developer",
        required_skills=["Python", "FastAPI", "SQL"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=5,
        education=None,
        leadership=False,
        seniority_level="senior",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="Backend Developer role",
    )

    # 2. Mock individual stages
    mock_parser = MagicMock()
    mock_parser.extract_text.return_value = "Mock raw resume text"

    mock_resume_extractor = MagicMock()
    mock_resume_extractor.extract.return_value = mock_resume_profile

    mock_job_extractor = MagicMock()
    mock_job_extractor.extract.return_value = mock_job_profile

    mock_embedder = MagicMock()
    mock_embedder.generate_embedding.return_value = MagicMock()

    mock_matcher = MagicMock()
    mock_matcher.compute_similarity.return_value = 0.85

    # Use a temporary directory for match reports to keep the workspace clean
    with tempfile.TemporaryDirectory() as tmp_dir:
        orchestrator = RecruitmentOrchestrator(
            resume_parser=mock_parser,
            resume_extractor=mock_resume_extractor,
            job_extractor=mock_job_extractor,
            embedding_generator=mock_embedder,
            semantic_matcher=mock_matcher,
            match_report_dir=tmp_dir,
        )

        result = orchestrator.run(
            resume_pdf_path="dummy_path.pdf",
            jd_text="Mock raw JD text",
            job_name="senior_engineer",
        )

        # 3. Assertions
        assert isinstance(result, OrchestratorResult)
        assert result.candidate_name == "John Doe"
        assert result.job_name == "senior_engineer"
        assert result.resume_profile == mock_resume_profile
        assert result.job_profile == mock_job_profile
        assert result.semantic_score == 0.85

        # Verify role classification occurred and was attached
        assert isinstance(result.role_profile, RoleProfile)
        assert result.role_profile.role_family == "software_engineering"
        assert result.role_profile.specialization == "backend_engineer"
        assert result.role_profile.seniority == "senior"
        assert result.role_profile.evaluation_profile == "senior_backend"

        # Verify evaluation strategy occurred and was attached
        from app.evaluation_strategy.models import EvaluationStrategy
        assert isinstance(result.evaluation_strategy, EvaluationStrategy)
        assert result.evaluation_strategy.evaluation_profile == "senior_backend"
        assert result.evaluation_strategy.strictness_level == "high"

        # Verify achievement profile occurred and was attached
        from app.achievement_analysis.models import AchievementProfile
        assert isinstance(result.achievement_profile, AchievementProfile)
        assert result.achievement_profile.achievement_score == 0.0  # mock profile has no achievements

        # Verify skill gap result exists and is populated
        from app.skill_gap.models import SkillGapResult
        assert isinstance(result.skill_gap_result, SkillGapResult)
        assert result.skill_gap_result.overall_gap_score >= 0.0
        assert result.skill_gap_result.decision_summary != ""

        # Verify hard requirement result exists and is populated
        from app.hard_requirements import HardRequirementResult
        assert isinstance(result.hard_requirement_result, HardRequirementResult)

        # Verify score independence
        score_before_gap = result.candidate_score.overall_score
        # Re-run gap engine manually with the same inputs to verify it has no side effects on scoring
        orchestrator._skill_gap_engine.analyze_gaps(
            job_profile=result.job_profile,
            hard_requirement_result=orchestrator._hard_requirement_engine.evaluate_compliance(
                result.job_profile,
                result.role_profile,
                orchestrator._capability_resolver.resolve_capabilities(result.resume_profile)
            ),
            confidence_profiles=orchestrator._skill_confidence_engine.analyze(result.resume_profile)
        )
        assert result.candidate_score.overall_score == score_before_gap

        # Verify match report saved
        assert os.path.exists(result.match_report_path)
        assert result.match_report_path.startswith(tmp_dir)

        # Verify the saved report contains the new fields
        import json
        with open(result.match_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
        assert "evaluation_strategy" in report_data
        assert "achievement_profile" in report_data
        assert "skill_gap_result" in report_data
        assert "hard_requirement_result" in report_data
        assert report_data["evaluation_strategy"]["evaluation_profile"] == "senior_backend"
        assert report_data["achievement_profile"]["achievement_score"] == 0.0
        assert isinstance(report_data["skill_gap_result"]["missing_required_skills"], list)
        assert isinstance(report_data["skill_gap_result"]["overall_gap_score"], float)
        assert isinstance(report_data["hard_requirement_result"]["missing_required"], list)

        # Verify parser, extractor, embedder, matcher were called
        mock_parser.extract_text.assert_called_once_with("dummy_path.pdf")
        mock_resume_extractor.extract.assert_called_once_with("Mock raw resume text")
        mock_job_extractor.extract.assert_called_once_with("Mock raw JD text")
        assert mock_embedder.generate_embedding.call_count == 2
        mock_matcher.compute_similarity.assert_called_once()

