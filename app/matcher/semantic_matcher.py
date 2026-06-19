"""
Backward-compatibility shim — app.matcher.semantic_matcher is preserved so
that existing tests still work. New code should import from app.matching.
"""
from app.matching.semantic_matcher import SemanticMatcher, SemanticMatchingError  # noqa: F401
