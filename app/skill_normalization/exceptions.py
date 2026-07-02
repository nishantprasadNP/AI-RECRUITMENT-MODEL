"""
Custom exceptions for the Skill Normalization module in ARIS.
"""

class SkillNormalizationError(Exception):
    """Base exception for all skill normalization errors."""
    pass


class AliasFileNotFoundError(SkillNormalizationError):
    """Exception raised when the aliases configuration JSON file is not found."""
    pass


class InvalidAliasFormatError(SkillNormalizationError):
    """Exception raised when the aliases file has an invalid structure or parse error."""
    pass
