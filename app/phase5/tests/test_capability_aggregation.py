"""
Unit tests for §5.4 CapabilityAggregationEngine.

Tests cover:
  - Capability score as average of evidenced descendants
  - Only capabilities with at least 1 evidenced descendant appear in output
  - Output sorted by confidence descending
  - Empty skill scores → empty result
  - No capability nodes → empty result
  - Case-insensitive matching of descendant names
"""

from __future__ import annotations

from typing import List, Optional

import pytest

from app.phase5.engines.capability_aggregation_engine import CapabilityAggregationEngine
from app.phase5.graph.skill_graph_adapter import ISkillGraphAdapter


# ---------------------------------------------------------------------------
# Mock graph adapter
# ---------------------------------------------------------------------------

class MockGraphAdapter(ISkillGraphAdapter):
    """
    Simulates:
        Capabilities: [Backend Development, Machine Learning Engineering]
        Backend Development → [Node.js, Express.js, FastAPI, MongoDB]
        Machine Learning Engineering → [Scikit-learn, PyTorch, TensorFlow]
    """

    _CAPABILITIES = ["Backend Development", "Machine Learning Engineering"]
    _DESCENDANTS = {
        "Backend Development": ["Node.js", "Express.js", "FastAPI", "MongoDB"],
        "Machine Learning Engineering": ["Scikit-learn", "PyTorch", "TensorFlow"],
    }

    def skill_exists(self, skill: str) -> bool:
        return True

    def get_dependencies(self, skill: str) -> List[str]:
        return []

    def get_ancestors(self, skill: str) -> List[str]:
        return []

    def get_descendants(self, skill: str) -> List[str]:
        return self._DESCENDANTS.get(skill, [])

    def get_requiring_skills(self, skill: str, candidate_skills: List[str]) -> List[str]:
        return []

    def get_capability_nodes(self) -> List[str]:
        return self._CAPABILITIES

    def resolve_canonical(self, skill: str) -> Optional[str]:
        return skill


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter() -> MockGraphAdapter:
    return MockGraphAdapter()


@pytest.fixture
def engine(adapter) -> CapabilityAggregationEngine:
    return CapabilityAggregationEngine(graph_adapter=adapter)


# ---------------------------------------------------------------------------
# Tests: Core aggregation
# ---------------------------------------------------------------------------

class TestCapabilityAggregationCore:
    def test_backend_capability_score_is_average_of_evidenced_descendants(self, engine):
        scores = {"FastAPI": 75.0, "Node.js": 50.0, "Express.js": 0.0, "MongoDB": 0.0}
        result = engine.aggregate(scores)
        backend = next((p for p in result if p.capability == "Backend Development"), None)
        assert backend is not None
        # Only FastAPI (75) and Node.js (50) have score > 0
        expected_confidence = (75.0 + 50.0) / 2  # = 62.5
        assert abs(backend.confidence - expected_confidence) < 0.01

    def test_only_evidenced_descendants_in_supporting_skills(self, engine):
        scores = {"FastAPI": 80.0, "MongoDB": 0.0}
        result = engine.aggregate(scores)
        backend = next((p for p in result if p.capability == "Backend Development"), None)
        assert backend is not None
        assert "FastAPI" in backend.supporting_skills
        assert "MongoDB" not in backend.supporting_skills

    def test_capability_with_no_evidenced_skills_excluded(self, engine):
        """
        Machine Learning Engineering has no evidenced skills → should not appear.
        """
        scores = {"FastAPI": 70.0}  # Only backend skill has evidence
        result = engine.aggregate(scores)
        ml = next((p for p in result if p.capability == "Machine Learning Engineering"), None)
        assert ml is None

    def test_both_capabilities_when_both_have_evidence(self, engine):
        scores = {"FastAPI": 75.0, "Scikit-learn": 60.0, "PyTorch": 80.0}
        result = engine.aggregate(scores)
        capability_names = [p.capability for p in result]
        assert "Backend Development" in capability_names
        assert "Machine Learning Engineering" in capability_names

    def test_ml_confidence_is_average_of_sklearn_and_pytorch(self, engine):
        scores = {"Scikit-learn": 60.0, "PyTorch": 80.0}
        result = engine.aggregate(scores)
        ml = next((p for p in result if p.capability == "Machine Learning Engineering"), None)
        assert ml is not None
        expected = (60.0 + 80.0) / 2  # = 70.0
        assert abs(ml.confidence - expected) < 0.01


# ---------------------------------------------------------------------------
# Tests: Sorting
# ---------------------------------------------------------------------------

class TestCapabilitySort:
    def test_output_sorted_by_confidence_descending(self, engine):
        scores = {
            "FastAPI": 90.0,   # Backend: 90
            "Scikit-learn": 50.0,  # ML: 50
        }
        result = engine.aggregate(scores)
        if len(result) >= 2:
            assert result[0].confidence >= result[1].confidence


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_skill_scores_returns_empty(self, engine):
        result = engine.aggregate({})
        assert result == []

    def test_no_capability_nodes_returns_empty(self):
        """If the graph has no capability nodes, output should be empty."""
        class EmptyCapAdapter(MockGraphAdapter):
            def get_capability_nodes(self) -> List[str]:
                return []

        eng = CapabilityAggregationEngine(graph_adapter=EmptyCapAdapter())
        result = eng.aggregate({"FastAPI": 75.0})
        assert result == []

    def test_case_insensitive_descendant_matching(self, engine):
        """Score keys may differ in case from graph descendant names."""
        scores = {"fastapi": 70.0}  # lowercase
        result = engine.aggregate(scores)
        backend = next((p for p in result if p.capability == "Backend Development"), None)
        assert backend is not None
        assert backend.confidence > 0
