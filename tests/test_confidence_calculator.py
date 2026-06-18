import pytest
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator, ConfidenceLevel


def test_confidence_calculator_example():
    """Verify example score and classification from prompt."""
    calc = SkillConfidenceCalculator()
    
    # Example 1: Proj=0.8, Prof=1.0, Depth=0.7, Complexity=0.9, Ach=0.2
    # Weighted: 0.30*0.8 + 0.25*1.0 + 0.20*0.7 + 0.15*0.9 + 0.10*0.2 = 0.785 -> 78.5
    # Classifies as: Very Strong Evidence
    score, level = calc.calculate(0.8, 1.0, 0.7, 0.9, 0.2)
    assert pytest.approx(score) == 78.5
    assert level == ConfidenceLevel.VERY_STRONG


def test_confidence_calculator_extreme_bounds():
    """Verify all-zero and all-one signal states."""
    calc = SkillConfidenceCalculator()
    
    # All-zero signals
    score_zero, level_zero = calc.calculate(0.0, 0.0, 0.0, 0.0, 0.0)
    assert score_zero == 0.0
    assert level_zero == ConfidenceLevel.WEAK
    
    # All-one signals
    score_one, level_one = calc.calculate(1.0, 1.0, 1.0, 1.0, 1.0)
    assert score_one == 100.0
    assert level_one == ConfidenceLevel.VERY_STRONG


def test_confidence_calculator_thresholds():
    """Verify classification thresholds behavior at transition edges (25.0, 50.0, 75.0)."""
    calc = SkillConfidenceCalculator()
    
    # Weak boundary <= 25.0
    # Weighted: 0.25 * 1.0 = 0.25 -> 25.0 -> WEAK
    score, level = calc.calculate(0.0, 1.0, 0.0, 0.0, 0.0)
    assert score == 25.0
    assert level == ConfidenceLevel.WEAK
    
    # Moderate boundary (25.0, 50.0]
    # Weighted: 0.25 * 1.0 + 0.10 * 0.1 = 0.26 -> 26.0 -> MODERATE
    score, level = calc.calculate(0.0, 1.0, 0.0, 0.0, 0.1)
    assert score == 26.0
    assert level == ConfidenceLevel.MODERATE
    
    # Weighted: 0.30 * 1.0 + 0.20 * 1.0 = 0.50 -> 50.0 -> MODERATE
    score, level = calc.calculate(1.0, 0.0, 1.0, 0.0, 0.0)
    assert score == 50.0
    assert level == ConfidenceLevel.MODERATE
    
    # Strong boundary (50.0, 75.0]
    # Weighted: 0.30 * 1.0 + 0.20 * 1.0 + 0.10 * 0.1 = 0.51 -> 51.0 -> STRONG
    score, level = calc.calculate(1.0, 0.0, 1.0, 0.0, 0.1)
    assert score == 51.0
    assert level == ConfidenceLevel.STRONG
    
    # Weighted: 0.30*1.0 + 0.25*1.0 + 0.20*1.0 = 0.75 -> 75.0 -> STRONG
    score, level = calc.calculate(1.0, 1.0, 1.0, 0.0, 0.0)
    assert score == 75.0
    assert level == ConfidenceLevel.STRONG
    
    # Very Strong boundary (75.0, 100.0]
    # Weighted: 0.30*1.0 + 0.25*1.0 + 0.20*1.0 + 0.10*0.1 = 0.76 -> 76.0 -> VERY_STRONG
    score, level = calc.calculate(1.0, 1.0, 1.0, 0.0, 0.1)
    assert score == 76.0
    assert level == ConfidenceLevel.VERY_STRONG


def test_confidence_calculator_clamping():
    """Verify out-of-bound signals are clamped to range [0.0, 1.0]."""
    calc = SkillConfidenceCalculator()
    
    # Signals above 1.0 (clamped to 1.0)
    score, level = calc.calculate(1.5, 2.0, 1.1, 3.5, 1.2)
    assert score == 100.0
    assert level == ConfidenceLevel.VERY_STRONG
    
    # Signals below 0.0 (clamped to 0.0)
    score, level = calc.calculate(-0.5, -2.0, -0.1, -1.0, 0.0)
    assert score == 0.0
    assert level == ConfidenceLevel.WEAK


def test_confidence_calculator_safety_normalization():
    """Verify safe coercion and fallback on invalid types without exception."""
    calc = SkillConfidenceCalculator()
    
    # Coercing valid numeric string ("0.8" -> 0.8)
    score, level = calc.calculate("0.8", 1.0, 0.7, 0.9, 0.2)
    assert pytest.approx(score) == 78.5
    assert level == ConfidenceLevel.VERY_STRONG
    
    # None type gets normalized to 0.0
    score, level = calc.calculate(None, 1.0, None, 1.0, None)
    # Prof(1.0*0.25) + Comp(1.0*0.15) = 0.40 -> 40.0 -> MODERATE
    assert score == 40.0
    assert level == ConfidenceLevel.MODERATE
    
    # Uncoercible string or complex structure defaults to 0.0 safely
    score, level = calc.calculate("invalid_number", 1.0, [1, 2], 1.0, {"val": 1.0})
    assert score == 40.0
    assert level == ConfidenceLevel.MODERATE
