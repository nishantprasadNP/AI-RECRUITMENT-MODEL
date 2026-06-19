from pydantic import BaseModel, Field


class RoleProfile(BaseModel):
    """
    Represents the classified role profile for a candidate or job description.
    """
    role_family: str = Field(
        description="The broad industry role family category, e.g., 'software_engineering'."
    )
    specialization: str = Field(
        description="The specific role specialization or focus area, e.g., 'backend_engineer'."
    )
    seniority: str = Field(
        description="The seniority level classification, e.g., 'mid_level'."
    )
    evaluation_profile: str = Field(
        description="The target profile identifier for scoring and mapping, e.g., 'mid_backend'."
    )
