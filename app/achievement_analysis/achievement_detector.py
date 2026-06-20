"""
Achievement Detection Engine for Phase 9 in ARIS V2.
"""

import re
import logging
from typing import List, Dict, Any
from app.schemas.resume_schema import ResumeProfile
from app.achievement_analysis.scoring import AchievementScorer
from app.achievement_analysis.models import AchievementProfile
from app.achievement_analysis.exceptions import AchievementAnalysisError, DetectionError

logger = logging.getLogger("aris.achievement_analysis")

# ---------------------------------------------------------------------------
# Regex rules for achievement detection
# ---------------------------------------------------------------------------

PATTERNS_ACADEMIC = [
    # JEE / AIR ranks
    (re.compile(r"\b(jee\s*(advanced|main)?|air|all\s*india\s*rank|state\s*rank)\b.*?\b(\d+)\b", re.IGNORECASE), "JEE/AIR Rank"),
    (re.compile(r"\brank\b.*?\b(\d+)\b.*?\b(jee|gate|cat|neet|upsc)\b", re.IGNORECASE), "Exam Rank"),
    # Scholarships & Olympiads
    (re.compile(r"\b(ntse|kvpy|olympiad|inspsire|scholarship|merit-cum-means|academic\s*award|dean's\s*list)\b", re.IGNORECASE), "Scholarship/Olympiad"),
    # GPA / Honors
    (re.compile(r"\b(gold\s*medalist|distinction|honors|honours|summa\s*cum\s*laude|magna\s*cum\s*laude|valedictorian)\b", re.IGNORECASE), "Academic Distinction"),
    (re.compile(r"\b(cgpa|gpa)\b.*?\b(9\.[0-9]|10(\.0)?)\b", re.IGNORECASE), "High GPA"),
    (re.compile(r"\b(9[0-9]|100)\s*%\s*(marks|score|aggregate)\b", re.IGNORECASE), "High Percentage")
]

PATTERNS_TECHNICAL = [
    # Hackathons
    (re.compile(r"\b(hackathon|hack)\b.*?\b(won|win|winner|1st|2nd|3rd|first|second|third|runner\s*up|champion|podium)\b", re.IGNORECASE), "Hackathon Win"),
    (re.compile(r"\b(won|win|winner|1st|2nd|3rd|first|second|third|runner\s*up|champion|podium)\b.*?\b(hackathon|hack)\b", re.IGNORECASE), "Hackathon Win"),
    (re.compile(r"\b(participated\s*in|finalist\s*in)\b.*?\b(hackathon|hack)\b", re.IGNORECASE), "Hackathon Participation"),
    # CP & Kaggle
    (re.compile(r"\b(kaggle)\b.*?\b(grandmaster|master|expert|gold|silver|bronze|medal|rank|top)\b", re.IGNORECASE), "Kaggle Achievement"),
    (re.compile(r"\b(codeforces|codechef|leetcode|hackerrank|topcoder|spoj|acm\s*icpc|icpc)\b.*?\b(grandmaster|master|candidate\s*master|expert|specialist|rank|rating|max\s*rating|global\s*rank|top|finalist|regionalist)\b", re.IGNORECASE), "Competitive Programming"),
    (re.compile(r"\b(rating\s*of\s*\d+|top\s*\d+(\.\d+)?%|global\s*rank\s*\d+)\b.*?\b(codeforces|codechef|leetcode|hackerrank)\b", re.IGNORECASE), "Competitive Programming"),
    # Open Source
    (re.compile(r"\b(gsoc|google\s*summer\s*of\s*code|lfx\s*mentorship|outreachy)\b", re.IGNORECASE), "Open Source Mentorship"),
    (re.compile(r"\b(open\s*source|contributor|contributed\s*to|github\s*stars|pull\s*request|pr\s*merged)\b.*?\b(kubernetes|docker|linux|tensorflow|pytorch|react|vue|django|fastapi|pandas|numpy|scipy|git)\b", re.IGNORECASE), "Open Source Contribution"),
    (re.compile(r"\b(stars\s*on\s*github|github\s*stars)\b", re.IGNORECASE), "Open Source Recognition")
]

PATTERNS_RESEARCH = [
    # Publications
    (re.compile(r"\b(published|publication|paper|ieee|acm|neurips|cvpr|icml|kdd|emnlp|acl|naacl|siggraph|journal|conference|arxiv)\b", re.IGNORECASE), "Publication/Research Paper"),
    # Patents
    (re.compile(r"\b(patent|patented|patents)\b", re.IGNORECASE), "Patent"),
    # Research internships/fellowships
    (re.compile(r"\b(research\s*intern|research\s*assistant|research\s*fellow|iisc\s*research|mit\s*media\s*lab|postdoc)\b", re.IGNORECASE), "Research Position")
]

PATTERNS_LEADERSHIP = [
    # Club leadership
    (re.compile(r"\b(president|vice\s*president|secretary|convenor|lead|founder|head|captain|treasurer)\b.*?\b(club|chapter|society|student\s*body|team|organization|cell)\b", re.IGNORECASE), "Club/Society Leadership"),
    # Mentorship
    (re.compile(r"\b(mentor|mentored|mentorship|teaching\s*assistant|ta|tutor|guided|instructed)\b", re.IGNORECASE), "Mentorship/Teaching"),
    # Team Management
    (re.compile(r"\b(managed|led|leading|manager|director|lead|head|coordinate|coordinated)\b.*?\b(team\s*of|group\s*of|developers|engineers|interns|people)\b", re.IGNORECASE), "Team Management"),
    (re.compile(r"\b(engineering\s*lead|team\s*lead|tech\s*lead|project\s*lead|scrum\s*master|delivery\s*manager)\b", re.IGNORECASE), "Leadership Role")
]

PATTERNS_ENTREPRENEURSHIP = [
    # Founder
    (re.compile(r"\b(founder|co-founder|cofounder|ceo|cto|cfo|coo|founding\s*member|founding\s*engineer)\b", re.IGNORECASE), "Startup Founder/Executive"),
    # YC
    (re.compile(r"\b(y\s*combinator|yc|y-combinator)\b", re.IGNORECASE), "YC-backed Startup"),
    # Scale/0 to 1
    (re.compile(r"\b(launched|built\s*from\s*scratch|scaled|0\s*to\s*1|product\s*owner|ownership|product\s*manager|pm|ipo|acquisition)\b", re.IGNORECASE), "Product Ownership/Scale")
]


class AchievementDetector:
    """
    Scans a ResumeProfile Pydantic object and detects exceptional achievement signals
    across all standard categories using regex and keyword logic.
    """
    def __init__(self) -> None:
        pass

    def detect_achievements(self, profile: ResumeProfile) -> Dict[str, List[Dict[str, Any]]]:
        """
        Processes a ResumeProfile to discover achievements.

        Args:
            profile: The validated candidate ResumeProfile Pydantic object.

        Returns:
            A dictionary mapping category name to lists of detected raw achievements.
        """
        detected = {
            "academic": [],
            "technical": [],
            "research": [],
            "leadership": [],
            "entrepreneurship": []
        }

        # 1. Check explicit achievements list (List[str])
        for idx, ach_str in enumerate(profile.achievements):
            self._scan_text(ach_str, "achievements", f"Entry #{idx + 1}", detected)

        # 2. Check education list (List[Education])
        for edu in profile.education:
            inst_text = edu.institution or ""
            deg_text = edu.degree or ""
            field_text = edu.field or ""

            # Check if university is a top tier institution
            if self._is_top_university(inst_text):
                detected["academic"].append({
                    "title": f"Graduated from Tier-1 Institution: {inst_text}",
                    "source_section": "education",
                    "source_detail": f"{deg_text} in {field_text} at {inst_text}" if field_text else f"{deg_text} at {inst_text}",
                    "match_type": "Tier-1 University",
                    "raw_text": inst_text
                })

            # Scan other education texts for distinctions
            combined_edu = f"{deg_text} {field_text} {inst_text}"
            self._scan_text(
                combined_edu,
                "education",
                f"{deg_text} at {inst_text}",
                detected,
                skip_categories=["technical", "research", "leadership", "entrepreneurship"]
            )

        # 3. Check projects list (List[Project])
        for proj in profile.projects:
            combined_proj = f"{proj.name}: {proj.description or ''}"
            self._scan_text(combined_proj, "projects", proj.name, detected)

        # 4. Check experience list (List[Experience])
        for exp in profile.experience:
            combined_exp = f"{exp.role or ''} at {exp.company or ''}: {exp.description or ''}"
            self._scan_text(
                combined_exp,
                "experience",
                f"{exp.role or 'Role'} at {exp.company or 'Company'}",
                detected
            )

        # Deduplicate results per category
        for cat in detected:
            detected[cat] = self._deduplicate_category(detected[cat])

        return detected

    def _is_top_university(self, inst_name: str) -> bool:
        if not inst_name:
            return False
        norm = inst_name.lower()
        top_uni_patterns = [
            r"\b(indian\s+institute\s+of\s+technology|iit|iiit|nit|bits|iisc)\b",
            r"\b(stanford|mit|harvard|yale|princeton|columbia|cornell|dartmouth|brown|upenn|pennsylvania|oxford|cambridge|berkeley|cmu|carnegie\s+mellon)\b"
        ]
        return any(re.search(pat, norm) for pat in top_uni_patterns)

    def _scan_text(
        self,
        text: str,
        section: str,
        detail: str,
        detected: Dict[str, List[Dict[str, Any]]],
        skip_categories: List[str] = None
    ) -> None:
        if not text:
            return
        if skip_categories is None:
            skip_categories = []

        # Split text into sentences/lines for granular matching
        sentences = [s.strip() for s in re.split(r'\.\s+|\n|;', text) if s.strip()]

        categories = {
            "academic": PATTERNS_ACADEMIC,
            "technical": PATTERNS_TECHNICAL,
            "research": PATTERNS_RESEARCH,
            "leadership": PATTERNS_LEADERSHIP,
            "entrepreneurship": PATTERNS_ENTREPRENEURSHIP
        }

        for sentence in sentences:
            for cat, patterns in categories.items():
                if cat in skip_categories:
                    continue
                for pattern, match_type in patterns:
                    match = pattern.search(sentence)
                    if match:
                        title = match.group(0).strip()
                        title = re.sub(r"\s+", " ", title)
                        # Use a context window if the matched title is very short
                        if len(title) < 15 and len(sentence) > len(title):
                            start = max(0, match.start() - 20)
                            end = min(len(sentence), match.end() + 20)
                            snippet = sentence[start:end].strip()
                            if start > 0:
                                snippet = "..." + snippet
                            if end < len(sentence):
                                snippet = snippet + "..."
                            title = snippet

                        detected[cat].append({
                            "title": title,
                            "source_section": section,
                            "source_detail": detail,
                            "match_type": match_type,
                            "raw_text": sentence
                        })
                        break  # Match only one pattern of this category per sentence

    def _deduplicate_category(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_titles = set()
        deduped = []
        for item in items:
            title_norm = item["title"].lower().strip()
            if title_norm not in seen_titles:
                seen_titles.add(title_norm)
                deduped.append(item)
        return deduped


class AchievementAnalyzer:
    """
    Consumes a ResumeProfile and produces a scored and trace-justified AchievementProfile.
    This coordinates the detection and scoring pipeline.
    """
    def __init__(self) -> None:
        self._detector = AchievementDetector()
        self._scorer = AchievementScorer()

    def analyze(self, resume_profile: ResumeProfile) -> AchievementProfile:
        """
        Runs the achievement detection and scoring pipeline.

        Args:
            resume_profile: Candidate's structured ResumeProfile.

        Returns:
            Calculated AchievementProfile containing scores and traces.

        Raises:
            DetectionError: If detection or scoring steps fail.
        """
        if resume_profile is None:
            raise DetectionError("ResumeProfile cannot be None.")
        
        try:
            detected_raw = self._detector.detect_achievements(resume_profile)
            return self._scorer.score_profile(detected_raw)
        except Exception as e:
            raise AchievementAnalysisError(f"Failed to analyze achievements: {e}") from e

