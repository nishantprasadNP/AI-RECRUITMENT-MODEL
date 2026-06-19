import pytest
from pydantic import ValidationError

from app.core.exceptions import ARISError
from app.hard_requirements import (
    HardRequirementResult,
    HardRequirementError,
    CapabilityResolutionError,
    RequirementMatchingError,
    CoverageEvaluationError,
)


def test_valid_model_creation():
    """Verify that HardRequirementResult validates correct inputs."""
    result = HardRequirementResult(
        passed=True,
        coverage_score=0.85,
        matched_required=["Python", "AWS"],
        missing_required=["Kafka"],
        matched_preferred=["Docker"],
        missing_preferred=["Kubernetes"],
        critical_failures=[],
        decision_reason="Candidate matches core criteria."
    )
    assert result.passed is True
    assert result.coverage_score == 0.85
    assert result.matched_required == ["Python", "AWS"]
    assert result.missing_required == ["Kafka"]
    assert result.matched_preferred == ["Docker"]
    assert result.missing_preferred == ["Kubernetes"]
    assert result.critical_failures == []
    assert result.decision_reason == "Candidate matches core criteria."


def test_empty_default_values():
    """Verify that HardRequirementResult initializes with default values."""
    result = HardRequirementResult()
    assert result.passed is False
    assert result.coverage_score == 0.0
    assert result.matched_required == []
    assert result.missing_required == []
    assert result.matched_preferred == []
    assert result.missing_preferred == []
    assert result.critical_failures == []
    assert result.decision_reason == ""


def test_coverage_score_zero():
    """Verify coverage_score = 0.0 is valid."""
    result = HardRequirementResult(coverage_score=0.0)
    assert result.coverage_score == 0.0


def test_coverage_score_one():
    """Verify coverage_score = 1.0 is valid."""
    result = HardRequirementResult(coverage_score=1.0)
    assert result.coverage_score == 1.0


def test_coverage_score_below_zero_fails():
    """Verify coverage_score < 0.0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HardRequirementResult(coverage_score=-0.1)
    assert "Input should be greater than or equal to 0" in str(exc_info.value)


def test_coverage_score_above_one_fails():
    """Verify coverage_score > 1.0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HardRequirementResult(coverage_score=1.1)
    assert "Input should be less than or equal to 1" in str(exc_info.value)


def test_strict_type_validation():
    """Verify that HardRequirementResult enforces strict type validation."""
    # Test strictness on passed (bool) - should not coerce "True"
    with pytest.raises(ValidationError) as exc_info:
        HardRequirementResult(passed="True")
    assert "Input should be a valid boolean" in str(exc_info.value)

    # Test strictness on coverage_score (float) - should not coerce "0.5"
    with pytest.raises(ValidationError) as exc_info:
        HardRequirementResult(coverage_score="0.5")
    assert "Input should be a valid number" in str(exc_info.value)

    # Test strictness on list fields - should not accept list of ints
    with pytest.raises(ValidationError) as exc_info:
        HardRequirementResult(matched_required=[1, 2])
    assert "Input should be a valid string" in str(exc_info.value)


def test_exception_inheritance_hierarchy():
    """Verify custom exception hierarchy and properties."""
    # Asserting that derived exceptions subclass HardRequirementError and ARISError
    assert issubclass(HardRequirementError, ARISError)
    assert issubclass(CapabilityResolutionError, HardRequirementError)
    assert issubclass(RequirementMatchingError, HardRequirementError)
    assert issubclass(CoverageEvaluationError, HardRequirementError)

    # Test raising exceptions and checking their propagation
    with pytest.raises(HardRequirementError) as exc_info:
        raise CapabilityResolutionError("Capability resolution failed")
    assert str(exc_info.value) == "Capability resolution failed"
    assert isinstance(exc_info.value, ARISError)

    with pytest.raises(HardRequirementError) as exc_info:
        raise RequirementMatchingError("Requirement matching failed")
    assert str(exc_info.value) == "Requirement matching failed"
    assert isinstance(exc_info.value, ARISError)

    with pytest.raises(HardRequirementError) as exc_info:
        raise CoverageEvaluationError("Coverage evaluation failed")
    assert str(exc_info.value) == "Coverage evaluation failed"
    assert isinstance(exc_info.value, ARISError)
