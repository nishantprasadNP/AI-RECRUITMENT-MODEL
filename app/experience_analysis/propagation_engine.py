"""
Evidence Propagation Engine for Phase 10 in ARIS V2.
Propagates raw evidence counts from frameworks/libraries to their language targets.
"""

import os
import logging
from typing import Dict, Set, Optional
from app.experience_analysis.models import SkillEvidence
from app.knowledge_graph.services.skill_graph_service import SkillGraphService

logger = logging.getLogger("app.experience_analysis.propagation_engine")


class EvidencePropagationEngine:
    """
    Service class that handles concept-aware, one-hop evidence propagation
    from framework/library nodes to language/platform nodes using the taxonomy graph.
    """

    def __init__(self, propagation_factor: Optional[float] = None) -> None:
        if propagation_factor is not None:
            self.propagation_factor = propagation_factor
        else:
            raw_val = os.getenv("FRAMEWORK_TO_LANGUAGE_PROPAGATION")
            if raw_val is None:
                self.propagation_factor = 0.6
            else:
                try:
                    val = float(raw_val)
                    if 0.0 <= val <= 1.0:
                        self.propagation_factor = val
                    else:
                        logger.warning(
                            "FRAMEWORK_TO_LANGUAGE_PROPAGATION value %s is out of range [0.0, 1.0]. Falling back to 0.6.",
                            raw_val
                        )
                        self.propagation_factor = 0.6
                except ValueError:
                    logger.warning(
                        "Invalid format for FRAMEWORK_TO_LANGUAGE_PROPAGATION '%s'. Falling back to 0.6.",
                        raw_val
                    )
                    self.propagation_factor = 0.6

        logger.info("Initialized EvidencePropagationEngine with propagation factor: %.2f", self.propagation_factor)

    def propagate(
        self,
        evidence_map: Dict[str, SkillEvidence],
        graph_service: Optional[SkillGraphService]
    ) -> Dict[str, SkillEvidence]:
        """
        Propagates raw direct mentions from children to parents using 'REQUIRES' edges.
        Only one-hop propagation from explicitly matched child terms is performed.

        Args:
            evidence_map: The collection of raw SkillEvidence objects by skill.
            graph_service: The SkillGraphService mapping taxonomy edges.

        Returns:
            The updated evidence map containing aggregated dependency mentions.
        """
        if not evidence_map:
            return {}
        if graph_service is None:
            logger.warning("No SkillGraphService provided. Skipping evidence propagation.")
            return evidence_map

        unique_skills = list(evidence_map.keys())

        # For each skill, check if other matched skills require it
        for parent_skill in unique_skills:
            if not graph_service.skill_exists(parent_skill):
                continue

            sources_set: Set[str] = set()
            dep_mentions_sum = 0.0

            for child_skill in unique_skills:
                if child_skill == parent_skill:
                    continue
                if not graph_service.skill_exists(child_skill):
                    continue

                # Check if child REQUIRES parent in the taxonomy
                if graph_service.has_relationship(child_skill, parent_skill, relation_type="REQUIRES"):
                    canonical_child = graph_service.get_canonical_name(child_skill) or child_skill
                    sources_set.add(canonical_child)
                    
                    # Add child direct mentions multiplied by propagation factor
                    dep_mentions_sum += evidence_map[child_skill].direct_mentions * self.propagation_factor

            # Update the parent evidence object
            evidence_map[parent_skill].dependency_mentions = dep_mentions_sum
            evidence_map[parent_skill].dependency_sources = sorted(list(sources_set))

            if dep_mentions_sum > 0:
                logger.debug(
                    "Propagated %.2f dependency mentions to '%s' from: %s",
                    dep_mentions_sum,
                    parent_skill,
                    evidence_map[parent_skill].dependency_sources
                )

        return evidence_map
