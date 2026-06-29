from app.hard_requirements.capability_resolver import CapabilityResolver
from app.hard_requirements.hard_requirement_engine import HardRequirementEngine

from app.knowledge_graph.repositories.networkx_repository import (
    NetworkXSkillGraphRepository,
)
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine

from app.models.resume_schema import ResumeProfile
from app.models.job_schema import JobProfile
from app.role_classification.models import RoleProfile


graph_repo = NetworkXSkillGraphRepository()
graph_service = SkillGraphService(graph_repo)
inference_engine = SkillInferenceEngine(graph_service)

resolver = CapabilityResolver(inference_engine)
engine = HardRequirementEngine()


resume = ResumeProfile(
    name="Test Candidate",
    skills=["FastAPI"]
)

job = JobProfile(
    title="Senior Software Engineer - FinTech Platform",
    required_skills=["Python"],      # <- ONLY THING WE CHANGE
    preferred_skills=[],

    critical_skills=[],
    experience_required=5,

    education={
        "degree": "Bachelor's",
        "field": "Computer Science"
    },

    leadership=False,
    seniority_level="senior",

    responsibility_themes=[],
    domain_knowledge=[],
    soft_skills=[],
    tools_and_technologies=[],

    hidden_hiring_signals={
        "autonomy_required": False,
        "client_facing": False,
        "research_oriented": False,
        "innovation_focused": False,
        "startup_environment": False,
        "high_ownership": False,
    },

    role_complexity_score=5,
    future_potential_signals=[],

    job_summary="Test Job"
)

role = RoleProfile(
    role_family="software_engineering",
    specialization="backend_engineer",
    seniority="mid",
    evaluation_profile="mid_backend"
)

capabilities = resolver.resolve_capabilities(resume)
print("\n=== FULL RESULT ===")
print(capabilities.model_dump())

print("\nCAPABILITIES")
print(capabilities.candidate_capabilities)

result = engine.evaluate_compliance(
    job,
    role,
    capabilities
)

print("\nRESULT")
print(result.model_dump())