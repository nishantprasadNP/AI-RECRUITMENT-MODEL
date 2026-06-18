import json
import os

from app.models.resume_schema import ResumeProfile

from app.knowledge_graph.repositories.networkx_repository import (
    NetworkXSkillGraphRepository
)
from app.knowledge_graph.services.skill_graph_service import (
    SkillGraphService
)

from app.phase5.services.phase5_factory import build_skill_evidence_engine
from app.phase5.engines.capability_aggregation_engine import CapabilityAggregationEngine
from app.phase5.engines.dependency_expansion_engine import DependencyExpansionEngine
from app.phase5.engines.evidence_collection_engine import EvidenceCollectionEngine
from app.phase5.engines.project_inheritance_engine import ProjectInheritanceEngine
from app.phase5.graph.skill_graph_adapter import ISkillGraphAdapter
from app.phase5.scoring.evidence_scorer import EvidenceScorer
from app.phase5.scoring.tier_classifier import TierClassifier
from app.phase5.services.skill_evidence_engine import SkillEvidenceEngine

PROFILE_PATH  = "data/extracted_profiles/nischay_verma.json"
TAXONOMY_PATH = "data/skill_graph/skills_taxonomy.json"


class _NullAdapter(ISkillGraphAdapter):
    """Fallback adapter used when the skill taxonomy file is not present."""
    def skill_exists(self, skill): return False
    def get_dependencies(self, skill): return []
    def get_ancestors(self, skill): return []
    def get_descendants(self, skill): return []
    def get_requiring_skills(self, skill, candidate_skills): return []
    def get_capability_nodes(self): return []
    def resolve_canonical(self, skill): return skill


def _build_engine_without_graph() -> SkillEvidenceEngine:
    adapter = _NullAdapter()
    return SkillEvidenceEngine(
        evidence_collection=EvidenceCollectionEngine(),
        dependency_expansion=DependencyExpansionEngine(graph_adapter=adapter),
        project_inheritance=ProjectInheritanceEngine(graph_adapter=adapter),
        capability_aggregation=CapabilityAggregationEngine(graph_adapter=adapter),
        evidence_scorer=EvidenceScorer(),
        tier_classifier=TierClassifier(),
        graph_adapter=adapter,
    )


def main():

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = ResumeProfile.model_validate(data)

    if os.path.exists(TAXONOMY_PATH):
        repo = NetworkXSkillGraphRepository()
        repo.initialize(TAXONOMY_PATH)
        service = SkillGraphService(repo)
        engine = build_skill_evidence_engine(service)
        graph_available = True
    else:
        print(f"[WARNING] Taxonomy not found at '{TAXONOMY_PATH}' — running without graph.")
        print("[WARNING] Dependency expansion and project inheritance are disabled.\n")
        engine = _build_engine_without_graph()
        graph_available = False

    result = engine.analyze(profile)

    ranked = result.top_skills(n=len(result.profiles))

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------

    print("\n")
    print("=" * 120)
    print("ARIS — PHASE 5: SKILL EVIDENCE ENGINE")
    print("=" * 120)

    # -----------------------------------------------------------------------
    # TOP 10 BY EVIDENCE SCORE
    # -----------------------------------------------------------------------

    print("\n")
    print("=" * 120)
    print("TOP 10 STRONGEST SKILLS BY EVIDENCE SCORE")
    print("=" * 120)
    for i, skill in enumerate(ranked[:10], 1):
        print(
            f"{i}. {skill.skill:<25} "
            f"| Evidence Score: {skill.skill_evidence_score:6.2f} "
            f"| Tier: {skill.skill_tier}"
        )
    print("=" * 120)

    # -----------------------------------------------------------------------
    # CAPABILITY PROFILES (only meaningful with graph)
    # -----------------------------------------------------------------------

    if result.capabilities:
        print("\n")
        print("=" * 120)
        print("CAPABILITY PROFILES (GRAPH-DERIVED)")
        print("=" * 120)
        for cap in result.capabilities:
            supporting_str = ", ".join(cap.supporting_skills[:6]) if cap.supporting_skills else "None"
            print(
                f"{cap.capability:<40} "
                f"| Confidence: {cap.confidence:6.2f} "
                f"| Skills: {supporting_str}"
            )
        print("=" * 120)

    # -----------------------------------------------------------------------
    # DETAILED EXPLAINABLE SKILL PROFILES (TOP 20)
    # -----------------------------------------------------------------------

    print("\n")
    print("=" * 120)
    print("DETAILED EXPLAINABLE SKILL PROFILES (TOP 20)")
    print("=" * 120)

    for skill in ranked[:20]:

        print(f"\n{skill.skill}")
        print("-" * 60)

        print(
            f"Evidence Score        : {skill.skill_evidence_score:.2f}"
        )

        print(
            f"Evidence Tier         : {skill.skill_tier}"
        )

        projects_str = ", ".join(skill.projects_used_in) if skill.projects_used_in else "None"
        print(
            f"Projects Used In      : {projects_str}"
        )

        support_str = ", ".join(skill.supporting_skills) if skill.supporting_skills else "None"
        print(
            f"Supporting Skills     : {support_str}"
        )

        roles_str = ", ".join(skill.professional_roles) if skill.professional_roles else "None"
        print(
            f"Professional Roles    : {roles_str}"
        )

        if skill.evidence_attribution:
            print(f"Evidence Chain        :")
            for source in skill.evidence_attribution:
                print(
                    f"  ├─ [{source.source_type:<20}] "
                    f"{source.source_name:<30} "
                    f"weight={source.weight:.1f}"
                )

    print("\n")
    print("=" * 120)
    print(
        f"Analysis complete. {len(result.profiles)} skill(s) profiled"
        + (f", {len(result.capabilities)} capability profile(s) generated." if result.capabilities else ".")
    )
    print("=" * 120)
    print("\n")


if __name__ == "__main__":
    main()