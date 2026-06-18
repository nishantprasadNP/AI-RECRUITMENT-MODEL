import os
import json

from app.models.resume_schema import ResumeProfile

from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.experience_analysis.complexity_calculator import ComplexityCalculator
from app.experience_analysis.signal_calculator import SignalCalculator
from app.experience_analysis.confidence_calculator import SkillConfidenceCalculator
from app.experience_analysis.skill_confidence_engine import SkillConfidenceEngine

from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService


def main():

    print("Loading resume profile...")

    with open(
        "data/extracted_profiles/nishant_prasad.json",
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    profile = ResumeProfile.model_validate(data)

    print("Resume loaded successfully.")
    print()

    print("Initializing Skill Knowledge Graph...")
    taxonomy_path = os.path.join("data", "skill_graph", "skills_taxonomy.json")
    repo = NetworkXSkillGraphRepository()
    repo.initialize(taxonomy_path)
    graph_service = SkillGraphService(repo)
    print("Skill Knowledge Graph initialized successfully.")
    print()

    print("=" * 80)
    print("DIAGNOSTICS: GRAPH EVIDENCE EXPANSION")
    print("=" * 80)
    collector = SkillEvidenceCollector(graph_service=graph_service)
    evidence_map = collector.collect(profile)
    
    print(f"{'Skill':<25} | {'Direct Mentions':<15} | {'Dep Mentions':<12} | {'Dependency Sources'}")
    print("-" * 80)
    for skill, evidence in sorted(evidence_map.items()):
        dep_sources_str = ", ".join(evidence.dependency_sources) if evidence.dependency_sources else "None"
        print(f"{skill:<25} | {evidence.direct_mentions:<15} | {evidence.dependency_mentions:<12.1f} | {dep_sources_str}")
    print("=" * 80)
    print()

    engine = SkillConfidenceEngine(
        evidence_collector=collector,
        complexity_calculator=ComplexityCalculator(),
        signal_calculator=SignalCalculator(),
        confidence_calculator=SkillConfidenceCalculator()
    )

    print("Running Phase 5 analysis...")
    print()

    results = engine.analyze(profile)


    print("=" * 80)
    print("PHASE 5 SKILL CONFIDENCE RESULTS")
    print("=" * 80)

    print(f"Skills analyzed: {len(results)}")
    print()

    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1].confidence_score,
        reverse=True
    )

    for skill, result in sorted_results:

        if result.confidence_score <= 0:
            continue

        print()
        print(skill)
        print("-" * 50)

        print(
            f"Confidence Score: "
            f"{result.confidence_score:.2f}"
        )

        print(
            f"Confidence Level: "
            f"{result.confidence_level}"
        )

        print(
            f"Project Signal: "
            f"{result.project_signal:.2f}"
        )

        print(
            f"Professional Signal: "
            f"{result.professional_signal:.2f}"
        )

        print(
            f"Depth Signal: "
            f"{result.depth_signal:.2f}"
        )

        print(
            f"Complexity Signal: "
            f"{result.complexity_signal:.2f}"
        )

        print(
            f"Achievement Signal: "
            f"{result.achievement_signal:.2f}"
        )

        print(
            f"Evidence Summary: "
            f"{result.evidence_summary}"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()