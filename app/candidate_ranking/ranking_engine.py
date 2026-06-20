"""
Candidate Ranking Engine for Phase 11 in ARIS V2.
"""

import logging
from typing import List
from app.candidate_scoring.models import CandidateScoreProfile
from app.candidate_ranking.models import RankedCandidate, RankedCandidateList
from app.candidate_ranking.tie_breakers import sort_candidates
from app.candidate_ranking.exceptions import RankingEngineError

logger = logging.getLogger("aris.candidate_ranking.engine")


class CandidateRankingEngine:
    """
    Ranks multiple candidates deterministically based on their weighted scores
    and tie-breaker signals, outputting strengths and concerns for each.
    """
    def __init__(self) -> None:
        pass

    def rank(self, profiles: List[CandidateScoreProfile]) -> RankedCandidateList:
        """
        Consumes a list of CandidateScoreProfiles, sorts them deterministically,
        extracts strengths/concerns, and returns a RankedCandidateList.

        Args:
            profiles: A list of candidate score profiles.

        Returns:
            A RankedCandidateList containing RankedCandidate objects.

        Raises:
            RankingEngineError: If ranking computation fails.
        """
        if profiles is None:
            raise RankingEngineError("Profiles list cannot be None.")

        try:
            logger.info("Ranking %d candidate profiles...", len(profiles))
            # Sort candidate profiles using deterministic tie-breaker hierarchy
            sorted_profiles = sort_candidates(profiles)

            ranked_list = []
            for rank_idx, profile in enumerate(sorted_profiles, start=1):
                strengths = self._extract_strengths(profile)
                concerns = self._extract_concerns(profile)

                ranked_c = RankedCandidate(
                    rank=rank_idx,
                    candidate=profile.candidate_name,
                    score=profile.overall_score,
                    strengths=strengths,
                    concerns=concerns
                )
                ranked_list.append(ranked_c)

            return RankedCandidateList(ranked_list)

        except Exception as e:
            raise RankingEngineError(f"Failed to rank candidates: {e}") from e

    def _extract_strengths(self, profile: CandidateScoreProfile) -> List[str]:
        """
        Heuristically extracts strengths from candidate score profiles.
        """
        strengths = []
        scores = profile.component_scores

        if "semantic" in scores and scores["semantic"] >= 80.0:
            strengths.append(f"High semantic alignment with requirements (score: {scores['semantic']:.1f}%).")
        
        if "skills" in scores and scores["skills"] >= 80.0:
            strengths.append(f"Strong verified skill confidence (score: {scores['skills']:.1f}%).")

        if "experience" in scores and scores["experience"] >= 80.0:
            strengths.append(f"Solid experience duration matching job expectations (score: {scores['experience']:.1f}%).")

        if "achievements" in scores and scores["achievements"] >= 80.0:
            strengths.append(f"Exceptional achievements and standout signals (score: {scores['achievements']:.1f}%).")

        if "projects" in scores and scores["projects"] >= 80.0:
            strengths.append(f"Excellent hands-on project portfolio (score: {scores['projects']:.1f}%).")

        if "leadership" in scores and scores["leadership"] >= 80.0:
            strengths.append("Demonstrated leadership, mentorship, or team management capabilities.")

        # Default fallback if no component scored >= 80
        if not strengths:
            # Find the highest component score
            if scores:
                best_comp = max(scores, key=scores.get)
                if scores[best_comp] >= 60.0:
                    strengths.append(f"Good performance in {best_comp} component (score: {scores[best_comp]:.1f}%).")
            if not strengths:
                strengths.append("Consistent, balanced performance across components.")

        return strengths

    def _extract_concerns(self, profile: CandidateScoreProfile) -> List[str]:
        """
        Heuristically extracts concerns from candidate score profiles.
        """
        concerns = []
        scores = profile.component_scores

        # Check hard requirements coverage
        if profile.hard_requirements_coverage < 1.0:
            pct = profile.hard_requirements_coverage * 100.0
            concerns.append(f"Missing some critical hard requirements (coverage: {pct:.1f}%).")

        if "semantic" in scores and scores["semantic"] < 50.0:
            concerns.append(f"Low semantic similarity to core role specifications (score: {scores['semantic']:.1f}%).")

        if "skills" in scores and scores["skills"] < 50.0:
            concerns.append(f"Limited verified evidence for required skills (score: {scores['skills']:.1f}%).")

        if "experience" in scores and scores["experience"] < 50.0:
            concerns.append(f"Experience duration falls short of target requirements (score: {scores['experience']:.1f}%).")

        # Check if they failed hard requirements check completely
        failed_hard = False
        for expl in profile.explanation:
            if "Hard Requirements: Failed compliance" in expl:
                failed_hard = True
                break
        if failed_hard:
            concerns.append("Did not pass critical hard requirement check.")

        return concerns
