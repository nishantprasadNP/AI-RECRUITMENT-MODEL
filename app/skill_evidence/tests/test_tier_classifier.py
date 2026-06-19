"""
Unit tests for §5.7 TierClassifier.

Tests cover:
  - Exact tier boundaries (0, 40, 70, 90, 100)
  - Mid-range values in each tier
  - Edge values (39.99, 40.0, 69.99, 70.0, 89.99, 90.0)
  - Input clamping (values > 100, negative values)
  - classify_all() batch classification
"""

from __future__ import annotations

import pytest

from app.skill_evidence.scoring.tier_classifier import EvidenceTier, TierClassifier


@pytest.fixture
def classifier() -> TierClassifier:
    return TierClassifier()


# ---------------------------------------------------------------------------
# Tests: Tier classification by range
# ---------------------------------------------------------------------------

class TestTierClassification:
    def test_score_100_is_expert(self, classifier):
        assert classifier.classify(100.0) == EvidenceTier.EXPERT.value

    def test_score_90_is_expert(self, classifier):
        assert classifier.classify(90.0) == EvidenceTier.EXPERT.value

    def test_score_89_is_strong(self, classifier):
        assert classifier.classify(89.0) == EvidenceTier.STRONG.value

    def test_score_70_is_strong(self, classifier):
        assert classifier.classify(70.0) == EvidenceTier.STRONG.value

    def test_score_69_is_moderate(self, classifier):
        assert classifier.classify(69.0) == EvidenceTier.MODERATE.value

    def test_score_40_is_moderate(self, classifier):
        assert classifier.classify(40.0) == EvidenceTier.MODERATE.value

    def test_score_39_is_limited(self, classifier):
        assert classifier.classify(39.0) == EvidenceTier.LIMITED.value

    def test_score_0_is_limited(self, classifier):
        assert classifier.classify(0.0) == EvidenceTier.LIMITED.value

    def test_mid_range_moderate(self, classifier):
        assert classifier.classify(55.0) == EvidenceTier.MODERATE.value

    def test_mid_range_strong(self, classifier):
        assert classifier.classify(80.0) == EvidenceTier.STRONG.value


# ---------------------------------------------------------------------------
# Tests: Edge values (boundary precision)
# ---------------------------------------------------------------------------

class TestBoundaryPrecision:
    def test_just_below_expert(self, classifier):
        assert classifier.classify(89.99) == EvidenceTier.STRONG.value

    def test_just_at_expert(self, classifier):
        assert classifier.classify(90.0) == EvidenceTier.EXPERT.value

    def test_just_below_strong(self, classifier):
        assert classifier.classify(69.99) == EvidenceTier.MODERATE.value

    def test_just_at_strong(self, classifier):
        assert classifier.classify(70.0) == EvidenceTier.STRONG.value

    def test_just_below_moderate(self, classifier):
        assert classifier.classify(39.99) == EvidenceTier.LIMITED.value

    def test_just_at_moderate(self, classifier):
        assert classifier.classify(40.0) == EvidenceTier.MODERATE.value


# ---------------------------------------------------------------------------
# Tests: Input clamping
# ---------------------------------------------------------------------------

class TestInputClamping:
    def test_score_above_100_clamped_to_expert(self, classifier):
        assert classifier.classify(150.0) == EvidenceTier.EXPERT.value

    def test_negative_score_clamped_to_limited(self, classifier):
        assert classifier.classify(-10.0) == EvidenceTier.LIMITED.value


# ---------------------------------------------------------------------------
# Tests: classify_all() batch
# ---------------------------------------------------------------------------

class TestClassifyAll:
    def test_classify_all_returns_all_skills(self, classifier):
        scores = {"Python": 82.0, "React.js": 25.0, "FastAPI": 55.0}
        result = classifier.classify_all(scores)
        assert set(result.keys()) == {"Python", "React.js", "FastAPI"}

    def test_classify_all_correct_tiers(self, classifier):
        scores = {
            "Python": 82.0,   # Strong Evidence
            "React.js": 25.0,  # Limited Evidence
            "FastAPI": 55.0,   # Moderate Evidence
            "PyTorch": 93.0,   # Expert Evidence
        }
        result = classifier.classify_all(scores)
        assert result["Python"] == EvidenceTier.STRONG.value
        assert result["React.js"] == EvidenceTier.LIMITED.value
        assert result["FastAPI"] == EvidenceTier.MODERATE.value
        assert result["PyTorch"] == EvidenceTier.EXPERT.value

    def test_classify_all_empty_returns_empty(self, classifier):
        result = classifier.classify_all({})
        assert result == {}
