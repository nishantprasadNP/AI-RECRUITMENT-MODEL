import logging
from typing import List, Dict, Set
from app.knowledge_graph.services.skill_graph_service import SkillGraphService

logger = logging.getLogger("app.knowledge_graph.inference.skill_inference_engine")

class SkillInferenceEngine:
    """
    Inference Engine to deduce implicit parent and domain skills from explicitly declared skills.
    Uses the SkillGraphService to safely resolve skills, traverse ancestors, and deduplicate results.
    """

    def __init__(self, skill_service: SkillGraphService) -> None:
        """
        Initializes the SkillInferenceEngine.
        
        Args:
            skill_service: The service layer orchestrating the Skill Knowledge Graph.
        """
        self._skill_service = skill_service

    def infer_skills(self, explicit_inputs: List[str]) -> Dict[str, List[str]]:
        """
        Analyzes a list of raw skill strings, resolves them to canonical graph nodes,
        traverses their ancestor hierarchies to infer parent skills, and returns 
        a deduplicated structure of explicit and inferred skills.
        
        Args:
            explicit_inputs: List of raw skill strings (e.g., ["CNN", "YOLO", "OpenCV"]).
            
        Returns:
            A dictionary in the format:
            {
                "explicit_skills": List of resolved canonical explicit skill names,
                "inferred_skills": List of resolved canonical inferred skill names
            }
        """
        resolved_explicit_names: Set[str] = set()
        inferred_names: Set[str] = set()

        for raw_skill in explicit_inputs:
            # 1. Validate skill existence using skill_exists()
            if not self._skill_service.skill_exists(raw_skill):
                logger.warning(f"Skill '{raw_skill}' is unknown and will be ignored safely.")
                continue

            # 2. Resolve canonical skill ID & retrieve node
            resolved_id = self._skill_service._resolve_skill_id(raw_skill)
            if not resolved_id:
                continue

            node = self._skill_service._repo.get_node(resolved_id)
            if not node:
                continue

            canonical_name = node.name
            resolved_explicit_names.add(canonical_name)

            # 3. Retrieve ancestors using get_ancestors()
            ancestors = self._skill_service.get_ancestors(canonical_name)
            for ancestor in ancestors:
                inferred_names.add(ancestor.name)

        # 4. Deduplicate results (remove skills already present in explicit_skills)
        inferred_names = inferred_names - resolved_explicit_names

        logger.error(
            "DEBUG infer_skills: input=%s resolved_explicit=%s inferred_before_return=%s",
            explicit_inputs,
            resolved_explicit_names,
            inferred_names,
        )
        
        # 5. Return lists sorted alphabetically for determinism
        return {
            "explicit_skills": sorted(list(resolved_explicit_names)),
            "inferred_skills": sorted(list(inferred_names))
        }
