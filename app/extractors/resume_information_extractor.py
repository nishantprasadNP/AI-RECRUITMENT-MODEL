import json
import logging
from openai import OpenAI
from pydantic import ValidationError

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.resume_schema import ResumeProfile
from app.prompts.extraction_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# Setup logger
logger = logging.getLogger("resume_parser.information_extractor")

# Custom Exceptions
class ResumeExtractorError(Exception):
    """Base exception for all errors in the Resume Information Extractor."""
    pass

class EmptyResumeTextError(ResumeExtractorError):
    """Exception raised when the input resume text is empty."""
    pass

class MissingAPIKeyError(ResumeExtractorError):
    """Exception raised when the OpenAI API key is missing."""
    pass

class OpenAIAPIError(ResumeExtractorError):
    """Exception raised when OpenAI API call fails or times out."""
    pass

class InvalidJSONResponseError(ResumeExtractorError):
    """Exception raised when the LLM response is not valid JSON."""
    pass

class ProfileValidationError(ResumeExtractorError):
    """Exception raised when the extracted JSON fails Pydantic validation."""
    pass

class ResumeInformationExtractor:
    """
    Service to extract structured profile information from raw resume text
    using OpenAI API and Pydantic validation.
    """

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initializes the extractor with API credentials and model configuration.
        """
        self.api_key = api_key if api_key is not None else OPENAI_API_KEY
        self.model = model if model is not None else OPENAI_MODEL

    def extract(self, resume_text: str) -> ResumeProfile:
        """
        Extracts structured profile details from the given resume text.

        Args:
            resume_text: Raw text string of the resume.

        Returns:
            An instance of ResumeProfile.

        Raises:
            EmptyResumeTextError: If resume_text is empty or whitespace only.
            MissingAPIKeyError: If OpenAI API Key is not configured.
            OpenAIAPIError: If the OpenAI client call fails.
            InvalidJSONResponseError: If the model output is not valid JSON.
            ProfileValidationError: If the parsed JSON fails Pydantic validation.
        """
        logger.info("Extraction started")

        # 1. Validate inputs
        if not resume_text or not resume_text.strip():
            logger.error("Extraction failed: Resume text is empty")
            raise EmptyResumeTextError("Resume text cannot be empty.")

        if not self.api_key:
            logger.error("Extraction failed: Missing OpenAI API Key")
            raise MissingAPIKeyError("OpenAI API Key is missing. Please set the OPENAI_API_KEY environment variable.")

        # 2. Build prompt
        system_prompt = SYSTEM_PROMPT
        user_prompt = USER_PROMPT_TEMPLATE.format(resume_text=resume_text)
        logger.info("Prompt generated")

        # 3. Call OpenAI API
        try:
            client = OpenAI(api_key=self.api_key)
            logger.info("API request sent")
            
            # Use JSON mode to guarantee a JSON object back
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            raw_response = response.choices[0].message.content
            logger.info("API response received")
            
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise OpenAIAPIError(f"OpenAI API call failed: {str(e)}") from e

        # 4. Parse JSON response
        try:
            json_data = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM: {raw_response}")
            raise InvalidJSONResponseError(f"LLM did not return valid JSON: {str(e)}") from e

        # 5. Validate with Pydantic
        try:
            profile = ResumeProfile.model_validate(json_data)
            logger.info("Validation successful")
            return profile
        except ValidationError as e:
            # Log the detailed Pydantic validation errors
            logger.error(f"Validation failed: {e.errors()}")
            raise ProfileValidationError(f"Pydantic validation failed: {str(e)}") from e
