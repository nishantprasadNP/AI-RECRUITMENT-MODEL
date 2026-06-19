"""
Phase 5 §5.4 — Capability Aggregation Engine.

Generates recruiter-level capability profiles by aggregating evidence scores
for all skills belonging to a graph-defined capability node (domain/category).

IMPORTANT: Capability nodes are NEVER hardcoded in this engine.
           They are discovered dynamically from the Skill Graph via
           ISkillGraphAdapter.get_capability_nodes().

Algorithm:
    For each capability node C in the graph:
        descendants = graph.get_descendants(C)
        evidenced_descendants = [s for s in descendants if s in skill_scores]
        if evidenced_descendants:
            capability_score = mean(skill_evidence_score for s in evidenced_descendants)
            → CapabilityProfile(capability=C, confidence=capability_score, ...)

Example:
    Capability: "Backend Development"
    Descendants: [Node.js, Express.js, FastAPI, MongoDB, PostgreSQL]
    Candidate evidence: FastAPI=75, Node.js=0 (not on resume), ...
    → confidence = mean([75]) = 75.0
    → supporting_skills = ["FastAPI"]
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.skill_evidence.graph.skill_graph_adapter import ISkillGraphAdapter
from app.skill_evidence.models.evidence_models import CapabilityProfile

logger = logging.getLogger("app.skill_evidence.engines.capability_aggregation_engine")


class CapabilityAggregationEngine:
    """
    §5.4 Aggregates skill evidence scores into capability-level profiles.

    Depends on:
      - ISkillGraphAdapter: to discover capability nodes and their descendants.
      - Dict[str, float]: the per-skill evidence scores produced by EvidenceScorer.

    Only capabilities where at least one descendant skill has a score > 0
    are included in the output. This avoids noise from empty profiles.
    """

    def __init__(self, graph_adapter: ISkillGraphAdapter) -> None:
        """
        Args:
            graph_adapter: Phase 5 graph adapter (inject mock in tests).
        """
        self._graph = graph_adapter

    def aggregate(
        self,
        skill_scores: Dict[str, float],
    ) -> List[CapabilityProfile]:
        """
        Computes CapabilityProfile objects for all graph capability nodes
        that have at least one evidenced descendant skill.

        Args:
            skill_scores: Dict mapping skill_name → skill_evidence_score (0–100).
                          Must include all skills that received scoring.

        Returns:
            List of CapabilityProfile objects, sorted by confidence descending.
            Empty list if the graph has no capability nodes or no evidence.
        """
        if not skill_scores:
            logger.info("CapabilityAggregationEngine: empty skill_scores — returning [].")
            return []

        # Build a lowercase lookup for case-insensitive matching of descendants
        scores_lower: Dict[str, float] = {
            k.lower(): v for k, v in skill_scores.items()
        }

        capability_nodes = self._graph.get_capability_nodes()
        if not capability_nodes:
            logger.info(
                "CapabilityAggregationEngine: no capability nodes found in graph."
            )
            return []

        profiles: List[CapabilityProfile] = []

        for capability in capability_nodes:
            descendants = self._graph.get_descendants(capability)
            if not descendants:
                logger.debug("Capability '%s' has no descendants — skipping.", capability)
                continue

            # Find descendant skills that have evidence scores
            supporting_skills: List[str] = []
            supporting_scores: List[float] = []

            for descendant in descendants:
                desc_lower = descendant.lower()
                if desc_lower in scores_lower and scores_lower[desc_lower] > 0:
                    supporting_skills.append(descendant)
                    supporting_scores.append(scores_lower[desc_lower])

            if not supporting_skills:
                logger.debug(
                    "Capability '%s' has no evidenced descendants — skipping.",
                    capability,
                )
                continue

            # capability_score = average of evidenced descendant scores
            capability_score = sum(supporting_scores) / len(supporting_scores)

            profiles.append(
                CapabilityProfile(
                    capability=capability,
                    confidence=round(capability_score, 2),
                    supporting_skills=sorted(supporting_skills),
                )
            )

            logger.debug(
                "Capability '%s' → confidence=%.2f, supporting=%s",
                capability,
                capability_score,
                supporting_skills,
            )

        # Sort by confidence descending for recruiter presentation
        profiles.sort(key=lambda p: p.confidence, reverse=True)

        logger.info(
            "CapabilityAggregationEngine: generated %d capability profile(s).",
            len(profiles),
        )
        return profiles
