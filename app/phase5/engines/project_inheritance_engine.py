"""
Phase 5 §5.3 — Project Inheritance Engine.

Infers foundational skill usage within projects via Skill Graph ancestry.

Example:
    Project CAF-MAI uses: [FastAPI, Scikit-learn, PyTorch]

    FastAPI  → ancestors include Python
    Scikit-learn → ancestors include Python
    PyTorch  → ancestors include Python

    → Python inherits usage in CAF-MAI with evidence_strength=0.3

The inherited evidence is weaker than direct evidence (0.3 vs 1.0) because
it represents an inference, not an explicit declaration by the candidate.

This engine is critical for foundational skills like Python, JavaScript, SQL
that candidates often omit from explicit technology lists within projects.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from app.models.resume_schema import ResumeProfile
from app.phase5.graph.skill_graph_adapter import ISkillGraphAdapter
from app.phase5.models.evidence_models import (
    EvidenceWeight,
    InheritedProjectEntry,
    InheritedProjectEvidence,
)

logger = logging.getLogger("app.phase5.engines.project_inheritance_engine")


class ProjectInheritanceEngine:
    """
    §5.3 Infers project evidence for foundational skills via graph ancestry.

    Algorithm:
      For each project P with technologies [T1, T2, ...]:
        For each technology Ti:
          ancestors = graph.get_ancestors(Ti)
          For each ancestor A (a foundational skill):
            A inherits evidence from project P with strength=INHERITED (0.3)

    Guarantees:
      - A foundational skill inherits a project at most once (deduplicated).
      - The engine only produces inheritance for skills that are already in
        the candidate's skill set OR are graph-resolved ancestors.
      - evidence_strength is always EvidenceWeight.INHERITED (0.3).
    """

    def __init__(self, graph_adapter: ISkillGraphAdapter) -> None:
        """
        Args:
            graph_adapter: Phase 5 graph adapter (inject mock in tests).
        """
        self._graph = graph_adapter

    def inherit(
        self,
        profile: ResumeProfile,
        candidate_skills: List[str],
    ) -> Dict[str, InheritedProjectEvidence]:
        """
        Computes inherited project evidence for all foundational skills.

        Args:
            profile: ResumeProfile containing projects and their technologies.
            candidate_skills: Deduplicated list of skill names from the resume.
                              Only skills in this list receive inherited evidence
                              (prevents generating evidence for unknown skills).

        Returns:
            Dict mapping skill_name → InheritedProjectEvidence.
            Only skills that inherit at least one project are included.
        """
        if not profile or not profile.projects:
            logger.info("ProjectInheritanceEngine: no projects found in profile.")
            return {}

        if not candidate_skills:
            logger.info("ProjectInheritanceEngine: no candidate skills provided.")
            return {}

        # Build a lowercase lookup set for fast membership checks
        candidate_skills_lower: Dict[str, str] = {
            s.lower(): s for s in candidate_skills
        }

        # inherited_map[skill_name] → set of project names already attributed
        inherited_map: Dict[str, Set[str]] = {}

        for project in profile.projects:
            project_name = (project.name or "").strip()
            if not project_name:
                continue

            techs = project.technologies or []
            if not techs:
                continue

            # Collect all foundational ancestors across all project technologies
            foundational_skills_for_project: Set[str] = set()

            for tech in techs:
                if not tech or not tech.strip():
                    continue

                tech_clean = tech.strip()

                # The technology itself might be a candidate skill — skip
                # (it's already handled by EvidenceCollectionEngine as a direct mention)

                # Get all ancestors of this technology from the graph
                try:
                    ancestors = self._graph.get_ancestors(tech_clean)
                except Exception as exc:
                    logger.debug(
                        "get_ancestors failed for tech '%s' in project '%s': %s",
                        tech_clean, project_name, exc,
                    )
                    ancestors = []

                for ancestor_name in ancestors:
                    # Only inherit evidence for skills the candidate already lists
                    ancestor_lower = ancestor_name.lower()
                    if ancestor_lower in candidate_skills_lower:
                        canonical = candidate_skills_lower[ancestor_lower]
                        foundational_skills_for_project.add(canonical)

            # Record the inheritance
            for skill in foundational_skills_for_project:
                if skill not in inherited_map:
                    inherited_map[skill] = set()
                inherited_map[skill].add(project_name)

        # Build output objects
        result: Dict[str, InheritedProjectEvidence] = {}
        for skill, project_names in inherited_map.items():
            entries = [
                InheritedProjectEntry(
                    project=pname,
                    evidence_strength=float(EvidenceWeight.INHERITED),
                )
                for pname in sorted(project_names)  # sorted for determinism
            ]
            result[skill] = InheritedProjectEvidence(
                skill=skill,
                inherited_projects=entries,
            )
            logger.debug(
                "ProjectInheritance: '%s' inherits %d project(s): %s",
                skill,
                len(entries),
                [e.project for e in entries],
            )

        logger.info(
            "ProjectInheritanceEngine: %d skill(s) received inherited project evidence.",
            len(result),
        )
        return result
