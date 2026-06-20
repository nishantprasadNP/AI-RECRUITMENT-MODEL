"""
Unit tests for Phase 11 Candidate Ranking Engine.
"""

import pytest
from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_ranking.models import RankedCandidate, RankedCandidateList
from app.candidate_ranking.ranking_engine import CandidateRankingEngine
from app.candidate_ranking.tie_breakers import sort_candidates, compare_candidates
from app.candidate_ranking.exceptions import RankingEngineError


def test_compare_candidates():
    # Base profiles
    p1 = CandidateScoreProfile(
        candidate_name="Alice",
        overall_score=85.0,
        component_scores={"skills": 80.0},
        weight_breakdown={"skills": 1.0},
        explanation=[],
        hard_requirements_coverage=1.0,
        semantic_score=0.85,
        skill_confidence_score=80.0,
        achievement_score=8.0
    )

    # 1. Test different overall_score (descending)
    p2 = p1.model_copy(update={"candidate_name": "Bob", "overall_score": 80.0})
    assert compare_candidates(p1, p2) == -1  # p1 is better, ranks higher
    assert compare_candidates(p2, p1) == 1

    # 2. Test different hard_requirements_coverage (descending)
    p3 = p1.model_copy(update={"candidate_name": "Charlie", "hard_requirements_coverage": 0.8})
    assert compare_candidates(p1, p3) == -1  # p1 has higher coverage
    assert compare_candidates(p3, p1) == 1

    # 3. Test different semantic_score (descending)
    p4 = p1.model_copy(update={"candidate_name": "David", "semantic_score": 0.75})
    assert compare_candidates(p1, p4) == -1  # p1 has higher semantic alignment
    assert compare_candidates(p4, p1) == 1

    # 4. Test different skill_confidence_score (descending)
    p5 = p1.model_copy(update={"candidate_name": "Eve", "skill_confidence_score": 70.0})
    assert compare_candidates(p1, p5) == -1  # p1 has higher skill confidence
    assert compare_candidates(p5, p1) == 1

    # 5. Test different achievement_score (descending)
    p6 = p1.model_copy(update={"candidate_name": "Frank", "achievement_score": 5.0})
    assert compare_candidates(p1, p6) == -1  # p1 has higher achievement score
    assert compare_candidates(p6, p1) == 1

    # 6. Test candidate_name (ascending alphabetical fallback)
    p7 = p1.model_copy(update={"candidate_name": "Zach"})
    # Alice < Zach, so Alice (p1) ranks higher
    assert compare_candidates(p1, p7) == -1
    assert compare_candidates(p7, p1) == 1

    # Identical profiles
    p8 = p1.model_copy()
    assert compare_candidates(p1, p8) == 0


def test_sort_candidates():
    p_alice = CandidateScoreProfile(
        candidate_name="Alice", overall_score=85.0, component_scores={}, weight_breakdown={},
        explanation=[], hard_requirements_coverage=1.0, semantic_score=0.85,
        skill_confidence_score=80.0, achievement_score=8.0
    )
    p_bob = CandidateScoreProfile(
        candidate_name="Bob", overall_score=85.0, component_scores={}, weight_breakdown={},
        explanation=[], hard_requirements_coverage=0.9, semantic_score=0.85,
        skill_confidence_score=80.0, achievement_score=8.0
    )
    p_charlie = CandidateScoreProfile(
        candidate_name="Charlie", overall_score=90.0, component_scores={}, weight_breakdown={},
        explanation=[], hard_requirements_coverage=0.9, semantic_score=0.85,
        skill_confidence_score=80.0, achievement_score=8.0
    )
    p_david = CandidateScoreProfile(
        candidate_name="David", overall_score=85.0, component_scores={}, weight_breakdown={},
        explanation=[], hard_requirements_coverage=1.0, semantic_score=0.85,
        skill_confidence_score=80.0, achievement_score=9.0
    )

    # Expected order:
    # 1. Charlie (overall_score = 90.0)
    # 2. David (overall_score = 85.0, coverage = 1.0, semantic = 0.85, skill = 80.0, achievement = 9.0)
    # 3. Alice (overall_score = 85.0, coverage = 1.0, semantic = 0.85, skill = 80.0, achievement = 8.0)
    # 4. Bob (overall_score = 85.0, coverage = 0.9)
    sorted_profiles = sort_candidates([p_bob, p_alice, p_charlie, p_david])
    assert [p.candidate_name for p in sorted_profiles] == ["Charlie", "David", "Alice", "Bob"]


def test_ranking_engine_rank():
    engine = CandidateRankingEngine()

    p_best = CandidateScoreProfile(
        candidate_name="Best Candidate",
        overall_score=95.0,
        component_scores={
            "semantic": 90.0,
            "skills": 95.0,
            "experience": 90.0,
            "achievements": 9.0
        },
        weight_breakdown={},
        explanation=[],
        hard_requirements_coverage=1.0,
        semantic_score=0.9,
        skill_confidence_score=95.0,
        achievement_score=9.0
    )

    p_weak = CandidateScoreProfile(
        candidate_name="Weak Candidate",
        overall_score=45.0,
        component_scores={
            "semantic": 40.0,
            "skills": 45.0,
            "experience": 40.0,
            "achievements": 2.0
        },
        weight_breakdown={},
        explanation=["Hard Requirements: Failed compliance check. Missing required skills: ['Go']"],
        hard_requirements_coverage=0.5,
        semantic_score=0.4,
        skill_confidence_score=45.0,
        achievement_score=2.0
    )

    ranked_list = engine.rank([p_weak, p_best])
    assert isinstance(ranked_list, RankedCandidateList)
    assert len(ranked_list.root) == 2

    # Check rank order
    first = ranked_list.root[0]
    second = ranked_list.root[1]

    assert first.rank == 1
    assert first.candidate_name == "Best Candidate"
    assert first.overall_score == 95.0
    assert len(first.strengths) > 0
    assert len(first.concerns) == 0

    assert second.rank == 2
    assert second.candidate_name == "Weak Candidate"
    assert second.overall_score == 45.0
    assert len(second.strengths) > 0  # might fallback
    assert len(second.concerns) > 0
    assert "Missing some critical hard requirements" in second.concerns[0]
    assert "Did not pass critical hard requirement check." in second.concerns


def test_ranked_candidate_model_aliasing():
    # Instantiate using aliases
    c1 = RankedCandidate(
        rank=1,
        candidate="Alice Smith",
        score=92.5,
        strengths=["Fast learner"],
        concerns=[]
    )
    assert c1.candidate_name == "Alice Smith"
    assert c1.overall_score == 92.5

    # Test serialization includes alias names (candidate/score)
    serialized = c1.model_dump(by_alias=True)
    assert "candidate" in serialized
    assert "score" in serialized
    assert serialized["candidate"] == "Alice Smith"
    assert serialized["score"] == 92.5


def test_ranking_engine_error():
    engine = CandidateRankingEngine()
    with pytest.raises(RankingEngineError):
        engine.rank(None)
