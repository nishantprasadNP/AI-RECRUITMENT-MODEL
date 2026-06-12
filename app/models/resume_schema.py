from pydantic import BaseModel, Field
from typing import List, Optional

class Skill(BaseModel):
    """
    Represents a specific skill.
    """
    name: str = Field(description="Normalized name of the skill.")

class Experience(BaseModel):
    """
    Represents a professional experience entry on a resume.
    """
    role: Optional[str] = Field(default=None, description="The job title or role held.")
    company: Optional[str] = Field(default=None, description="Name of the company or organization.")
    start_date: Optional[str] = Field(default=None, description="Start date of employment (e.g. June 2025, 06/2025).")
    end_date: Optional[str] = Field(default=None, description="End date of employment or 'Present' (e.g. July 2025, 07/2025).")
    duration: Optional[str] = Field(default=None, description="Total duration of employment (e.g. 2 months, 2 years).")
    description: Optional[str] = Field(default=None, description="Detailed description of responsibilities and accomplishments.")

class Project(BaseModel):
    """
    Represents a project worked on by the candidate.
    """
    name: str = Field(description="Name of the project.")
    technologies: List[str] = Field(default_factory=list, description="List of technologies, frameworks, and programming languages used in the project.")
    description: Optional[str] = Field(default=None, description="Brief summary of what the project does and its goals.")

class Certification(BaseModel):
    """
    Represents a professional certification or license.
    """
    name: str = Field(description="Official name of the certification.")
    issuer: Optional[str] = Field(default=None, description="Organization or body that issued the certification.")
    year: Optional[str] = Field(default=None, description="Year the certification was obtained.")

class Education(BaseModel):
    """
    Represents an educational qualification entry.
    """
    degree: Optional[str] = Field(default=None, description="Degree or credential obtained (e.g. B.Tech, B.S., M.S., High School Diploma).")
    institution: Optional[str] = Field(default=None, description="Name of the school, college, or university.")
    field: Optional[str] = Field(default=None, description="Field of study or major (e.g. Computer Science, Information Technology).")
    graduation_year: Optional[str] = Field(default=None, description="Year of graduation or expected graduation (e.g. 2027, 2023).")

class Achievement(BaseModel):
    """
    Represents a candidate's achievement (awards, hackathons, publications, scholarships, etc.).
    """
    title: str = Field(description="The achievement details (e.g. Won National Hackathon, AIR 15120 in JEE Main).")
    category: Optional[str] = Field(default=None, description="Type of achievement (e.g. Award, Hackathon, Publication, Scholarship, Recognition).")

class ResumeProfile(BaseModel):
    """
    The complete extracted candidate resume profile.
    """
    name: Optional[str] = Field(default=None, description="Candidate's full name.")
    skills: List[str] = Field(default_factory=list, description="Unique, normalized list of candidate skills.")
    experience: List[Experience] = Field(default_factory=list, description="List of professional work experience entries.")
    projects: List[Project] = Field(default_factory=list, description="List of projects completed by the candidate.")
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications.")
    certifications: List[Certification] = Field(default_factory=list, description="List of certifications obtained.")
    achievements: List[str] = Field(default_factory=list, description="List of achievements, hackathons, publications, and awards (as strings).")
