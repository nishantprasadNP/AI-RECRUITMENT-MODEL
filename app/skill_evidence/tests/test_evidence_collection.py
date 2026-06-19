"""
Unit tests for §5.1 EvidenceCollectionEngine.

Tests cover:
  - Direct mention counting from skills section
  - Project technology matching (boundary-safe)
  - Experience technology + description matching
  - Skill deduplication (case-insensitive)
  - Empty profile handling
  - Skills with special characters (C++, .NET, Go)
"""

from __future__ import annotations

import pytest

from app.schemas.resume_schema import Experience, Project, ResumeProfile
from app.skill_evidence.engines.evidence_collection_engine import EvidenceCollectionEngine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine() -> EvidenceCollectionEngine:
    return EvidenceCollectionEngine()


def _make_profile(
    skills=None,
    projects=None,
    experience=None,
) -> ResumeProfile:
    """Helper to build a minimal ResumeProfile."""
    return ResumeProfile(
        skills=skills or [],
        projects=projects or [],
        experience=experience or [],
    )


# ---------------------------------------------------------------------------
# Tests: Direct mentions
# ---------------------------------------------------------------------------

class TestDirectMentions:
    def test_skill_listed_once_has_direct_mention_of_one(self, engine):
        profile = _make_profile(skills=["Python"])
        result = engine.collect(profile)
        assert result["Python"].direct_mentions == 1

    def test_multiple_skills_each_have_direct_mention_of_one(self, engine):
        profile = _make_profile(skills=["Python", "FastAPI", "React.js"])
        result = engine.collect(profile)
        assert result["Python"].direct_mentions == 1
        assert result["FastAPI"].direct_mentions == 1
        assert result["React.js"].direct_mentions == 1


# ---------------------------------------------------------------------------
# Tests: Project technology matching
# ---------------------------------------------------------------------------

class TestProjectMentions:
    def test_skill_in_project_technologies(self, engine):
        profile = _make_profile(
            skills=["FastAPI"],
            projects=[Project(name="MyApp", technologies=["FastAPI", "PostgreSQL"])],
        )
        result = engine.collect(profile)
        assert "MyApp" in result["FastAPI"].project_mentions

    def test_skill_not_in_project_technologies(self, engine):
        profile = _make_profile(
            skills=["Django"],
            projects=[Project(name="MyApp", technologies=["FastAPI", "PostgreSQL"])],
        )
        result = engine.collect(profile)
        assert result["Django"].project_mentions == []

    def test_skill_appears_in_multiple_projects(self, engine):
        profile = _make_profile(
            skills=["Python"],
            projects=[
                Project(name="Proj1", technologies=["Python", "Flask"]),
                Project(name="Proj2", technologies=["Python", "Django"]),
            ],
        )
        result = engine.collect(profile)
        assert "Proj1" in result["Python"].project_mentions
        assert "Proj2" in result["Python"].project_mentions

    def test_project_not_counted_twice(self, engine):
        """Same project should appear at most once in project_mentions."""
        profile = _make_profile(
            skills=["Python"],
            projects=[Project(name="Proj1", technologies=["Python", "Python"])],
        )
        result = engine.collect(profile)
        assert result["Python"].project_mentions.count("Proj1") == 1

    def test_case_insensitive_tech_matching(self, engine):
        profile = _make_profile(
            skills=["fastapi"],
            projects=[Project(name="API", technologies=["FastAPI"])],
        )
        result = engine.collect(profile)
        assert "API" in result["fastapi"].project_mentions

    def test_word_boundary_prevents_false_positive(self, engine):
        """'Go' should NOT match 'MongoDB'."""
        profile = _make_profile(
            skills=["Go"],
            projects=[Project(name="DB App", technologies=["MongoDB"])],
        )
        result = engine.collect(profile)
        assert result["Go"].project_mentions == []


# ---------------------------------------------------------------------------
# Tests: Experience matching
# ---------------------------------------------------------------------------

class TestExperienceMentions:
    def test_skill_in_experience_description(self, engine):
        profile = _make_profile(
            skills=["React.js"],
            experience=[
                Experience(
                    role="Frontend Developer",
                    company="Acme",
                    description="Built UI components using React.js and TypeScript.",
                )
            ],
        )
        result = engine.collect(profile)
        assert "Frontend Developer" in result["React.js"].experience_mentions

    def test_skill_not_in_experience(self, engine):
        profile = _make_profile(
            skills=["Kubernetes"],
            experience=[
                Experience(role="Backend Dev", description="Worked on Django REST APIs.")
            ],
        )
        result = engine.collect(profile)
        assert result["Kubernetes"].experience_mentions == []

    def test_experience_deduplication(self, engine):
        """Same role should not appear twice even if skill matches multiple fields."""
        profile = _make_profile(
            skills=["Python"],
            experience=[
                Experience(
                    role="Data Scientist",
                    description="Used Python for data analysis. Python is great.",
                )
            ],
        )
        result = engine.collect(profile)
        assert result["Python"].experience_mentions.count("Data Scientist") == 1


# ---------------------------------------------------------------------------
# Tests: Skill deduplication
# ---------------------------------------------------------------------------

class TestSkillDeduplication:
    def test_duplicate_skills_case_insensitive(self, engine):
        profile = _make_profile(skills=["Python", "python", "PYTHON"])
        result = engine.collect(profile)
        # Only one entry should exist
        assert len(result) == 1
        assert "Python" in result

    def test_preserves_first_casing(self, engine):
        profile = _make_profile(skills=["Python", "PYTHON"])
        result = engine.collect(profile)
        assert "Python" in result


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_profile_returns_empty(self, engine):
        result = engine.collect(ResumeProfile())
        assert result == {}

    def test_empty_skills_returns_empty(self, engine):
        profile = _make_profile(
            skills=[],
            projects=[Project(name="X", technologies=["Python"])],
        )
        result = engine.collect(profile)
        assert result == {}

    def test_none_profile_returns_empty(self, engine):
        result = engine.collect(None)
        assert result == {}

    def test_skill_with_special_chars(self, engine):
        """C++ should match 'C++' in technologies without regex errors."""
        profile = _make_profile(
            skills=["C++"],
            projects=[Project(name="Game", technologies=["C++", "OpenGL"])],
        )
        result = engine.collect(profile)
        assert "Game" in result["C++"].project_mentions

    def test_dotnet_skill(self, engine):
        profile = _make_profile(
            skills=[".NET"],
            projects=[Project(name="Enterprise", technologies=[".NET", "C#"])],
        )
        result = engine.collect(profile)
        assert "Enterprise" in result[".NET"].project_mentions
