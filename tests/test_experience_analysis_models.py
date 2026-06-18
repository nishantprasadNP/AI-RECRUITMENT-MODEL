import pytest
from pydantic import ValidationError
from app.experience_analysis.models import SkillEvidence, SkillConfidenceProfile


def test_skill_evidence_defaults():
    """Test that SkillEvidence initializes correctly with default values."""
    evidence = SkillEvidence(skill="Python")
    
    assert evidence.skill == "Python"
    assert evidence.project_count == 0
    assert evidence.projects == []
    assert evidence.professional_usage is False
    assert evidence.roles == []
    assert evidence.skill_mentions == 0
    assert evidence.achievement_mentions == 0


def test_skill_evidence_custom():
    """Test that SkillEvidence initializes correctly with valid custom values."""
    evidence = SkillEvidence(
        skill="Go",
        project_count=3,
        projects=["Project A", "Project B"],
        professional_usage=True,
        roles=["Backend Engineer", "Tech Lead"],
        skill_mentions=5,
        achievement_mentions=2
    )
    
    assert evidence.skill == "Go"
    assert evidence.project_count == 3
    assert evidence.projects == ["Project A", "Project B"]
    assert evidence.professional_usage is True
    assert evidence.roles == ["Backend Engineer", "Tech Lead"]
    assert evidence.skill_mentions == 5
    assert evidence.achievement_mentions == 2


def test_skill_evidence_strict_validation():
    """Test that SkillEvidence enforces strict type validation."""
    # Test strictness on integer (should not coerce string to int)
    with pytest.raises(ValidationError) as exc_info:
        SkillEvidence(skill="Python", project_count="3")
    assert "Input should be a valid integer" in str(exc_info.value)

    # Test strictness on boolean (should not coerce string or int to bool)
    with pytest.raises(ValidationError) as exc_info:
        SkillEvidence(skill="Python", professional_usage="True")
    assert "Input should be a valid boolean" in str(exc_info.value)

    # Test strictness on list of strings (should not accept list of ints)
    with pytest.raises(ValidationError) as exc_info:
        SkillEvidence(skill="Python", projects=[1, 2])
    assert "Input should be a valid string" in str(exc_info.value)


def test_skill_confidence_profile_valid():
    """Test that SkillConfidenceProfile initializes correctly with valid inputs."""
    profile = SkillConfidenceProfile(
        skill="Python",
        professional_signal=1.0,
        depth_signal=0.6,
        complexity_signal=0.7,
        confidence_score=72.0,
        confidence_level="High",
        evidence_summary={"projects": 2}
    )
    
    assert profile.skill == "Python"
    assert profile.professional_signal == 1.0
    assert profile.depth_signal == 0.6
    assert profile.complexity_signal == 0.7
    assert profile.confidence_score == 72.0
    assert profile.confidence_level == "High"
    assert profile.skill_tier == "Beginner"  # Default value
    assert profile.evidence_summary == {"projects": 2}


def test_skill_confidence_profile_missing_fields():
    """Test that SkillConfidenceProfile validation fails if required fields are missing."""
    with pytest.raises(ValidationError) as exc_info:
        # Missing skill and signals
        SkillConfidenceProfile(
            professional_signal=1.0
        )
    assert "Field required" in str(exc_info.value)


def test_skill_confidence_profile_strict_validation():
    """Test that SkillConfidenceProfile enforces strict type validation for floats."""
    # Test strictness on float (should not coerce string to float)
    with pytest.raises(ValidationError) as exc_info:
        SkillConfidenceProfile(
            skill="Python",
            professional_signal="1.0",
            depth_signal=0.6,
            complexity_signal=0.7,
            confidence_score=72.0,
            confidence_level="High"
        )
    assert "Input should be a valid number" in str(exc_info.value)

