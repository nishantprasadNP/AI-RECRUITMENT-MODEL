import os
import pytest
from unittest.mock import MagicMock
from app.experience_analysis.models import SkillEvidence
from app.experience_analysis.propagation_engine import EvidencePropagationEngine
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService

TAXONOMY_PATH = "data/skill_graph/skills_taxonomy.json"


def test_propagation_engine_env_variable_boundaries():
    # 1. No environment variable -> should default to 0.6
    if "FRAMEWORK_TO_LANGUAGE_PROPAGATION" in os.environ:
        del os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"]
    engine = EvidencePropagationEngine()
    assert engine.propagation_factor == 0.6

    # 2. Valid environment variable -> should use it
    os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"] = "0.75"
    engine = EvidencePropagationEngine()
    assert engine.propagation_factor == 0.75

    # 3. Value out of range (too large) -> should fallback to 0.6
    os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"] = "1.5"
    engine = EvidencePropagationEngine()
    assert engine.propagation_factor == 0.6

    # 4. Value out of range (negative) -> should fallback to 0.6
    os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"] = "-0.1"
    engine = EvidencePropagationEngine()
    assert engine.propagation_factor == 0.6

    # 5. Invalid format -> should fallback to 0.6
    os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"] = "invalid_number"
    engine = EvidencePropagationEngine()
    assert engine.propagation_factor == 0.6

    # Cleanup
    if "FRAMEWORK_TO_LANGUAGE_PROPAGATION" in os.environ:
        del os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"]


def test_evidence_propagation_calculation():
    # Setup real taxonomy graph service
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    service = SkillGraphService(repo)

    # Initialize engine with propagation factor 0.6
    os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"] = "0.6"
    engine = EvidencePropagationEngine()

    # Create mock evidence map:
    # Python: 1 direct mention
    # FastAPI: 3 direct mentions
    # React.js: 4 direct mentions
    # JavaScript: 0 direct mentions
    # Git: 2 direct mentions (GitHub: 1 direct mention)
    # MySQL: 1 direct mention (MySQL requires SQL)
    evidence_map = {
        "Python": SkillEvidence(
            skill="Python",
            project_count=0,
            projects=[],
            professional_usage=False,
            roles=[],
            skill_mentions=1,
            achievement_mentions=0,
            direct_mentions=1,
            dependency_mentions=0.0,
            dependency_sources=[]
        ),
        "FastAPI": SkillEvidence(
            skill="FastAPI",
            project_count=1,
            projects=["CAF-MAI"],
            professional_usage=False,
            roles=[],
            skill_mentions=3,
            achievement_mentions=0,
            direct_mentions=3,
            dependency_mentions=0.0,
            dependency_sources=[]
        ),
        "JavaScript": SkillEvidence(
            skill="JavaScript",
            project_count=0,
            projects=[],
            professional_usage=False,
            roles=[],
            skill_mentions=0,
            achievement_mentions=0,
            direct_mentions=0,
            dependency_mentions=0.0,
            dependency_sources=[]
        ),
        "React.js": SkillEvidence(
            skill="React.js",
            project_count=2,
            projects=["A", "B"],
            professional_usage=False,
            roles=[],
            skill_mentions=4,
            achievement_mentions=0,
            direct_mentions=4,
            dependency_mentions=0.0,
            dependency_sources=[]
        )
    }

    # Run propagation
    updated_map = engine.propagate(evidence_map, service)

    # Check Python propagation (FastAPI -> Python)
    # Own: 1, FastAPI: 3 -> 1 + 0.6 * 3 = 2.8
    assert updated_map["Python"].dependency_mentions == pytest.approx(1.8)
    assert updated_map["Python"].dependency_sources == ["FastAPI"]

    # Check JavaScript propagation (React.js -> JavaScript)
    # Own: 0, React.js: 4 -> 0 + 0.6 * 4 = 2.4
    assert updated_map["JavaScript"].dependency_mentions == pytest.approx(2.4)
    assert updated_map["JavaScript"].dependency_sources == ["React.js"]

    # Check child nodes are unmodified
    assert updated_map["FastAPI"].dependency_mentions == 0.0
    assert updated_map["React.js"].dependency_mentions == 0.0

    # Cleanup
    if "FRAMEWORK_TO_LANGUAGE_PROPAGATION" in os.environ:
        del os.environ["FRAMEWORK_TO_LANGUAGE_PROPAGATION"]
