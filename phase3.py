from app.knowledge_graph.repositories.networkx_repository import NetworkXSkillGraphRepository


repo = NetworkXSkillGraphRepository()


print("Exists:", repo.skill_exists("FastAPI"))
print("Resolved:", repo.resolve_skill_id("FastAPI"))