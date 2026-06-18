import pytest
from typing import Set, List, Dict, Optional
from app.models.resume_schema import ResumeProfile, Project, Experience
from app.experience_analysis.models import SkillConfidenceProfile
from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.experience_analysis.complexity_calculator import ComplexityCalculator
from app.experience_analysis.signal_calculator import SignalCalculator
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator
from app.experience_analysis.skill_confidence_engine import SkillConfidenceEngine


@pytest.fixture
def confidence_engine():
    """Provides a SkillConfidenceEngine instance initialized with real sub-components."""
    collector = SkillEvidenceCollector()
    complexity = ComplexityCalculator()
    signals = SignalCalculator()
    confidence = SkillConfidenceCalculator()
    return SkillConfidenceEngine(
        evidence_collector=collector,
        complexity_calculator=complexity,
        signal_calculator=signals,
        confidence_calculator=confidence
    )


def test_engine_empty_resume(confidence_engine):
    """Verify engine handles empty/None profiles safely and returns empty dict."""
    # None profile
    assert confidence_engine.analyze(None) == {}

    # Empty skills list
    empty_profile = ResumeProfile(skills=[], projects=[])
    assert confidence_engine.analyze(empty_profile) == {}


def test_engine_skill_no_evidence(confidence_engine):
    """Verify that a skill with no evidence gets calculated with base scores and signals = 0.0."""
    profile = ResumeProfile(
        skills=["Git"],
        projects=[]
    )
    
    results = confidence_engine.analyze(profile)
    assert "Git" in results
    prof = results["Git"]
    
    assert isinstance(prof, SkillConfidenceProfile)
    assert prof.project_signal == 0.0
    assert prof.professional_signal == 0.0
    assert prof.depth_signal == 1.0
    assert prof.complexity_signal == 0.0
    assert prof.achievement_signal == 0.0
    # Weighted score: 0.20 * 1.0 (depth) = 0.20 -> 20.0 -> Weak Evidence
    assert prof.confidence_score == 20.0
    assert prof.confidence_level == "Weak Evidence"
    assert prof.evidence_summary["projects"] == 0
    assert prof.evidence_summary["mentions"] == 1  # 1 mention in skills section


def test_engine_end_to_end(confidence_engine):
    """Verify end-to-end confidence score aggregation, thresholds, and evidence summary propagation."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI"],
        projects=[
            Project(
                name="Project Alpha",
                technologies=["Python", "FastAPI", "Docker", "AWS"],
                description="designed and implemented a highly concurrent distributed pipeline."
            )
        ],
        experience=[
            Experience(
                role="Python Backend Intern",
                description="Used Python and FastAPI to build cloud microservices."
            )
        ],
        achievements=[
            "Winner of Python coding competition."
        ]
    )

    results = confidence_engine.analyze(profile)
    
    assert "Python" in results
    python_profile = results["Python"]
    
    # 1. Project Signal: 1 matching project / 1 project = 1.0
    assert python_profile.project_signal == 1.0
    
    # 2. Professional Signal: roles contains 'Python Backend Intern'.
    # Contains 'Intern', so it detects as internship -> 0.5
    assert python_profile.professional_signal == 0.5
    
    # 3. Depth Signal: Mentions counts:
    # Python: skills (1), project technologies (1), experience desc (1), total = 3.
    # Max mentions in resume is for Python: 3 mentions (skills: Python, tech: Python, exp: Python. FastAPI has 2).
    # depth_signal = 3 / 3 = 1.0
    assert python_profile.depth_signal == 1.0
    
    # 4. Complexity Signal:
    # Project Alpha complexity check:
    # Base: 2.0
    # Categories: Python (BACKEND), FastAPI (BACKEND), Docker (DEVOPS), AWS (CLOUD) -> 3 categories -> +3.0
    # Domain: distributed, concurrency, pipeline -> 3 matches -> capped at 2.0
    # Deployment: AWS, Docker -> +2.0
    # Indicators: designed, implemented, pipeline -> 3 matches -> +0.75
    # Advanced: None -> +0.0
    # Total complexity score = 2.0 + 3.0 + 2.0 + 2.0 + 0.75 = 9.75
    # Normalized complexity signal = 9.75 / 10.0 = 0.975
    assert pytest.approx(python_profile.complexity_signal) == 0.975
    
    # 5. Achievement Signal: 1 achievement mention / 5 = 0.2
    assert python_profile.achievement_signal == 0.2
    
    # 6. Confidence score:
    # 0.30*1.0 + 0.25*0.5 + 0.20*1.0 + 0.15*0.975 + 0.10*0.2 = 0.79125 -> 79.125
    assert pytest.approx(python_profile.confidence_score) == 79.125
    assert python_profile.confidence_level == "Very Strong Evidence"  # (75.0, 100.0]
    
    # 7. Schema verification:
    assert python_profile.evidence_summary["projects"] == 1
    assert python_profile.evidence_summary["mentions"] == 3
    assert python_profile.evidence_summary["professional_usage"] is True
    assert python_profile.evidence_summary["professional_roles"] == ["Python Backend Intern"]
