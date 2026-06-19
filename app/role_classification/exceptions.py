from app.core.exceptions import ARISError


class RoleClassificationError(ARISError):
    """Base exception for all role classification errors."""
    pass


class RoleFamilyDetectionError(RoleClassificationError):
    """Raised when detection of the role family fails."""
    pass


class SpecializationDetectionError(RoleClassificationError):
    """Raised when detection of the specialization fails."""
    pass


class SeniorityDetectionError(RoleClassificationError):
    """Raised when detection of the seniority level fails."""
    pass
