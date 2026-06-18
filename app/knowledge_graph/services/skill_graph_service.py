import logging
from typing import List, Optional
from app.knowledge_graph.repositories.skill_graph_repository import ISkillGraphRepository
from app.knowledge_graph.models import SkillNode

logger = logging.getLogger("app.knowledge_graph.services.skill_graph_service")

class SkillGraphService:
    """
    Domain service orchestrating operations on the Skill Knowledge Graph.
    Acts as the entry point for high-level components to query taxonomical relations,
    perform name resolution (synonyms mapping), and traverse hierarchies.
    """

    def __init__(self, repository: ISkillGraphRepository) -> None:
        self._repo = repository

    def _resolve_skill_id(self, skill: str) -> Optional[str]:
        """
        Resolves a raw skill string (e.g., 'Py', 'Frontend Development', 'python3') 
        to its canonical node ID in the graph using ID, Name, or Synonyms.
        Returns None if the skill is not found.
        """
        if not skill:
            return None

        # Clean and normalize the query
        normalized = skill.lower().strip()
        slugified = normalized.replace(" ", "_")

        # 1. Direct ID lookup
        if self._repo.get_node(slugified) is not None:
            return slugified

        # 2. Case-insensitive lookup by name or synonym
        for node in self._repo.get_all_nodes():
            if node.name.lower() == normalized:
                return node.id
            if any(syn.lower() == normalized for syn in node.synonyms):
                return node.id

        return None

    def skill_exists(self, skill: str) -> bool:
        """
        Checks if a skill exists in the graph by ID, name, or synonym.
        
        Args:
            skill: Raw skill string to check.
            
        Returns:
            True if the skill exists in the taxonomy, False otherwise.
        """
        return self._resolve_skill_id(skill) is not None

    def get_parents(self, skill: str) -> List[SkillNode]:
        """
        Retrieves direct parents of the specified skill.
        
        Args:
            skill: Raw skill string.
            
        Returns:
            List of parent SkillNode instances.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []
        return self._repo.get_parents(resolved_id)

    def get_children(self, skill: str) -> List[SkillNode]:
        """
        Retrieves direct children of the specified skill.
        
        Args:
            skill: Raw skill string.
            
        Returns:
            List of child SkillNode instances.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []
        return self._repo.get_children(resolved_id)

    def get_ancestors(self, skill: str) -> List[SkillNode]:
        """
        Retrieves all recursive ancestors of the specified skill (parents, parents of parents, etc.).
        Uses Breadth-First Search (BFS) to traverse up the taxonomy.
        
        Args:
            skill: Raw skill string.
            
        Returns:
            List of ancestor SkillNode instances.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []

        ancestors: List[SkillNode] = []
        visited = {resolved_id}
        queue = [resolved_id]

        while queue:
            current_id = queue.pop(0)
            parents = self._repo.get_parents(current_id)
            for parent in parents:
                if parent.id not in visited:
                    visited.add(parent.id)
                    ancestors.append(parent)
                    queue.append(parent.id)

        return ancestors

    def get_descendants(self, skill: str) -> List[SkillNode]:
        """
        Retrieves all recursive descendants of the specified skill (children, children of children, etc.).
        Uses Breadth-First Search (BFS) to traverse down the taxonomy.
        
        Args:
            skill: Raw skill string.
            
        Returns:
            List of descendant SkillNode instances.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []

        descendants: List[SkillNode] = []
        visited = {resolved_id}
        queue = [resolved_id]

        while queue:
            current_id = queue.pop(0)
            children = self._repo.get_children(current_id)
            for child in children:
                if child.id not in visited:
                    visited.add(child.id)
                    descendants.append(child)
                    queue.append(child.id)

        return descendants

    def has_relationship(
        self,
        source_skill: str,
        target_skill: str,
        relation_type: str
    ) -> bool:
        """
        Checks if a directed relationship of the specified type exists between two skills.
        Resolves raw skill strings (name or synonyms) to their canonical IDs first.
        """
        source_id = self._resolve_skill_id(source_skill)
        target_id = self._resolve_skill_id(target_skill)
        if not source_id or not target_id:
            return False
        return self._repo.has_relationship(source_id, target_id, relation_type)

    def get_canonical_name(self, skill: str) -> Optional[str]:
        """
        Resolves a raw skill string to its canonical name in the graph.
        Returns None if the skill cannot be resolved.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            return None
        node = self._repo.get_node(resolved_id)
        return node.name if node else None

