import pytest
from app.candidate_scoring.score_calculators import ComponentScoreCalculators
from app.experience_analysis.models import SkillConfidenceProfile


def make_profile(skill: str, confidence: float) -> SkillConfidenceProfile:
    """Minimal SkillConfidenceProfile with only confidence_score set."""
    return SkillConfidenceProfile(
        skill=skill,
        confidence_score=confidence,
        confidence_level="Basic",
        professional_signal=0.0,
        depth_signal=0.0,
        complexity_signal=0.0,
        skill_tier="Tier 3",
        evidence_summary={}
    )


def test_empty_confidence_profiles():
    # 1. Empty confidence_profiles → returns 0.
    assert ComponentScoreCalculators.calculate_skills_score({}) == 0.0


def test_less_than_10_skills():
    # 2. Less than 10 skills (e.g. 6 skills) → average all 6.
    profiles = {
        f"Skill{i}": make_profile(f"Skill{i}", 60.0 + i)
        for i in range(6)
    }
    # Scores: 60, 61, 62, 63, 64, 65.
    # Sum: 375. Average: 375 / 6 = 62.5.
    score = ComponentScoreCalculators.calculate_skills_score(profiles)
    assert score == pytest.approx(62.5, abs=0.05)


def test_exactly_10_skills():
    # 3. Exactly 10 skills → average all 10.
    profiles = {
        f"Skill{i}": make_profile(f"Skill{i}", 70.0 + i)
        for i in range(10)
    }
    # Scores: 70 to 79.
    # Sum: 745. Average: 74.5.
    score = ComponentScoreCalculators.calculate_skills_score(profiles)
    assert score == pytest.approx(74.5, abs=0.05)


def test_more_than_10_skills():
    # 4. More than 10 skills → average only the highest 10.
    # Create 12 profiles with confidence scores from 50 to 61
    profiles = {
        f"Skill{i}": make_profile(f"Skill{i}", 50.0 + i)
        for i in range(12)
    }
    # Scores: 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61.
    # Sorted descending: 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50.
    # Highest 10: 61, 60, 59, 58, 57, 56, 55, 54, 53, 52.
    # Sum of highest 10: 565.
    # Average: 56.5.
    score = ComponentScoreCalculators.calculate_skills_score(profiles)
    assert score == pytest.approx(56.5, abs=0.05)


def test_tool_filtering():
    # 5. Tool filtering
    # VS Code = 95
    # Python = 70
    # React.js = 68
    profiles = {
        "VS Code": make_profile("VS Code", 95.0),
        "Python": make_profile("Python", 70.0),
        "React.js": make_profile("React.js", 68.0)
    }
    # VS Code is excluded because it's a tool/editor.
    # Remaining: Python (70.0) and React.js (68.0).
    # Average: (70 + 68) / 2 = 69.0.
    score = ComponentScoreCalculators.calculate_skills_score(profiles)
    assert score == pytest.approx(69.0, abs=0.05)


def test_verify_sorting():
    # 6. Verify sorting
    # Highest confidence skills are always selected.
    # Mix of 15 skills: 5 tools (should be excluded), 10 core skills.
    # Core scores: 40, 50, 60, 70, 75, 80, 85, 90, 95, 100.
    # Let's add 2 more lower core skills (30, 20) to ensure they are excluded since they are lowest.
    profiles = {
        "Python": make_profile("Python", 100.0),
        "React.js": make_profile("React.js", 95.0),
        "Django": make_profile("Django", 90.0),
        "PostgreSQL": make_profile("PostgreSQL", 85.0),
        "MongoDB": make_profile("MongoDB", 80.0),
        "FastAPI": make_profile("FastAPI", 75.0),
        "Flask": make_profile("Flask", 70.0),
        "HTML": make_profile("HTML", 60.0),
        "CSS": make_profile("CSS", 50.0),
        "TypeScript": make_profile("TypeScript", 40.0),
        
        # Lower core skills (should be sorted out of top 10)
        "C++": make_profile("C++", 30.0),
        "Java": make_profile("Java", 20.0),

        # Tool/Editor/IDE skills (should be ignored by filter)
        "VS Code": make_profile("VS Code", 99.0),
        "PyCharm": make_profile("PyCharm", 98.0),
        "Android Studio": make_profile("Android Studio", 97.0),
    }

    # Selected top 10 core skills should be:
    # Python (100.0), React.js (95.0), Django (90.0), PostgreSQL (85.0), MongoDB (80.0),
    # FastAPI (75.0), Flask (70.0), HTML (60.0), CSS (50.0), TypeScript (40.0).
    # Sum: 100+95+90+85+80+75+70+60+50+40 = 745.
    # Average: 74.5.
    score = ComponentScoreCalculators.calculate_skills_score(profiles)
    assert score == pytest.approx(74.5, abs=0.05)
