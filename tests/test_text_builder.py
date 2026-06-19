import pytest
from app.schemas.resume_schema import (
    ResumeProfile,
    Experience,
    Project,
    Education,
    Certification
)
from app.schemas.job_schema import (
    JobProfile,
    EducationRequirement,
    HiddenHiringSignals
)
from app.embeddings.text_builder import build_resume_text, build_job_text

def test_build_resume_text_success():
    """Test building resume text from a complete ResumeProfile."""
    profile = ResumeProfile(
        name="Jane Doe",
        skills=["Python", "Machine Learning", "TensorFlow"],
        experience=[
            Experience(
                role="Software Engineer",
                company="ABC Corp",
                start_date="June 2025",
                end_date="Present",
                duration="1 year",
                description="Developing machine learning models."
            )
        ],
        projects=[
            Project(
                name="ATS System",
                technologies=["Python", "FastAPI"],
                description="An automated ATS tracking system."
            )
        ],
        education=[
            Education(
                degree="B.Tech",
                field="Computer Science",
                institution="XYZ University",
                graduation_year="2026"
            )
        ],
        certifications=[
            Certification(
                name="AWS Solutions Architect",
                issuer="Amazon Web Services",
                year="2025"
            )
        ],
        achievements=["Won National Hackathon 2025"]
    )

    text = build_resume_text(profile)
    
    # Assert section headers exist
    assert "Skills:" in text
    assert "Experience:" in text
    assert "Projects:" in text
    assert "Education:" in text
    assert "Certifications:" in text
    assert "Achievements:" in text

    # Assert content matches expectation
    assert "Python" in text
    assert "Machine Learning" in text
    assert "TensorFlow" in text
    
    assert "Software Engineer at ABC Corp (June 2025 to Present (1 year))" in text
    assert "Description: Developing machine learning models." in text
    
    assert "ATS System" in text
    assert "Technologies: Python, FastAPI" in text
    assert "Description: An automated ATS tracking system." in text
    
    assert "B.Tech in Computer Science from XYZ University (Graduated: 2026)" in text
    assert "AWS Solutions Architect issued by Amazon Web Services (2025)" in text
    assert "Won National Hackathon 2025" in text


def test_build_resume_text_empty_optional_fields():
    """Test building resume text when many fields are optional/None."""
    profile = ResumeProfile(
        name=None,
        skills=[],
        experience=[],
        projects=[],
        education=[],
        certifications=[],
        achievements=[]
    )
    
    text = build_resume_text(profile)
    assert text == ""  # All optional lists and None values result in an empty string


def test_build_resume_text_invalid_input():
    """Test input validation for build_resume_text."""
    with pytest.raises(TypeError, match="Input must be an instance of ResumeProfile"):
        build_resume_text({"skills": ["Python"]})  # dict instead of ResumeProfile


def test_build_job_text_success():
    """Test building job text from a complete JobProfile."""
    job = JobProfile(
        required_skills=["Python", "SQL"],
        preferred_skills=["AWS"],
        critical_skills=["FastAPI"],
        experience_required=3,
        education=EducationRequirement(degree="B.Tech", field="CS"),
        leadership=False,
        seniority_level="mid",
        responsibility_themes=["Backend Development"],
        domain_knowledge=["FinTech"],
        soft_skills=["Communication"],
        tools_and_technologies=["PostgreSQL"],
        hidden_hiring_signals=HiddenHiringSignals(
            autonomy_required=True,
            client_facing=False,
            research_oriented=False,
            innovation_focused=True,
            startup_environment=False,
            high_ownership=True
        ),
        role_complexity_score=5,
        future_potential_signals=["Curiosity"],
        job_summary="Looking for a mid-level backend engineer."
    )

    text = build_job_text(job)
    
    # Assert headers exist
    assert "Job Summary:" in text
    assert "Critical Skills:" in text
    assert "Required Skills:" in text
    assert "Preferred Skills:" in text
    assert "Responsibility Themes:" in text
    assert "Soft Skills:" in text
    assert "Domain Knowledge:" in text
    assert "Tools and Technologies:" in text

    # Assert content matches expectation
    assert "Looking for a mid-level backend engineer." in text
    assert "FastAPI" in text
    assert "Python" in text
    assert "SQL" in text
    assert "AWS" in text
    assert "Backend Development" in text
    assert "Communication" in text
    assert "FinTech" in text
    assert "PostgreSQL" in text


def test_build_job_text_empty_fields():
    """Test that a job profile with only seniority_level produces at least that section."""
    job = JobProfile(
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="junior",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=1,
        future_potential_signals=[],
        job_summary=""
    )

    # seniority_level="junior" is now included — text must be non-empty
    text = build_job_text(job)
    assert "junior" in text
    assert "Seniority Level" in text


def test_build_job_text_all_empty_raises():
    """Test that a fully empty job profile raises ValueError instead of returning empty string."""
    job = JobProfile(
        required_skills=[],
        preferred_skills=[],
        critical_skills=[],
        experience_required=None,
        education=None,
        leadership=False,
        seniority_level="",
        responsibility_themes=[],
        domain_knowledge=[],
        soft_skills=[],
        tools_and_technologies=[],
        hidden_hiring_signals=HiddenHiringSignals(),
        role_complexity_score=1,
        future_potential_signals=[],
        job_summary=""
    )

    with pytest.raises(ValueError, match="Job profile text is empty"):
        build_job_text(job)


def test_build_job_text_invalid_input():
    """Test input validation for build_job_text."""
    with pytest.raises(TypeError, match="Input must be an instance of JobProfile"):
        build_job_text("just a string")  # str instead of JobProfile
