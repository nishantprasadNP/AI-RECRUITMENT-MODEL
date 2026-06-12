import json
import logging
import re
import google.generativeai as genai
from pydantic import ValidationError

from app.config import GEMINI_API_KEY, GEMINI_MODEL
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
    """Exception raised when the Gemini API key is missing."""
    pass

class GeminiAPIError(ResumeExtractorError):
    """Exception raised when Gemini API call fails or times out."""
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
    using Google Gemini API and Pydantic validation.
    """

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initializes the extractor with API credentials and model configuration.
        """
        self.api_key = api_key if api_key is not None else GEMINI_API_KEY
        self.model = model if model is not None else GEMINI_MODEL

    def _clean_json_response(self, raw_text: str) -> str:
        """
        Cleans raw response from Gemini to extract JSON string.
        Strips markdown code blocks (e.g. ```json ... ```) if present.
        """
        if not raw_text:
            return ""
        
        cleaned = raw_text.strip()
        
        # Regex to strip ```json ... ``` or ``` ... ```
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
            
        return cleaned

    def extract(self, resume_text: str) -> ResumeProfile:
        """
        Extracts structured profile details from the given resume text.

        Args:
            resume_text: Raw text string of the resume.

        Returns:
            An instance of ResumeProfile.

        Raises:
            EmptyResumeTextError: If resume_text is empty or whitespace only.
            MissingAPIKeyError: If Gemini API Key is not configured.
            GeminiAPIError: If the Gemini client call fails.
            InvalidJSONResponseError: If the model output is not valid JSON.
            ProfileValidationError: If the parsed JSON fails Pydantic validation.
        """
        logger.info("Extraction started")

        # 1. Validate inputs
        if not resume_text or not resume_text.strip():
            logger.error("Extraction failed: Resume text is empty")
            raise EmptyResumeTextError("Resume text cannot be empty.")

        if not self.api_key:
            logger.error("Extraction failed: Missing Gemini API Key")
            raise MissingAPIKeyError("Gemini API Key is missing. Please set the GEMINI_API_KEY environment variable.")

        # 2. Build prompts
        system_prompt = SYSTEM_PROMPT
        user_prompt = USER_PROMPT_TEMPLATE.format(resume_text=resume_text)
        logger.info("Prompt generated")

        # 3. Call Google Gemini API
        try:
            genai.configure(api_key=self.api_key)
            
            # Setup the generative model with the system instruction
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_prompt
            )
            
            logger.info("API request sent")
            
            response = model.generate_content(
                user_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            raw_response = response.text
            
            if not raw_response:
                logger.error("API request failed: Empty response received")
                raise GeminiAPIError("Empty response received from Gemini.")
                
            logger.info("API response received")
            
        except Exception as e:
            if isinstance(e, GeminiAPIError):
                raise
            logger.error(f"API request failed: {str(e)}")
            raise GeminiAPIError(f"Gemini API call failed: {str(e)}") from e

        # 4. Clean response text (handles markdown formatting)
        cleaned_response = self._clean_json_response(raw_response)

        # 5. Parse JSON response
        try:
            json_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM: {raw_response}")
            raise InvalidJSONResponseError(f"LLM did not return valid JSON: {str(e)}") from e

        # 6. Validate with Pydantic
        try:
            profile = ResumeProfile.model_validate(json_data)
            logger.info("Validation successful")
            return profile
        except ValidationError as e:
            # Log the detailed Pydantic validation errors
            logger.error(f"Validation failed: {e.errors()}")
            raise ProfileValidationError(f"Pydantic validation failed: {str(e)}") from e
