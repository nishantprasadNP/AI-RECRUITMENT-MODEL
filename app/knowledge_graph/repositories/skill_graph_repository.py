from abc import ABC, abstractmethod
from typing import List, Optional
from app.knowledge_graph.models import SkillNode, SkillEdge

class ISkillGraphRepository(ABC):
    """
    Interface definition for the Skill Knowledge Graph repository layer.
    Ensures decoupled query logic and simple future database migration (e.g., to Neo4j).
    """

    @abstractmethod
    def initialize(self, data_path: str) -> None:
        """
        Loads and initializes the graph from the given database/taxonomy file path.
        
        Args:
            data_path: Path to the taxonomy file or connection string.
            
        Raises:
            GraphInitializationError: If validation fails or loading fails.
        """
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[SkillNode]:
        """
        Retrieves a node by its unique identifier.
        
        Args:
            node_id: Slugified lowercase identifier.
            
        Returns:
            The SkillNode instance if found, otherwise None.
        """
        pass

    @abstractmethod
    def get_all_nodes(self) -> List[SkillNode]:
        """
        Retrieves all skill nodes in the graph.
        
        Returns:
            List of all SkillNode instances.
        """
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[SkillNode]:
        """
        Retrieves direct neighboring nodes of a skill, optionally filtered by relationship type.
        
        Args:
            node_id: Slugified lowercase identifier.
            relation_type: Optional relation category filter (e.g. 'RELATED_TO', 'PARENT_OF').
            
        Returns:
            List of adjacent SkillNode instances.
        """
        pass

    @abstractmethod
    def get_parents(self, node_id: str) -> List[SkillNode]:
        """
        Retrieves the parent nodes for a given skill (nodes that have PARENT_OF pointing to node_id).
        
        Args:
            node_id: Slugified lowercase identifier.
            
        Returns:
            List of parent SkillNode instances.
        """
        pass

    @abstractmethod
    def get_children(self, node_id: str) -> List[SkillNode]:
        """
        Retrieves the child nodes for a given skill (nodes that node_id has a PARENT_OF relationship to).
        
        Args:
            node_id: Slugified lowercase identifier.
            
        Returns:
            List of child SkillNode instances.
        """
        pass

    @abstractmethod
    def get_path_distance(self, source_id: str, target_id: str) -> float:
        """
        Calculates the shortest path distance between two nodes.
        
        Args:
            source_id: Slugified lowercase identifier of the starting node.
            target_id: Slugified lowercase identifier of the ending node.
            
        Returns:
            A float representing the distance. Returns infinity (float('inf')) if no path exists.
        """
        pass

    @abstractmethod
    def has_relationship(self, source_id: str, target_id: str, relation_type: Optional[str] = None) -> bool:
        """
        Checks if a relationship exists between two nodes.
        
        Args:
            source_id: ID of the source node.
            target_id: ID of the target node.
            relation_type: Optional filter for relationship type.
            
        Returns:
            True if relationship exists, False otherwise.
        """
        pass
