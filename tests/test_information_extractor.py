import pytest
from unittest.mock import MagicMock, patch

from app.extractors.resume_information_extractor import (
    ResumeInformationExtractor,
    EmptyResumeTextError,
    MissingAPIKeyError,
    GeminiAPIError,
    InvalidJSONResponseError,
    ProfileValidationError
)
from app.models.resume_schema import ResumeProfile

@pytest.fixture
def mock_extracted_json():
    """Fixture to provide mock structured JSON response."""
    return """{
      "name": "John Doe",
      "skills": ["Python", "SQL", "TensorFlow"],
      "experience": [
        {
          "role": "Data Analyst",
          "company": "ABC Corp",
          "duration": "2 years",
          "start_date": "June 2023",
          "end_date": "Present",
          "description": "Analyzed complex datasets."
        }
      ],
      "projects": [
        {
          "name": "Fraud Detection System",
          "technologies": ["Python", "TensorFlow"],
          "description": "A ML system to prevent fraud."
        }
      ],
      "education": [
        {
          "degree": "B.Tech",
          "institution": "NIT Jalandhar",
          "field": "Computer Science",
          "graduation_year": "2027"
        }
      ],
      "certifications": [
        {
          "name": "Google Data Analytics",
          "issuer": "Google",
          "year": "2025"
        }
      ],
      "achievements": ["Won National Hackathon"]
    }"""

@patch("app.extractors.resume_information_extractor.genai")
def test_valid_extraction(mock_genai, mock_extracted_json):
    """Verify that a valid LLM response yields a correctly parsed ResumeProfile Pydantic object."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_extracted_json
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = ResumeInformationExtractor(api_key="mock_key", model="gemini-2.5-flash")
    profile = extractor.extract("Mock resume text")

    assert isinstance(profile, ResumeProfile)
    assert profile.name == "John Doe"
    assert profile.skills == ["Python", "SQL", "TensorFlow"]
    assert len(profile.experience) == 1
    assert profile.experience[0].role == "Data Analyst"
    assert profile.experience[0].company == "ABC Corp"
    
    # Assert genai configure was called
    mock_genai.configure.assert_called_once_with(api_key="mock_key")
    mock_genai.GenerativeModel.assert_called_once()

@patch("app.extractors.resume_information_extractor.genai")
def test_valid_extraction_with_markdown_fences(mock_genai, mock_extracted_json):
    """Verify that the extractor automatically strips markdown code block wrapping from the JSON response."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    # Wrap response text in markdown code fences
    mock_response.text = f"```json\n{mock_extracted_json}\n```"
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = ResumeInformationExtractor(api_key="mock_key", model="gemini-2.5-flash")
    profile = extractor.extract("Mock resume text")

    assert isinstance(profile, ResumeProfile)
    assert profile.name == "John Doe"
    assert profile.skills == ["Python", "SQL", "TensorFlow"]

def test_empty_resume_handling():
    """Verify that extracting from empty or whitespace-only resume text raises EmptyResumeTextError."""
    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(EmptyResumeTextError):
        extractor.extract("")
        
    with pytest.raises(EmptyResumeTextError):
        extractor.extract("   ")

def test_missing_api_key_handling():
    """Verify that attempting extraction without an API key raises MissingAPIKeyError."""
    extractor = ResumeInformationExtractor(api_key="")
    
    with pytest.raises(MissingAPIKeyError):
        extractor.extract("Valid resume text")

@patch("app.extractors.resume_information_extractor.genai")
def test_malformed_json_handling(mock_genai):
    """Verify that a non-JSON LLM response raises InvalidJSONResponseError."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Malformed response, not standard JSON."
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(InvalidJSONResponseError):
        extractor.extract("Mock resume text")

@patch("app.extractors.resume_information_extractor.genai")
def test_validation_failure_handling(mock_genai):
    """Verify that a response with an incorrect structure raises ProfileValidationError."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    # 'skills' should be a list of strings, but is an integer here
    mock_response.text = """{
      "name": "John Doe",
      "skills": 12345,
      "experience": [],
      "projects": [],
      "education": [],
      "certifications": [],
      "achievements": []
    }"""
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(ProfileValidationError):
        extractor.extract("Mock resume text")

@patch("app.extractors.resume_information_extractor.genai")
def test_api_failure_handling(mock_genai):
    """Verify that standard Gemini API errors raise GeminiAPIError."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("Google Generative AI quota exceeded")

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(GeminiAPIError):
        extractor.extract("Mock resume text")
