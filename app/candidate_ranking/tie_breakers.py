"""
Tie-breaker comparator logic for Phase 11 Candidate Ranking Engine in ARIS V2.
"""

from functools import cmp_to_key
from typing import List
from app.candidate_scoring.models import CandidateScoreProfile


def compare_candidates(c1: CandidateScoreProfile, c2: CandidateScoreProfile) -> int:
    """
    Compares two CandidateScoreProfile objects deterministically.
    
    Order of preference (descending):
        1. overall_score
        2. hard_requirements_coverage
        3. semantic_score
        4. skill_confidence_score
        5. achievement_score
        6. candidate_name (ascending alphabetical fallback)

    Returns:
        -1 if c1 should rank HIGHER than c2 (comes first in list).
        1 if c1 should rank LOWER than c2 (comes later in list).
        0 if they are identical.
    """
    # 1. Overall Score (descending)
    if c1.overall_score != c2.overall_score:
        return -1 if c1.overall_score > c2.overall_score else 1

    # 2. Hard Requirement Coverage (descending)
    if c1.hard_requirements_coverage != c2.hard_requirements_coverage:
        return -1 if c1.hard_requirements_coverage > c2.hard_requirements_coverage else 1

    # 3. Semantic Match Score (descending)
    if c1.semantic_score != c2.semantic_score:
        return -1 if c1.semantic_score > c2.semantic_score else 1

    # 4. Skill Confidence Score (descending)
    if c1.skill_confidence_score != c2.skill_confidence_score:
        return -1 if c1.skill_confidence_score > c2.skill_confidence_score else 1

    # 5. Achievement Score (descending)
    if c1.achievement_score != c2.achievement_score:
        return -1 if c1.achievement_score > c2.achievement_score else 1

    # 6. Candidate Name (ascending alphabetical fallback)
    name1 = (c1.candidate_name or "").lower().strip()
    name2 = (c2.candidate_name or "").lower().strip()
    if name1 != name2:
        return -1 if name1 < name2 else 1

    return 0


def sort_candidates(profiles: List[CandidateScoreProfile]) -> List[CandidateScoreProfile]:
    """
    Sorts a list of CandidateScoreProfile objects deterministically.
    """
    return sorted(profiles, key=cmp_to_key(compare_candidates))
