class SkillGraphError(Exception):
    """Base exception for all skill graph errors."""
    pass

class GraphInitializationError(SkillGraphError):
    """Raised when the graph fails to initialize or load."""
    pass

class DuplicateNodeError(GraphInitializationError):
    """Raised when duplicate node IDs are detected in the taxonomy."""
    pass

class MissingNodeReferenceError(GraphInitializationError):
    """Raised when an edge references a node ID that is not defined in the taxonomy."""
    pass
