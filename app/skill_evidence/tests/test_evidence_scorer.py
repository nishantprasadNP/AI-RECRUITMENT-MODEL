"""
Unit tests for §5.6 EvidenceScorer.

Tests cover:
  - Score formula accuracy (raw → normalized)
  - Each evidence source contributes the correct weight
  - Normalization cap at 100.0
  - Skills with only direct mentions score in Limited Evidence range
  - Skills with full multi-source evidence score in Strong Evidence range
  - Empty inputs produce zero scores
"""

from __future__ import annotations

import pytest

from app.skill_evidence.models.evidence_models import (
    DependencyEvidence,
    EvidenceWeight,
    InheritedProjectEntry,
    InheritedProjectEvidence,
    SkillEvidence,
)
from app.skill_evidence.scoring.evidence_scorer import SCALING_FACTOR, EvidenceScorer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_evidence(
    skill: str = "Python",
    direct_mentions: int = 0,
    project_mentions=None,
    experience_mentions=None,
) -> SkillEvidence:
    return SkillEvidence(
        skill=skill,
        direct_mentions=direct_mentions,
        project_mentions=project_mentions or [],
        experience_mentions=experience_mentions or [],
    )


def make_dependency(skill: str = "Python", supporting: list = None) -> DependencyEvidence:
    return DependencyEvidence(skill=skill, supporting_skills=supporting or [])


def make_inheritance(skill: str = "Python", projects: list = None) -> InheritedProjectEvidence:
    entries = [
        InheritedProjectEntry(project=p, evidence_strength=float(EvidenceWeight.INHERITED))
        for p in (projects or [])
    ]
    return InheritedProjectEvidence(skill=skill, inherited_projects=entries)


@pytest.fixture
def scorer() -> EvidenceScorer:
    return EvidenceScorer()


# ---------------------------------------------------------------------------
# Tests: Weight contributions
# ---------------------------------------------------------------------------

class TestWeightContributions:
    def test_direct_mention_only(self, scorer):
        """Only a direct mention: raw = 1.0 → score = 1.0 × 25 = 25.0"""
        evidence = make_evidence(direct_mentions=1)
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={},
            inheritance_map={},
        )
        expected = min(100.0, float(EvidenceWeight.DIRECT) * SCALING_FACTOR)
        assert abs(result["Python"] - expected) < 0.01

    def test_one_project_mention_adds_project_weight(self, scorer):
        """direct(1.0) + project(0.8) = 1.8 → score = 1.8 × 25 = 45.0"""
        evidence = make_evidence(direct_mentions=1, project_mentions=["CAF-MAI"])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={},
            inheritance_map={},
        )
        raw = float(EvidenceWeight.DIRECT) + float(EvidenceWeight.PROJECT)
        expected = min(100.0, raw * SCALING_FACTOR)
        assert abs(result["Python"] - expected) < 0.01

    def test_experience_mention_uses_project_weight(self, scorer):
        """Experience mention uses EvidenceWeight.PROJECT (0.8) per spec."""
        evidence = make_evidence(direct_mentions=1, experience_mentions=["SWE Intern"])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={},
            inheritance_map={},
        )
        raw = float(EvidenceWeight.DIRECT) + float(EvidenceWeight.PROJECT)
        expected = min(100.0, raw * SCALING_FACTOR)
        assert abs(result["Python"] - expected) < 0.01

    def test_dependency_adds_half_weight(self, scorer):
        """Each dependency supporting skill adds EvidenceWeight.DEPENDENCY (0.5)."""
        evidence = make_evidence(direct_mentions=1)
        dependency = make_dependency(supporting=["FastAPI", "Scikit-learn"])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={"Python": dependency},
            inheritance_map={},
        )
        raw = float(EvidenceWeight.DIRECT) + 2 * float(EvidenceWeight.DEPENDENCY)
        expected = min(100.0, raw * SCALING_FACTOR)
        assert abs(result["Python"] - expected) < 0.01

    def test_inherited_project_adds_inherited_weight(self, scorer):
        """Each inherited project adds EvidenceWeight.INHERITED (0.3)."""
        evidence = make_evidence(direct_mentions=1)
        inheritance = make_inheritance(projects=["CAF-MAI"])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={},
            inheritance_map={"Python": inheritance},
        )
        raw = float(EvidenceWeight.DIRECT) + float(EvidenceWeight.INHERITED)
        expected = min(100.0, raw * SCALING_FACTOR)
        assert abs(result["Python"] - expected) < 0.01

    def test_full_evidence_scores_in_strong_range(self, scorer):
        """
        direct(1.0) + project(0.8) + dep×3(1.5) + inherited(0.3) = 3.6
        score = min(100, 3.6 × 25) = 90.0 → Expert Evidence
        """
        evidence = make_evidence(
            direct_mentions=1,
            project_mentions=["CAF-MAI"],
        )
        dependency = make_dependency(supporting=["FastAPI", "Scikit-learn", "PyTorch"])
        inheritance = make_inheritance(projects=["CAF-MAI"])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={"Python": dependency},
            inheritance_map={"Python": inheritance},
        )
        assert result["Python"] >= 70.0  # At minimum Strong Evidence


# ---------------------------------------------------------------------------
# Tests: Normalization cap
# ---------------------------------------------------------------------------

class TestNormalizationCap:
    def test_score_capped_at_100(self, scorer):
        """A very large raw score must be capped at 100."""
        evidence = make_evidence(
            direct_mentions=1,
            project_mentions=[f"Proj{i}" for i in range(10)],  # 10 × 0.8
            experience_mentions=[f"Role{i}" for i in range(10)],  # 10 × 0.8
        )
        dependency = make_dependency(supporting=[f"Skill{i}" for i in range(10)])
        inheritance = make_inheritance(projects=[f"InhProj{i}" for i in range(10)])
        result = scorer.score(
            evidence_map={"Python": evidence},
            dependency_map={"Python": dependency},
            inheritance_map={"Python": inheritance},
        )
        assert result["Python"] <= 100.0


# ---------------------------------------------------------------------------
# Tests: Multiple skills
# ---------------------------------------------------------------------------

class TestMultipleSkills:
    def test_each_skill_scored_independently(self, scorer):
        evidence_map = {
            "Python": make_evidence(direct_mentions=1, project_mentions=["Proj1"]),
            "React.js": make_evidence(direct_mentions=1),
        }
        result = scorer.score(
            evidence_map=evidence_map,
            dependency_map={},
            inheritance_map={},
        )
        assert "Python" in result
        assert "React.js" in result
        # Python has more evidence → higher score
        assert result["Python"] > result["React.js"]


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_maps_returns_empty(self, scorer):
        result = scorer.score({}, {}, {})
        assert result == {}
