"""
Phase 5 Skill Graph Adapter.

A thin, Phase-5-specific facade over SkillGraphService. This adapter:

  1. Translates SkillGraphService's SkillNode-based API into plain string
     lists that Phase 5 engines can consume without importing graph internals.
  2. Provides a clean seam for unit testing — tests mock this adapter,
     not the full graph stack.
  3. Exposes only the operations Phase 5 actually needs, keeping the
     engine code free of graph traversal details.

Design principle: Phase 5 engines depend on SkillGraphAdapter (an interface),
not on SkillGraphService (a concrete implementation). This makes Phases 6–9
trivial to wire in without changing any engine code.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from app.knowledge_graph.services.skill_graph_service import SkillGraphService

logger = logging.getLogger("app.skill_evidence.graph.skill_graph_adapter")


# ---------------------------------------------------------------------------
# Abstract Interface — engines depend on this, NOT on the concrete class
# ---------------------------------------------------------------------------

class ISkillGraphAdapter(ABC):
    """
    Abstract interface for the Phase 5 graph adapter.

    All Phase 5 engines type-hint against this interface so that
    tests can inject mock adapters without touching the real graph.
    """

    @abstractmethod
    def skill_exists(self, skill: str) -> bool:
        """Returns True if the skill is known to the graph."""

    @abstractmethod
    def get_dependencies(self, skill: str) -> List[str]:
        """
        Returns skills that `skill` REQUIRES (i.e., foundational dependencies).

        Example: get_dependencies("FastAPI") → ["Python"]
        """

    @abstractmethod
    def get_ancestors(self, skill: str) -> List[str]:
        """
        Returns all recursive ancestor skill names for the given skill.

        Example: get_ancestors("FastAPI") → ["Python", "Backend Development"]
        """

    @abstractmethod
    def get_descendants(self, skill: str) -> List[str]:
        """
        Returns all recursive descendant skill names for the given skill.

        Example: get_descendants("Backend Development") → ["Node.js", "FastAPI", ...]
        """

    @abstractmethod
    def get_requiring_skills(self, skill: str, candidate_skills: List[str]) -> List[str]:
        """
        From a list of candidate skills, returns those that have a REQUIRES
        relationship pointing to `skill`.

        Example: get_requiring_skills("Python", ["FastAPI", "Scikit-learn", "React.js"])
                 → ["FastAPI", "Scikit-learn"]
        """

    @abstractmethod
    def get_capability_nodes(self) -> List[str]:
        """
        Returns the display names of all capability-level nodes in the graph
        (nodes of type 'domain' or 'category').

        These drive CapabilityAggregationEngine without any hardcoding.
        """

    @abstractmethod
    def resolve_canonical(self, skill: str) -> Optional[str]:
        """
        Resolves a raw skill string to its canonical display name.
        Returns None if the skill is not found in the graph.
        """


# ---------------------------------------------------------------------------
# Concrete Implementation backed by SkillGraphService
# ---------------------------------------------------------------------------

class SkillGraphAdapter(ISkillGraphAdapter):
    """
    Production implementation of ISkillGraphAdapter.

    Wraps SkillGraphService and translates SkillNode objects into plain
    Python strings for consumption by Phase 5 engines.
    """

    # Node types treated as "capability" nodes for aggregation.
    # This list is the ONLY place where graph type names appear in Phase 5.
    _CAPABILITY_TYPES: frozenset[str] = frozenset({"domain", "category"})

    def __init__(self, graph_service: SkillGraphService) -> None:
        """
        Args:
            graph_service: Initialized SkillGraphService backed by a loaded repository.
        """
        self._service = graph_service

    # ------------------------------------------------------------------
    # Interface implementation
    # ------------------------------------------------------------------

    def skill_exists(self, skill: str) -> bool:
        """Returns True if the skill resolves to a known graph node."""
        return self._service.skill_exists(skill)

    def get_dependencies(self, skill: str) -> List[str]:
        """
        Returns direct parent skill names (skills that `skill` depends on).

        Uses get_parents() — a parent in the hierarchy is a dependency.
        Example: FastAPI's parents include Python.
        """
        try:
            parents = self._service.get_parents(skill)
            return [node.name for node in parents if node]
        except Exception as exc:
            logger.warning("get_dependencies failed for '%s': %s", skill, exc)
            return []

    def get_ancestors(self, skill: str) -> List[str]:
        """Returns all recursive ancestor skill names."""
        try:
            ancestors = self._service.get_ancestors(skill)
            return [node.name for node in ancestors if node]
        except Exception as exc:
            logger.warning("get_ancestors failed for '%s': %s", skill, exc)
            return []

    def get_descendants(self, skill: str) -> List[str]:
        """Returns all recursive descendant skill names."""
        try:
            descendants = self._service.get_descendants(skill)
            return [node.name for node in descendants if node]
        except Exception as exc:
            logger.warning("get_descendants failed for '%s': %s", skill, exc)
            return []

    def get_requiring_skills(self, skill: str, candidate_skills: List[str]) -> List[str]:
        """
        Filters `candidate_skills` to those that have a REQUIRES relationship
        pointing to `skill`.

        Strategy:
          For each candidate skill, check if `skill` is an ancestor of it.
          If yes, the candidate skill "requires" (depends on) `skill`.

        This is graph-direction-aware: FastAPI → Python means FastAPI requires Python,
        so Python's requiring skills include FastAPI.
        """
        requiring: List[str] = []
        skill_lower = skill.lower().strip()

        for candidate in candidate_skills:
            if candidate.lower().strip() == skill_lower:
                continue  # Skip self-reference
            try:
                # Check direct REQUIRES relationship first (fast path)
                if self._service.has_relationship(candidate, skill, relation_type="REQUIRES"):
                    requiring.append(candidate)
                    continue

                # Fall back to ancestor traversal: if `skill` is an ancestor
                # of `candidate`, then `candidate` implicitly requires `skill`
                ancestors = self._service.get_ancestors(candidate)
                ancestor_names_lower = {a.name.lower() for a in ancestors if a}
                if skill_lower in ancestor_names_lower:
                    requiring.append(candidate)

            except Exception as exc:
                logger.debug(
                    "get_requiring_skills check failed for '%s' → '%s': %s",
                    candidate,
                    skill,
                    exc,
                )

        return requiring

    def get_capability_nodes(self) -> List[str]:
        """
        Returns display names of all capability-level nodes (type: domain or category).

        This drives the CapabilityAggregationEngine with zero hardcoded strings.
        """
        try:
            all_nodes = self._service._repo.get_all_nodes()
            return [
                node.name
                for node in all_nodes
                if node and node.type in self._CAPABILITY_TYPES
            ]
        except Exception as exc:
            logger.warning("get_capability_nodes failed: %s", exc)
            return []

    def resolve_canonical(self, skill: str) -> Optional[str]:
        """Resolves a raw skill string to its canonical display name."""
        try:
            return self._service.get_canonical_name(skill)
        except Exception as exc:
            logger.debug("resolve_canonical failed for '%s': %s", skill, exc)
            return None
