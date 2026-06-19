"""
Phase 5 §5.5 + §5.8 — Skill Evidence Engine (Main Orchestrator).

Wires all Phase 5 sub-engines together through a single, clean pipeline.
All dependencies are injected — this class has no hidden imports or global state.

Pipeline (in execution order):
  1. EvidenceCollectionEngine  → collect direct evidence per skill
  2. DependencyExpansionEngine → expand via graph dependency relationships
  3. ProjectInheritanceEngine  → infer foundational skill usage in projects
  4. EvidenceAttribution build → assemble ordered evidence chains (§5.5)
  5. EvidenceScorer            → compute normalized skill_evidence_score (§5.6)
  6. TierClassifier            → classify scores into tiers (§5.7)
  7. CapabilityAggregationEngine → aggregate capability profiles (§5.4)
  8. ExplainableSkillProfile assemble → build final output objects (§5.8)
  9. SkillEvidenceResult       → return complete analysis result

This class is the ONLY entry point for Phase 5 analysis. Callers should
use phase5_factory.build_skill_evidence_engine() to instantiate it rather
than constructing it directly, unless they need custom dependency injection.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from app.schemas.resume_schema import ResumeProfile
from app.skill_evidence.engines.capability_aggregation_engine import CapabilityAggregationEngine
from app.skill_evidence.engines.dependency_expansion_engine import DependencyExpansionEngine
from app.skill_evidence.engines.evidence_collection_engine import EvidenceCollectionEngine
from app.skill_evidence.engines.project_inheritance_engine import ProjectInheritanceEngine
from app.skill_evidence.graph.skill_graph_adapter import ISkillGraphAdapter
from app.skill_evidence.models.evidence_models import (
    DependencyEvidence,
    EvidenceSource,
    EvidenceWeight,
    ExplainableSkillProfile,
    InheritedProjectEvidence,
    SkillEvidence,
)
from app.skill_evidence.scoring.evidence_scorer import EvidenceScorer
from app.skill_evidence.scoring.tier_classifier import TierClassifier
from app.skill_evidence.services.skill_evidence_result import SkillEvidenceResult

logger = logging.getLogger("app.skill_evidence.services.skill_evidence_engine")


class SkillEvidenceEngine:
    """
    Phase 5 main orchestrator: Skill Evidence Engine.

    Analyzes a ResumeProfile and produces a SkillEvidenceResult containing
    ExplainableSkillProfile objects for each skill and CapabilityProfile
    objects for graph-defined capability nodes.

    Use phase5_factory.build_skill_evidence_engine() to create an instance
    unless you need custom dependency injection (e.g., in tests).
    """

    def __init__(
        self,
        evidence_collection: EvidenceCollectionEngine,
        dependency_expansion: DependencyExpansionEngine,
        project_inheritance: ProjectInheritanceEngine,
        capability_aggregation: CapabilityAggregationEngine,
        evidence_scorer: EvidenceScorer,
        tier_classifier: TierClassifier,
        graph_adapter: ISkillGraphAdapter,
    ) -> None:
        """
        Args:
            evidence_collection:   §5.1 direct evidence collector
            dependency_expansion:  §5.2 graph dependency expander
            project_inheritance:   §5.3 project inheritance inferencer
            capability_aggregation:§5.4 capability profile aggregator
            evidence_scorer:       §5.6 evidence score calculator
            tier_classifier:       §5.7 evidence tier classifier
            graph_adapter:         Phase 5 graph facade (ISkillGraphAdapter)
        """
        self._collection = evidence_collection
        self._dependency = dependency_expansion
        self._inheritance = project_inheritance
        self._capability = capability_aggregation
        self._scorer = evidence_scorer
        self._tier = tier_classifier
        self._graph = graph_adapter

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def analyze(self, profile: ResumeProfile) -> SkillEvidenceResult:
        """
        Runs the full Phase 5 evidence analysis pipeline on a ResumeProfile.

        Args:
            profile: Validated ResumeProfile from Phase 1–4 pipeline.

        Returns:
            SkillEvidenceResult with profiles and capabilities populated.
            Returns an empty result if the profile has no skills.
        """
        logger.info("SkillEvidenceEngine: starting analysis.")

        if not profile or not profile.skills:
            logger.info("SkillEvidenceEngine: empty profile — returning empty result.")
            return SkillEvidenceResult()

        # Deduplicate candidate skills for consistent downstream processing
        candidate_skills = self._deduplicate_skills(profile.skills)
        logger.info("SkillEvidenceEngine: analyzing %d unique skill(s).", len(candidate_skills))

        # ------------------------------------------------------------------
        # Step 1: Collect direct evidence (§5.1)
        # ------------------------------------------------------------------
        evidence_map: Dict[str, SkillEvidence] = self._collection.collect(profile)

        # ------------------------------------------------------------------
        # Step 2: Expand dependency evidence (§5.2)
        # ------------------------------------------------------------------
        dependency_map: Dict[str, DependencyEvidence] = self._dependency.expand(candidate_skills)

        # ------------------------------------------------------------------
        # Step 3: Inherit project evidence (§5.3)
        # ------------------------------------------------------------------
        inheritance_map: Dict[str, InheritedProjectEvidence] = self._inheritance.inherit(
            profile=profile,
            candidate_skills=candidate_skills,
        )

        # ------------------------------------------------------------------
        # Step 4: Score each skill (§5.6)
        # ------------------------------------------------------------------
        skill_scores: Dict[str, float] = self._scorer.score(
            evidence_map=evidence_map,
            dependency_map=dependency_map,
            inheritance_map=inheritance_map,
        )

        # ------------------------------------------------------------------
        # Step 5: Classify tiers (§5.7)
        # ------------------------------------------------------------------
        skill_tiers: Dict[str, str] = self._tier.classify_all(skill_scores)

        # ------------------------------------------------------------------
        # Step 6: Aggregate capabilities (§5.4)
        # ------------------------------------------------------------------
        capability_profiles = self._capability.aggregate(skill_scores)

        # ------------------------------------------------------------------
        # Step 7: Build evidence attribution chains (§5.5)
        #         + assemble ExplainableSkillProfile objects (§5.8)
        # ------------------------------------------------------------------
        profiles: Dict[str, ExplainableSkillProfile] = {}

        for skill in candidate_skills:
            evidence = evidence_map.get(skill)
            dependency = dependency_map.get(skill)
            inheritance = inheritance_map.get(skill)

            # Build attribution chain
            attribution = self._build_attribution(skill, evidence, dependency, inheritance)

            # Collect projects used in (direct + inherited)
            projects_used_in = self._collect_projects(evidence, inheritance)

            # Collect supporting skills (from dependency expansion)
            supporting_skills: List[str] = (
                dependency.supporting_skills if dependency else []
            )

            # Collect professional roles (from experience evidence)
            professional_roles: List[str] = (
                evidence.experience_mentions if evidence else []
            )

            profiles[skill] = ExplainableSkillProfile(
                skill=skill,
                skill_evidence_score=skill_scores.get(skill, 0.0),
                skill_tier=skill_tiers.get(skill, "Limited Evidence"),
                projects_used_in=projects_used_in,
                supporting_skills=supporting_skills,
                professional_roles=professional_roles,
                evidence_attribution=attribution,
            )

        logger.info(
            "SkillEvidenceEngine: analysis complete. "
            "%d skill profile(s), %d capability profile(s).",
            len(profiles),
            len(capability_profiles),
        )

        return SkillEvidenceResult(profiles=profiles, capabilities=capability_profiles)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _deduplicate_skills(skills: List[str]) -> List[str]:
        """Deduplicates skill list case-insensitively, preserving first-seen casing."""
        seen: set[str] = set()
        result: List[str] = []
        for skill in skills:
            if skill and skill.strip():
                key = skill.strip().lower()
                if key not in seen:
                    seen.add(key)
                    result.append(skill.strip())
        return result

    @staticmethod
    def _build_attribution(
        skill: str,
        evidence: SkillEvidence | None,
        dependency: DependencyEvidence | None,
        inheritance: InheritedProjectEvidence | None,
    ) -> List[EvidenceSource]:
        """
        Builds an ordered, weighted evidence attribution chain for a skill.

        Sources are ordered by descending weight so the strongest evidence
        appears first — critical for Phase 8 explainability rendering.
        """
        sources: List[EvidenceSource] = []

        # Direct mention (weight=1.0)
        if evidence and evidence.direct_mentions > 0:
            sources.append(
                EvidenceSource(
                    source_type="skills_section",
                    source_name=skill,
                    weight=float(EvidenceWeight.DIRECT),
                )
            )

        # Project technology mentions (weight=0.8 each)
        if evidence:
            for project_name in evidence.project_mentions:
                sources.append(
                    EvidenceSource(
                        source_type="project",
                        source_name=project_name,
                        weight=float(EvidenceWeight.PROJECT),
                    )
                )

        # Experience mentions (weight=0.8 each)
        if evidence:
            for role in evidence.experience_mentions:
                sources.append(
                    EvidenceSource(
                        source_type="experience",
                        source_name=role,
                        weight=float(EvidenceWeight.PROJECT),
                    )
                )

        # Dependency supporting skills (weight=0.5 each)
        if dependency:
            for supporting_skill in dependency.supporting_skills:
                sources.append(
                    EvidenceSource(
                        source_type="dependency",
                        source_name=supporting_skill,
                        weight=float(EvidenceWeight.DEPENDENCY),
                    )
                )

        # Inherited project evidence (weight=0.3 each)
        if inheritance:
            for entry in inheritance.inherited_projects:
                sources.append(
                    EvidenceSource(
                        source_type="inherited_project",
                        source_name=entry.project,
                        weight=float(EvidenceWeight.INHERITED),
                    )
                )

        # Sort by weight descending — strongest evidence first
        sources.sort(key=lambda s: s.weight, reverse=True)

        return sources

    @staticmethod
    def _collect_projects(
        evidence: SkillEvidence | None,
        inheritance: InheritedProjectEvidence | None,
    ) -> List[str]:
        """
        Merges direct and inherited project lists, deduplicating by name.

        Direct project mentions (weight=0.8) take priority in ordering;
        inherited projects (weight=0.3) are appended after, deduplicated.
        """
        seen: set[str] = set()
        projects: List[str] = []

        # Direct project technology mentions (highest signal)
        if evidence:
            for p in evidence.project_mentions:
                if p and p not in seen:
                    seen.add(p)
                    projects.append(p)

        # Inherited project evidence (graph-inferred)
        if inheritance:
            for entry in inheritance.inherited_projects:
                if entry.project and entry.project not in seen:
                    seen.add(entry.project)
                    projects.append(entry.project)

        return projects
