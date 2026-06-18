"""
Phase 5 Pydantic data contracts.

All models represent immutable evidence objects — they are produced by
engines, consumed by downstream phases, and never mutated after creation.

NOTE: All scores in this module represent Skill Evidence Strength,
      NOT proficiency levels. The naming convention `skill_evidence_score`
      must be maintained across all downstream consumers.
"""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Evidence Weight Constants
# ---------------------------------------------------------------------------

class EvidenceWeight(float, Enum):
    """
    Canonical weight assigned to each evidence source type.

    Weights are intentionally NOT equal — direct mention carries
    more signal than an inferred project inheritance.

    These values drive raw_score accumulation in EvidenceScorer.
    """
    DIRECT = 1.0       # Skill explicitly listed in the skills section
    PROJECT = 0.8      # Skill appears in a project's technology list
    DEPENDENCY = 0.5   # Skill is a dependency of another evidenced skill
    INHERITED = 0.3    # Skill is inferred as used in a project via graph ancestry


# ---------------------------------------------------------------------------
# 5.5 Evidence Attribution
# ---------------------------------------------------------------------------

class EvidenceSource(BaseModel):
    """
    A single traceable piece of evidence contributing to a skill's score.

    Consumed by Phase 8 (Explainability) and Phase 10 (Recruiter Copilot)
    to generate human-readable justifications.
    """
    source_type: str = Field(
        ...,
        description=(
            "Category of the evidence source. "
            "One of: 'skills_section', 'project', 'experience', "
            "'dependency', 'inherited_project'."
        ),
    )
    source_name: str = Field(
        ...,
        description=(
            "The concrete identifier of the source. "
            "For a project, this is the project name. "
            "For a dependency, this is the supporting skill name."
        ),
    )
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Attribution weight contributed by this source (from EvidenceWeight).",
    )


class EvidenceAttribution(BaseModel):
    """
    Complete, ordered evidence chain for a single skill.

    The `evidence` list is ordered by descending weight so that the
    strongest evidence appears first (important for explainability rendering).
    """
    skill: str = Field(..., description="Normalized skill name.")
    evidence: List[EvidenceSource] = Field(
        default_factory=list,
        description="Ordered list of evidence sources contributing to this skill's score.",
    )


# ---------------------------------------------------------------------------
# 5.1 Evidence Collection
# ---------------------------------------------------------------------------

class SkillEvidence(BaseModel):
    """
    Direct evidence collected for a single skill from the candidate's profile.

    Output of EvidenceCollectionEngine (§5.1).
    """
    skill: str = Field(..., description="Normalized skill name.")
    direct_mentions: int = Field(
        default=0,
        ge=0,
        description="Number of times this skill appears in the skills section.",
    )
    project_mentions: List[str] = Field(
        default_factory=list,
        description="Deduplicated list of project names where this skill appears in technologies.",
    )
    experience_mentions: List[str] = Field(
        default_factory=list,
        description=(
            "Deduplicated list of role/company identifiers where this skill "
            "appears in experience technologies or description."
        ),
    )


# ---------------------------------------------------------------------------
# 5.2 Dependency Evidence Expansion
# ---------------------------------------------------------------------------

class DependencyEvidence(BaseModel):
    """
    Graph-derived evidence: other skills that depend on (and thus support) this skill.

    Example:
        FastAPI → Python, Scikit-learn → Python
        → DependencyEvidence(skill="Python", supporting_skills=["FastAPI", "Scikit-learn"])

    Output of DependencyExpansionEngine (§5.2).
    """
    skill: str = Field(..., description="The foundational skill being supported.")
    supporting_skills: List[str] = Field(
        default_factory=list,
        description=(
            "Skills present on the resume that declare a REQUIRES relationship "
            "to this skill via the Skill Graph."
        ),
    )


# ---------------------------------------------------------------------------
# 5.3 Project Inheritance
# ---------------------------------------------------------------------------

class InheritedProjectEntry(BaseModel):
    """
    A single project from which a foundational skill inherits evidence.

    Evidence strength is fixed at EvidenceWeight.INHERITED (0.3).
    """
    project: str = Field(..., description="Name of the project from which evidence is inherited.")
    evidence_strength: float = Field(
        default=EvidenceWeight.INHERITED,
        ge=0.0,
        le=1.0,
        description="Attribution strength for this inherited project link.",
    )


class InheritedProjectEvidence(BaseModel):
    """
    All projects from which a foundational skill inherits usage evidence.

    Example:
        CAF-MAI uses [FastAPI, Scikit-learn, PyTorch], all of which depend on Python.
        → InheritedProjectEvidence(skill="Python", inherited_projects=[InheritedProjectEntry("CAF-MAI")])

    Output of ProjectInheritanceEngine (§5.3).
    """
    skill: str = Field(..., description="The foundational skill inheriting project evidence.")
    inherited_projects: List[InheritedProjectEntry] = Field(
        default_factory=list,
        description="Deduplicated list of projects from which evidence is inherited.",
    )


# ---------------------------------------------------------------------------
# 5.4 Capability Aggregation
# ---------------------------------------------------------------------------

class CapabilityProfile(BaseModel):
    """
    Recruiter-level capability derived from graph-defined capability nodes.

    Capabilities are NEVER hardcoded — they are read from the Skill Graph
    as domain/category nodes whose descendants overlap with the candidate's
    evidenced skills.

    Output of CapabilityAggregationEngine (§5.4).
    """
    capability: str = Field(
        ...,
        description="Display name of the capability node (e.g., 'Backend Development').",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "Capability evidence confidence score (0–100). "
            "Computed as the average skill_evidence_score of evidenced descendant skills."
        ),
    )
    supporting_skills: List[str] = Field(
        default_factory=list,
        description="Descendant skills that contributed evidence to this capability score.",
    )


# ---------------------------------------------------------------------------
# 5.6 / 5.7 Scoring & Tier
# ---------------------------------------------------------------------------

class ScoredSkill(BaseModel):
    """Intermediate object holding the raw evidence score before tier assignment."""
    skill: str = Field(..., description="Normalized skill name.")
    skill_evidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "Normalized evidence score (0–100). "
            "This is NOT a proficiency score — it represents the strength of "
            "observed evidence across sources."
        ),
    )


class TieredSkill(BaseModel):
    """Intermediate object pairing a skill with its evidence tier label."""
    skill: str = Field(..., description="Normalized skill name.")
    tier: str = Field(
        ...,
        description=(
            "Human-readable evidence tier. "
            "One of: 'Expert Evidence', 'Strong Evidence', "
            "'Moderate Evidence', 'Limited Evidence'."
        ),
    )


# ---------------------------------------------------------------------------
# 5.8 Explainable Skill Profile (Final Output)
# ---------------------------------------------------------------------------

class ExplainableSkillProfile(BaseModel):
    """
    Final, recruiter-ready evidence profile for a single skill.

    This is the canonical output object of Phase 5. It is consumed by:
      - Phase 6: Job Requirement Intelligence (gap analysis)
      - Phase 7: Candidate Matching (weighted overlap)
      - Phase 8: Explainability (justification generation)
      - Phase 9: Ranking (ordered candidate lists)

    IMPORTANT: `skill_evidence_score` represents evidence strength, NOT proficiency.
    """
    skill: str = Field(..., description="Normalized skill name.")
    skill_evidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description=(
            "Normalized evidence score (0–100). "
            "Evidence strength — not proficiency."
        ),
    )
    skill_tier: str = Field(
        ...,
        description=(
            "Qualitative evidence tier: "
            "'Expert Evidence' | 'Strong Evidence' | "
            "'Moderate Evidence' | 'Limited Evidence'."
        ),
    )
    projects_used_in: List[str] = Field(
        default_factory=list,
        description=(
            "Projects where this skill appears directly in technologies, "
            "or is inferred via graph-based project inheritance."
        ),
    )
    supporting_skills: List[str] = Field(
        default_factory=list,
        description=(
            "Skills on this resume that depend on (and thus provide evidence for) "
            "this foundational skill, as determined by Skill Graph REQUIRES edges."
        ),
    )
    professional_roles: List[str] = Field(
        default_factory=list,
        description=(
            "Professional roles or companies where this skill was used, "
            "based on experience technology matches."
        ),
    )
    evidence_attribution: List[EvidenceSource] = Field(
        default_factory=list,
        description=(
            "Ordered, weighted evidence chain. "
            "Each entry is one traceable source of evidence for this skill."
        ),
    )
