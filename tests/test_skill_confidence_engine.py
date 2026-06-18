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
    assert prof.professional_signal == 0.0
    assert prof.depth_signal == 1.0
    assert prof.complexity_signal == 0.0
    
    # Weighted score: 0.45 * 1.0 (depth) = 0.45 -> 45.0 -> Moderate Evidence
    assert prof.confidence_score == 45.0
    assert prof.confidence_level == "Moderate Evidence"
    assert prof.skill_tier == "Intermediate"
    
    assert prof.evidence_summary["project_count"] == 0
    assert prof.evidence_summary["projects_used_in"] == []
    assert prof.evidence_summary["direct_mentions"] == 1  # 1 mention in skills section
    assert prof.evidence_summary["supporting_technologies"] == []
    assert prof.evidence_summary["professional_roles"] == []


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
    
    # 1. Professional Signal: roles contains 'Python Backend Intern'.
    # Contains 'Intern', so it detects as internship -> 0.5
    assert python_profile.professional_signal == 0.5
    
    # 2. Depth Signal: Mentions counts:
    # Python: skills (1), project technologies (1), experience desc (1), total = 3.
    # Max mentions in resume is for Python: 3 mentions.
    # depth_signal = 3 / 3 = 1.0
    assert python_profile.depth_signal == 1.0
    
    # 3. Complexity Signal:
    # Project Alpha complexity score: 9.75 -> Normalized = 0.975
    assert pytest.approx(python_profile.complexity_signal) == 0.975
    
    # 4. Confidence score:
    # 0.45 * 1.0 (depth) + 0.30 * 0.5 (prof) + 0.25 * 0.975 (comp) = 0.45 + 0.15 + 0.24375 = 0.84375 -> 84.375
    assert pytest.approx(python_profile.confidence_score) == 84.375
    assert python_profile.confidence_level == "Very Strong Evidence"
    assert python_profile.skill_tier == "Advanced"
    
    # 5. Schema verification:
    assert python_profile.evidence_summary["project_count"] == 1
    assert python_profile.evidence_summary["projects_used_in"] == ["Project Alpha"]
    assert python_profile.evidence_summary["direct_mentions"] == 3
    assert python_profile.evidence_summary["supporting_technologies"] == []
    assert python_profile.evidence_summary["professional_roles"] == ["Python Backend Intern"]
