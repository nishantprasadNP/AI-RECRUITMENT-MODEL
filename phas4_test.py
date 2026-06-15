from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository
from app.knowledge_graph.services.skill_graph_service import SkillGraphService
from app.knowledge_graph.inference.skill_inference_engine import SkillInferenceEngine

repo = NetworkXSkillGraphRepository()
repo.initialize("data/skill_graph/skills_taxonomy.json")

service = SkillGraphService(repo)

engine = SkillInferenceEngine(service)

result = engine.infer_skills(
    ["CNN", "YOLO", "OpenCV"]
)

print(result)