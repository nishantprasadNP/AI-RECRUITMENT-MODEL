import os
import re
import logging
from app.models.resume_schema import ResumeProfile

logger = logging.getLogger("resume_parser.profile_storage")

def save_profile(profile: ResumeProfile, output_dir: str = "data/extracted_profiles") -> str:
    """
    Saves a ResumeProfile instance to a filesystem-safe JSON file.
    The filename is generated based on the normalized candidate name.
    
    Args:
        profile: The ResumeProfile instance to save.
        output_dir: The directory where the profile should be saved.
        
    Returns:
        The absolute path to the saved JSON file.
    
    Raises:
        OSError: If writing to the file fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract name, default to "anonymous" if missing
    candidate_name = profile.name or "anonymous"
    
    # Normalize name: lowercase, replace non-alphanumeric characters with underscores
    safe_name = candidate_name.lower().strip()
    safe_name = re.sub(r'[^a-z0-9]+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    
    if not safe_name:
        safe_name = "anonymous"
        
    filename = f"{safe_name}.json"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Convert Pydantic model to pretty JSON
        profile_json = profile.model_dump_json(indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(profile_json)
        logger.info(f"JSON saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save profile JSON to {filepath}: {str(e)}")
        raise OSError(f"Failed to write profile file: {str(e)}") from e
