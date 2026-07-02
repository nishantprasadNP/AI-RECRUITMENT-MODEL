from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


class SkillRequirementString(str):
    """
    Backward-compatible string subclass for SkillRequirement.
    Behaves like a normal string for downstream engines but carries
    importance and reason attributes.
    """
    def __new__(cls, skill: str, importance: float, reason: str):
        obj = super().__new__(cls, skill)
        obj.importance = importance
        obj.reason = reason
        return obj

    def __reduce__(self):
        return (self.__class__, (str(self), self.importance, self.reason))

    def __repr__(self):
        return f"SkillRequirement(skill={str(self)!r}, importance={self.importance}, reason={self.reason!r})"


class SkillRequirement(BaseModel):
    """
    Structured skill requirement model containing importance and reason.
    """
    skill: str = Field(..., description="The name of the skill.")
    importance: float = Field(..., description="Weight / importance score between 1.0 and 10.0.")
    reason: str = Field(..., description="The reason why this skill is required or preferred.")

    @field_validator("skill", mode="before")
    @classmethod
    def validate_skill(cls, v):
        if not isinstance(v, str):
            raise ValueError("skill must be a string")
        v = v.strip()
        if not v:
            raise ValueError("skill cannot be empty")
        return v

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v):
        if not (1.0 <= v <= 10.0):
            raise ValueError("importance must be between 1.0 and 10.0")
        return v


class EducationRequirement(BaseModel):
    """
    Represents the education credentials required for the job.
    """
    degree: Optional[str] = Field(default=None, description="The required degree type, e.g. B.Tech, M.S.")
    field: Optional[str] = Field(default=None, description="The field of study or major, e.g. Computer Science.")


class HiddenHiringSignals(BaseModel):
    """
    Inferred implicit signals from the JD regarding operational style.
    """
    autonomy_required: bool = Field(default=False, description="Whether the role requires high autonomy and independent work.")
    client_facing: bool = Field(default=False, description="Whether the role involves direct client interaction.")
    research_oriented: bool = Field(default=False, description="Whether the role requires scientific research or literature reviews.")
    innovation_focused: bool = Field(default=False, description="Whether the role is focused heavily on R&D and creating new things.")
    startup_environment: bool = Field(default=False, description="Whether the role requires thrive-in-chaos/fast-paced startup operations.")
    high_ownership: bool = Field(default=False, description="Whether the role demands taking high levels of personal ownership over tasks.")


class JobProfile(BaseModel):
    """
    The complete extracted and validated job description hiring profile.
    """
    title: Optional[str] = None
    required_skills: List[SkillRequirement] = Field(default_factory=list, description="List of mandatory skills for performing the role.")
    preferred_skills: List[SkillRequirement] = Field(default_factory=list, description="List of preferred or beneficial skills (nice-to-have).")
    normalized_required_skills: List[SkillRequirement] = Field(default_factory=list, description="Normalized list of mandatory skills for performing the role.")
    normalized_preferred_skills: List[SkillRequirement] = Field(default_factory=list, description="Normalized list of preferred or beneficial skills.")
    canonical_to_raw_map: Dict[str, Any] = Field(default_factory=dict, description="Maps canonical skills back to original raw names and confidence.")
    critical_skills: List[str] = Field(default_factory=list, description="Top 5 most important skills for ranking candidates.")
    experience_required: Optional[int] = Field(default=None, description="Minimum years of experience required.")
    education: Optional[EducationRequirement] = Field(default=None, description="Academic degree and field of study requirements.")
    leadership: bool = Field(default=False, description="True if role requires leadership, mentoring, or project ownership.")
    seniority_level: str = Field(description="Inferred seniority level (intern, entry, junior, mid, senior, lead, manager, director).")
    responsibility_themes: List[str] = Field(default_factory=list, description="Major work categories/themes (limit to 10).")
    domain_knowledge: List[str] = Field(default_factory=list, description="Industry or domain expertise (e.g. FinTech, Healthcare).")
    soft_skills: List[str] = Field(default_factory=list, description="Extracted or strongly implied soft skills.")
    tools_and_technologies: List[str] = Field(default_factory=list, description="Frameworks, libraries, platforms, databases, cloud providers, software tools.")
    hidden_hiring_signals: HiddenHiringSignals = Field(description="Implicit hiring signal indicators.")
    role_complexity_score: int = Field(description="Role complexity score from 1 (simple) to 10 (highly strategic).")
    future_potential_signals: List[str] = Field(default_factory=list, description="Employer values indicators (adaptability, curiosity, growth potential).")
    job_summary: str = Field(description="A concise summary of the job and core objectives.")

    @field_validator("required_skills", mode="before")
    @classmethod
    def validate_required_skills(cls, v):
        if not isinstance(v, list):
            return v
        validated = []
        for item in v:
            if isinstance(item, str):
                validated.append({
                    "skill": item,
                    "importance": 5.0,
                    "reason": "Required skill"
                })
            elif isinstance(item, dict):
                validated.append({
                    "skill": item.get("skill"),
                    "importance": item.get("importance", 5.0),
                    "reason": item.get("reason", "Required skill")
                })
            else:
                validated.append(item)
        return validated

    @field_validator("preferred_skills", mode="before")
    @classmethod
    def validate_preferred_skills(cls, v):
        if not isinstance(v, list):
            return v
        validated = []
        for item in v:
            if isinstance(item, str):
                validated.append({
                    "skill": item,
                    "importance": 5.0,
                    "reason": "Preferred skill"
                })
            elif isinstance(item, dict):
                validated.append({
                    "skill": item.get("skill"),
                    "importance": item.get("importance", 5.0),
                    "reason": item.get("reason", "Preferred skill")
                })
            else:
                validated.append(item)
        return validated

    def __getattribute__(self, name):
        val = super().__getattribute__(name)
        if name in ("required_skills", "preferred_skills", "normalized_required_skills", "normalized_preferred_skills"):
            try:
                if isinstance(val, list):
                    return [
                        SkillRequirementString(req.skill, req.importance, req.reason)
                        if isinstance(req, SkillRequirement) else req
                        for req in val
                    ]
            except Exception:
                pass
        return val
