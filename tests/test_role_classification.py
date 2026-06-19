import pytest
from pydantic import ValidationError

from app.core.exceptions import ARISError
from app.role_classification.models import RoleProfile
from app.role_classification.exceptions import (
    RoleClassificationError,
    RoleFamilyDetectionError,
    SpecializationDetectionError,
    SeniorityDetectionError,
)


def test_role_profile_validation():
    """Verify that RoleProfile correctly validates correct inputs."""
    data = {
        "role_family": "software_engineering",
        "specialization": "backend_engineer",
        "seniority": "mid_level",
        "evaluation_profile": "mid_backend",
    }
    profile = RoleProfile(**data)
    assert profile.role_family == "software_engineering"
    assert profile.specialization == "backend_engineer"
    assert profile.seniority == "mid_level"
    assert profile.evaluation_profile == "mid_backend"


def test_role_profile_validation_missing_fields():
    """Verify that RoleProfile validation fails if required fields are missing."""
    data = {
        "role_family": "software_engineering",
        "specialization": "backend_engineer",
    }
    with pytest.raises(ValidationError):
        RoleProfile(**data)


def test_role_profile_validation_invalid_types():
    """Verify that RoleProfile validation fails if fields have incorrect types."""
    data = {
        "role_family": "software_engineering",
        "specialization": "backend_engineer",
        "seniority": 123,  # Should be string
        "evaluation_profile": "mid_backend",
    }
    with pytest.raises(ValidationError):
        RoleProfile(**data)


def test_custom_exceptions():
    """Verify exception hierarchy and properties."""
    with pytest.raises(RoleClassificationError) as exc_info:
        raise RoleFamilyDetectionError("Failed to detect role family")
    assert str(exc_info.value) == "Failed to detect role family"
    assert isinstance(exc_info.value, ARISError)

    with pytest.raises(RoleClassificationError) as exc_info:
        raise SpecializationDetectionError("Failed to detect specialization")
    assert str(exc_info.value) == "Failed to detect specialization"
    assert isinstance(exc_info.value, ARISError)

    with pytest.raises(RoleClassificationError) as exc_info:
        raise SeniorityDetectionError("Failed to detect seniority")
    assert str(exc_info.value) == "Failed to detect seniority"
    assert isinstance(exc_info.value, ARISError)


def test_role_rules_constants():
    """Verify that all deterministic mapping constants are set up correctly."""
    from app.role_classification.role_rules import (
        BACKEND_SKILLS,
        FRONTEND_SKILLS,
        ML_SKILLS,
        DATA_ENGINEERING_SKILLS,
        DEVOPS_SKILLS,
        SECURITY_SKILLS,
        ROLE_FAMILY_KEYWORDS,
        SPECIALIZATION_KEYWORDS,
    )

    # 1. Assert helper skill constants are lists of strings
    for skill_list in (
        BACKEND_SKILLS,
        FRONTEND_SKILLS,
        ML_SKILLS,
        DATA_ENGINEERING_SKILLS,
        DEVOPS_SKILLS,
        SECURITY_SKILLS,
    ):
        assert isinstance(skill_list, list)
        assert len(skill_list) > 0
        assert all(isinstance(skill, str) for skill in skill_list)

    # 2. Verify expected role family keys exist
    expected_families = [
        "software_engineering",
        "data_ai",
        "cloud_engineering",
        "security_engineering",
        "product_management",
    ]
    for family in expected_families:
        assert family in ROLE_FAMILY_KEYWORDS
        assert isinstance(ROLE_FAMILY_KEYWORDS[family], list)
        assert len(ROLE_FAMILY_KEYWORDS[family]) > 0

    # 3. Verify expected specialization keys exist
    expected_specs = [
        "backend_engineer",
        "frontend_engineer",
        "fullstack_engineer",
        "mobile_engineer",
        "ml_engineer",
        "data_engineer",
        "data_scientist",
        "ai_research_engineer",
        "devops_engineer",
        "cloud_engineer",
        "security_engineer",
        "product_manager",
    ]
    for spec in expected_specs:
        assert spec in SPECIALIZATION_KEYWORDS
        assert isinstance(SPECIALIZATION_KEYWORDS[spec], list)
        assert len(SPECIALIZATION_KEYWORDS[spec]) > 0


def test_classifier_detect_role_family():
    """Verify role family detection based on title, skills, or responsibilities."""
    from app.schemas.job_schema import JobProfile, HiddenHiringSignals
    from app.role_classification.role_classifier import RoleClassifier

    classifier = RoleClassifier()

    # 1. Detect via Title (highest priority)
    job_title = JobProfile(
        title="Senior Machine Learning Architect",
        required_skills=["Python"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
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
        job_summary="ML role",
    )
    assert classifier.detect_role_family(job_title) == "data_ai"

    # 2. Detect via Skills (medium priority)
    job_skills = JobProfile(
        title="Unknown Title",
        required_skills=["Docker", "Kubernetes", "Terraform"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="mid",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="Cloud role",
    )
    assert classifier.detect_role_family(job_skills) == "cloud_engineering"

    # 3. Detect via Responsibility Themes (lowest priority)
    job_responsibilities = JobProfile(
        title="Unknown Title",
        required_skills=["Something Random"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="mid",
        responsibility_themes=["Manage product lifecycle as product manager", "Define roadmap"],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="Product role",
    )
    assert classifier.detect_role_family(job_responsibilities) == "product_management"

    # 4. Unknown raises detection error
    job_unknown = JobProfile(
        title="Unknown Title",
        required_skills=["Something Random"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="mid",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="Unknown role",
    )
    with pytest.raises(RoleFamilyDetectionError):
        classifier.detect_role_family(job_unknown)


def test_classifier_detect_specialization():
    """Verify specialization detection within a role family."""
    from app.schemas.job_schema import JobProfile, HiddenHiringSignals
    from app.role_classification.role_classifier import RoleClassifier

    classifier = RoleClassifier()

    # 1. Match from title
    job = JobProfile(
        title="React Frontend Developer",
        required_skills=["Python"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
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
        job_summary="Frontend role",
    )
    assert classifier.detect_specialization(job, "software_engineering") == "frontend_engineer"

    # 2. Match from skills
    job_skills = JobProfile(
        title="Developer",
        required_skills=["React", "TypeScript", "CSS"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
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
        job_summary="Frontend role",
    )
    assert classifier.detect_specialization(job_skills, "software_engineering") == "frontend_engineer"

    # 3. Default specialization fallback when no signals
    job_default = JobProfile(
        title="General Software Engineer",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
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
        job_summary="General role",
    )
    assert classifier.detect_specialization(job_default, "software_engineering") == "backend_engineer"


def test_classifier_detect_seniority():
    """Verify seniority detection from labels and years of experience."""
    from app.schemas.job_schema import JobProfile, HiddenHiringSignals
    from app.role_classification.role_classifier import RoleClassifier

    classifier = RoleClassifier()

    # 1. Map labels (intern / mid_level / senior / staff)
    def make_job(seniority_level="", exp=None):
        return JobProfile(
            title="Dev",
            required_skills=[],
            preferred_skills=[],
            critical_skills=[],
            experience_required=exp,
            education=None,
            leadership=False,
            seniority_level=seniority_level,
            responsibility_themes=[],
            domain_knowledge=[],
            soft_skills=[],
            tools_and_technologies=[],
            hidden_hiring_signals=HiddenHiringSignals(),
            role_complexity_score=5,
            future_potential_signals=[],
            job_summary="Dev",
        )

    assert classifier.detect_seniority(make_job(seniority_level="graduate")) == "intern"
    assert classifier.detect_seniority(make_job(seniority_level="junior")) == "mid_level"
    assert classifier.detect_seniority(make_job(seniority_level="lead")) == "senior"
    assert classifier.detect_seniority(make_job(seniority_level="architect")) == "staff"

    # 2. Map years of experience when label is missing
    assert classifier.detect_seniority(make_job(exp=0)) == "intern"
    assert classifier.detect_seniority(make_job(exp=2)) == "mid_level"
    assert classifier.detect_seniority(make_job(exp=5)) == "senior"
    assert classifier.detect_seniority(make_job(exp=10)) == "staff"

    # 3. Default fallback
    assert classifier.detect_seniority(make_job()) == "mid_level"


def test_classifier_build_evaluation_profile():
    """Verify evaluation profile construction and stripping of suffix."""
    from app.role_classification.role_classifier import RoleClassifier

    classifier = RoleClassifier()
    assert classifier.build_evaluation_profile("mid_level", "backend_engineer") == "mid_backend"
    assert classifier.build_evaluation_profile("intern", "ml_engineer") == "intern_ml"
    assert classifier.build_evaluation_profile("senior", "product_manager") == "senior_product_manager"
    assert classifier.build_evaluation_profile("staff", "devops_engineer") == "staff_devops"


def test_classifier_classify_success():
    """Verify full end-to-end classification returns correct RoleProfile."""
    from app.schemas.job_schema import JobProfile, HiddenHiringSignals
    from app.role_classification.role_classifier import RoleClassifier
    from app.role_classification.models import RoleProfile

    classifier = RoleClassifier()
    job = JobProfile(
        title="Staff DevOps Engineer",
        required_skills=["AWS", "Docker", "Terraform"],
        preferred_skills=[],
        critical_skills=[],
        experience_required=8,
        education=None,
        leadership=True,
        seniority_level="staff",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=8,
        future_potential_signals=[],
        job_summary="DevOps Role",
    )
    profile = classifier.classify(job)
    assert isinstance(profile, RoleProfile)
    assert profile.role_family == "cloud_engineering"
    assert profile.specialization == "devops_engineer"
    assert profile.seniority == "staff"
    assert profile.evaluation_profile == "staff_devops"


def test_classifier_classify_fallback():
    """Verify that classification falls back gracefully on exceptions."""
    from app.schemas.job_schema import JobProfile, HiddenHiringSignals
    from app.role_classification.role_classifier import RoleClassifier

    classifier = RoleClassifier()
    # Trigger an error by passing inputs that cause family detection failure
    job = JobProfile(
        title="",
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=5,
        future_potential_signals=[],
        job_summary="",
    )
    profile = classifier.classify(job)
    assert profile.role_family == "software_engineering"
    assert profile.specialization == "backend_engineer"
    assert profile.seniority == "mid_level"
    assert profile.evaluation_profile == "mid_backend"


