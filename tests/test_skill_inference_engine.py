import os
import pytest
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine

TAXONOMY_PATH = os.path.join("data", "skill_graph", "skills_taxonomy.json")

@pytest.fixture
def inference_engine():
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    service = SkillGraphService(repo)
    return SkillInferenceEngine(service)

def test_inference_valid_skills(inference_engine):
    """Verify inference works for valid inputs, returning canonical names."""
    result = inference_engine.infer_skills(["python", "java"])
    
    assert "Python" in result["explicit_skills"]
    assert "Java" in result["explicit_skills"]
    assert "Programming" in result["inferred_skills"]
    assert "Software Engineering" in result["inferred_skills"]

def test_inference_duplicate_skills(inference_engine):
    """Verify input duplicates are handled and deduplicated in the explicit output."""
    result = inference_engine.infer_skills(["Python", "python", "Py"])
    
    # Python and Py both resolve to the canonical "Python" node
    assert result["explicit_skills"] == ["Python"]
    assert "Programming" in result["inferred_skills"]
    assert "Software Engineering" in result["inferred_skills"]

def test_inference_unknown_skills(inference_engine):
    """Verify that unknown skills are ignored safely and not included in either list."""
    result = inference_engine.infer_skills(["NonExistentTool", "UnknownSkillxyz"])
    
    assert result["explicit_skills"] == []
    assert result["inferred_skills"] == []

def test_inference_mixed_skills(inference_engine):
    """Verify mixed valid and invalid skills are processed correctly."""
    result = inference_engine.infer_skills(["CNN", "NonExistentTool", "python", "UnknownSkill"])
    
    # CNN and Python should be resolved, NonExistentTool and UnknownSkill should be ignored
    assert "CNN" in result["explicit_skills"]
    assert "Python" in result["explicit_skills"]
    assert "NonExistentTool" not in result["explicit_skills"]
    
    # Inferred skills should cover ancestors of both CNN and Python
    inferred = result["inferred_skills"]
    assert "Computer Vision" in inferred
    assert "Deep Learning" in inferred
    assert "Programming" in inferred
    assert "Software Engineering" in inferred

def test_inference_deduplication(inference_engine):
    """Verify that explicit skills are subtracted from the inferred skills list."""
    # Machine Learning is an ancestor of Deep Learning.
    # If we pass both, "Machine Learning" should ONLY appear in explicit_skills.
    result = inference_engine.infer_skills(["Deep Learning", "Machine Learning"])
    
    assert "Deep Learning" in result["explicit_skills"]
    assert "Machine Learning" in result["explicit_skills"]
    
    # Machine Learning must be excluded from inferred_skills because it is explicitly declared
    assert "Machine Learning" not in result["inferred_skills"]
    # But other ancestors like Data Science should still be inferred
    assert "Data Science" in result["inferred_skills"]

def test_ancestor_inference_flow(inference_engine):
    """Verify recursive ancestor traversal matches our expected path (CNN -> CV -> DL -> ML -> DS)."""
    result = inference_engine.infer_skills(["CNN"])
    
    assert result["explicit_skills"] == ["CNN"]
    expected_inferred = ["Computer Vision", "Data Science", "Deep Learning", "Machine Learning"]
    for skill in expected_inferred:
        assert skill in result["inferred_skills"]
