import pytest
from app.models.resume_schema import ResumeProfile, Project
from app.experience_analysis.complexity_calculator import ComplexityCalculator


def test_contains_skill_helper():
    """Verify boundary-safe regex matching for skill search."""
    calc = ComplexityCalculator()
    
    # Standard matches
    assert calc._contains_skill("Python", "Python developer") is True
    assert calc._contains_skill("Python", "Wrote code in python.") is True
    
    # Boundary tests (no substrings)
    assert calc._contains_skill("Go", "Google Cloud") is False
    assert calc._contains_skill("Go", "Django web app") is False
    assert calc._contains_skill("Go", "Let's Go!") is True
    
    # Special characters
    assert calc._contains_skill("C++", "C++ Development") is True
    assert calc._contains_skill(".NET", "Using .NET Core") is True


def test_get_project_categories_helper():
    """Verify that technologies are correctly categorized and deduplicated."""
    calc = ComplexityCalculator()
    
    techs = ["React.js", "FastAPI", "MongoDB", "react", "AWS"]
    categories = calc._get_project_categories(techs)
    
    # Categories: React/react -> FRONTEND, FastAPI -> BACKEND, MongoDB -> DATABASE, AWS -> CLOUD
    assert categories == {"FRONTEND", "BACKEND", "DATABASE", "CLOUD"}


def test_calculate_project_complexity_base():
    """Verify that a minimal project gets the base score of 2.0."""
    calc = ComplexityCalculator()
    
    proj = Project(name="Test Project")
    # Base = 2.0, no bonuses
    assert calc.calculate_project_complexity(proj) == 2.0


def test_calculate_project_complexity_bonuses():
    """Verify calculation of various project complexity bonuses."""
    calc = ComplexityCalculator()

    # 1. Technology Category Bonus (+1.0 per unique category, max 3.0)
    # React (FRONTEND), FastAPI (BACKEND) -> 2.0 bonus
    proj_tech = Project(
        name="Tech Project",
        technologies=["React", "FastAPI"]
    )
    assert calc.calculate_project_complexity(proj_tech) == 4.0  # 2.0 base + 2.0 category

    # 2. Domain Complexity Bonus (+1.0 per keyword, max 2.0)
    # Keywords: "distributed", "concurrency" -> 2.0 bonus
    proj_domain = Project(
        name="Domain Project",
        description="A distributed system with high concurrency."
    )
    assert calc.calculate_project_complexity(proj_domain) == 4.0  # 2.0 base + 2.0 domain

    # 3. Deployment Bonus (+1.0 per deployment/infra matching, max 2.0)
    # AWS, Docker -> 2.0 bonus
    proj_deploy = Project(
        name="Deploy Project",
        technologies=["AWS"],
        description="Using Docker."
    )
    # Technologies: AWS (CLOUD -> +1.0 category)
    # Deployment matches: AWS, Docker -> +2.0 deployment
    assert calc.calculate_project_complexity(proj_deploy) == 5.0  # 2.0 base + 1.0 category + 2.0 deployment

    # 4. Description Quality Bonus (+0.25 per engineering indicator, max 1.0)
    # Indicators: "designed", "implemented", "optimized", "deployed" -> 4 matches -> 1.0 bonus
    proj_desc = Project(
        name="Desc Project",
        description="designed, implemented, optimized, and deployed code."
    )
    # Deployment matches: None -> +0.0 deployment
    # Description quality matches: designed, implemented, optimized, deployed -> 4 * 0.25 = +1.0 description
    assert calc.calculate_project_complexity(proj_desc) == 3.0  # 2.0 base + 1.0 description

    # 5. Advanced Skill Bonus (+1.0 if any match, max 1.0)
    # Advanced skill: "transformer" -> 1.0 bonus
    proj_adv = Project(
        name="Advanced Project",
        description="Built a transformer model."
    )
    # Domain matches: "machine learning" is NOT matched, but "transformer" is advanced
    # Advanced skill matched -> +1.0
    assert calc.calculate_project_complexity(proj_adv) == 3.0  # 2.0 base + 1.0 advanced


def test_calculate_project_complexity_capping():
    """Verify that complexity score is capped at 10.0."""
    calc = ComplexityCalculator()
    
    # Highly complex project with multiple high-score features
    proj = Project(
        name="Mega System",
        technologies=["React.js", "FastAPI", "MongoDB", "Docker", "AWS", "Kafka"],
        # Categories: React.js (FRONTEND), FastAPI (BACKEND), MongoDB (DATABASE), Docker (DEVOPS), AWS (CLOUD), Kafka (DISTRIBUTED_SYSTEMS)
        # Unique categories: 6 -> category bonus capped at 3.0
        # Deployment techs: Docker, AWS -> +2.0 deployment bonus
        description="designed, implemented, and optimized a distributed, scalable deep learning pipeline using yolo and transformer models.",
        # Domain keywords: distributed, scalable, deep learning, pipeline -> 4 matches -> capped at 2.0
        # Quality indicators: designed, implemented, optimized, pipeline -> 4 matches -> +1.0 description bonus
        # Advanced skills: yolo, transformer, deep learning, distributed systems -> matches -> +1.0 advanced skill bonus
    )
    # Total score = 2.0 (base) + 3.0 (category) + 2.0 (domain) + 2.0 (deployment) + 1.0 (description) + 1.0 (advanced) = 11.0
    # Capped at 10.0
    assert calc.calculate_project_complexity(proj) == 10.0


def test_get_skill_complexity_normalization_and_selection():
    """Verify that get_skill_complexity selects the highest score and normalizes it correctly."""
    calc = ComplexityCalculator()
    
    # Project 1: Low complexity (Python Backend)
    p1 = Project(
        name="Simple Script",
        technologies=["Python"],  # category Backend -> +1.0
        description="Simple script."  # base only
    )  # Score = 2.0 base + 1.0 category = 3.0
    
    # Project 2: High complexity (Python AI/ML Pipeline)
    p2 = Project(
        name="Complex ML Pipeline",
        technologies=["Python", "Scikit-learn", "Docker"],
        # Categories: Python (BACKEND), Scikit-learn (MACHINE_LEARNING), Docker (DEVOPS) -> 3 categories -> +3.0 category bonus
        # Deployment: Docker -> +1.0 deployment bonus
        description="designed a scalable machine learning pipeline."
        # Domain: scalable, machine learning, pipeline -> 3 matches -> capped at 2.0 domain bonus
        # Indicators: designed, scalable, pipeline -> 3 matches -> +0.75 description bonus
    )  # Score = 2.0 base + 3.0 category + 2.0 domain + 1.0 deployment + 0.75 description = 8.75
    
    profile = ResumeProfile(
        skills=["Python"],
        projects=[p1, p2]
    )
    
    # "Python" is matched in both projects.
    # Highest score is 8.75.
    # Normalized score should be 8.75 / 10.0 = 0.875
    assert pytest.approx(calc.get_skill_complexity("Python", profile)) == 0.875


def test_get_skill_complexity_fallback():
    """Verify safe fallback (0.0) when no projects exist or skill is missing."""
    calc = ComplexityCalculator()
    
    # None profile
    assert calc.get_skill_complexity("Python", None) == 0.0
    
    # Profile with None/missing projects (defaults to empty list in Pydantic)
    profile_no_projects = ResumeProfile(skills=["Python"])
    assert calc.get_skill_complexity("Python", profile_no_projects) == 0.0
    
    # Profile with empty projects list
    profile_empty = ResumeProfile(skills=["Python"], projects=[])
    assert calc.get_skill_complexity("Python", profile_empty) == 0.0
    
    # Skill not present in any projects
    p1 = Project(name="Project A", technologies=["Java"], description="Java project.")
    profile_no_match = ResumeProfile(skills=["Python"], projects=[p1])
    assert calc.get_skill_complexity("Python", profile_no_match) == 0.0
