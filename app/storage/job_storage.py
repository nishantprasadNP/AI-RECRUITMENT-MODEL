import os
import re
import logging
from app.models.job_schema import JobProfile

logger = logging.getLogger("resume_parser.job_storage")

def save_job_profile(profile: JobProfile, role_name: str = "job_profile", output_dir: str = "data/extracted_jobs") -> str:
    """
    Saves a JobProfile instance to a filesystem-safe JSON file.
    The filename is generated based on the normalized role_name.
    
    Args:
        profile: The JobProfile instance to save.
        role_name: The name of the role (e.g. Senior Software Engineer) used for filename.
        output_dir: The directory where the profile should be saved.
        
    Returns:
        The absolute path to the saved JSON file.
    
    Raises:
        OSError: If writing to the file fails.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Normalize role name: lowercase, replace non-alphanumeric characters with underscores
    safe_name = role_name.lower().strip()
    safe_name = re.sub(r'[^a-z0-9]+', '_', safe_name)
    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')
    
    if not safe_name:
        safe_name = "job_profile"
        
    filename = f"{safe_name}.json"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Convert Pydantic model to pretty JSON
        profile_json = profile.model_dump_json(indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(profile_json)
        logger.info(f"Job JSON saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save job profile JSON to {filepath}: {str(e)}")
        raise OSError(f"Failed to write job profile file: {str(e)}") from e
