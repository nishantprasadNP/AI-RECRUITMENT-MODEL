import pytest
from unittest.mock import MagicMock, patch

from app.extractors.resume_information_extractor import (
    ResumeInformationExtractor,
    EmptyResumeTextError,
    MissingAPIKeyError,
    OpenAIAPIError,
    InvalidJSONResponseError,
    ProfileValidationError
)
from app.models.resume_schema import ResumeProfile

@pytest.fixture
def mock_openai_response():
    """Fixture to mock a successful structured JSON response from OpenAI."""
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    # Mock return JSON
    mock_message.content = """{
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
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    return mock_response

@patch("app.extractors.resume_information_extractor.OpenAI")
def test_valid_extraction(mock_openai_class, mock_openai_response):
    """Verify that a valid LLM response yields a correctly parsed ResumeProfile Pydantic object."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value = mock_openai_response

    extractor = ResumeInformationExtractor(api_key="mock_key", model="gpt-4.1-mini")
    profile = extractor.extract("Mock resume text")

    assert isinstance(profile, ResumeProfile)
    assert profile.name == "John Doe"
    assert profile.skills == ["Python", "SQL", "TensorFlow"]
    assert len(profile.experience) == 1
    assert profile.experience[0].role == "Data Analyst"
    assert profile.experience[0].company == "ABC Corp"
    assert profile.experience[0].duration == "2 years"
    assert profile.experience[0].start_date == "June 2023"
    assert profile.experience[0].end_date == "Present"
    assert profile.experience[0].description == "Analyzed complex datasets."
    
    assert len(profile.projects) == 1
    assert profile.projects[0].name == "Fraud Detection System"
    assert profile.projects[0].technologies == ["Python", "TensorFlow"]
    assert profile.projects[0].description == "A ML system to prevent fraud."
    
    assert len(profile.education) == 1
    assert profile.education[0].degree == "B.Tech"
    assert profile.education[0].institution == "NIT Jalandhar"
    assert profile.education[0].field == "Computer Science"
    assert profile.education[0].graduation_year == "2027"
    
    assert len(profile.certifications) == 1
    assert profile.certifications[0].name == "Google Data Analytics"
    assert profile.certifications[0].issuer == "Google"
    assert profile.certifications[0].year == "2025"
    
    assert profile.achievements == ["Won National Hackathon"]

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

@patch("app.extractors.resume_information_extractor.OpenAI")
def test_malformed_json_handling(mock_openai_class):
    """Verify that a non-JSON LLM response raises InvalidJSONResponseError."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Malformed response, not standard JSON."
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(InvalidJSONResponseError):
        extractor.extract("Mock resume text")

@patch("app.extractors.resume_information_extractor.OpenAI")
def test_validation_failure_handling(mock_openai_class):
    """Verify that a response with an incorrect structure raises ProfileValidationError."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    # 'skills' should be a list of strings, but is an integer here
    mock_message.content = """{
      "name": "John Doe",
      "skills": 12345,
      "experience": [],
      "projects": [],
      "education": [],
      "certifications": [],
      "achievements": []
    }"""
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(ProfileValidationError):
        extractor.extract("Mock resume text")

@patch("app.extractors.resume_information_extractor.OpenAI")
def test_api_failure_handling(mock_openai_class):
    """Verify that standard OpenAI client errors raise OpenAIAPIError."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")

    extractor = ResumeInformationExtractor(api_key="mock_key")
    
    with pytest.raises(OpenAIAPIError):
        extractor.extract("Mock resume text")
