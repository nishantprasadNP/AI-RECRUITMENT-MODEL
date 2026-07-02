import re
from typing import Dict, List, Set, Optional
from app.schemas.resume_schema import ResumeProfile
from app.experience_analysis.models import SkillEvidence


class SkillEvidenceCollector:
    """
    Analyzes a ResumeProfile to collect qualitative and quantitative evidence for each skill.
    """

    def __init__(self) -> None:
        pass

    def _is_matched(self, skill: str, text: str) -> bool:
        """
        Helper method to check if a skill matches a text string case-insensitively.
        Uses word boundary constraints for alphanumeric boundaries to prevent false positives.
        """
        if not skill or not text:
            return False
        escaped = re.escape(skill)
        pattern = escaped
        if skill[0].isalnum():
            pattern = r"\b" + pattern
        if skill[-1].isalnum():
            pattern = pattern + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _count_matches(self, skill: str, text: str) -> int:
        """
        Helper method to count occurrences of a skill within a text string case-insensitively.
        Uses word boundary constraints for alphanumeric boundaries to prevent false positives.
        """
        if not skill or not text:
            return 0
        escaped = re.escape(skill)
        pattern = escaped
        if skill[0].isalnum():
            pattern = r"\b" + pattern
        if skill[-1].isalnum():
            pattern = pattern + r"\b"
        return len(re.findall(pattern, text, re.IGNORECASE))

    def collect(self, profile: ResumeProfile) -> Dict[str, SkillEvidence]:
        """
        Collects project, professional, depth, and achievement evidence for each skill
        listed in the candidate's profile.

        Args:
            profile: The parsed ResumeProfile object.

        Returns:
            A dictionary mapping skill names to their computed SkillEvidence objects.
        """
        evidence_map: Dict[str, SkillEvidence] = {}
        if not profile:
            return evidence_map

        skills = profile.skills or []
        projects = profile.projects or []
        experience = profile.experience or []
        achievements = profile.achievements or []

        # Deduplicate skills case-insensitively, preserving original casing of first occurrence
        unique_skills: List[str] = []
        seen_skills_lower: Set[str] = set()
        for sk in skills:
            if sk and sk.strip():
                sk_stripped = sk.strip()
                sk_lower = sk_stripped.lower()
                if sk_lower not in seen_skills_lower:
                    seen_skills_lower.add(sk_lower)
                    unique_skills.append(sk_stripped)

        for s in unique_skills:
            # 1. Project Evidence
            matched_projects: List[str] = []
            seen_projects: Set[str] = set()
            for p in projects:
                name = p.name or ""
                desc = p.description or ""
                techs = p.technologies or []
                
                name_match = self._is_matched(s, name)
                desc_match = self._is_matched(s, desc)
                tech_match = any(self._is_matched(s, t) for t in techs if t)
                
                if name_match or desc_match or tech_match:
                    if name and name not in seen_projects:
                        seen_projects.add(name)
                        matched_projects.append(name)
            
            # 2. Professional Evidence
            matched_roles: List[str] = []
            seen_roles: Set[str] = set()
            professional_usage = False
            for exp in experience:
                role = exp.role or ""
                desc = exp.description or ""
                
                role_match = self._is_matched(s, role)
                desc_match = self._is_matched(s, desc)
                
                # Check technologies attribute if dynamically set on the experience model
                tech_match = False
                exp_techs = getattr(exp, "technologies", None)
                if exp_techs:
                    if isinstance(exp_techs, list):
                        tech_match = any(self._is_matched(s, t) for t in exp_techs if t)
                    elif isinstance(exp_techs, str):
                        tech_match = self._is_matched(s, exp_techs)

                if role_match or desc_match or tech_match:
                    professional_usage = True
                    if role and role not in seen_roles:
                        seen_roles.add(role)
                        matched_roles.append(role)

            # 3. Depth Evidence (mentions across: skills, project technologies, project descriptions, experience descriptions)
            skill_mentions = 0
            
            # Count in skills list (using original skills list, comparing case-insensitively)
            for sk in skills:
                if sk:
                    skill_mentions += self._count_matches(s, sk)
            
            # Count in project technologies and descriptions
            for p in projects:
                for tech in (p.technologies or []):
                    if tech:
                        skill_mentions += self._count_matches(s, tech)
                if p.description:
                    skill_mentions += self._count_matches(s, p.description)

            # Count in experience descriptions
            for exp in experience:
                if exp.description:
                    skill_mentions += self._count_matches(s, exp.description)

            # 4. Achievement Evidence
            achievement_mentions = 0
            for ach in achievements:
                if ach:
                    achievement_mentions += self._count_matches(s, ach)

            evidence_map[s] = SkillEvidence(
                skill=s,
                project_count=len(matched_projects),
                projects=matched_projects,
                professional_usage=professional_usage,
                roles=matched_roles,
                skill_mentions=skill_mentions,
                achievement_mentions=achievement_mentions,
                direct_mentions=skill_mentions,
                dependency_mentions=0.0,
                dependency_sources=[]
            )

        return evidence_map

