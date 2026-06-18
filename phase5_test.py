import json

from app.models.resume_schema import ResumeProfile

from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.experience_analysis.complexity_calculator import ComplexityCalculator
from app.experience_analysis.signal_calculator import SignalCalculator
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator
from app.experience_analysis.skill_confidence_engine import SkillConfidenceEngine

from app.knowledge_graph.repositories.networkx_repository import (
    NetworkXSkillGraphRepository
)
from app.knowledge_graph.services.skill_graph_service import (
    SkillGraphService
)


def main():

    with open(
        "data/extracted_profiles/nishant_prasad.json",
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    profile = ResumeProfile.model_validate(data)

    repo = NetworkXSkillGraphRepository()
    repo.initialize("data/skill_graph/skills_taxonomy.json")

    service = SkillGraphService(repo)

    collector = SkillEvidenceCollector(
        graph_service=service
    )

    engine = SkillConfidenceEngine(
        evidence_collector=collector,
        complexity_calculator=ComplexityCalculator(),
        signal_calculator=SignalCalculator(),
        confidence_calculator=SkillConfidenceCalculator()
    )

    results = engine.analyze(profile)

    print("\n")
    print("=" * 120)
    print("TOP SKILLS BY CONFIDENCE")
    print("=" * 120)

    ranked = sorted(
        results.values(),
        key=lambda x: x.confidence_score,
        reverse=True
    )

    print("\n")
    print("=" * 120)
    print("TOP 10 STRONGEST SKILLS")
    print("=" * 120)
    for i, skill in enumerate(ranked[:10], 1):
        print(f"{i}. {skill.skill:<25} | Score: {skill.confidence_score:.2f} | Level: {skill.confidence_level:<20} | Tier: {skill.skill_tier}")
    print("=" * 120)

    print("\n")
    print("=" * 120)
    print("DETAILED SKILL CONFIDENCE PROFILES (TOP 20)")
    print("=" * 120)

    for skill in ranked[:20]:

        print(f"\n{skill.skill}")
        print("-" * 60)

        print(
            f"Confidence Score      : {skill.confidence_score:.2f}"
        )

        print(
            f"Confidence Level      : {skill.confidence_level}"
        )

        print(
            f"Skill Tier            : {skill.skill_tier}"
        )

        print(
            f"Depth Signal          : {skill.depth_signal:.2f}"
        )

        print(
            f"Professional Signal   : {skill.professional_signal:.2f}"
        )

        print(
            f"Complexity Signal     : {skill.complexity_signal:.2f}"
        )

        projects_used = skill.evidence_summary.get("projects_used_in", [])
        projects_str = ", ".join(projects_used) if projects_used else "None"
        print(
            f"Projects Used In      : {projects_str}"
        )

        dep_sources = skill.evidence_summary.get("supporting_technologies", [])
        dep_str = ", ".join(dep_sources) if dep_sources else "None"
        print(
            f"Supporting Techs      : {dep_str}"
        )

        prof_roles = skill.evidence_summary.get("professional_roles", [])
        roles_str = ", ".join(prof_roles) if prof_roles else "None"
        print(
            f"Professional Roles    : {roles_str}"
        )

    print("\n")
    print("=" * 120)


if __name__ == "__main__":
    main()
