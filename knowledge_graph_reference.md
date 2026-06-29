# ARIS V2 Knowledge Graph & Hard Requirements Engine Reference

This file compiles the codebase implementations and configurations requested for reference.

---

## 1. Dependency Wiring
* **Location**: [app/orchestrator.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/orchestrator.py#L156-L164)
* **Code snippet**:

```python
        # Initialize knowledge graph components for Hard Requirements and Skill Confidence
        skills_repo = NetworkXSkillGraphRepository()
        try:
            skills_repo.initialize("data/skill_graph/skills_taxonomy.json")
        except Exception:
            pass
        skills_service = SkillGraphService(skills_repo)
        self._inference_engine = SkillInferenceEngine(skills_service)
        self._capability_resolver = CapabilityResolver(self._inference_engine)
```

---

## 2. Repository Implementation (initialize method)
* **Location**: [app/knowledge_graph/repositories/networkx_repository.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/knowledge_graph/repositories/networkx_repository.py#L26-L121)
* **Code snippet**:

```python
    def initialize(self, data_path: str) -> None:
        """
        Loads the taxonomy JSON file, validates nodes and edges, and constructs the NetworkX graph.
        
        Args:
            data_path: Absolute or relative path to the taxonomy JSON file.
            
        Raises:
            GraphInitializationError: If the file does not exist, is invalid JSON, or fails integrity checks.
        """
        if not os.path.exists(data_path):
            raise GraphInitializationError(f"Taxonomy file not found at: {data_path}")

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise GraphInitializationError(f"Failed to parse taxonomy JSON file: {str(e)}") from e
        except Exception as e:
            raise GraphInitializationError(f"Unexpected error reading taxonomy file: {str(e)}") from e

        raw_nodes = data.get("nodes", [])
        raw_edges = data.get("edges", [])

        # Reset graph state
        self._graph.clear()

        # 1. Parse and Validate Nodes
        parsed_nodes: List[SkillNode] = []
        seen_ids = set()

        for node_index, node_data in enumerate(raw_nodes):
            try:
                # Basic Pydantic validation
                node = SkillNode.model_validate(node_data)
            except Exception as e:
                raise GraphInitializationError(f"Validation error in node at index {node_index}: {str(e)}") from e

            # Validate duplicate nodes
            if node.id in seen_ids:
                raise DuplicateNodeError(f"Duplicate node ID detected during initialization: '{node.id}'")
            
            seen_ids.add(node.id)
            parsed_nodes.append(node)

        # 2. Parse and Validate Edges
        parsed_edges: List[SkillEdge] = []
        for edge_index, edge_data in enumerate(raw_edges):
            try:
                edge = SkillEdge.model_validate(edge_data)
            except Exception as e:
                raise GraphInitializationError(f"Validation error in edge at index {edge_index}: {str(e)}") from e

            # Validate missing references (source and target must exist in the node set)
            if edge.source not in seen_ids:
                raise MissingNodeReferenceError(
                    f"Edge at index {edge_index} references undefined source node: '{edge.source}'"
                )
            if edge.target not in seen_ids:
                raise MissingNodeReferenceError(
                    f"Edge at index {edge_index} references undefined target node: '{edge.target}'"
                )

            parsed_edges.append(edge)

        # 3. Build NetworkX Directed Graph
        for node in parsed_nodes:
            self._graph.add_node(node.id, model=node)

        for edge in parsed_edges:
            # Set distance cost inversely proportional to similarity weight (avoid division by zero)
            distance_cost = 1.0 / max(edge.weight, 0.01)
            
            # Add primary directed relationship
            self._graph.add_edge(
                edge.source,
                edge.target,
                relation_type=edge.relation_type,
                weight=edge.weight,
                distance_cost=distance_cost
            )

            # Bidirectional relations mapping
            if edge.relation_type in ("RELATED_TO", "USED_WITH"):
                # Add reverse edge for non-hierarchical related association in directed graph
                self._graph.add_edge(
                    edge.target,
                    edge.source,
                    relation_type=edge.relation_type,
                    weight=edge.weight,
                    distance_cost=distance_cost
                )

        logger.info(
            f"Successfully initialized Skill Graph with {self._graph.number_of_nodes()} nodes "
        )
```

---

## 3. Skill Graph Service (SkillGraphService class)
* **Location**: [app/knowledge_graph/services/skill_graph_service.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/knowledge_graph/services/skill_graph_service.py)
* **Code snippet**:

```python
class SkillGraphService:
    """
    Domain service orchestrating operations on the Skill Knowledge Graph.
    Acts as the entry point for high-level components to query taxonomical relations,
    perform name resolution (synonyms mapping), and traverse hierarchies.
    """

    def __init__(self, repository: ISkillGraphRepository) -> None:
        self._repo = repository

    def _resolve_skill_id(self, skill: str) -> Optional[str]:
        """
        Resolves a raw skill string (e.g., 'Py', 'Frontend Development', 'python3') 
        to its canonical node ID in the graph using ID, Name, or Synonyms.
        Returns None if the skill is not found.
        """
        if not skill:
            return None

        # Clean and normalize the query
        normalized = skill.lower().strip()
        slugified = normalized.replace(" ", "_")

        # 1. Direct ID lookup
        if self._repo.get_node(slugified) is not None:
            return slugified

        # 2. Case-insensitive lookup by name or synonym
        for node in self._repo.get_all_nodes():
            if node.name.lower() == normalized:
                return node.id
            if any(syn.lower() == normalized for syn in node.synonyms):
                return node.id

        return None

    def skill_exists(self, skill: str) -> bool:
        """
        Checks if a skill exists in the graph by ID, name, or synonym.
        """
        return self._resolve_skill_id(skill) is not None

    def get_parents(self, skill: str) -> List[SkillNode]:
        """
        Retrieves direct parents of the specified skill.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []
        return self._repo.get_parents(resolved_id)

    def get_children(self, skill: str) -> List[SkillNode]:
        """
        Retrieves direct children of the specified skill.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []
        return self._repo.get_children(resolved_id)

    def get_ancestors(self, skill: str) -> List[SkillNode]:
        """
        Retrieves all recursive ancestors of the specified skill (parents, parents of parents, etc.).
        Uses Breadth-First Search (BFS) to traverse up the taxonomy.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []

        ancestors: List[SkillNode] = []
        visited = {resolved_id}
        queue = [resolved_id]

        while queue:
            current_id = queue.pop(0)
            parents = self._repo.get_parents(current_id)
            for parent in parents:
                if parent.id not in visited:
                    visited.add(parent.id)
                    ancestors.append(parent)
                    queue.append(parent.id)

        return ancestors

    def get_descendants(self, skill: str) -> List[SkillNode]:
        """
        Retrieves all recursive descendants of the specified skill (children, children of children, etc.).
        Uses Breadth-First Search (BFS) to traverse down the taxonomy.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            logger.warning(f"Skill '{skill}' could not be resolved in the graph.")
            return []

        descendants: List[SkillNode] = []
        visited = {resolved_id}
        queue = [resolved_id]

        while queue:
            current_id = queue.pop(0)
            children = self._repo.get_children(current_id)
            for child in children:
                if child.id not in visited:
                    visited.add(child.id)
                    descendants.append(child)
                    queue.append(child.id)

        return descendants

    def has_relationship(
        self,
        source_skill: str,
        target_skill: str,
        relation_type: str
    ) -> bool:
        """
        Checks if a directed relationship of the specified type exists between two skills.
        """
        source_id = self._resolve_skill_id(source_skill)
        target_id = self._resolve_skill_id(target_skill)
        if not source_id or not target_id:
            return False
        return self._repo.has_relationship(source_id, target_id, relation_type)

    def get_canonical_name(self, skill: str) -> Optional[str]:
        """
        Resolves a raw skill string to its canonical name in the graph.
        """
        resolved_id = self._resolve_skill_id(skill)
        if not resolved_id:
            return None
        node = self._repo.get_node(resolved_id)
        return node.name if node else None
```

---

## 4. Taxonomy JSON Schema (First 30 Lines)
* **Location**: [data/skill_graph/skills_taxonomy.json](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/data/skill_graph/skills_taxonomy.json#L1-L30)
* **JSON snippet**:

```json
{
    "metadata": {
        "version": "1.1.0",
        "updated_at": "2026-06-18T21:10:00Z",
        "description": "Master skill graph taxonomy for ARIS containing node classification and edge relations."
    },
    "nodes": [
        {
            "id": "software_engineering",
            "name": "Software Engineering",
            "type": "domain",
            "description": "The systematic application of engineering principles to the development of software.",
            "synonyms": [
                "Software Development",
                "SWE",
                "App Development"
            ]
        },
        {
            "id": "data_science",
            "name": "Data Science",
            "type": "domain",
            "description": "An interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge from data.",
            "synonyms": [
                "Data Analytics",
                "DS"
            ]
        },
        {
            "id": "programming",
```

---

## 5. Hard Requirements & Capability Resolution / Skill Matching
### Capability Resolver
* **Location**: [app/hard_requirements/capability_resolver.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/hard_requirements/capability_resolver.py)
* **Code snippet**:

```python
class CapabilityResolver:
    """
    Resolves candidate skills into a canonical, expanded set of capabilities
    using ordered deduplication and tracking graph provenance.
    """

    def __init__(self, skill_inference_engine: SkillInferenceEngine) -> None:
        if not skill_inference_engine:
            raise CapabilityResolutionError("SkillInferenceEngine is required.")
        self._inference_engine = skill_inference_engine

    def resolve_capabilities(self, resume_profile: ResumeProfile) -> CapabilityResolutionResult:
        logger.info("CapabilityResolver: Starting capability resolution.")
        if not resume_profile:
            logger.error("CapabilityResolver: ResumeProfile is missing.")
            raise CapabilityResolutionError("ResumeProfile is missing or None.")

        raw_skills = resume_profile.skills or []
        logger.info("CapabilityResolver: Processing %d raw skills from profile.", len(raw_skills))

        explicit_resolved: List[str] = []
        skill_origins: Dict[str, List[str]] = {}

        seen_explicit_lower = set()

        for raw_skill in raw_skills:
            if not raw_skill or not raw_skill.strip():
                continue

            # Use SkillInferenceEngine to infer skills for this single skill
            try:
                res = self._inference_engine.infer_skills([raw_skill])
            except Exception as e:
                logger.error("CapabilityResolver: Inference failed for '%s': %s", raw_skill, str(e))
                raise CapabilityResolutionError(f"Skill inference failed: {str(e)}") from e

            # If the skill resolved in the graph
            if res.get("explicit_skills"):
                canonical = res["explicit_skills"][0]
                lower_canonical = canonical.lower()
                if lower_canonical not in seen_explicit_lower:
                    seen_explicit_lower.add(lower_canonical)
                    explicit_resolved.append(canonical)

                # The inferred skills are the ancestors for this specific canonical skill
                for ancestor in res.get("inferred_skills", []):
                    # Track graph provenance: map this ancestor to its source skill
                    if ancestor not in skill_origins:
                        skill_origins[ancestor] = []
                    if canonical not in skill_origins[ancestor]:
                        skill_origins[ancestor].append(canonical)
            else:
                # If it didn't resolve in the graph (i.e. unknown skill), we treat it as an explicit skill
                # and keep its raw stripped name as fallback.
                cleaned = raw_skill.strip()
                lower_cleaned = cleaned.lower()
                if lower_cleaned not in seen_explicit_lower:
                    seen_explicit_lower.add(lower_cleaned)
                    explicit_resolved.append(cleaned)

        # Collect inferred skills in the order they were first discovered
        # and filter out any inferred skill that is also explicitly declared on the resume
        inferred_resolved: List[str] = []
        final_skill_origins: Dict[str, List[str]] = {}

        for ancestor, sources in skill_origins.items():
            if ancestor.lower() not in seen_explicit_lower:
                inferred_resolved.append(ancestor)
                final_skill_origins[ancestor] = sources

        # Build combined capabilities preserving order: explicit first, then inferred
        candidate_capabilities = explicit_resolved + inferred_resolved

        return CapabilityResolutionResult(
            explicit_skills=explicit_resolved,
            inferred_skills=inferred_resolved,
            candidate_capabilities=candidate_capabilities,
            skill_origins=final_skill_origins
        )
```

### Requirement Matcher
* **Location**: [app/hard_requirements/requirement_matcher.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/hard_requirements/requirement_matcher.py)
* **Code snippet**:

```python
class RequirementMatcher:
    """
    Evaluates how closely a candidate's resolved capabilities match the
    required and preferred skills of a job description.
    """

    def match_requirements(
        self,
        job_profile: JobProfile,
        capabilities: CapabilityResolutionResult
    ) -> RequirementMatchResult:
        # 1. Build a lowercase set from candidate capabilities
        candidate_capabilities_set = {
            skill.strip().lower() for skill in capabilities.candidate_capabilities
        }

        matched_required = []
        missing_required = []
        matched_preferred = []
        missing_preferred = []

        # 2. Match required skills (case-insensitive, preserving original casing)
        for skill in job_profile.required_skills:
            if skill.strip().lower() in candidate_capabilities_set:
                matched_required.append(skill)
            else:
                missing_required.append(skill)

        # 3. Match preferred skills (case-insensitive, preserving original casing)
        for skill in job_profile.preferred_skills:
            if skill.strip().lower() in candidate_capabilities_set:
                matched_preferred.append(skill)
            else:
                missing_preferred.append(skill)

        # 4. Coverage score
        total_required = len(job_profile.required_skills)
        if total_required == 0:
            coverage_score = 1.0
        else:
            coverage_score = len(matched_required) / total_required

        # 5. critical_failures = missing_required
        critical_failures = list(missing_required)

        return RequirementMatchResult(
            matched_required=matched_required,
            missing_required=missing_required,
            matched_preferred=matched_preferred,
            missing_preferred=missing_preferred,
            coverage_score=coverage_score,
            critical_failures=critical_failures,
        )
```

### Hard Requirement Engine
* **Location**: [app/hard_requirements/hard_requirement_engine.py](file:///Users/navinprasad/aris/AI-RECRUITMENT-MODEL/app/hard_requirements/hard_requirement_engine.py)
* **Code snippet**:

```python
class HardRequirementEngine:
    """
    Evaluates resolved candidate capabilities against required and preferred job criteria
    using the RequirementMatcher layer.
    """

    def __init__(self, matcher: Optional[RequirementMatcher] = None) -> None:
        self._matcher = matcher or RequirementMatcher()

    def evaluate_compliance(
        self,
        job_profile: JobProfile,
        role_profile: RoleProfile,
        capabilities: CapabilityResolutionResult
    ) -> HardRequirementResult:
        if job_profile is None:
            raise RequirementMatchingError("job_profile cannot be None.")
        if role_profile is None:
            raise RequirementMatchingError("role_profile cannot be None.")
        if capabilities is None:
            raise RequirementMatchingError("capabilities cannot be None.")

        try:
            logger.info("Evaluating hard requirements compliance...")

            # 1. Call RequirementMatcher
            match_result = self._matcher.match_requirements(job_profile, capabilities)

            # 2. Determine pass/fail
            passed = len(match_result.missing_required) == 0

            # 3. Decision Reason
            if passed:
                decision_reason = "All required skills satisfied."
            else:
                decision_reason = f"Missing required skills: {', '.join(match_result.missing_required)}"

            # Build and return the result Pydantic model
            return HardRequirementResult(
                passed=passed,
                coverage_score=match_result.coverage_score,
                matched_required=match_result.matched_required,
                missing_required=match_result.missing_required,
                matched_preferred=match_result.matched_preferred,
                missing_preferred=match_result.missing_preferred,
                critical_failures=match_result.critical_failures,
                decision_reason=decision_reason
            )

        except Exception as e:
            if isinstance(e, RequirementMatchingError):
                raise
            raise RequirementMatchingError(f"Compliance evaluation failed: {e}") from e
```
