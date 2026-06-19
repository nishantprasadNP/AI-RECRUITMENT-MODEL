"""
Capability resolver for building a unified candidate capability set.
"""

import logging
from typing import List, Dict
from app.schemas.resume_schema import ResumeProfile
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine
from app.hard_requirements.models import CapabilityResolutionResult
from app.hard_requirements.exceptions import CapabilityResolutionError

logger = logging.getLogger("app.hard_requirements.capability_resolver")


class CapabilityResolver:
    """
    Resolves candidate skills into a canonical, expanded set of capabilities
    using ordered deduplication and tracking graph provenance.
    """

    def __init__(self, skill_inference_engine: SkillInferenceEngine) -> None:
        """
        Initializes the CapabilityResolver.

        Args:
            skill_inference_engine: The inference engine for traversing the skill graph.
        """
        if not skill_inference_engine:
            raise CapabilityResolutionError("SkillInferenceEngine is required.")
        self._inference_engine = skill_inference_engine

    def resolve_capabilities(self, resume_profile: ResumeProfile) -> CapabilityResolutionResult:
        """
        Extracts skills from ResumeProfile, resolves them to canonical names,
        infers parent skills using the SkillInferenceEngine, and builds a combined,
        deduplicated capability list preserving the natural order of evidence.

        Args:
            resume_profile: The candidate's parsed resume profile.

        Returns:
            CapabilityResolutionResult containing explicit, inferred, combined capabilities
            and graph provenance mapping.
        """
        logger.info("CapabilityResolver: Starting capability resolution.")
        if not resume_profile:
            logger.error("CapabilityResolver: ResumeProfile is missing.")
            raise CapabilityResolutionError("ResumeProfile is missing or None.")

        raw_skills = resume_profile.skills or []
        logger.info("CapabilityResolver: Processing %d raw skills from profile.", len(raw_skills))

        explicit_resolved: List[str] = []
        skill_origins: Dict[str, List[str]] = {}

        seen_explicit_lower = set()

        for raw_skill in raw_skills:
            if not raw_skill or not raw_skill.strip():
                continue

            # Use SkillInferenceEngine to infer skills for this single skill
            try:
                res = self._inference_engine.infer_skills([raw_skill])
            except Exception as e:
                logger.error("CapabilityResolver: Inference failed for '%s': %s", raw_skill, str(e))
                raise CapabilityResolutionError(f"Skill inference failed: {str(e)}") from e

            # If the skill resolved in the graph
            if res.get("explicit_skills"):
                canonical = res["explicit_skills"][0]
                lower_canonical = canonical.lower()
                if lower_canonical not in seen_explicit_lower:
                    seen_explicit_lower.add(lower_canonical)
                    explicit_resolved.append(canonical)

                # The inferred skills are the ancestors for this specific canonical skill
                for ancestor in res.get("inferred_skills", []):
                    # Track graph provenance: map this ancestor to its source skill
                    if ancestor not in skill_origins:
                        skill_origins[ancestor] = []
                    if canonical not in skill_origins[ancestor]:
                        skill_origins[ancestor].append(canonical)
            else:
                # If it didn't resolve in the graph (i.e. unknown skill), we treat it as an explicit skill
                # and keep its raw stripped name as fallback.
                cleaned = raw_skill.strip()
                lower_cleaned = cleaned.lower()
                if lower_cleaned not in seen_explicit_lower:
                    seen_explicit_lower.add(lower_cleaned)
                    explicit_resolved.append(cleaned)

        # Collect inferred skills in the order they were first discovered
        # and filter out any inferred skill that is also explicitly declared on the resume
        inferred_resolved: List[str] = []
        final_skill_origins: Dict[str, List[str]] = {}

        for ancestor, sources in skill_origins.items():
            if ancestor.lower() not in seen_explicit_lower:
                inferred_resolved.append(ancestor)
                final_skill_origins[ancestor] = sources

        # Build combined capabilities preserving order: explicit first, then inferred
        candidate_capabilities = explicit_resolved + inferred_resolved

        logger.info(
            "CapabilityResolver: Completed resolution. "
            "Explicit: %d, Inferred: %d, Total Capabilities: %d",
            len(explicit_resolved),
            len(inferred_resolved),
            len(candidate_capabilities)
        )

        return CapabilityResolutionResult(
            explicit_skills=explicit_resolved,
            inferred_skills=inferred_resolved,
            candidate_capabilities=candidate_capabilities,
            skill_origins=final_skill_origins
        )
