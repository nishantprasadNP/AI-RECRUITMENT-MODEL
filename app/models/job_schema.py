from pydantic import BaseModel, Field
from typing import List, Optional

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
    required_skills: List[str] = Field(default_factory=list, description="List of mandatory skills for performing the role.")
    preferred_skills: List[str] = Field(default_factory=list, description="List of preferred or beneficial skills (nice-to-have).")
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
