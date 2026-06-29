from app.knowledge_graph import services
from app.knowledge_graph import services
from app.knowledge_graph import services
from app.knowledge_graph.services import skill_graph_service
import os
import pytest
from unittest.mock import MagicMock

from app.schemas.resume_schema import ResumeProfile
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine
from app.hard_requirements import CapabilityResolver, CapabilityResolutionResult, CapabilityResolutionError

TAXONOMY_PATH = os.path.join("data", "skill_graph", "skills_taxonomy.json")


@pytest.fixture
def inference_engine():
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)

    print("\n========== GRAPH DEBUG ==========")
    print("Nodes:", repo._graph.number_of_nodes())
    print("Edges:", repo._graph.number_of_edges())
    print("=================================\n")

    print("Has node 'fastapi':", repo._graph.has_node("fastapi"))
    print("Has node 'FastAPI':", repo._graph.has_node("FastAPI"))

    print("repo.get_node('fastapi'):", repo.get_node("fastapi"))
    print("repo.get_node('FastAPI'):", repo.get_node("FastAPI"))

    service = SkillGraphService(repo)

    print("service.skill_exists('FastAPI'):", service.skill_exists("FastAPI"))
    print("service.skill_exists('fastapi'):", service.skill_exists("fastapi"))

    # return SkillInferenceEngine(service)
    engine = SkillInferenceEngine(service)

    print("Infer FastAPI:")
    print(engine.infer_skills(["FastAPI"]))

    return engine

@pytest.fixture
def resolver(inference_engine):
    return CapabilityResolver(inference_engine)


def test_resolver_initialization_validation():
    """Verify resolver raises CapabilityResolutionError when initialized with None."""
    with pytest.raises(CapabilityResolutionError) as exc_info:
        CapabilityResolver(None)
    assert "SkillInferenceEngine is required" in str(exc_info.value)


def test_resolve_capabilities_validation_none_profile(resolver):
    """Verify resolve_capabilities raises CapabilityResolutionError when profile is None."""
    with pytest.raises(CapabilityResolutionError) as exc_info:
        resolver.resolve_capabilities(None)
    assert "ResumeProfile is missing" in str(exc_info.value)


def test_resolve_capabilities_empty_skills(resolver):
    """Verify resolving a profile with no skills returns empty capability lists."""
    profile = ResumeProfile(skills=[])
    result = resolver.resolve_capabilities(profile)

    assert isinstance(result, CapabilityResolutionResult)
    assert result.explicit_skills == []
    assert result.inferred_skills == []
    assert result.candidate_capabilities == []
    assert result.skill_origins == {}


def test_resolve_capabilities_success_and_order(resolver):
    """Verify capability resolution preserves order, deduplicates, and tracks origins."""
    # FastAPI, Kafka, AWS
    profile = ResumeProfile(skills=["FastAPI", "Kafka", "AWS"])
    result = resolver.resolve_capabilities(profile)

    # 1. Check explicit skills list matches resume order
    assert result.explicit_skills == ["FastAPI", "Apache Kafka", "AWS"]

    # 2. Inferred skills should contain parents/ancestors
    # Backend is ancestor of FastAPI. Distributed Systems is ancestor of Kafka.
    # Cloud Computing is ancestor of AWS.
    assert "Backend" in result.inferred_skills
    assert "Distributed Systems" in result.inferred_skills
    assert "Cloud Computing" in result.inferred_skills

    # Explicit skills should NOT be in inferred skills
    assert "AWS" not in result.inferred_skills
    assert "Apache Kafka" not in result.inferred_skills
    assert "FastAPI" not in result.inferred_skills

    # 3. Check combined capabilities preserves order: explicit skills first, then inferred
    expected_combined_prefix = ["FastAPI", "Apache Kafka", "AWS"]
    assert result.candidate_capabilities[:3] == expected_combined_prefix
    assert len(result.candidate_capabilities) == len(result.explicit_skills) + len(result.inferred_skills)

    # 4. Check origins map correctly tracks provenance
    assert "FastAPI" in result.skill_origins["Backend"]
    assert "Apache Kafka" in result.skill_origins["Distributed Systems"]
    assert "AWS" in result.skill_origins["Cloud Computing"]

    # Software Engineering is inferred from FastAPI, Apache Kafka, and AWS in standard taxonomy
    if "Software Engineering" in result.skill_origins:
        sources = result.skill_origins["Software Engineering"]
        assert "FastAPI" in sources
        assert "Apache Kafka" in sources
        assert "AWS" in sources




def test_resolve_capabilities_duplicate_handling(resolver):
    """Verify that duplicate inputs are deduplicated case-insensitively while preserving order."""
    profile = ResumeProfile(skills=["FastAPI", "fastapi", "AWS", "FASTAPI"])
    result = resolver.resolve_capabilities(profile)

    # fastapi and FASTAPI are ignored, only first-seen FastAPI is kept
    assert result.explicit_skills == ["FastAPI", "AWS"]
    assert result.candidate_capabilities[:2] == ["FastAPI", "AWS"]


def test_resolve_capabilities_unknown_skills_preserved(resolver):
    """Verify that unknown/unrecognized skills are kept in explicit_skills but have no inferred ancestors."""
    profile = ResumeProfile(skills=["FastAPI", "SuperUnrecognizedSkillXYZ", "AWS"])
    result = resolver.resolve_capabilities(profile)

    # Unrecognized skill is preserved in explicit lists
    assert "SuperUnrecognizedSkillXYZ" in result.explicit_skills
    assert "SuperUnrecognizedSkillXYZ" in result.candidate_capabilities
    assert result.explicit_skills == ["FastAPI", "SuperUnrecognizedSkillXYZ", "AWS"]

    # Provenance and inferred lists should not contain it
    for inferred, origins in result.skill_origins.items():
        assert "SuperUnrecognizedSkillXYZ" not in origins


def test_resolve_capabilities_inference_engine_exception(resolver):
    """Verify resolver raises CapabilityResolutionError if inference engine fails."""
    mock_inference_engine = MagicMock(spec=SkillInferenceEngine)
    mock_inference_engine.infer_skills.side_effect = Exception("Mock DB Failure")

    faulty_resolver = CapabilityResolver(mock_inference_engine)
    profile = ResumeProfile(skills=["Python"])

    with pytest.raises(CapabilityResolutionError) as exc_info:
        faulty_resolver.resolve_capabilities(profile)
    assert "Skill inference failed" in str(exc_info.value)
