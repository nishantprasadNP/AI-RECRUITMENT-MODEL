import json
import logging
import re
import google.generativeai as genai
from pydantic import ValidationError

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models.job_schema import JobProfile
from app.prompts.job_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# Setup logger
logger = logging.getLogger("resume_parser.job_extractor")

# Custom Exceptions
class JobExtractorError(Exception):
    """Base exception for all errors in the Job Description Extractor."""
    pass

class EmptyJobTextError(JobExtractorError):
    """Exception raised when the input job description text is empty."""
    pass

class MissingAPIKeyError(JobExtractorError):
    """Exception raised when the Gemini API key is missing."""
    pass

class GeminiAPIError(JobExtractorError):
    """Exception raised when Gemini API call fails or times out."""
    pass

class InvalidJSONResponseError(JobExtractorError):
    """Exception raised when the LLM response is not valid JSON."""
    pass

class ProfileValidationError(JobExtractorError):
    """Exception raised when the extracted JSON fails Pydantic validation."""
    pass

class JobExtractor:
    """
    Service to extract structured profile information from raw job description text
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

    def extract(self, job_text: str) -> JobProfile:
        """
        Extracts structured job profile details from the given job description text.

        Args:
            job_text: Raw text string of the job description.

        Returns:
            An instance of JobProfile.

        Raises:
            EmptyJobTextError: If job_text is empty or whitespace only.
            MissingAPIKeyError: If Gemini API Key is not configured.
            GeminiAPIError: If the Gemini client call fails.
            InvalidJSONResponseError: If the model output is not valid JSON.
            ProfileValidationError: If the parsed JSON fails Pydantic validation.
        """
        logger.info("Job extraction started")

        # 1. Validate inputs
        if not job_text or not job_text.strip():
            logger.error("Job extraction failed: Job text is empty")
            raise EmptyJobTextError("Job description text cannot be empty.")

        if not self.api_key:
            logger.error("Job extraction failed: Missing Gemini API Key")
            raise MissingAPIKeyError("Gemini API Key is missing. Please set the GEMINI_API_KEY environment variable.")

        # 2. Build prompts
        system_prompt = SYSTEM_PROMPT
        user_prompt = USER_PROMPT_TEMPLATE.format(job_description=job_text)
        logger.info("Job prompt generated")

        # 3. Call Google Gemini API
        try:
            genai.configure(api_key=self.api_key)
            
            # Setup the generative model with the system instruction
            model = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_prompt
            )
            
            logger.info("Job API request sent")
            
            response = model.generate_content(
                user_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            raw_response = response.text
            
            if not raw_response:
                logger.error("Job API request failed: Empty response received")
                raise GeminiAPIError("Empty response received from Gemini.")
                
            logger.info("Job API response received")
            
        except Exception as e:
            if isinstance(e, GeminiAPIError):
                raise
            logger.error(f"Job API request failed: {str(e)}")
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
            profile = JobProfile.model_validate(json_data)
            logger.info("Job validation successful")
            return profile
        except ValidationError as e:
            logger.error(f"Job validation failed: {e.errors()}")
            raise ProfileValidationError(f"Pydantic validation failed: {str(e)}") from e
