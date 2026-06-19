"""
Phase 5 §5.1 — Evidence Collection Engine.

Collects direct evidence for every skill from three sources:
  1. Skills Section  (direct_mentions)
  2. Project Technologies  (project_mentions)
  3. Experience Technologies / Descriptions  (experience_mentions)

This engine is deliberately free of any graph logic — it operates
purely on the ResumeProfile's raw data. Graph-aware expansion is
handled downstream by DependencyExpansionEngine and ProjectInheritanceEngine.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Set

from app.schemas.resume_schema import ResumeProfile
from app.skill_evidence.models.evidence_models import SkillEvidence

logger = logging.getLogger("app.skill_evidence.engines.evidence_collection_engine")


class EvidenceCollectionEngine:
    """
    §5.1 Collects all direct evidence for every skill in the candidate's profile.

    Output: Dict[skill_name, SkillEvidence]

    Design notes:
      - Case-insensitive, word-boundary-aware matching prevents false positives
        (e.g., "Go" matching inside "MongoDB").
      - Skills are deduplicated before processing (case-insensitive, first-seen wins).
      - This engine is pure and stateless — safe to call multiple times.
    """

    # -----------------------------------------------------------------------
    # Matching helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_pattern(skill: str) -> re.Pattern[str]:
        """
        Builds a boundary-safe, case-insensitive regex pattern for `skill`.

        Word boundaries (\b) are applied only at alphanumeric edges to handle
        skills that start/end with special characters (e.g., "C++", ".NET").
        """
        escaped = re.escape(skill)
        if skill and skill[0].isalnum():
            escaped = r"\b" + escaped
        if skill and skill[-1].isalnum():
            escaped = escaped + r"\b"
        return re.compile(escaped, re.IGNORECASE)

    @staticmethod
    def _matches(pattern: re.Pattern[str], text: str) -> bool:
        """Returns True if `pattern` matches anywhere in `text`."""
        return bool(pattern.search(text)) if text else False

    # -----------------------------------------------------------------------
    # Deduplication
    # -----------------------------------------------------------------------

    @staticmethod
    def _deduplicate_skills(raw_skills: List[str]) -> List[str]:
        """
        Returns a deduplicated list of skills, case-insensitively, preserving
        the original casing and order of the first occurrence.
        """
        seen: Set[str] = set()
        result: List[str] = []
        for skill in raw_skills:
            if not skill or not skill.strip():
                continue
            key = skill.strip().lower()
            if key not in seen:
                seen.add(key)
                result.append(skill.strip())
        return result

    # -----------------------------------------------------------------------
    # Core collection logic
    # -----------------------------------------------------------------------

    def collect(self, profile: ResumeProfile) -> Dict[str, SkillEvidence]:
        """
        Collects direct evidence for each skill in the candidate's profile.

        Args:
            profile: Validated ResumeProfile object.

        Returns:
            Dict mapping skill name → SkillEvidence with populated source lists.
        """
        if not profile:
            logger.warning("EvidenceCollectionEngine received an empty profile.")
            return {}

        skills = self._deduplicate_skills(profile.skills or [])
        projects = profile.projects or []
        experience = profile.experience or []

        if not skills:
            logger.info("No skills found in profile — returning empty evidence map.")
            return {}

        evidence_map: Dict[str, SkillEvidence] = {}

        for skill in skills:
            pattern = self._build_pattern(skill)

            # ----------------------------------------------------------------
            # Source 1: Skills Section
            # ----------------------------------------------------------------
            # A skill is directly mentioned once for appearing in the skills list.
            direct_mentions = 1  # presence in skills section is the direct mention

            # ----------------------------------------------------------------
            # Source 2: Project Technologies
            # ----------------------------------------------------------------
            project_mentions: List[str] = []
            seen_projects: Set[str] = set()

            for project in projects:
                project_name = (project.name or "").strip()
                if not project_name:
                    continue

                techs = project.technologies or []
                tech_match = any(
                    self._matches(pattern, t) for t in techs if t
                )

                if tech_match and project_name not in seen_projects:
                    seen_projects.add(project_name)
                    project_mentions.append(project_name)

            # ----------------------------------------------------------------
            # Source 3: Experience Technologies / Descriptions
            # ----------------------------------------------------------------
            experience_mentions: List[str] = []
            seen_roles: Set[str] = set()

            for exp in experience:
                role = (exp.role or "").strip()
                company = (exp.company or "").strip()
                description = exp.description or ""

                # Determine a stable identifier for this experience entry
                identifier = role or company or "Unknown Role"

                # Check technologies list (duck-typed; Experience model may
                # not declare this field but data may include it post-extraction)
                exp_techs: List[str] = []
                raw_techs = getattr(exp, "technologies", None)
                if raw_techs:
                    if isinstance(raw_techs, list):
                        exp_techs = [t for t in raw_techs if t]
                    elif isinstance(raw_techs, str):
                        exp_techs = [raw_techs]

                tech_match = any(self._matches(pattern, t) for t in exp_techs)
                desc_match = self._matches(pattern, description)

                if (tech_match or desc_match) and identifier not in seen_roles:
                    seen_roles.add(identifier)
                    experience_mentions.append(identifier)

            evidence_map[skill] = SkillEvidence(
                skill=skill,
                direct_mentions=direct_mentions,
                project_mentions=project_mentions,
                experience_mentions=experience_mentions,
            )

            logger.debug(
                "Skill '%s' → direct=%d, projects=%s, experience=%s",
                skill,
                direct_mentions,
                project_mentions,
                experience_mentions,
            )

        logger.info(
            "EvidenceCollectionEngine: collected evidence for %d skill(s).",
            len(evidence_map),
        )
        return evidence_map
