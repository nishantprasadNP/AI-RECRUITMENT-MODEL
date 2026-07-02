"""
Normalized score calculators (0-100) for candidate scoring components in ARIS V2.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import SkillRequirementString
from app.achievement_analysis.models import AchievementProfile
from app.experience_analysis.models import SkillConfidenceProfile

logger = logging.getLogger("aris.candidate_scoring.calculators")


def parse_duration_to_years(duration_str: Optional[str]) -> float:
    """
    Parses a duration string (e.g. '2 years', '6 months', '1 year 6 months')
    and returns the equivalent float value in years.
    """
    if not duration_str:
        return 0.0
    
    duration_str = duration_str.lower()
    years = 0.0
    
    # Match years patterns: e.g. "2 years", "1.5 yrs", "1 year"
    year_match = re.search(r"(\d+(\.\d+)?)\s*(year|yr)", duration_str)
    if year_match:
        years += float(year_match.group(1))
        
    # Match months patterns: e.g. "6 months", "3 mos", "1 month"
    month_match = re.search(r"(\d+(\.\d+)?)\s*(month|mo)", duration_str)
    if month_match:
        years += float(month_match.group(1)) / 12.0
        
    # Fallback if no keywords matched but digits are present, assume years
    if years == 0.0:
        digits_match = re.search(r"(\d+(\.\d+)?)", duration_str)
        if digits_match:
            years += float(digits_match.group(1))
            
    return years


class ComponentScoreCalculators:
    """
    Utility calculators that compute normalized (0-100) scores for different candidate areas.
    """

    @staticmethod
    def calculate_semantic_score(semantic_score: float) -> float:
        """
        Calculates the normalized Semantic Alignment score.
        """
        # Bounded cosine similarity scaled to [0, 100]
        normalized = max(0.0, min(1.0, float(semantic_score))) * 100.0
        return round(normalized, 1)

    _dry_run_executed = False
    _skills_taxonomy_type_cache = None

    @staticmethod
    def _load_taxonomy_types() -> Dict[str, str]:
        if ComponentScoreCalculators._skills_taxonomy_type_cache is not None:
            return ComponentScoreCalculators._skills_taxonomy_type_cache

        type_map = {}
        import os
        import json

        curr_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = [
            os.path.join(curr_dir, "..", "..", "data", "skill_graph", "skills_taxonomy.json"),
            os.path.join(curr_dir, "data", "skill_graph", "skills_taxonomy.json"),
            "data/skill_graph/skills_taxonomy.json",
            "AI-RECRUITMENT-MODEL/data/skill_graph/skills_taxonomy.json",
        ]

        taxonomy_path = None
        for path in candidate_paths:
            if os.path.exists(path):
                taxonomy_path = path
                break

        if taxonomy_path and os.path.exists(taxonomy_path):
            try:
                with open(taxonomy_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_nodes = data.get("nodes", [])
                    raw_edges = data.get("edges", [])

                    # BFS to find all database-related nodes
                    database_ids = {"databases", "sql", "nosql", "database_design", "database_management"}
                    db_keywords = {
                        "postgresql", "postgres", "mysql", "sqlite", "redis", "mongodb", "mongo",
                        "cassandra", "oracle", "dynamodb", "mariadb", "neo4j", "elasticsearch",
                        "db2", "influxdb", "couchdb", "hbase", "firebase", "firestore", "supabase",
                        "cockroachdb", "memcached", "snowflake", "redshift", "bigquery", "clickhouse",
                        "scylladb"
                    }
                    database_ids.update(db_keywords)

                    requires_map = {}
                    parent_of_map = {}
                    for edge in raw_edges:
                        src = edge.get("source", "").lower().strip()
                        tgt = edge.get("target", "").lower().strip()
                        rel = edge.get("relation_type", "").upper().strip()
                        if rel == "REQUIRES":
                            requires_map.setdefault(tgt, []).append(src)
                        elif rel == "PARENT_OF":
                            parent_of_map.setdefault(src, []).append(tgt)

                    queue = list(database_ids)
                    visited_databases = set(database_ids)
                    while queue:
                        curr = queue.pop(0)
                        for node in requires_map.get(curr, []):
                            if node not in visited_databases:
                                visited_databases.add(node)
                                queue.append(node)
                        for node in parent_of_map.get(curr, []):
                            if node not in visited_databases:
                                visited_databases.add(node)
                                queue.append(node)

                    # Populate type_map with force-overridden types for databases
                    for node in raw_nodes:
                        node_type = node.get("type", "").lower().strip()
                        node_id = node.get("id", "").lower().strip()
                        node_name = node.get("name", "").lower().strip()
                        
                        if node_id in visited_databases:
                            node_type = "databases"
                            
                        if node_id:
                            type_map[node_id] = node_type
                        if node_name:
                            type_map[node_name] = node_type
                        for syn in node.get("synonyms", []):
                            syn_cleaned = syn.lower().strip()
                            if syn_cleaned:
                                type_map[syn_cleaned] = node_type
            except Exception:
                pass

        ComponentScoreCalculators._skills_taxonomy_type_cache = type_map
        return type_map

    @staticmethod
    def _get_skills_taxonomy_types() -> Dict[str, str]:
        return ComponentScoreCalculators._load_taxonomy_types()

    @staticmethod
    def _run_dry_run() -> None:
        ComponentScoreCalculators._dry_run_executed = True
        mock_data = {
            "VS Code": 95.0,
            "PyCharm": 92.0,
            "Android Studio": 90.0,
            "IntelliJ IDEA": 88.0,
            "Git": 85.0,
            "Kubernetes": 82.0,
            "Docker": 80.0,
            "PostgreSQL": 90.0,
            "TypeScript": 88.0,
            "Django": 85.0,
            "FastAPI": 80.0,
            "MongoDB": 78.0,
            "Flask": 75.0,
            "Python": 70.0,
            "React.js": 68.0,
            "CSS": 65.0,
            "HTML": 60.0,
        }

        profiles = {}
        for skill_name, score in mock_data.items():
            profiles[skill_name] = SkillConfidenceProfile(
                skill=skill_name,
                confidence_score=score,
                confidence_level="Expert" if score >= 75 else "Medium",
                professional_signal=0.0,
                depth_signal=0.0,
                complexity_signal=0.0,
                skill_tier="Tier 3",
                evidence_summary={}
            )

        type_map = ComponentScoreCalculators._load_taxonomy_types()
        common_excluded = {
            "vs code", "vs_code", "visual studio code", "vscode",
            "intellij", "intellij idea", "intellij_idea",
            "google colab", "google_colab", "colab",
            "pycharm",
            "android studio", "android_studio",
            "sublime text", "sublime",
            "atom",
            "vim",
            "emacs",
            "eclipse",
            "xcode",
            "notepad++",
            "webstorm",
            "jupyter notebook", "jupyter", "jupyter_notebook",
        }

        removed_skills = []
        remaining_skills = []
        for name, score in mock_data.items():
            name_lower = name.lower().strip()
            tax_type = type_map.get(name_lower)
            if tax_type in {"tool", "ide", "editor"} or name_lower in common_excluded:
                resolved_type = tax_type if tax_type else "editor/ide/tool fallback"
                removed_skills.append(f"{name} (type: {resolved_type})")
            else:
                remaining_skills.append((name, score))

        remaining_skills.sort(key=lambda x: x[1], reverse=True)
        sorted_scores_str = [f"{name}: {score}" for name, score in remaining_skills]

        top_k = min(10, len(remaining_skills))
        selected = remaining_skills[:top_k]
        selected_str = [f"{name}: {score}" for name, score in selected]

        final_score = round(sum(score for name, score in selected) / top_k, 1) if top_k > 0 else 0.0

        print("\n=== SKILLS SCORE DRY RUN ===")
        print("Original confidence profiles:")
        for name, score in mock_data.items():
            print(f"  - {name}: {score}")
        print("\nSkills removed because they are tools/IDEs/editors:")
        for rem in removed_skills:
            print(f"  - {rem}")
        print("\nRemaining skills:")
        for rem_n, rem_s in remaining_skills:
            print(f"  - {rem_n}: {rem_s}")
        print("\nSorted scores:")
        for s_str in sorted_scores_str:
            print(f"  - {s_str}")
        print("\nSelected Top K:")
        for sel in selected_str:
            print(f"  - {sel}")
        print(f"\nFinal Skills Score: {final_score}")
        print("============================\n")

    @staticmethod
    def calculate_skills_score(
        confidence_profiles: Dict[str, SkillConfidenceProfile],
        required_skills: Optional[List[Any]] = None
    ) -> float:
        """
        Calculates the normalized Skill Strength score using the new algorithm.
        """
        if not ComponentScoreCalculators._dry_run_executed:
            ComponentScoreCalculators._run_dry_run()

        if not confidence_profiles:
            return 0.0

        type_map = ComponentScoreCalculators._load_taxonomy_types()
        common_excluded = {
            "vs code", "vs_code", "visual studio code", "vscode",
            "intellij", "intellij idea", "intellij_idea",
            "google colab", "google_colab", "colab",
            "pycharm",
            "android studio", "android_studio",
            "sublime text", "sublime",
            "atom",
            "vim",
            "emacs",
            "eclipse",
            "xcode",
            "notepad++",
            "webstorm",
            "jupyter notebook", "jupyter", "jupyter_notebook",
        }

        remaining_profiles = []
        for name, profile in confidence_profiles.items():
            name_lower = name.lower().strip()
            tax_type = type_map.get(name_lower)
            if tax_type in {"tool", "ide", "editor"} or name_lower in common_excluded:
                continue
            remaining_profiles.append(profile)

        if not remaining_profiles:
            return 0.0

        remaining_profiles.sort(key=lambda p: p.confidence_score, reverse=True)

        top_k = min(10, len(remaining_profiles))
        if top_k == 0:
            return 0.0

        selected_profiles = remaining_profiles[:top_k]
        score_sum = sum(p.confidence_score for p in selected_profiles)
        
        return round(score_sum / top_k, 1)

    @staticmethod
    def calculate_experience_score(
        resume_profile: ResumeProfile,
        experience_required: Optional[int]
    ) -> float:
        """
        Calculates the normalized Experience Quality score by comparing candidate's
        parsed years of experience against the job's experience requirements.
        """
        if not resume_profile or not resume_profile.experience:
            return 0.0

        # Calculate total years of experience
        total_years = 0.0
        for exp in resume_profile.experience:
            duration_str = getattr(exp, "duration", None)
            total_years += parse_duration_to_years(duration_str)

        # Fallback if no durations are parsed but items exist: assume 1 year per entry
        if total_years == 0.0 and len(resume_profile.experience) > 0:
            total_years = float(len(resume_profile.experience))

        required_years = max(1.0, float(experience_required or 1.0))
        ratio = total_years / required_years
        normalized = min(100.0, ratio * 100.0)
        return round(normalized, 1)

    @staticmethod
    def calculate_achievements_score(achievement_profile: AchievementProfile) -> float:
        """
        Calculates the normalized Achievement Impact score.
        """
        if not achievement_profile:
            return 0.0
        # Scales 0.0-10.0 score to 0.0-100.0
        normalized = max(0.0, min(10.0, achievement_profile.achievement_score)) * 10.0
        return round(normalized, 1)

    @staticmethod
    def calculate_projects_score(
        resume_profile: ResumeProfile,
        required_skills: List[str]
    ) -> float:
        """
        Calculates the normalized Projects Strength score based on project quantity
        and technologies matching the job's required skills.
        """
        if not resume_profile or not resume_profile.projects:
            return 0.0

        total_projects = len(resume_profile.projects)
        req_clean = {s.lower().strip() for s in required_skills if s and s.strip()}

        relevant_projects_count = 0
        for proj in resume_profile.projects:
            techs = {t.lower().strip() for t in (proj.technologies or []) if t}
            if req_clean & techs:
                relevant_projects_count += 1

        # Score consists of 20% per project + 20% per relevant project, capped at 100.0
        score = (total_projects * 20.0) + (relevant_projects_count * 20.0)
        normalized = min(100.0, score)
        return round(normalized, 1)

    @staticmethod
    def calculate_leadership_score(
        resume_profile: ResumeProfile,
        achievement_profile: AchievementProfile
    ) -> float:
        """
        Calculates the normalized Leadership Strength score based on candidate experience
        lead roles and achievements.
        """
        if not resume_profile:
            return 0.0

        # Check if candidate held any explicit lead or manager role
        has_lead_role = False
        lead_keywords = ["lead", "manager", "head", "director", "founder", "president", "cto", "ceo"]
        for exp in resume_profile.experience:
            role = (exp.role or "").lower()
            if any(kw in role for kw in lead_keywords):
                has_lead_role = True
                break

        # Check achievement profile for leadership signals
        achievement_leadership_count = 0
        if achievement_profile and achievement_profile.leadership:
            achievement_leadership_count = len(achievement_profile.leadership)

        if has_lead_role:
            return 100.0
        
        # Scale based on leadership achievements: 50 points per achievement
        score = achievement_leadership_count * 50.0
        normalized = min(100.0, score)
        return round(normalized, 1)
