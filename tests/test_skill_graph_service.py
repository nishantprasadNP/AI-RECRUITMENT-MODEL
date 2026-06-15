import os
import pytest
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService

TAXONOMY_PATH = os.path.join("data", "skill_graph", "skills_taxonomy.json")

@pytest.fixture
def skill_service():
    repo = NetworkXSkillGraphRepository()
    repo.initialize(TAXONOMY_PATH)
    return SkillGraphService(repo)

def test_skill_exists(skill_service):
    """Verify that skill_exists works for IDs, names, and synonyms."""
    # Test by ID
    assert skill_service.skill_exists("python")
    assert skill_service.skill_exists("deep_learning")

    # Test by Name (case-insensitive)
    assert skill_service.skill_exists("Python")
    assert skill_service.skill_exists("Deep Learning")
    
    # Test by Synonym
    assert skill_service.skill_exists("Py")
    assert skill_service.skill_exists("GenAI")
    assert skill_service.skill_exists("Large Language Models")

    # Test non-existent
    assert not skill_service.skill_exists("non_existent_skill_for_sure")

def test_get_parents_and_children(skill_service):
    """Verify get_parents and get_children retrieve direct relationships."""
    # Parents of python
    parents = skill_service.get_parents("Py")  # Resolves Py -> python
    parent_ids = [p.id for p in parents]
    assert "programming" in parent_ids

    # Children of programming
    children = skill_service.get_children("Programming")
    child_ids = [c.id for c in children]
    assert "python" in child_ids
    assert "java" in child_ids
    assert "cpp" in child_ids

def test_get_ancestors(skill_service):
    """Verify get_ancestors recursively retrieves all parent hierarchy nodes."""
    # generative_ai -> deep_learning -> machine_learning -> data_science (via PARENT_OF)
    # also generative_ai is child of nlp (RELATED_TO or PARENT_OF?)
    # Let's check: in taxonomy deep_learning -> generative_ai (PARENT_OF)
    # So generative_ai's ancestors should include deep_learning, machine_learning, data_science
    ancestors = skill_service.get_ancestors("generative_ai")
    ancestor_ids = [a.id for a in ancestors]
    
    assert "deep_learning" in ancestor_ids
    assert "machine_learning" in ancestor_ids
    assert "data_science" in ancestor_ids
    
    # Python -> programming -> software_engineering
    python_ancestors = skill_service.get_ancestors("python")
    py_ancestor_ids = [a.id for a in python_ancestors]
    assert "programming" in py_ancestor_ids
    assert "software_engineering" in py_ancestor_ids

def test_get_descendants(skill_service):
    """Verify get_descendants recursively retrieves all child hierarchy nodes."""
    # machine_learning descendants should include deep_learning, computer_vision, nlp, generative_ai
    descendants = skill_service.get_descendants("machine_learning")
    descendant_ids = [d.id for d in descendants]
    
    assert "deep_learning" in descendant_ids
    assert "computer_vision" in descendant_ids
    assert "nlp" in descendant_ids
    assert "generative_ai" in descendant_ids

def test_unresolved_skill_returns_empty(skill_service):
    """Verify service methods return empty list for invalid skills."""
    assert skill_service.get_parents("invalid_skill") == []
    assert skill_service.get_children("invalid_skill") == []
    assert skill_service.get_ancestors("invalid_skill") == []
    assert skill_service.get_descendants("invalid_skill") == []
