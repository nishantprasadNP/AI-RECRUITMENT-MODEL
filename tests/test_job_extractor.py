import pytest
from unittest.mock import MagicMock, patch

from app.extractors.job_extractor import (
    JobExtractor,
    EmptyJobTextError,
    MissingAPIKeyError,
    GeminiAPIError,
    InvalidJSONResponseError,
    ProfileValidationError
)
from app.models.job_schema import JobProfile

@pytest.fixture
def mock_job_json():
    """Fixture to provide mock structured Job Profile JSON response."""
    return """{
      "required_skills": ["Python", "SQL", "API Design"],
      "preferred_skills": ["AWS", "Docker"],
      "critical_skills": ["Python", "SQL", "API Design", "AWS", "Docker"],
      "experience_required": 5,
      "education": {
        "degree": "B.Tech",
        "field": "Computer Science"
      },
      "leadership": true,
      "seniority_level": "senior",
      "responsibility_themes": ["Backend Development", "API Development"],
      "domain_knowledge": ["FinTech"],
      "soft_skills": ["Leadership", "Mentorship", "Problem Solving"],
      "tools_and_technologies": ["FastAPI", "PostgreSQL", "AWS"],
      "hidden_hiring_signals": {
        "autonomy_required": true,
        "client_facing": false,
        "research_oriented": false,
        "innovation_focused": true,
        "startup_environment": true,
        "high_ownership": true
      },
      "role_complexity_score": 7,
      "future_potential_signals": ["adaptability", "willingness to learn"],
      "job_summary": "Responsible for developing high-concurrency APIs."
    }"""

@patch("app.extractors.job_extractor.genai")
def test_valid_job_extraction(mock_genai, mock_job_json):
    """Verify that a valid LLM response yields a correctly parsed JobProfile Pydantic object."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_job_json
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = JobExtractor(api_key="mock_key", model="gemini-2.5-flash")
    profile = extractor.extract("Mock job description text")

    assert isinstance(profile, JobProfile)
    assert profile.experience_required == 5
    assert profile.seniority_level == "senior"
    assert profile.required_skills == ["Python", "SQL", "API Design"]
    assert profile.education.degree == "B.Tech"
    assert profile.leadership is True
    assert profile.hidden_hiring_signals.high_ownership is True
    
    mock_genai.configure.assert_called_once_with(api_key="mock_key")
    mock_genai.GenerativeModel.assert_called_once()

@patch("app.extractors.job_extractor.genai")
def test_valid_job_extraction_with_markdown_fences(mock_genai, mock_job_json):
    """Verify that the extractor automatically strips markdown code block wrapping from the JSON response."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = f"```json\n{mock_job_json}\n```"
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = JobExtractor(api_key="mock_key", model="gemini-2.5-flash")
    profile = extractor.extract("Mock job description text")

    assert isinstance(profile, JobProfile)
    assert profile.experience_required == 5
    assert profile.seniority_level == "senior"

def test_empty_job_handling():
    """Verify that extracting from empty or whitespace-only job text raises EmptyJobTextError."""
    extractor = JobExtractor(api_key="mock_key")
    
    with pytest.raises(EmptyJobTextError):
        extractor.extract("")
        
    with pytest.raises(EmptyJobTextError):
        extractor.extract("   ")

def test_missing_api_key_handling():
    """Verify that attempting extraction without an API key raises MissingAPIKeyError."""
    extractor = JobExtractor(api_key="")
    
    with pytest.raises(MissingAPIKeyError):
        extractor.extract("Valid job description text")

@patch("app.extractors.job_extractor.genai")
def test_malformed_json_handling(mock_genai):
    """Verify that a non-JSON LLM response raises InvalidJSONResponseError."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Malformed response, not standard JSON."
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = JobExtractor(api_key="mock_key")
    
    with pytest.raises(InvalidJSONResponseError):
        extractor.extract("Mock job description text")

@patch("app.extractors.job_extractor.genai")
def test_validation_failure_handling(mock_genai):
    """Verify that a response with an incorrect structure raises ProfileValidationError."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    # 'role_complexity_score' should be an integer, but is a string here which fails numeric requirements or schema
    # Also 'hidden_hiring_signals' is missing completely (which is required by the JobProfile model structure)
    mock_response.text = """{
      "required_skills": [],
      "preferred_skills": [],
      "critical_skills": [],
      "experience_required": null,
      "education": null,
      "leadership": false,
      "seniority_level": "entry",
      "responsibility_themes": [],
      "domain_knowledge": [],
      "soft_skills": [],
      "tools_and_technologies": [],
      "role_complexity_score": "not_an_int",
      "future_potential_signals": [],
      "job_summary": "Summary"
    }"""
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = JobExtractor(api_key="mock_key")
    
    with pytest.raises(ProfileValidationError):
        extractor.extract("Mock job description text")

@patch("app.extractors.job_extractor.genai")
def test_api_failure_handling(mock_genai):
    """Verify that standard Gemini API errors raise GeminiAPIError."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("Google Generative AI quota exceeded")

    extractor = JobExtractor(api_key="mock_key")
    
    with pytest.raises(GeminiAPIError):
        extractor.extract("Mock job description text")
