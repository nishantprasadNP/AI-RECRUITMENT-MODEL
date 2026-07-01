import os
import shutil
import logging
import uuid
from typing import Dict, Any, List
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from app.orchestrator import RecruitmentOrchestrator
from app.ingestion.resume_parser import ResumeParser
from app.schemas.recruiter_copilot import RecruiterRecommendation

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


def generate_recruiter_recommendation_data(
    result: Any,
    confidence_profiles: Dict[str, Any]
) -> Dict[str, Any]:
    why_score = []
    
    # 1. Hard requirements evaluation
    if result.hard_requirement_result:
        if result.hard_requirement_result.passed:
            why_score.append("✓ Passed all hard requirements")
        else:
            why_score.append(f"✗ Failed hard requirements: {result.hard_requirement_result.decision_reason}")
    
    # 2. Semantic alignment
    if hasattr(result, "semantic_score"):
        semantic_score_pct = result.semantic_score * 100
        if semantic_score_pct >= 80.0:
            why_score.append("✓ High semantic alignment with JD")
        elif semantic_score_pct >= 60.0:
            why_score.append("✓ Moderate semantic alignment with JD")
        else:
            why_score.append("✗ Low semantic alignment with JD")

    # 3. Project experience
    spec_str = ""
    if result.role_profile and result.role_profile.specialization:
        spec_str = result.role_profile.specialization.replace("_", " ").title()
    
    project_score = 0.0
    if result.candidate_score and "projects" in result.candidate_score.component_scores:
        project_score = result.candidate_score.component_scores["projects"]
    
    if project_score >= 80.0:
        if spec_str:
            why_score.append(f"✓ Strong {spec_str} project experience")
        else:
            why_score.append("✓ Strong project experience")
            
    # 4. Internship experience
    has_internship = False
    if result.resume_profile and result.resume_profile.experience:
        for exp in result.resume_profile.experience:
            role = (exp.role or "").lower()
            desc = (exp.description or "").lower()
            if "intern" in role or "internship" in role or "intern" in desc or "internship" in desc:
                has_internship = True
                break
    if has_internship:
        why_score.append("✓ Internship experience")
        
    # 5. Skill confidence (list top skills with high confidence, e.g. >= 75)
    high_conf_skills = []
    for skill, prof in confidence_profiles.items():
        score = getattr(prof, "confidence_score", 0.0)
        if score >= 75.0:
            high_conf_skills.append((skill, score))
            
    high_conf_skills.sort(key=lambda x: x[1], reverse=True)
    for skill, _ in high_conf_skills[:3]:
        why_score.append(f"✓ Strong {skill} confidence")
        
    # 6. Missing skills
    missing_skills = []
    if result.skill_gap_result:
        missing_skills.extend(result.skill_gap_result.missing_required_skills)
        missing_skills.extend(result.skill_gap_result.missing_preferred_skills)
        
    missing_skills = sorted(list(set(missing_skills)))
    
    # 7. Strengths
    strengths = []
    if result.candidate_score:
        from app.candidate_ranking.ranking_engine import CandidateRankingEngine
        ranking_eng = CandidateRankingEngine()
        strengths = ranking_eng._extract_strengths(result.candidate_score)
        
    # 8. Recommendation
    score = result.candidate_score.overall_score if result.candidate_score else 0.0
    passed_hard = result.hard_requirement_result.passed if result.hard_requirement_result else False
    
    if not passed_hard:
        recommendation = "Reject"
    elif score >= 85.0:
        recommendation = "Proceed to Technical Interview"
    elif score >= 70.0:
        recommendation = "Recruiter Review"
    else:
        recommendation = "Not Recommended"
        
    # 9. Confidence summary
    confidence_summary = {}
    for skill, prof in confidence_profiles.items():
        c_score = getattr(prof, "confidence_score", 0.0)
        confidence_summary[skill] = c_score
        
    return {
        "overall_score": score,
        "why_score": why_score,
        "strengths": strengths,
        "missing_skills": missing_skills,
        "recommendation": recommendation,
        "confidence_summary": confidence_summary
    }


@app.post("/analyze/multiple", status_code=status.HTTP_200_OK)
async def analyze_multiple_candidates(
    resumes: List[UploadFile] = File(...),
    jd: UploadFile = File(...)
):
    """
    Evaluates multiple candidates (resumes) against a single job description.
    Ranks the candidates and provides explainability DTOs for recruiter review.
    """
    logger.info("Request received: POST /analyze/multiple")

    # 1. Validate file types
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one resume file must be uploaded"
        )

    for resume in resumes:
        if not resume.filename.lower().endswith(".pdf"):
            logger.warning(f"Invalid resume file type: {resume.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Resume file '{resume.filename}' must be a PDF file (.pdf)"
            )
    
    if not (jd.filename.lower().endswith(".txt") or jd.filename.lower().endswith(".pdf")):
        logger.warning(f"Invalid JD file type: {jd.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job Description must be a text (.txt) or PDF (.pdf) file"
        )

    req_id = str(uuid.uuid4())
    temp_jd_path = os.path.join(TEMP_DIR, f"jd_{req_id}_{jd.filename}")
    temp_resume_paths = []

    try:
        # 2. Save uploaded JD to the temp directory
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

        orchestrator = RecruitmentOrchestrator()
        results = []

        # 4. Run existing pipeline independently for every resume
        for resume in resumes:
            temp_resume_path = os.path.join(TEMP_DIR, f"resume_{req_id}_{resume.filename}")
            temp_resume_paths.append(temp_resume_path)
            
            # Save resume file
            resume.file.seek(0) # ensure read from beginning
            with open(temp_resume_path, "wb") as buffer:
                shutil.copyfileobj(resume.file, buffer)
            
            logger.info("Orchestrator started for resume %s in batch mode", resume.filename)
            result = orchestrator.run(
                resume_pdf_path=temp_resume_path,
                jd_text=jd_text,
                job_name="Software Engineer"
            )
            results.append(result)

        # 5. Collect all CandidateScoreProfiles
        score_profiles = []
        for res in results:
            if res.candidate_score:
                score_profiles.append(res.candidate_score)
            else:
                logger.warning("Candidate %s has no score profile.", res.candidate_name)

        # 6. Pass the complete list into the existing CandidateRankingEngine
        ranked_list = orchestrator._candidate_ranking_engine.rank(score_profiles)

        # 7. Build DTO explanation results for each ranked candidate
        ranked_candidates_data = []
        for rc in ranked_list.root:
            # Find the original orchestrator result for this candidate name
            orig_res = next((r for r in results if r.candidate_name == rc.candidate_name), None)
            if not orig_res:
                logger.warning(f"Could not find matching orchestrator result for candidate: {rc.candidate_name}")
                continue

            # Extract additional confidence profiles
            confidence_profiles = {}
            if orig_res.resume_profile:
                try:
                    confidence_profiles = orchestrator._skill_confidence_engine.analyze(orig_res.resume_profile)
                except Exception as e:
                    logger.warning(f"Failed to calculate skill confidence profiles: {e}")

            # Generate Recruiter Recommendation DTO
            rec_data = generate_recruiter_recommendation_data(orig_res, confidence_profiles)
            
            # Map into schema dictionary
            item = {
                "rank": rc.rank,
                "candidate": rc.candidate_name, # alias compatibility
                "candidate_name": rc.candidate_name,
                "score": rc.overall_score, # alias compatibility
                "overall_score": rc.overall_score,
                "strengths": rc.strengths,
                "concerns": rc.concerns,
                "recommendation": rec_data["recommendation"],
                "hard_requirement_status": "Passed" if (orig_res.hard_requirement_result and orig_res.hard_requirement_result.passed) else "Failed",
                "semantic_score": round(orig_res.semantic_score * 100, 1),
                "recruiter_recommendation": rec_data,
                "component_scores": orig_res.candidate_score.component_scores if orig_res.candidate_score else {},
                # We can also put the full RecruiterRecommendation fields flat-mapped or nested for flexibility
                "why_score": rec_data["why_score"],
                "missing_skills": rec_data["missing_skills"],
                "confidence_summary": rec_data["confidence_summary"]
            }
            ranked_candidates_data.append(item)

        # 8. Compute recruiter summary metrics
        total_evaluated = len(results)
        passed_hard_count = sum(1 for r in results if r.hard_requirement_result and r.hard_requirement_result.passed)
        failed_hard_count = total_evaluated - passed_hard_count

        recommendation_counts = {
            "Proceed to Technical Interview": 0,
            "Recruiter Review": 0,
            "Not Recommended": 0,
            "Reject": 0
        }
        for item in ranked_candidates_data:
            rec = item["recommendation"]
            if rec in recommendation_counts:
                recommendation_counts[rec] += 1

        recruiter_summary = {
            "total_evaluated": total_evaluated,
            "passed_hard_requirements": passed_hard_count,
            "failed_hard_requirements": failed_hard_count,
            "recommendations_breakdown": recommendation_counts
        }

        # 9. Get Job profile information
        job_data = {}
        if results and results[0].job_profile:
            job_data = serialize_model(results[0].job_profile)

        response_data = {
            "job": job_data,
            "ranked_candidates": ranked_candidates_data,
            "recruiter_summary": recruiter_summary
        }

        logger.info("Response sent for POST /analyze/multiple: 200 OK")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected pipeline execution error in batch endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during batch analysis: {str(e)}"
        )
    finally:
        # Clean up temporary files
        all_temp_paths = [temp_jd_path] + temp_resume_paths
        for path in all_temp_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temporary file {path}: {cleanup_err}")
