"""
Scoring and trace generation for Phase 9 Achievement Analyzer in ARIS V2.
"""

import re
from typing import List, Dict, Any, Tuple
from app.achievement_analysis.models import AchievementDetail, AchievementProfile
from app.achievement_analysis.exceptions import ScoringError


class AchievementScorer:
    """
    Evaluates detected raw achievements, computes category and consolidated scores,
    and constructs explainability traces.
    """
    def __init__(self) -> None:
        pass

    def score_profile(self, detected_raw: Dict[str, List[Dict[str, Any]]]) -> AchievementProfile:
        """
        Calculates the complete AchievementProfile containing details, category scores,
        consolidated overall score, and explanation traces.

        Args:
            detected_raw: Dictionary mapping categories to raw detected achievements.

        Returns:
            A structured AchievementProfile Pydantic object.
        """
        profile_data = {
            "academic": [],
            "technical": [],
            "research": [],
            "leadership": [],
            "entrepreneurship": []
        }
        category_scores = {}
        explanation_traces = []

        # 1. Evaluate each category
        for category, raw_items in detected_raw.items():
            category_details = []
            for item in raw_items:
                contrib, expl = self._determine_score_contribution(category, item)
                detail = AchievementDetail(
                    title=item["title"],
                    source_section=item["source_section"],
                    source_detail=item["source_detail"],
                    score_contribution=contrib,
                    explanation=expl
                )
                category_details.append(detail)

            # Cap individual category score at 10.0
            sum_scores = sum(d.score_contribution for d in category_details)
            cat_score = min(10.0, round(sum_scores, 1))

            profile_data[category] = category_details
            category_scores[category] = cat_score

            # Add to explanation traces if there is a score
            if cat_score > 0:
                explanation_traces.append(
                    f"{category.capitalize()} Score: {cat_score}/10.0 based on {len(category_details)} signal(s)."
                )

        # 2. Consolidated overall score calculation
        # overall_score = min(10.0, round(max(category_scores.values()) * 0.6 + sum_of_other_scores * 0.4, 1))
        scores_list = list(category_scores.values())
        max_score = max(scores_list) if scores_list else 0.0
        sum_others = sum(scores_list) - max_score

        overall_score = min(10.0, round(max_score * 0.6 + sum_others * 0.4, 1))

        # Compile overall explanation traces
        explanation_traces.append(
            f"Overall Achievement Score: {overall_score}/10.0. "
            f"Calculated as (Max Category Score {max_score} * 60%) + (Sum of other categories {sum_others:.1f} * 40%), capped at 10.0."
        )

        # Standout highlights per category
        for category in ["academic", "technical", "research", "leadership", "entrepreneurship"]:
            details = profile_data[category]
            if details:
                standout = max(details, key=lambda d: d.score_contribution)
                explanation_traces.append(
                    f"Standout {category.capitalize()} Signal: '{standout.title}' in {standout.source_section} "
                    f"({standout.source_detail}) contributing +{standout.score_contribution}."
                )

        return AchievementProfile(
            achievement_score=overall_score,
            academic=profile_data["academic"],
            technical=profile_data["technical"],
            research=profile_data["research"],
            leadership=profile_data["leadership"],
            entrepreneurship=profile_data["entrepreneurship"],
            category_scores=category_scores,
            explanation_traces=explanation_traces
        )

    def _determine_score_contribution(self, category: str, item: Dict[str, Any]) -> Tuple[float, str]:
        match_type = item.get("match_type", "")
        title_lower = item["title"].lower()

        if category == "academic":
            if "air" in title_lower or "jee" in title_lower or "rank" in title_lower:
                rank_match = re.search(r"\b(air|rank)\b.*?\b(\d+)\b", title_lower)
                if rank_match:
                    rank = int(rank_match.group(2))
                    if rank <= 1000:
                        return 4.5, "Exceptional academic performance: top 1000 JEE/AIR rank."
                    if rank <= 5000:
                        return 3.5, "Strong academic performance: top 5000 JEE/AIR rank."
                    if rank <= 10000:
                        return 2.5, "Noteworthy academic performance: top 10000 JEE/AIR rank."
                return 2.0, "Academic rank or JEE achievement mentioned."
            if match_type == "Tier-1 University":
                return 3.5, "Graduated from a top tier global or national academic institution."
            if any(kw in title_lower for kw in ["scholarship", "ntse", "kvpy", "olympiad"]):
                return 3.0, "Prestigious academic award or scholarship (NTSE, KVPY, Olympiad)."
            if "cgpa" in title_lower or "gpa" in title_lower:
                gpa_match = re.search(r"\b(9\.[5-9]|10)\b", title_lower)
                if gpa_match:
                    return 3.0, "Outstanding academic performance: CGPA >= 9.5 or equivalent."
                return 2.0, "Strong academic performance: CGPA >= 9.0 or equivalent."
            return 1.5, "Academic distinction or merit signal detected."

        elif category == "technical":
            if match_type == "Hackathon Win" or any(kw in title_lower for kw in ["won", "winner", "1st", "champion"]):
                return 4.0, "Won or secured a top position in a hackathon or technical competition."
            if "hackathon" in title_lower:
                return 1.5, "Hackathon participation or finalist signal."
            if any(kw in title_lower for kw in ["kaggle", "codeforces", "codechef", "icpc"]):
                if any(kw in title_lower for kw in ["grandmaster", "master", "gold", "regionalist", "finalist"]):
                    return 4.5, "Exceptional competitive programming credentials (Kaggle/Codeforces/ICPC)."
                return 2.5, "Active profile on competitive coding platforms (Codeforces/Codechef/Leetcode)."
            if "gsoc" in title_lower or "google summer of code" in title_lower or "lfx" in title_lower:
                return 3.5, "Successful participation in highly selective open-source mentorship (GSoC/LFX)."
            if "open source" in title_lower or "contributor" in title_lower or "github" in title_lower:
                return 2.0, "Demonstrated contributions to open-source software or github recognition."
            return 1.5, "Technical achievement signal detected."

        elif category == "research":
            if "patent" in title_lower:
                return 4.5, "Filed or granted patent representing proprietary research innovation."
            if any(kw in title_lower for kw in ["published", "publication", "paper", "ieee", "acm", "neurips"]):
                return 4.0, "Author or co-author of a published scientific paper in a recognized venue."
            if "research" in title_lower:
                return 3.0, "Research internship or research assistantship experience."
            return 1.5, "Research signal detected."

        elif category == "leadership":
            if any(kw in title_lower for kw in ["engineering lead", "team lead", "tech lead", "lead engineer"]):
                return 4.0, "Held professional lead role coordinating engineering teams."
            if any(kw in title_lower for kw in ["managed team", "led team", "mentored", "mentor"]):
                return 3.0, "Active experience in mentorship, coaching, or leading developer teams."
            if any(kw in title_lower for kw in ["president", "vice president", "secretary", "lead"]):
                return 2.5, "Leadership role in student body, club, or community organization."
            return 1.5, "Leadership signal detected."

        elif category == "entrepreneurship":
            if any(kw in title_lower for kw in ["founder", "co-founder", "cofounder"]):
                return 5.0, "Co-founded or founded a startup/company demonstrating extreme initiative."
            if "y combinator" in title_lower or "yc" in title_lower:
                return 4.0, "Work experience or backing from Y Combinator startup accelerator."
            if any(kw in title_lower for kw in ["launched", "0 to 1", "scaled"]):
                return 3.0, "Built and shipped products from 0 to 1, or scaled them to significant volumes."
            return 1.5, "Entrepreneurship signal detected."

        return 1.0, "Standout achievement signal detected."
