import json

from app.models.resume_schema import ResumeProfile
from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine

with open(
    "data/extracted_profiles/nishant_prasad.json",
    "r",
    encoding="utf-8"
) as f:
    data = json.load(f)

profile = ResumeProfile.model_validate(data)

repo = NetworkXSkillGraphRepository()
repo.initialize("data/skill_graph/skills_taxonomy.json")

service = SkillGraphService(repo)

engine = SkillInferenceEngine(service)

result = engine.infer_skills(profile.skills)

print("\nEXPLICIT")
print(result["explicit_skills"])

print("\nINFERRED")
print(result["inferred_skills"])