"""
Unit tests for Phase 4 Evaluation Strategy Engine.
"""

import pytest
from pydantic import ValidationError

from app.role_classification.models import RoleProfile
from app.evaluation_strategy.models import EvaluationStrategy
from app.evaluation_strategy.strategy_rules import StrategyRuleLibrary
from app.evaluation_strategy.strategy_engine import EvaluationStrategyEngine
from app.evaluation_strategy.exceptions import (
    EvaluationStrategyError,
    StrategyNotFoundError,
    InvalidStrategyConfigError,
)


def test_evaluation_strategy_model_validation():
    # Valid weights
    valid_data = {
        "evaluation_profile": "intern_backend",
        "strictness_level": "low",
        "component_weights": {
            "skills": 0.35,
            "projects": 0.40,
            "experience": 0.20,
            "achievements": 0.05
        },
        "minimum_skill_confidence": 30.0,
        "hard_requirement_tolerance": 30.0
    }
    strategy = EvaluationStrategy(**valid_data)
    assert strategy.evaluation_profile == "intern_backend"

    # Invalid weights sum
    invalid_data = dict(valid_data)
    invalid_data["component_weights"] = {
        "skills": 0.50,
        "projects": 0.40,
        "experience": 0.20
    }
    with pytest.raises(ValidationError) as excinfo:
        EvaluationStrategy(**invalid_data)
    assert "Component weights must sum to approximately 1.0" in str(excinfo.value)


def test_strategy_rule_library():
    lib = StrategyRuleLibrary()

    # Predefined profiles
    assert lib.has_profile("intern_backend")
    assert lib.has_profile("senior_backend")
    assert lib.has_profile("senior_ml")

    # Get config
    config = lib.get_profile_config("intern_backend")
    assert config["strictness_level"] == "low"
    assert config["component_weights"]["skills"] == 0.30

    # Get non-existent
    with pytest.raises(StrategyNotFoundError):
        lib.get_profile_config("non_existent_profile")

    # Register custom profile
    custom_config = {
        "evaluation_profile": "custom_profile",
        "strictness_level": "medium",
        "component_weights": {
            "skills": 0.50,
            "projects": 0.50
        },
        "minimum_skill_confidence": 50.0,
        "hard_requirement_tolerance": 15.0
    }
    lib.register_profile("custom_profile", custom_config)
    assert lib.has_profile("custom_profile")
    assert lib.get_profile_config("custom_profile")["strictness_level"] == "medium"

    # Register invalid config
    bad_config = dict(custom_config)
    bad_config["component_weights"] = {"skills": 0.80}  # Doesn't sum to 1
    with pytest.raises(InvalidStrategyConfigError):
        lib.register_profile("bad_profile", bad_config)


def test_evaluation_strategy_engine():
    engine = EvaluationStrategyEngine()

    # Valid RoleProfile matching direct rule
    role = RoleProfile(
        role_family="software_engineering",
        specialization="backend_engineer",
        seniority="senior",
        evaluation_profile="senior_backend"
    )
    strategy = engine.generate_strategy(role)
    assert strategy.evaluation_profile == "senior_backend"
    assert strategy.strictness_level == "high"
    assert strategy.component_weights["experience"] == 0.35

    # Fallback to senior_backend when staff_backend or staff_engineer is requested but not in rule library (we added staff_backend, let's test a brand new one like staff_frontend)
    role_fallback = RoleProfile(
        role_family="software_engineering",
        specialization="frontend_engineer",
        seniority="staff",
        evaluation_profile="staff_frontend"
    )
    strategy_fb = engine.generate_strategy(role_fallback)
    # staff maps to senior, frontend removes _engineer, so senior_frontend. Since senior_frontend doesn't exist, it maps to senior_backend
    assert strategy_fb.evaluation_profile == "senior_backend"

    # Fallback to mid_backend for unknown role and unknown seniority
    role_unknown = RoleProfile(
        role_family="unknown_family",
        specialization="unknown_spec",
        seniority="unknown_seniority",
        evaluation_profile="unknown_profile"
    )
    strategy_fb2 = engine.generate_strategy(role_unknown)
    assert strategy_fb2.evaluation_profile == "mid_backend"


def test_evaluation_strategy_engine_none_input():
    engine = EvaluationStrategyEngine()
    with pytest.raises(EvaluationStrategyError):
        engine.generate_strategy(None)
