"""
Phase 5 §5.2 — Dependency Evidence Expansion Engine.

Uses the Skill Graph to determine which skills on the candidate's resume
act as supporting evidence for a foundational skill.

Example:
    FastAPI → Python  (FastAPI requires Python)
    Scikit-learn → Python
    PyTorch → Python

    → DependencyEvidence(skill="Python", supporting_skills=["FastAPI", "Scikit-learn", "PyTorch"])

IMPORTANT: Dependency evidence is intentionally weighted LOWER than direct
evidence (weight=0.5 vs 1.0). A developer listing FastAPI suggests Python
knowledge, but does not prove it as strongly as a direct Python listing.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.phase5.graph.skill_graph_adapter import ISkillGraphAdapter
from app.phase5.models.evidence_models import DependencyEvidence

logger = logging.getLogger("app.phase5.engines.dependency_expansion_engine")


class DependencyExpansionEngine:
    """
    §5.2 Expands skill evidence using Skill Graph dependency relationships.

    For each skill, finds all other skills on the resume that declare
    a REQUIRES (or implicit ancestor) relationship pointing to it.
    These become `supporting_skills` — secondary evidence contributors.

    This engine is graph-aware but profile-agnostic: it only needs the
    list of candidate skill names and the graph adapter.
    """

    def __init__(self, graph_adapter: ISkillGraphAdapter) -> None:
        """
        Args:
            graph_adapter: Phase 5 graph adapter (inject mock in tests).
        """
        self._graph = graph_adapter

    def expand(self, candidate_skills: List[str]) -> Dict[str, DependencyEvidence]:
        """
        For each skill, discovers which other candidate skills depend on it
        (i.e., have it as an ancestor in the Skill Graph).

        Args:
            candidate_skills: Deduplicated list of skill names from the resume.

        Returns:
            Dict mapping skill_name → DependencyEvidence with supporting_skills populated.
            Every input skill gets an entry (empty supporting_skills if none found).
        """
        if not candidate_skills:
            logger.info("DependencyExpansionEngine: no candidate skills provided.")
            return {}

        dependency_map: Dict[str, DependencyEvidence] = {}

        for skill in candidate_skills:
            # Query the graph for skills in the candidate's list that
            # have a REQUIRES / ancestor relationship pointing to this skill
            supporting = self._graph.get_requiring_skills(
                skill=skill,
                candidate_skills=candidate_skills,
            )

            # Deduplicate and sort for determinism
            unique_supporting = sorted(set(supporting))

            dependency_map[skill] = DependencyEvidence(
                skill=skill,
                supporting_skills=unique_supporting,
            )

            if unique_supporting:
                logger.debug(
                    "DependencyExpansion: '%s' ← supported by %s",
                    skill,
                    unique_supporting,
                )

        logger.info(
            "DependencyExpansionEngine: processed %d skill(s), "
            "%d have dependency support.",
            len(dependency_map),
            sum(1 for d in dependency_map.values() if d.supporting_skills),
        )

        return dependency_map
