"""
Unit tests for Phase 9 Achievement Analyzer.
"""

import pytest
from app.schemas.resume_schema import ResumeProfile, Education, Experience, Project
from app.achievement_analysis.models import AchievementProfile, AchievementDetail
from app.achievement_analysis.achievement_detector import AchievementDetector, AchievementAnalyzer
from app.achievement_analysis.scoring import AchievementScorer
from app.achievement_analysis.exceptions import AchievementAnalysisError, DetectionError


def test_achievement_detector():
    detector = AchievementDetector()

    # Create mock ResumeProfile with diverse signals
    mock_profile = ResumeProfile(
        name="Candidate A",
        skills=["Python"],
        education=[
            Education(
                degree="B.Tech",
                institution="Indian Institute of Technology, Madras",
                field="Computer Science",
                graduation_year="2024"
            )
        ],
        experience=[
            Experience(
                role="Co-Founder & CTO",
                company="TechStartup",
                start_date="2024",
                end_date="Present",
                duration="2 years",
                description="Built core products from scratch and led a team of 5 developers. Joined Y Combinator W24."
            )
        ],
        projects=[
            Project(
                name="Deep Learning Library",
                technologies=["Python", "PyTorch"],
                description="Built a novel framework and published a paper at CVPR. Won 1st place in AI Hackathon."
            )
        ],
        certifications=[],
        achievements=[
            "AIR 150 in JEE Advanced",
            "Kaggle Grandmaster"
        ]
    )

    detected = detector.detect_achievements(mock_profile)

    # Check academic detections
    academic_titles = [item["title"] for item in detected["academic"]]
    assert any("Tier-1 Institution" in title or "IIT" in title for title in academic_titles)
    assert any("JEE" in title for title in academic_titles)

    # Check technical detections
    tech_titles = [item["title"] for item in detected["technical"]]
    assert any("Hackathon" in title or "won" in title or "1st" in title for title in tech_titles)
    assert any("Kaggle" in title for title in tech_titles)

    # Check research detections
    research_titles = [item["title"] for item in detected["research"]]
    assert any("published" in title or "CVPR" in title for title in research_titles)

    # Check leadership detections
    leader_titles = [item["title"] for item in detected["leadership"]]
    assert any("team of" in title or "led" in title for title in leader_titles)

    # Check entrepreneurship detections
    ent_titles = [item["title"] for item in detected["entrepreneurship"]]
    assert any("CTO" in title or "Founder" in title for title in ent_titles)
    assert any("Y Combinator" in title or "YC" in title for title in ent_titles)


def test_achievement_scorer():
    scorer = AchievementScorer()

    # Setup detected raw items
    detected_raw = {
        "academic": [
            {
                "title": "Graduated from Tier-1 Institution: IIT Madras",
                "source_section": "education",
                "source_detail": "B.Tech at IIT Madras",
                "match_type": "Tier-1 University"
            },
            {
                "title": "AIR 150 in JEE Advanced",
                "source_section": "achievements",
                "source_detail": "Entry #1",
                "match_type": "JEE/AIR Rank"
            }
        ],
        "technical": [
            {
                "title": "Won 1st place in AI Hackathon",
                "source_section": "projects",
                "source_detail": "Deep Learning Library",
                "match_type": "Hackathon Win"
            }
        ],
        "research": [],
        "leadership": [],
        "entrepreneurship": []
    }

    profile = scorer.score_profile(detected_raw)

    assert isinstance(profile, AchievementProfile)
    assert profile.category_scores["academic"] > 0
    assert profile.category_scores["technical"] > 0
    assert profile.category_scores["research"] == 0.0

    # Academic score calculations: IIT (3.5) + JEE AIR 150 (4.5) = 8.0
    assert profile.category_scores["academic"] == 8.0
    # Technical score calculations: Hackathon Win (4.0) = 4.0
    assert profile.category_scores["technical"] == 4.0

    # Overall score: Max category (academic = 8.0) * 0.6 + sum of others (technical = 4.0) * 0.4 = 4.8 + 1.6 = 6.4
    assert profile.achievement_score == 6.4

    # Ensure traces are generated
    assert len(profile.explanation_traces) > 0
    assert any("Overall Achievement Score" in trace for trace in profile.explanation_traces)
    assert any("IIT" in trace or "JEE" in trace for trace in profile.explanation_traces)


def test_achievement_analyzer_end_to_end():
    analyzer = AchievementAnalyzer()
    
    mock_profile = ResumeProfile(
        name="John Doe",
        skills=["Python"],
        education=[],
        experience=[],
        projects=[],
        certifications=[],
        achievements=[]
    )

    profile = analyzer.analyze(mock_profile)
    assert profile.achievement_score == 0.0
    assert len(profile.academic) == 0

    with pytest.raises(DetectionError):
        analyzer.analyze(None)
