import os
import json
import logging
from typing import List, Optional
import networkx as nx

from app.knowledge_graph.repositories.skill_graph_repository import ISkillGraphRepository
from app.knowledge_graph.models import SkillNode, SkillEdge
from app.knowledge_graph.exceptions import (
    GraphInitializationError,
    DuplicateNodeError,
    MissingNodeReferenceError
)

logger = logging.getLogger("app.knowledge_graph.repositories.networkx_repository")

class NetworkXSkillGraphRepository(ISkillGraphRepository):
    """
    In-memory NetworkX implementation of the ISkillGraphRepository.
    Loads a skill taxonomy from a JSON file, validates integrity, and constructs a directed graph.
    """

    def __init__(self) -> None:
        self._graph = nx.DiGraph()

    def initialize(self, data_path: str) -> None:
        """
        Loads the taxonomy JSON file, validates nodes and edges, and constructs the NetworkX graph.
        
        Args:
            data_path: Absolute or relative path to the taxonomy JSON file.
            
        Raises:
            GraphInitializationError: If the file does not exist, is invalid JSON, or fails integrity checks.
        """
        if not os.path.exists(data_path):
            raise GraphInitializationError(f"Taxonomy file not found at: {data_path}")

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise GraphInitializationError(f"Failed to parse taxonomy JSON file: {str(e)}") from e
        except Exception as e:
            raise GraphInitializationError(f"Unexpected error reading taxonomy file: {str(e)}") from e

        raw_nodes = data.get("nodes", [])
        raw_edges = data.get("edges", [])

        # Reset graph state
        self._graph.clear()

        # 1. Parse and Validate Nodes
        parsed_nodes: List[SkillNode] = []
        seen_ids = set()

        for node_index, node_data in enumerate(raw_nodes):
            try:
                # Basic Pydantic validation
                node = SkillNode.model_validate(node_data)
            except Exception as e:
                raise GraphInitializationError(f"Validation error in node at index {node_index}: {str(e)}") from e

            # Validate duplicate nodes
            if node.id in seen_ids:
                raise DuplicateNodeError(f"Duplicate node ID detected during initialization: '{node.id}'")
            
            seen_ids.add(node.id)
            parsed_nodes.append(node)

        # 2. Parse and Validate Edges
        parsed_edges: List[SkillEdge] = []
        for edge_index, edge_data in enumerate(raw_edges):
            try:
                edge = SkillEdge.model_validate(edge_data)
            except Exception as e:
                raise GraphInitializationError(f"Validation error in edge at index {edge_index}: {str(e)}") from e

            # Validate missing references (source and target must exist in the node set)
            if edge.source not in seen_ids:
                raise MissingNodeReferenceError(
                    f"Edge at index {edge_index} references undefined source node: '{edge.source}'"
                )
            if edge.target not in seen_ids:
                raise MissingNodeReferenceError(
                    f"Edge at index {edge_index} references undefined target node: '{edge.target}'"
                )

            parsed_edges.append(edge)

        # 3. Build NetworkX Directed Graph
        for node in parsed_nodes:
            self._graph.add_node(node.id, model=node)

        for edge in parsed_edges:
            # Set distance cost inversely proportional to similarity weight (avoid division by zero)
            distance_cost = 1.0 / max(edge.weight, 0.01)
            
            # Add primary directed relationship
            self._graph.add_edge(
                edge.source,
                edge.target,
                relation_type=edge.relation_type,
                weight=edge.weight,
                distance_cost=distance_cost
            )

            # Bidirectional relations mapping
            if edge.relation_type in ("RELATED_TO", "USED_WITH"):
                # Add reverse edge for non-hierarchical related association in directed graph
                self._graph.add_edge(
                    edge.target,
                    edge.source,
                    relation_type=edge.relation_type,
                    weight=edge.weight,
                    distance_cost=distance_cost
                )

        logger.info(
            f"Successfully initialized Skill Graph with {self._graph.number_of_nodes()} nodes "
            f"and {self._graph.number_of_edges()} edges."
        )

    def get_node(self, node_id: str) -> Optional[SkillNode]:
        """Retrieves a node by its unique identifier."""
        if not self._graph.has_node(node_id):
            return None
        return self._graph.nodes[node_id]["model"]

    def get_all_nodes(self) -> List[SkillNode]:
        """Retrieves all skill nodes in the graph."""
        return [data["model"] for _, data in self._graph.nodes(data=True)]

    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[SkillNode]:
        """Retrieves direct neighboring nodes of a skill, optionally filtered by relationship type."""
        if not self._graph.has_node(node_id):
            return []
        
        neighbors = []
        for _, target, data in self._graph.out_edges(node_id, data=True):
            if relation_type is None or data.get("relation_type") == relation_type:
                neighbors.append(self._graph.nodes[target]["model"])
        return neighbors

    def get_parents(self, node_id: str) -> List[SkillNode]:
        """Retrieves parent nodes for a given skill (directed sources of PARENT_OF, targets of BELONGS_TO_DOMAIN, or targets of REQUIRES)."""
        if not self._graph.has_node(node_id):
            return []
        
        parents = []
        # Case 1: Incoming edges where u -> node_id is PARENT_OF (u is parent)
        for source, _, data in self._graph.in_edges(node_id, data=True):
            if data.get("relation_type") == "PARENT_OF":
                parents.append(self._graph.nodes[source]["model"])
                
        # Case 2: Outgoing edges where node_id -> v is BELONGS_TO_DOMAIN (v is parent domain)
        for _, target, data in self._graph.out_edges(node_id, data=True):
            if data.get("relation_type") == "BELONGS_TO_DOMAIN":
                parents.append(self._graph.nodes[target]["model"])

        # Case 3: Outgoing edges where node_id -> v is REQUIRES (v is required dependency)
        for _, target, data in self._graph.out_edges(node_id, data=True):
            if data.get("relation_type") == "REQUIRES":
                parents.append(self._graph.nodes[target]["model"])
                
        return parents

    def get_children(self, node_id: str) -> List[SkillNode]:
        """Retrieves child nodes for a given skill (directed targets of PARENT_OF or sources of BELONGS_TO_DOMAIN)."""
        if not self._graph.has_node(node_id):
            return []
            
        children = []
        # Case 1: Outgoing edges where node_id -> v is PARENT_OF (v is child)
        for _, target, data in self._graph.out_edges(node_id, data=True):
            if data.get("relation_type") == "PARENT_OF":
                children.append(self._graph.nodes[target]["model"])
                
        # Case 2: Incoming edges where u -> node_id is BELONGS_TO_DOMAIN (u is child)
        for source, _, data in self._graph.in_edges(node_id, data=True):
            if data.get("relation_type") == "BELONGS_TO_DOMAIN":
                children.append(self._graph.nodes[source]["model"])
                
        return children

    def get_path_distance(self, source_id: str, target_id: str) -> float:
        """
        Calculates the shortest path distance between two nodes (undirected traversal).
        Returns float('inf') if no path exists.
        """
        if not self._graph.has_node(source_id) or not self._graph.has_node(target_id):
            return float("inf")
            
        if source_id == target_id:
            return 0.0
            
        try:
            # Create an undirected view of the graph to allow bidirectional pathing
            undirected_view = self._graph.to_undirected()
            return nx.shortest_path_length(
                undirected_view,
                source=source_id,
                target=target_id,
                weight="distance_cost"
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf")

    def has_relationship(self, source_id: str, target_id: str, relation_type: Optional[str] = None) -> bool:
        """Checks if a directed relationship exists between two nodes."""
        if not self._graph.has_edge(source_id, target_id):
            return False
        if relation_type is not None:
            return self._graph.edges[source_id, target_id].get("relation_type") == relation_type
        return True
