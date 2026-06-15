from pydantic import BaseModel, Field
from typing import List, Optional

class SkillNode(BaseModel):
    id: str = Field(..., description="Unique slugified lowercase identifier")
    name: str = Field(..., description="Display name of the skill")
    type: str = Field(..., description="Type of skill: domain, category, language, framework, library, tool, etc.")
    description: Optional[str] = Field(None, description="Brief explanation of the skill")
    synonyms: List[str] = Field(default_factory=list, description="Alternative names for parsing/matching")

class SkillEdge(BaseModel):
    source: str = Field(..., description="ID of the source skill")
    target: str = Field(..., description="ID of the target skill")
    relation_type: str = Field(..., description="Type of relationship: PARENT_OF, RELATED_TO, BELONGS_TO_DOMAIN")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Strength or weight of the relationship")
