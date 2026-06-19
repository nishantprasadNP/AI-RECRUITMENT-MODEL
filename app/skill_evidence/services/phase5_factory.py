"""
Phase 5 Factory.

Provides a single wiring point for constructing a fully-configured
SkillEvidenceEngine from a live SkillGraphService.

Usage (from any future phase):
    from app.skill_evidence.services.phase5_factory import build_skill_evidence_engine
    from app.knowledge_graph.services.skill_graph_service import SkillGraphService

    graph_service = ...  # already initialized SkillGraphService
    engine = build_skill_evidence_engine(graph_service)
    result = engine.analyze(profile)

This factory is the ONLY place in Phase 5 where concrete classes are
assembled. All other modules depend on interfaces or abstract base classes,
keeping the dependency graph acyclic and easy to test.
"""

from __future__ import annotations

from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.skill_evidence.engines.capability_aggregation_engine import CapabilityAggregationEngine
from app.skill_evidence.engines.dependency_expansion_engine import DependencyExpansionEngine
from app.skill_evidence.engines.evidence_collection_engine import EvidenceCollectionEngine
from app.skill_evidence.engines.project_inheritance_engine import ProjectInheritanceEngine
from app.skill_evidence.graph.skill_graph_adapter import SkillGraphAdapter
from app.skill_evidence.scoring.evidence_scorer import EvidenceScorer
from app.skill_evidence.scoring.tier_classifier import TierClassifier
from app.skill_evidence.services.skill_evidence_engine import SkillEvidenceEngine


def build_skill_evidence_engine(graph_service: SkillGraphService) -> SkillEvidenceEngine:
    """
    Constructs a fully-wired SkillEvidenceEngine.

    All dependencies are constructed here and injected into the engine.
    No global state, no singletons — each call produces a fresh instance.

    Args:
        graph_service: An initialized SkillGraphService backed by a loaded
                       NetworkXSkillGraphRepository (or any ISkillGraphRepository).

    Returns:
        A ready-to-use SkillEvidenceEngine.

    Example:
        from app.knowledge_graph.repositories.networkx_repository import (
            NetworkXSkillGraphRepository,
        )
        from app.knowledge_graph.services.skill_graph_service import SkillGraphService
        from app.skill_evidence.services.phase5_factory import build_skill_evidence_engine

        repo = NetworkXSkillGraphRepository()
        repo.initialize("data/skill_graph/skills_taxonomy.json")
        service = SkillGraphService(repo)
        engine = build_skill_evidence_engine(service)
    """
    # Build the graph adapter (sole dependency of all graph-aware engines)
    adapter = SkillGraphAdapter(graph_service)

    return SkillEvidenceEngine(
        evidence_collection=EvidenceCollectionEngine(),
        dependency_expansion=DependencyExpansionEngine(graph_adapter=adapter),
        project_inheritance=ProjectInheritanceEngine(graph_adapter=adapter),
        capability_aggregation=CapabilityAggregationEngine(graph_adapter=adapter),
        evidence_scorer=EvidenceScorer(),
        tier_classifier=TierClassifier(),
        graph_adapter=adapter,
    )
