import os
import json
import pytest
import tempfile
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.exceptions import (
    GraphInitializationError,
    DuplicateNodeError,
    MissingNodeReferenceError
)
from app.knowledge_graph.models import SkillNode

TAXONOMY_PATH = os.path.join("data", "skill_graph", "skills_taxonomy.json")

def test_initialize_and_load_valid_taxonomy():
    """Verify that the repository initializes successfully with a valid taxonomy file."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    
    # Check that nodes are loaded correctly
    nodes = repo.get_all_nodes()
    assert len(nodes) >= 17  # The taxonomy file has at least 17 skills
    
    # Check Python node exists and is mapped to type 'language'
    python_node = repo.get_node("python")
    assert python_node is not None
    assert python_node.name == "Python"
    assert python_node.type == "language"
    assert "Py" in python_node.synonyms

def test_get_parents_and_children():
    """Verify retrieving parents and children of nodes works correctly."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    
    # Test parents of Python: should be 'programming' (through PARENT_OF)
    parents_of_python = repo.get_parents("python")
    parent_ids = [node.id for node in parents_of_python]
    assert "programming" in parent_ids
    
    # Test parents of DevOps: should be 'cloud_computing' (through PARENT_OF)
    parents_of_devops = repo.get_parents("devops")
    devops_parent_ids = [node.id for node in parents_of_devops]
    assert "cloud_computing" in devops_parent_ids
    
    # Test children of deep learning: cv, nlp, generative_ai
    children_of_dl = repo.get_children("deep_learning")
    child_ids = [node.id for node in children_of_dl]
    assert "computer_vision" in child_ids
    assert "nlp" in child_ids
    assert "generative_ai" in child_ids

def test_neighbors_filtering():
    """Verify neighbors can be retrieved and filtered by relationship type."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    
    # Neighbors of Python: 'data_science' (RELATED_TO bidirectional), 'django' if it existed in taxonomy
    # In taxonomy: python is related to data_science, django is related to python.
    # Because django -> python is RELATED_TO, it adds bidirectional, so python out-edges include django and data_science.
    neighbors_of_python = repo.get_neighbors("python", relation_type="RELATED_TO")
    neighbor_ids = [node.id for node in neighbors_of_python]
    assert "data_science" in neighbor_ids

def test_path_distance_calculations():
    """Verify shortest path distance calculation works on undirected representation."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    
    # Direct parent-child: programming -> python (weight 1.0 -> distance cost 1.0)
    dist_direct = repo.get_path_distance("programming", "python")
    assert dist_direct == 1.0
    
    # Siblings: python <-> programming <-> java (each edge weight 1.0 -> total distance 2.0)
    dist_siblings = repo.get_path_distance("python", "java")
    assert dist_siblings == 2.0
    
    # NLP and Generative AI are related (RELATED_TO, weight 0.95 -> cost ~1.05)
    dist_nlp_genai = repo.get_path_distance("nlp", "generative_ai")
    assert pytest.approx(dist_nlp_genai, 0.01) == 1.05
    
    # Self-distance should be 0.0
    assert repo.get_path_distance("python", "python") == 0.0
    
    # Non-existent node distance should be infinity
    assert repo.get_path_distance("python", "non_existent_skill") == float("inf")

def test_duplicate_nodes_validation():
    """Verify initialization fails when duplicate nodes are defined."""
    duplicate_taxonomy = {
        "nodes": [
            {"id": "python", "name": "Python", "type": "language"},
            {"id": "python", "name": "Python Duplicate", "type": "language"}
        ],
        "edges": []
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False, encoding="utf-8") as temp_file:
        json.dump(duplicate_taxonomy, temp_file)
        temp_file_path = temp_file.name

    try:
        repo = NetworkXSkillGraphRepository()
        with pytest.raises(DuplicateNodeError) as excinfo:
            repo.initialize(temp_file_path)
        assert "Duplicate node ID detected" in str(excinfo.value)
    finally:
        os.remove(temp_file_path)

def test_missing_node_references_validation():
    """Verify initialization fails when edges reference undefined nodes."""
    invalid_edge_taxonomy = {
        "nodes": [
            {"id": "python", "name": "Python", "type": "language"},
            {"id": "programming", "name": "Programming", "type": "category"}
        ],
        "edges": [
            {
                "source": "programming",
                "target": "java",  # Java does not exist in nodes list
                "relation_type": "PARENT_OF",
                "weight": 1.0
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w+", delete=False, encoding="utf-8") as temp_file:
        json.dump(invalid_edge_taxonomy, temp_file)
        temp_file_path = temp_file.name

    try:
        repo = NetworkXSkillGraphRepository()
        with pytest.raises(MissingNodeReferenceError) as excinfo:
            repo.initialize(temp_file_path)
        assert "references undefined target node" in str(excinfo.value)
    finally:
        os.remove(temp_file_path)

def test_new_relation_types():
    """Verify that the new relation types (REQUIRES and USED_WITH) load and operate correctly."""
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    
    # 1. Test REQUIRES: react_js requires javascript
    assert repo.has_relationship("react_js", "javascript", relation_type="REQUIRES")
    
    # 2. Test USED_WITH: react_js used with node_js (should be bidirectional)
    assert repo.has_relationship("react_js", "node_js", relation_type="USED_WITH")
    assert repo.has_relationship("node_js", "react_js", relation_type="USED_WITH")

