"""
Unit tests for §5.2 DependencyExpansionEngine.

Tests cover:
  - Skills with REQUIRES graph relationships
  - Skills with no dependencies
  - Empty candidate skills
  - Self-reference exclusion
  - Deterministic output ordering
"""

from __future__ import annotations

from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from app.skill_evidence.engines.dependency_expansion_engine import DependencyExpansionEngine
from app.skill_evidence.graph.skill_graph_adapter import ISkillGraphAdapter


# ---------------------------------------------------------------------------
# Test-double: Mock graph adapter
# ---------------------------------------------------------------------------

class MockGraphAdapter(ISkillGraphAdapter):
    """
    Mock implementation of ISkillGraphAdapter.

    Simulates:
        FastAPI → Python  (FastAPI requires Python)
        Scikit-learn → Python
        PyTorch → Python
        React.js → JavaScript
    """

    _REQUIRES: dict[str, list[str]] = {
        "FastAPI": ["Python"],
        "Scikit-learn": ["Python"],
        "PyTorch": ["Python"],
        "React.js": ["JavaScript"],
    }

    def skill_exists(self, skill: str) -> bool:
        return True

    def get_dependencies(self, skill: str) -> List[str]:
        return self._REQUIRES.get(skill, [])

    def get_ancestors(self, skill: str) -> List[str]:
        return self._REQUIRES.get(skill, [])

    def get_descendants(self, skill: str) -> List[str]:
        return []

    def get_requiring_skills(self, skill: str, candidate_skills: List[str]) -> List[str]:
        """Returns candidate skills that declare `skill` as a dependency (ancestor)."""
        requiring = []
        for candidate in candidate_skills:
            if candidate == skill:
                continue
            ancestors = self._REQUIRES.get(candidate, [])
            if skill in ancestors:
                requiring.append(candidate)
        return requiring

    def get_capability_nodes(self) -> List[str]:
        return []

    def resolve_canonical(self, skill: str) -> Optional[str]:
        return skill


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter() -> MockGraphAdapter:
    return MockGraphAdapter()


@pytest.fixture
def engine(adapter) -> DependencyExpansionEngine:
    return DependencyExpansionEngine(graph_adapter=adapter)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDependencyExpansion:
    def test_python_gets_fastapi_and_sklearn_as_supporting(self, engine):
        skills = ["Python", "FastAPI", "Scikit-learn"]
        result = engine.expand(skills)
        assert "FastAPI" in result["Python"].supporting_skills
        assert "Scikit-learn" in result["Python"].supporting_skills

    def test_all_three_pytorch_fastapi_sklearn_support_python(self, engine):
        skills = ["Python", "FastAPI", "Scikit-learn", "PyTorch"]
        result = engine.expand(skills)
        assert set(result["Python"].supporting_skills) == {"FastAPI", "Scikit-learn", "PyTorch"}

    def test_skill_with_no_dependents_has_empty_supporting(self, engine):
        skills = ["Python", "FastAPI"]
        result = engine.expand(skills)
        # FastAPI does not have any candidate skills depending on it
        assert result["FastAPI"].supporting_skills == []

    def test_self_reference_excluded(self, engine):
        """A skill should not appear as its own supporting skill."""
        skills = ["Python"]
        result = engine.expand(skills)
        assert "Python" not in result["Python"].supporting_skills

    def test_all_skills_have_entry_even_with_no_dependents(self, engine):
        skills = ["Python", "FastAPI", "React.js"]
        result = engine.expand(skills)
        assert "Python" in result
        assert "FastAPI" in result
        assert "React.js" in result

    def test_empty_skills_returns_empty(self, engine):
        result = engine.expand([])
        assert result == {}

    def test_supporting_skills_sorted_deterministically(self, engine):
        skills = ["Python", "PyTorch", "FastAPI", "Scikit-learn"]
        result = engine.expand(skills)
        # Should be sorted alphabetically
        assert result["Python"].supporting_skills == sorted(
            result["Python"].supporting_skills
        )

    def test_javascript_gets_reactjs_as_supporting(self, engine):
        skills = ["JavaScript", "React.js"]
        result = engine.expand(skills)
        assert "React.js" in result["JavaScript"].supporting_skills
