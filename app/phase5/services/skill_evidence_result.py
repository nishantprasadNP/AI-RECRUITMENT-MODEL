"""
Phase 5 result container.

SkillEvidenceResult is the top-level output object returned by
SkillEvidenceEngine.analyze(). It is consumed by Phases 6–9.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field

from app.phase5.models.evidence_models import CapabilityProfile, ExplainableSkillProfile


class SkillEvidenceResult(BaseModel):
    """
    Complete output of Phase 5's Skill Evidence Engine analysis.

    Fields:
        profiles: Per-skill explainable evidence profiles, keyed by skill name.
                  This is the primary output for Phase 7 (Matching) and Phase 8 (Explainability).

        capabilities: Capability-level aggregated profiles, sorted by confidence descending.
                      This is the primary output for Phase 6 (Job Requirement Intelligence).
    """

    profiles: Dict[str, ExplainableSkillProfile] = Field(
        default_factory=dict,
        description=(
            "Per-skill explainable evidence profiles. "
            "Keys are normalized skill names; values are ExplainableSkillProfile objects."
        ),
    )
    capabilities: List[CapabilityProfile] = Field(
        default_factory=list,
        description=(
            "Capability-level evidence profiles derived from the Skill Graph. "
            "Sorted by confidence score descending."
        ),
    )

    def top_skills(self, n: int = 10) -> List[ExplainableSkillProfile]:
        """
        Returns the top-n skills by skill_evidence_score, descending.

        Useful for recruiter dashboards and ranking summaries.
        """
        return sorted(
            self.profiles.values(),
            key=lambda p: p.skill_evidence_score,
            reverse=True,
        )[:n]

    def get_by_tier(self, tier: str) -> List[ExplainableSkillProfile]:
        """
        Returns all skill profiles matching the given tier label.

        Args:
            tier: One of "Expert Evidence", "Strong Evidence",
                  "Moderate Evidence", "Limited Evidence".
        """
        return [p for p in self.profiles.values() if p.skill_tier == tier]
