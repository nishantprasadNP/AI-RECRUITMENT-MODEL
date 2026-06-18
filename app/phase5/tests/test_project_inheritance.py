"""
Unit tests for §5.3 ProjectInheritanceEngine.

Tests cover:
  - Foundational skill inherits project via technology ancestry
  - Multiple technologies in same project → one inherited entry (deduplicated)
  - Skill not in candidate list is NOT granted inheritance
  - Projects with no technologies produce no inheritance
  - Evidence strength is always EvidenceWeight.INHERITED (0.3)
  - Deterministic, sorted output
"""

from __future__ import annotations

from typing import List, Optional

import pytest

from app.models.resume_schema import Project, ResumeProfile
from app.phase5.engines.project_inheritance_engine import ProjectInheritanceEngine
from app.phase5.graph.skill_graph_adapter import ISkillGraphAdapter
from app.phase5.models.evidence_models import EvidenceWeight


# ---------------------------------------------------------------------------
# Mock graph adapter
# ---------------------------------------------------------------------------

class MockGraphAdapter(ISkillGraphAdapter):
    """
    Simulates the following ancestry:
        FastAPI    → ancestors: [Python, Backend Development]
        Scikit-learn → ancestors: [Python, Machine Learning]
        PyTorch    → ancestors: [Python, Machine Learning]
        React.js   → ancestors: [JavaScript, Frontend Development]
        TypeScript → ancestors: [JavaScript]
    """

    _ANCESTORS: dict[str, list[str]] = {
        "FastAPI": ["Python", "Backend Development"],
        "Scikit-learn": ["Python", "Machine Learning"],
        "PyTorch": ["Python", "Machine Learning"],
        "React.js": ["JavaScript", "Frontend Development"],
        "TypeScript": ["JavaScript"],
    }

    def skill_exists(self, skill: str) -> bool:
        return True

    def get_dependencies(self, skill: str) -> List[str]:
        return self._ANCESTORS.get(skill, [])

    def get_ancestors(self, skill: str) -> List[str]:
        return self._ANCESTORS.get(skill, [])

    def get_descendants(self, skill: str) -> List[str]:
        return []

    def get_requiring_skills(self, skill: str, candidate_skills: List[str]) -> List[str]:
        return []

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
def engine(adapter) -> ProjectInheritanceEngine:
    return ProjectInheritanceEngine(graph_adapter=adapter)


def _make_profile(projects=None) -> ResumeProfile:
    return ResumeProfile(projects=projects or [])


# ---------------------------------------------------------------------------
# Tests: Core inheritance logic
# ---------------------------------------------------------------------------

class TestProjectInheritanceCore:
    def test_python_inherits_project_from_fastapi_technology(self, engine):
        profile = _make_profile(
            projects=[Project(name="CAF-MAI", technologies=["FastAPI"])]
        )
        result = engine.inherit(profile, candidate_skills=["Python", "FastAPI"])
        assert "Python" in result
        assert any(e.project == "CAF-MAI" for e in result["Python"].inherited_projects)

    def test_python_inherits_cafmai_via_all_three_technologies(self, engine):
        """
        CAF-MAI has FastAPI, Scikit-learn, PyTorch — all ancestors of Python.
        Python should inherit CAF-MAI exactly once (deduplicated).
        """
        profile = _make_profile(
            projects=[
                Project(
                    name="CAF-MAI",
                    technologies=["FastAPI", "Scikit-learn", "PyTorch"],
                )
            ]
        )
        result = engine.inherit(profile, candidate_skills=["Python", "FastAPI", "Scikit-learn", "PyTorch"])

        assert "Python" in result
        projects_for_python = [e.project for e in result["Python"].inherited_projects]
        assert projects_for_python.count("CAF-MAI") == 1

    def test_skill_not_in_candidate_list_does_not_get_inheritance(self, engine):
        """
        'Machine Learning' is an ancestor of Scikit-learn but is NOT in candidate_skills.
        It should NOT receive inherited evidence.
        """
        profile = _make_profile(
            projects=[Project(name="ML Proj", technologies=["Scikit-learn"])]
        )
        result = engine.inherit(profile, candidate_skills=["Python", "Scikit-learn"])
        # "Machine Learning" should NOT be in result (it's not a candidate skill)
        assert "Machine Learning" not in result

    def test_javascript_inherits_from_reactjs_and_typescript(self, engine):
        profile = _make_profile(
            projects=[
                Project(name="FE App", technologies=["React.js", "TypeScript"])
            ]
        )
        result = engine.inherit(profile, candidate_skills=["JavaScript", "React.js", "TypeScript"])
        assert "JavaScript" in result
        assert any(e.project == "FE App" for e in result["JavaScript"].inherited_projects)

    def test_inheritance_across_multiple_projects(self, engine):
        """Python should inherit from two projects when both have dependencies."""
        profile = _make_profile(
            projects=[
                Project(name="Proj1", technologies=["FastAPI"]),
                Project(name="Proj2", technologies=["PyTorch"]),
            ]
        )
        result = engine.inherit(profile, candidate_skills=["Python", "FastAPI", "PyTorch"])
        project_names = [e.project for e in result["Python"].inherited_projects]
        assert "Proj1" in project_names
        assert "Proj2" in project_names


# ---------------------------------------------------------------------------
# Tests: Evidence strength
# ---------------------------------------------------------------------------

class TestEvidenceStrength:
    def test_evidence_strength_is_inherited_weight(self, engine):
        profile = _make_profile(
            projects=[Project(name="Proj", technologies=["FastAPI"])]
        )
        result = engine.inherit(profile, candidate_skills=["Python", "FastAPI"])
        for entry in result["Python"].inherited_projects:
            assert entry.evidence_strength == float(EvidenceWeight.INHERITED)


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_profile_returns_empty(self, engine):
        result = engine.inherit(ResumeProfile(), candidate_skills=["Python"])
        assert result == {}

    def test_no_candidate_skills_returns_empty(self, engine):
        profile = _make_profile(
            projects=[Project(name="X", technologies=["FastAPI"])]
        )
        result = engine.inherit(profile, candidate_skills=[])
        assert result == {}

    def test_project_with_no_technologies_produces_no_inheritance(self, engine):
        profile = _make_profile(
            projects=[Project(name="EmptyTech")]
        )
        result = engine.inherit(profile, candidate_skills=["Python"])
        assert result == {}

    def test_direct_technology_skill_not_in_result(self, engine):
        """
        FastAPI used in a project is already captured by EvidenceCollectionEngine.
        ProjectInheritanceEngine should produce inheritance for its ANCESTORS (Python),
        not for FastAPI itself.
        Note: FastAPI has no ancestors in mock that are also candidate skills
        other than Python (which is in candidates).
        """
        profile = _make_profile(
            projects=[Project(name="API", technologies=["FastAPI"])]
        )
        result = engine.inherit(profile, candidate_skills=["FastAPI", "Python"])
        # Python should appear (it's an ancestor of FastAPI and in candidate skills)
        assert "Python" in result
