import pytest
from app.models.resume_schema import ResumeProfile, Project
from app.experience_analysis.models import SkillEvidence
from app.experience_analysis.signal_calculator import SignalCalculator


def test_project_signal_normal():
    """Verify project signal calculations in normal cases."""
    calc = SignalCalculator()
    
    profile = ResumeProfile(
        skills=["Python"],
        projects=[Project(name="P1"), Project(name="P2"), Project(name="P3"), Project(name="P4")]
    )
    
    # 2 matching projects out of 4 (2/4 = 0.5)
    evidence_half = SkillEvidence(skill="Python", project_count=2)
    assert calc.calculate_project_signal(evidence_half, profile) == 0.5
    
    # 4 matching projects out of 4 (4/4 = 1.0)
    evidence_all = SkillEvidence(skill="Python", project_count=4)
    assert calc.calculate_project_signal(evidence_all, profile) == 1.0


def test_project_signal_safety():
    """Verify division-by-zero and None safety for project signal."""
    calc = SignalCalculator()
    evidence = SkillEvidence(skill="Python", project_count=2)
    
    # None profile
    assert calc.calculate_project_signal(evidence, None) == 0.0
    
    # None projects (Pydantic defaults to empty list)
    profile_no_projects = ResumeProfile(skills=["Python"])
    assert calc.calculate_project_signal(evidence, profile_no_projects) == 0.0
    
    # Empty projects list
    profile_empty = ResumeProfile(skills=["Python"], projects=[])
    assert calc.calculate_project_signal(evidence, profile_empty) == 0.0


def test_project_signal_clamping():
    """Verify clamping range [0.0, 1.0] for project signal."""
    calc = SignalCalculator()
    profile = ResumeProfile(
        skills=["Python"],
        projects=[Project(name="P1"), Project(name="P2")]
    )
    
    # Underflow (negative project count - though schema protects this, verify logic clamping)
    evidence_neg = SkillEvidence(skill="Python", project_count=-1)
    assert calc.calculate_project_signal(evidence_neg, profile) == 0.0
    
    # Overflow (more matched projects than total projects)
    evidence_over = SkillEvidence(skill="Python", project_count=5)
    assert calc.calculate_project_signal(evidence_over, profile) == 1.0


def test_professional_signal_no_usage():
    """Verify professional signal returns 0.0 when no professional usage or empty roles."""
    calc = SignalCalculator()
    
    # professional_usage is False
    e1 = SkillEvidence(skill="Python", professional_usage=False, roles=["Software Engineer"])
    assert calc.calculate_professional_signal(e1) == 0.0
    
    # roles is empty
    e2 = SkillEvidence(skill="Python", professional_usage=True, roles=[])
    assert calc.calculate_professional_signal(e2) == 0.0


def test_professional_signal_internship():
    """Verify professional signal returns 0.5 for internship roles."""
    calc = SignalCalculator()
    
    # Single internship role
    e1 = SkillEvidence(skill="Python", professional_usage=True, roles=["Software Engineering Intern"])
    assert calc.calculate_professional_signal(e1) == 0.5
    
    # Multiple internship roles
    e2 = SkillEvidence(skill="Python", professional_usage=True, roles=["Research Intern", "Teaching Assistant", "Co-op"])
    assert calc.calculate_professional_signal(e2) == 0.5


def test_professional_signal_full_time():
    """Verify professional signal returns 1.0 for full-time roles."""
    calc = SignalCalculator()
    
    # Single full-time role
    e1 = SkillEvidence(skill="Python", professional_usage=True, roles=["Software Engineer"])
    assert calc.calculate_professional_signal(e1) == 1.0
    
    # Mixed roles: internship + full-time (should return 1.0)
    e2 = SkillEvidence(skill="Python", professional_usage=True, roles=["Research Intern", "Senior Developer"])
    assert calc.calculate_professional_signal(e2) == 1.0


def test_professional_signal_case_insensitivity():
    """Verify internship keyword detection is case-insensitive."""
    calc = SignalCalculator()
    
    # uppercase keyword
    e1 = SkillEvidence(skill="Python", professional_usage=True, roles=["RESEARCH INTERN"])
    assert calc.calculate_professional_signal(e1) == 0.5
    
    # mixed case keyword
    e2 = SkillEvidence(skill="Python", professional_usage=True, roles=["Co-Op"])
    assert calc.calculate_professional_signal(e2) == 0.5


def test_depth_signal_normalization():
    """Verify depth signal dynamic normalization."""
    calc = SignalCalculator()
    
    # 8 mentions out of 10 maximum (8/10 = 0.8)
    e1 = SkillEvidence(skill="React", skill_mentions=8)
    assert pytest.approx(calc.calculate_depth_signal(e1, 10)) == 0.8
    
    # 0 mentions
    e2 = SkillEvidence(skill="React", skill_mentions=0)
    assert calc.calculate_depth_signal(e2, 10) == 0.0
    
    # Invalid max mentions (<= 0) should safely return 0.0
    assert calc.calculate_depth_signal(e1, 0) == 0.0
    assert calc.calculate_depth_signal(e1, -5) == 0.0


def test_depth_signal_clamping():
    """Verify depth signal clamping to [0.0, 1.0]."""
    calc = SignalCalculator()
    
    # Mentions exceed max mentions (15/10 = 1.5 -> clamped to 1.0)
    e1 = SkillEvidence(skill="React", skill_mentions=15)
    assert calc.calculate_depth_signal(e1, 10) == 1.0
    
    # Negative mentions (clamped to 0.0)
    e2 = SkillEvidence(skill="React", skill_mentions=-3)
    assert calc.calculate_depth_signal(e2, 10) == 0.0


def test_achievement_signal_normalization():
    """Verify achievement signal normalization using denominator 5."""
    calc = SignalCalculator()
    
    # 1 mention (1/5 = 0.2)
    e1 = SkillEvidence(skill="Python", achievement_mentions=1)
    assert pytest.approx(calc.calculate_achievement_signal(e1)) == 0.2
    
    # 3 mentions (3/5 = 0.6)
    e2 = SkillEvidence(skill="Python", achievement_mentions=3)
    assert pytest.approx(calc.calculate_achievement_signal(e2)) == 0.6
    
    # 0 mentions
    e3 = SkillEvidence(skill="Python", achievement_mentions=0)
    assert calc.calculate_achievement_signal(e3) == 0.0


def test_achievement_signal_clamping():
    """Verify achievement signal clamping to [0.0, 1.0]."""
    calc = SignalCalculator()
    
    # 5 mentions (5/5 = 1.0)
    e1 = SkillEvidence(skill="Python", achievement_mentions=5)
    assert calc.calculate_achievement_signal(e1) == 1.0
    
    # 8 mentions (8/5 = 1.6 -> clamped to 1.0)
    e2 = SkillEvidence(skill="Python", achievement_mentions=8)
    assert calc.calculate_achievement_signal(e2) == 1.0
    
    # Negative mentions (clamped to 0.0)
    e3 = SkillEvidence(skill="Python", achievement_mentions=-2)
    assert calc.calculate_achievement_signal(e3) == 0.0
