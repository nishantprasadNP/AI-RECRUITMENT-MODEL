import pytest
from typing import List, Optional
from pydantic import Field
from app.models.resume_schema import ResumeProfile, Project, Experience
from app.experience_analysis.evidence_collector import SkillEvidenceCollector
from app.knowledge_graph.services.skill_graph_service import SkillGraphService




def test_evidence_collector_empty():
    """Test collector with empty/None profiles."""
    collector = SkillEvidenceCollector()
    
    # None profile
    assert collector.collect(None) == {}
    
    # Profile with no skills
    empty_profile = ResumeProfile(skills=[])
    assert collector.collect(empty_profile) == {}


def test_evidence_collector_basic():
    """Test collector on a basic resume profile with standard skills."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI"],
        projects=[
            Project(
                name="Project A",
                technologies=["python", "Docker"],
                description="Built an API using FastAPI."
            ),
            Project(
                name="Project B",
                technologies=["FastAPI", "React"],
                description="Frontend + backend app. Python is also used here."
            )
        ],
        experience=[
            Experience(
                role="Python Developer",
                description="Wrote Python backend scripts daily."
            ),
            Experience(
                role="Software Engineer",
                description="Used FastAPI for modern microservices."
            )
        ],
        achievements=[
            "Best Python Hackathon Project",
            "Certified FastAPI Developer"
        ]
    )

    collector = SkillEvidenceCollector()
    evidence_map = collector.collect(profile)

    # Check "Python"
    assert "Python" in evidence_map
    python_evidence = evidence_map["Python"]
    assert python_evidence.skill == "Python"
    # Project A (tech contains 'python') and Project B (desc contains 'Python')
    assert python_evidence.project_count == 2
    assert sorted(python_evidence.projects) == ["Project A", "Project B"]
    # Exp 1 (role contains 'Python' and desc contains 'Python')
    assert python_evidence.professional_usage is True
    assert python_evidence.roles == ["Python Developer"]
    # Mentions count:
    # 1. skills section: "Python" (1)
    # 2. project technologies: "python" in Project A (1)
    # 3. project description: "Python" in Project B (1)
    # 4. experience descriptions: "Python" in Exp 1 (1)
    # Total = 4 mentions
    assert python_evidence.skill_mentions == 4
    # Achievements: "Best Python Hackathon Project" (1)
    assert python_evidence.achievement_mentions == 1

    # Check "FastAPI"
    assert "FastAPI" in evidence_map
    fastapi_evidence = evidence_map["FastAPI"]
    assert fastapi_evidence.skill == "FastAPI"
    # Project A (desc contains 'FastAPI') and Project B (tech contains 'FastAPI')
    assert fastapi_evidence.project_count == 2
    assert sorted(fastapi_evidence.projects) == ["Project A", "Project B"]
    # Exp 2 (desc contains 'FastAPI')
    assert fastapi_evidence.professional_usage is True
    assert fastapi_evidence.roles == ["Software Engineer"]
    # Mentions:
    # 1. skills section: "FastAPI" (1)
    # 2. project technologies: "FastAPI" in Project B (1)
    # 3. project description: "FastAPI" in Project A (1)
    # 4. experience descriptions: "FastAPI" in Exp 2 (1)
    # Total = 4
    assert fastapi_evidence.skill_mentions == 4
    # Achievements: "Certified FastAPI Developer" (1)
    assert fastapi_evidence.achievement_mentions == 1


def test_evidence_collector_word_boundaries_and_special_chars():
    """Test that skills are matched using proper word boundaries (especially short and special character skills)."""
    profile = ResumeProfile(
        skills=["Go", "C++", ".NET", "React.js"],
        projects=[
            Project(
                name="Go Project",
                technologies=["Go", "Django"],  # Django has 'go' inside it, shouldn't match 'Go'
                description="Built Google Cloud services. Gopher."  # Google has 'go' inside it, shouldn't match 'Go'
            ),
            Project(
                name="C++ Core",
                technologies=["C++", "Qt"],
                description="Embedded software written in C++development."  # C++ is matched literally even if concatenated with word char
            ),
            Project(
                name="DotNet Service",
                technologies=[".NET"],
                description="Enterprise app using .NET Core"
            )
        ],
        experience=[
            Experience(
                role="Golang Lead",
                description="Wrote Go microservices."
            )
        ],
        achievements=[
            "Winner of C++ Hackathon"
        ]
    )

    collector = SkillEvidenceCollector()
    evidence_map = collector.collect(profile)

    # "Go" checks:
    # Google (no), Django (no), Golang (no - since we require word boundary), Go (yes)
    go_evidence = evidence_map["Go"]
    assert go_evidence.project_count == 1
    assert go_evidence.projects == ["Go Project"]
    assert go_evidence.professional_usage is True
    assert go_evidence.roles == ["Golang Lead"]  # Match in exp description: "Wrote Go microservices"
    # Mentions count:
    # 1. skills: "Go" (1)
    # 2. project technologies: "Go" in Project 1 (1)
    # 3. experience descriptions: "Go" in "Wrote Go microservices." (1)
    # Total = 3
    assert go_evidence.skill_mentions == 3

    # "C++" checks:
    cpp_evidence = evidence_map["C++"]
    assert cpp_evidence.project_count == 1
    assert cpp_evidence.projects == ["C++ Core"]
    assert cpp_evidence.achievement_mentions == 1

    # ".NET" checks:
    dotnet_evidence = evidence_map[".NET"]
    assert dotnet_evidence.project_count == 1
    assert dotnet_evidence.projects == ["DotNet Service"]


def test_evidence_collector_deduplication():
    """Test that project names and roles are properly deduplicated."""
    profile = ResumeProfile(
        skills=["Python"],
        projects=[
            Project(
                name="Duplicate Name",
                technologies=["Python"],
                description="Python description."
            ),
            Project(
                name="Duplicate Name",
                technologies=["Python"],
                description="Another Python project with duplicate name."
            )
        ],
        experience=[
            Experience(
                role="Software Engineer",
                description="Python developer."
            ),
            Experience(
                role="Software Engineer",
                description="Another Python role."
            )
        ]
    )

    collector = SkillEvidenceCollector()
    evidence_map = collector.collect(profile)

    python_evidence = evidence_map["Python"]
    assert python_evidence.project_count == 1
    assert python_evidence.projects == ["Duplicate Name"]
    assert python_evidence.roles == ["Software Engineer"]


def test_evidence_collector_dynamic_experience_technologies():
    """Test that dynamic experience technologies are searched if they exist."""
    # Experience schema does not define technologies. We subclass it to add the field.
    class ExperienceWithTech(Experience):
        technologies: List[str] = Field(default_factory=list)

    exp_with_tech = ExperienceWithTech(
        role="Cloud Architect",
        description="Worked on cloud systems.",
        technologies=["AWS", "Terraform"]
    )

    profile = ResumeProfile(
        skills=["AWS"],
        experience=[exp_with_tech]
    )

    collector = SkillEvidenceCollector()
    evidence_map = collector.collect(profile)

    aws_evidence = evidence_map["AWS"]
    assert aws_evidence.professional_usage is True
    assert aws_evidence.roles == ["Cloud Architect"]


class FakeSkillGraphService(SkillGraphService):
    def __init__(self, skills_dict, relationships, canonical_names=None):
        super().__init__(None)  # type: ignore
        self._skills = skills_dict
        self._relationships = relationships
        self._canonical_names = canonical_names or {}

    def skill_exists(self, skill: str) -> bool:
        return skill in self._skills

    def has_relationship(self, source_skill: str, target_skill: str, relation_type: str) -> bool:
        return (source_skill, target_skill, relation_type) in self._relationships

    def get_canonical_name(self, skill: str) -> Optional[str]:
        return self._canonical_names.get(skill, skill)


def test_evidence_collector_dependency_propagation():
    """Verify single dependency propagation: FastAPI (4 mentions) -> Python (2.0 dependency mentions)."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI"],
        projects=[
            Project(
                name="Project A",
                technologies=["FastAPI"],
                description="FastAPI project with multiple FastAPI mentions. FastAPI FastAPI FastAPI."
            )
        ]
    )
    skills_dict = {"Python": True, "FastAPI": True}
    relationships = {("FastAPI", "Python", "REQUIRES"): True}
    canonical_names = {"Python": "Python", "FastAPI": "FastAPI"}
    fake_service = FakeSkillGraphService(skills_dict, relationships, canonical_names)

    collector = SkillEvidenceCollector(graph_service=fake_service)
    evidence_map = collector.collect(profile)

    assert "FastAPI" in evidence_map
    assert evidence_map["FastAPI"].direct_mentions == 7
    assert evidence_map["FastAPI"].dependency_mentions == 0.0
    assert evidence_map["FastAPI"].dependency_sources == []

    assert "Python" in evidence_map
    assert evidence_map["Python"].direct_mentions == 1
    assert evidence_map["Python"].dependency_mentions == 3.5  # 7 * 0.5
    assert evidence_map["Python"].dependency_sources == ["FastAPI"]


def test_evidence_collector_multiple_dependency_sources():
    """Verify multiple dependency sources: FastAPI + NumPy -> Python."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI", "NumPy"],
        projects=[
            Project(
                name="Project A",
                technologies=["FastAPI", "NumPy"],
                description="FastAPI NumPy details. NumPy FastAPI."
            )
        ]
    )
    skills_dict = {"Python": True, "FastAPI": True, "NumPy": True}
    relationships = {
        ("FastAPI", "Python", "REQUIRES"): True,
        ("NumPy", "Python", "REQUIRES"): True
    }
    canonical_names = {"Python": "Python", "FastAPI": "FastAPI", "NumPy": "NumPy"}
    fake_service = FakeSkillGraphService(skills_dict, relationships, canonical_names)

    collector = SkillEvidenceCollector(graph_service=fake_service)
    evidence_map = collector.collect(profile)

    assert "Python" in evidence_map
    assert evidence_map["Python"].dependency_mentions == 4.0  # (4 * 0.5) + (4 * 0.5)
    assert evidence_map["Python"].dependency_sources == ["FastAPI", "NumPy"]



def test_evidence_collector_one_hop_constraint():
    """Verify one-hop propagation constraint: AwesomeAPI -> FastAPI -> Python."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI", "AwesomeAPI"],
        projects=[
            Project(
                name="Project A",
                technologies=["AwesomeAPI"],
                description="AwesomeAPI AwesomeAPI."
            )
        ]
    )
    skills_dict = {"Python": True, "FastAPI": True, "AwesomeAPI": True}
    relationships = {
        ("AwesomeAPI", "FastAPI", "REQUIRES"): True,
        ("FastAPI", "Python", "REQUIRES"): True
    }
    canonical_names = {"Python": "Python", "FastAPI": "FastAPI", "AwesomeAPI": "AwesomeAPI"}
    fake_service = FakeSkillGraphService(skills_dict, relationships, canonical_names)

    collector = SkillEvidenceCollector(graph_service=fake_service)
    evidence_map = collector.collect(profile)

    assert evidence_map["FastAPI"].dependency_mentions == 2.0
    assert evidence_map["FastAPI"].dependency_sources == ["AwesomeAPI"]

    assert evidence_map["Python"].dependency_mentions == 0.5
    assert evidence_map["Python"].dependency_sources == ["FastAPI"]


def test_evidence_collector_loop_prevention():
    """Verify mutual dependencies do not cause loops/infinite recursion."""
    profile = ResumeProfile(
        skills=["SkillA", "SkillB"],
        projects=[
            Project(
                name="Project A",
                technologies=["SkillA", "SkillB"],
                description="SkillA SkillB."
            )
        ]
    )
    skills_dict = {"SkillA": True, "SkillB": True}
    relationships = {
        ("SkillA", "SkillB", "REQUIRES"): True,
        ("SkillB", "SkillA", "REQUIRES"): True
    }
    canonical_names = {"SkillA": "SkillA", "SkillB": "SkillB"}
    fake_service = FakeSkillGraphService(skills_dict, relationships, canonical_names)

    collector = SkillEvidenceCollector(graph_service=fake_service)
    evidence_map = collector.collect(profile)

    assert evidence_map["SkillA"].dependency_mentions == 1.5
    assert evidence_map["SkillA"].dependency_sources == ["SkillB"]

    assert evidence_map["SkillB"].dependency_mentions == 1.5
    assert evidence_map["SkillB"].dependency_sources == ["SkillA"]


def test_evidence_collector_edge_types_and_uniqueness():
    """Verify only REQUIRES edges propagate evidence, and sources are unique/sorted."""
    profile = ResumeProfile(
        skills=["Python", "FastAPI", "Django"],
        projects=[
            Project(
                name="Project A",
                technologies=["FastAPI", "Django"],
                description="FastAPI Django."
            )
        ]
    )
    skills_dict = {"Python": True, "FastAPI": True, "Django": True}
    relationships = {
        ("FastAPI", "Python", "REQUIRES"): True,
        ("Django", "Python", "USED_WITH"): True,
        ("Django", "Python", "RELATED_TO"): True,
    }
    canonical_names = {"Python": "Python", "FastAPI": "FastAPI", "Django": "Django"}
    fake_service = FakeSkillGraphService(skills_dict, relationships, canonical_names)

    collector = SkillEvidenceCollector(graph_service=fake_service)
    evidence_map = collector.collect(profile)

    assert evidence_map["Python"].dependency_mentions == 1.5
    assert evidence_map["Python"].dependency_sources == ["FastAPI"]

