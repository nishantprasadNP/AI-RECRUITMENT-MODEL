import os
import shutil
import logging
import uuid
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from app.orchestrator import RecruitmentOrchestrator
from app.ingestion.resume_parser import ResumeParser

# Setup logging (API wrapper logs)
logger = logging.getLogger("aris.api")
if not logger.handlers:
  handler = logging.StreamHandler()
  formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.setLevel(logging.INFO)

app = FastAPI(
    title="ARIS API",
    description="FastAPI REST API wrapper for the AI Recruitment Intelligence System (ARIS)",
    version="2.0.0"
)

# CORS configuration for the React frontend running on http://localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


def serialize_model(model: Any) -> Any:
    """Helper to safely serialize Pydantic V1/V2 models or return None."""
    if model is None:
        return None
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return jsonable_encoder(model)


def extract_text_from_jd_file(file_path: str) -> str:
    """Extracts job description text from either .txt or .pdf files."""
    if file_path.lower().endswith(".pdf"):
        # Reuse existing PDF parser logic from the codebase
        parser = ResumeParser()
        return parser.extract_text(file_path)
    else:
        # Default to reading as plain text UTF-8
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


@app.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_candidate_fit(
    resume: UploadFile = File(...),
    jd: UploadFile = File(...)
):
    """
    Exposes the complete ARIS evaluation pipeline.
    Accepts:
      - resume: PDF file containing candidate's profile.
      - jd: Text (.txt) or PDF (.pdf) file containing job specifications.
    """
    logger.info("Request received: POST /analyze")

    # 1. Validate file types
    if not resume.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid resume file type: {resume.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be a PDF file (.pdf)"
        )
    
    if not (jd.filename.lower().endswith(".txt") or jd.filename.lower().endswith(".pdf")):
        logger.warning(f"Invalid JD file type: {jd.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job Description must be a text (.txt) or PDF (.pdf) file"
        )

    # Generate unique filenames to avoid collision in concurrent environments
    req_id = str(uuid.uuid4())
    temp_resume_path = os.path.join(TEMP_DIR, f"resume_{req_id}.pdf")
    temp_jd_path = os.path.join(TEMP_DIR, f"jd_{req_id}_{jd.filename}")

    try:
        # 2. Save uploaded files to the temp directory
        with open(temp_resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        with open(temp_jd_path, "wb") as buffer:
            shutil.copyfileobj(jd.file, buffer)

        # 3. Read and parse Job Description text
        try:
            jd_text = extract_text_from_jd_file(temp_jd_path)
        except Exception as e:
            logger.error(f"Failed to read/parse Job Description file: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read/parse Job Description file: {e}"
            )

        if not jd_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job Description file is empty."
            )

        # 4. Instantiate and run orchestrator
        logger.info("Orchestrator started for resume %s and job %s", resume.filename, jd.filename)
        orchestrator = RecruitmentOrchestrator()
        
        result = orchestrator.run(
            resume_pdf_path=temp_resume_path,
            jd_text=jd_text,
            job_name="Software Engineer"
        )
        logger.info("Orchestrator completed successfully")

        # 5. Extract additional confidence profiles (without modifying orchestrator.py)
        confidence_profiles = {}
        if result.resume_profile:
            try:
                confidence_profiles = orchestrator._skill_confidence_engine.analyze(result.resume_profile)
            except Exception as e:
                logger.warning(f"Failed to calculate skill confidence profiles: {e}")

        # 6. Build response object and serialize Pydantic models
        serialized_confidence = {
            skill: serialize_model(prof) 
            for skill, prof in confidence_profiles.items()
        }

        response_data = {
            "candidate_name": result.candidate_name,
            "semantic_score": result.semantic_score,
            "role_profile": serialize_model(result.role_profile),
            "hard_requirement_result": serialize_model(result.hard_requirement_result),
            "confidence_profiles": serialized_confidence,
            "achievement_profile": serialize_model(result.achievement_profile),
            "skill_gap": serialize_model(result.skill_gap_result),
            "skill_gap_result": serialize_model(result.skill_gap_result), # Double export for frontend compatibility
            "candidate_score": serialize_model(result.candidate_score),
            "match_report_path": result.match_report_path
        }

        logger.info("Response sent: 200 OK")
        return response_data

    except HTTPException:
        # Re-raise FastAPIs HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Unexpected pipeline execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(e)}"
        )
    finally:
        # 7. Clean up temporary files
        for path in (temp_resume_path, temp_jd_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temporary file {path}: {cleanup_err}")
