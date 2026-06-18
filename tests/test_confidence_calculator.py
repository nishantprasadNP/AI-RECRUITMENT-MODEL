import pytest
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator, ConfidenceLevel


def test_confidence_calculator_example():
    """Verify example score and classification from prompt."""
    calc = SkillConfidenceCalculator()
    
    # Signals: professional_signal=1.0, depth_signal=0.7, complexity_signal=0.9
    # Weighted: 0.45 * 0.7 (depth) + 0.30 * 1.0 (prof) + 0.25 * 0.9 (comp) = 0.315 + 0.30 + 0.225 = 0.84 -> 84.0
    # Classifies as: Very Strong Evidence
    score, level = calc.calculate(1.0, 0.7, 0.9)
    assert pytest.approx(score) == 84.0
    assert level == ConfidenceLevel.VERY_STRONG
    
    tier = calc.get_skill_tier(score)
    assert tier == "Advanced"


def test_confidence_calculator_extreme_bounds():
    """Verify all-zero and all-one signal states."""
    calc = SkillConfidenceCalculator()
    
    # All-zero signals
    score_zero, level_zero = calc.calculate(0.0, 0.0, 0.0)
    assert score_zero == 0.0
    assert level_zero == ConfidenceLevel.WEAK
    assert calc.get_skill_tier(score_zero) == "Beginner"
    
    # All-one signals
    score_one, level_one = calc.calculate(1.0, 1.0, 1.0)
    assert score_one == 100.0
    assert level_one == ConfidenceLevel.VERY_STRONG
    assert calc.get_skill_tier(score_one) == "Expert"


def test_confidence_calculator_thresholds():
    """Verify classification thresholds behavior at transition edges (25.0, 50.0, 75.0)."""
    calc = SkillConfidenceCalculator()
    
    # Weak boundary <= 25.0
    # Weighted: 0.25 * 1.0 = 0.25 -> 25.0 -> WEAK
    score, level = calc.calculate(0.0, 0.0, 1.0)
    assert score == 25.0
    assert level == ConfidenceLevel.WEAK
    
    # Moderate boundary (25.0, 50.0]
    # Weighted: 0.30 * 0.1 + 0.45 * 0.2 + 0.25 * 0.56 = 0.03 + 0.09 + 0.14 = 0.26 -> 26.0 -> MODERATE
    score, level = calc.calculate(0.1, 0.2, 0.56)
    assert score == 26.0
    assert level == ConfidenceLevel.MODERATE
    
    # Weighted: 0.30 * 1.0 + 0.25 * 0.8 = 0.50 -> 50.0 -> MODERATE
    score, level = calc.calculate(1.0, 0.0, 0.8)
    assert score == 50.0
    assert level == ConfidenceLevel.MODERATE
    
    # Strong boundary (50.0, 75.0]
    # Weighted: 0.30 * 1.0 + 0.25 * 0.84 = 0.51 -> 51.0 -> STRONG
    score, level = calc.calculate(1.0, 0.0, 0.84)
    assert score == 51.0
    assert level == ConfidenceLevel.STRONG
    
    # Weighted: 0.30 * 1.0 + 0.45 * 1.0 = 0.75 -> 75.0 -> STRONG
    score, level = calc.calculate(1.0, 1.0, 0.0)
    assert score == 75.0
    assert level == ConfidenceLevel.STRONG
    
    # Very Strong boundary (75.0, 100.0]
    # Weighted: 0.30 * 1.0 + 0.45 * 1.0 + 0.25 * 0.04 = 0.76 -> 76.0 -> VERY_STRONG
    score, level = calc.calculate(1.0, 1.0, 0.04)
    assert score == 76.0
    assert level == ConfidenceLevel.VERY_STRONG


def test_confidence_calculator_clamping():
    """Verify out-of-bound signals are clamped to range [0.0, 1.0]."""
    calc = SkillConfidenceCalculator()
    
    # Signals above 1.0 (clamped to 1.0)
    score, level = calc.calculate(2.0, 1.1, 3.5)
    assert score == 100.0
    assert level == ConfidenceLevel.VERY_STRONG
    
    # Signals below 0.0 (clamped to 0.0)
    score, level = calc.calculate(-2.0, -0.1, -1.0)
    assert score == 0.0
    assert level == ConfidenceLevel.WEAK


def test_confidence_calculator_safety_normalization():
    """Verify safe coercion and fallback on invalid types without exception."""
    calc = SkillConfidenceCalculator()
    
    # Coercing valid numeric string ("0.8" -> 0.8, "0.7" -> 0.7, etc.)
    score, level = calc.calculate("1.0", "0.7", "0.9")
    assert pytest.approx(score) == 84.0
    assert level == ConfidenceLevel.VERY_STRONG
    
    # None type gets normalized to 0.0
    score, level = calc.calculate(1.0, None, 1.0)
    # Prof(1.0*0.30) + Comp(1.0*0.25) = 0.55 -> 55.0 -> STRONG
    assert pytest.approx(score) == 55.0
    assert level == ConfidenceLevel.STRONG
    
    # Uncoercible string or complex structure defaults to 0.0 safely
    score, level = calc.calculate(1.0, [1, 2], 1.0)
    assert pytest.approx(score) == 55.0
    assert level == ConfidenceLevel.STRONG



def test_confidence_calculator_tiers():
    """Verify qualitative skill tier mappings."""
    calc = SkillConfidenceCalculator()
    
    assert calc.get_skill_tier(95.0) == "Expert"
    assert calc.get_skill_tier(90.0) == "Expert"
    assert calc.get_skill_tier(89.0) == "Advanced"
    assert calc.get_skill_tier(70.0) == "Advanced"
    assert calc.get_skill_tier(69.0) == "Intermediate"
    assert calc.get_skill_tier(40.0) == "Intermediate"
    assert calc.get_skill_tier(39.0) == "Beginner"
    assert calc.get_skill_tier(0.0) == "Beginner"
    
    # Out of bounds clamping check in tiering
    assert calc.get_skill_tier(105.0) == "Expert"
    assert calc.get_skill_tier(-10.0) == "Beginner"
