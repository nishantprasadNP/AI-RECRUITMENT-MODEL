"""
Unit tests for the SkillNormalizer module in ARIS.
"""

import pytest
from app.skill_normalization import SkillNormalizer, NormalizedSkill
from app.skill_normalization.exceptions import AliasFileNotFoundError


def test_normalizer_dry_runs():
    # Load normalizer using the copied skill_aliases.json
    normalizer = SkillNormalizer(alias_file_path="data/skill_graph/skill_aliases.json")

    # 1. ReactJS -> React.js (100%)
    res = normalizer.normalize("ReactJS")
    assert len(res) == 1
    assert res[0].canonical == "React.js"
    assert res[0].confidence == 100

    # 2. NodeJS -> Node.js (100%)
    res = normalizer.normalize("NodeJS")
    assert len(res) == 1
    assert res[0].canonical == "Node.js"
    assert res[0].confidence == 100

    # 3. DSA -> Data Structures and Algorithms (100%)
    res = normalizer.normalize("DSA")
    assert len(res) == 1
    assert res[0].canonical == "Data Structures and Algorithms"
    assert res[0].confidence == 100

    # 4. DS -> Data Structures and Algorithms and Data Science (50% each)
    res = normalizer.normalize("DS")
    assert len(res) == 2
    canonicals = {item.canonical for item in res}
    confidences = {item.confidence for item in res}
    assert canonicals == {"Data Structures and Algorithms", "Data Science"}
    assert confidences == {50}

    # 5. Mongo -> MongoDB (100%)
    res = normalizer.normalize("Mongo")
    assert len(res) == 1
    assert res[0].canonical == "MongoDB"
    assert res[0].confidence == 100

    # 6. Postgres -> PostgreSQL (100%)
    res = normalizer.normalize("Postgres")
    assert len(res) == 1
    assert res[0].canonical == "PostgreSQL"
    assert res[0].confidence == 100

    # 7. Python3 -> Python (100%)
    res = normalizer.normalize("Python3")
    assert len(res) == 1
    assert res[0].canonical == "Python"
    assert res[0].confidence == 100


def test_normalizer_fallback():
    normalizer = SkillNormalizer(alias_file_path="data/skill_graph/skill_aliases.json")

    # An unknown skill should return the original skill trimmed with 100% confidence
    res = normalizer.normalize("  UnknownSkill   ")
    assert len(res) == 1
    assert res[0].canonical == "UnknownSkill"
    assert res[0].confidence == 100


def test_normalizer_invalid_inputs():
    normalizer = SkillNormalizer(alias_file_path="data/skill_graph/skill_aliases.json")

    # Empty inputs or invalid types should return empty lists gracefully
    assert normalizer.normalize("") == []
    assert normalizer.normalize(None) == []


def test_normalizer_missing_file():
    with pytest.raises(AliasFileNotFoundError):
        SkillNormalizer(alias_file_path="missing_file.json")


def test_job_profile_normalization():
    from app.schemas.job_schema import JobProfile, SkillRequirement, HiddenHiringSignals
    
    # Create a job profile with raw skills
    profile = JobProfile(
        title="Software Engineer",
        required_skills=[
            SkillRequirement(skill="ReactJS", importance=8.0, reason="Frontend development"),
            SkillRequirement(skill="DS", importance=9.0, reason="Data analysis")
        ],
        preferred_skills=[
            SkillRequirement(skill="Mongo", importance=6.0, reason="Database storage")
        ],
        seniority_level="senior",
        role_complexity_score=7,
        hidden_hiring_signals=HiddenHiringSignals(),
        job_summary="Sample summary"
    )

    # Let's normalize it using the orchestrator's normalization logic
    normalizer = SkillNormalizer(alias_file_path="data/skill_graph/skill_aliases.json")

    # Required skills normalization
    normalized_req = []
    for req in profile.required_skills:
        normalized = normalizer.normalize(str(req))
        for norm_skill in normalized:
            normalized_req.append(SkillRequirement(
                skill=norm_skill.canonical,
                importance=req.importance,
                reason=req.reason
            ))
    profile.normalized_required_skills = normalized_req

    # Preferred skills normalization
    normalized_pref = []
    for req in profile.preferred_skills:
        normalized = normalizer.normalize(str(req))
        for norm_skill in normalized:
            normalized_pref.append(SkillRequirement(
                skill=norm_skill.canonical,
                importance=req.importance,
                reason=req.reason
            ))
    profile.normalized_preferred_skills = normalized_pref

    # Verify original skills are preserved
    assert len(profile.required_skills) == 2
    assert str(profile.required_skills[0]) == "ReactJS"
    assert str(profile.required_skills[1]) == "DS"

    # Verify normalized skills are correctly mapped
    # "ReactJS" -> "React.js"
    # "DS" -> ["Data Structures and Algorithms", "Data Science"] (so it duplicates/expands the requirements)
    assert len(profile.normalized_required_skills) == 3
    
    skills = {str(req) for req in profile.normalized_required_skills}
    assert skills == {"React.js", "Data Structures and Algorithms", "Data Science"}

    # Verify preferred normalized
    assert len(profile.normalized_preferred_skills) == 1
    assert str(profile.normalized_preferred_skills[0]) == "MongoDB"


def test_normalize_list_exact_and_ambiguous():
    normalizer = SkillNormalizer(alias_file_path="data/skill_graph/skill_aliases.json")

    # Raw list containing exact and ambiguous aliases
    raw_skills = ["ReactJS", "NodeJS", "Mongo", "DS"]

    normalized_skills, canonical_to_raw_map = normalizer.normalize_list(raw_skills)

    # Verify canonical list deduplicated and resolved
    assert "React.js" in normalized_skills
    assert "Node.js" in normalized_skills
    assert "MongoDB" in normalized_skills
    assert "Data Science" in normalized_skills
    assert "Data Structures and Algorithms" in normalized_skills

    # Verify mapping structure
    assert canonical_to_raw_map["React.js"] == "ReactJS"
    assert canonical_to_raw_map["Node.js"] == "NodeJS"
    assert canonical_to_raw_map["MongoDB"] == "Mongo"
    assert canonical_to_raw_map["Data Science"] == ("DS", 50)
    assert canonical_to_raw_map["Data Structures and Algorithms"] == ("DS", 50)

