import logging
from app.schemas.resume_schema import ResumeProfile
from app.schemas.job_schema import JobProfile

# Configure logging
logger = logging.getLogger(__name__)

def build_resume_text(profile: ResumeProfile) -> str:
    """
    Converts a ResumeProfile object into a clean, semantic text representation.

    Args:
        profile (ResumeProfile): The validated resume profile model.

    Returns:
        str: A formatted text representation of the resume.

    Raises:
        TypeError: If the input is not a ResumeProfile instance.
    """
    if not isinstance(profile, ResumeProfile):
        logger.error(f"Invalid input type: expected ResumeProfile, got {type(profile)}")
        raise TypeError("Input must be an instance of ResumeProfile")

    sections = []

    # 1. Skills
    if profile.skills:
        skills_text = "Skills:\n" + "\n".join(profile.skills)
        sections.append(skills_text)

    # 2. Experience
    if profile.experience:
        exp_texts = []
        for exp in profile.experience:
            role_comp = []
            if exp.role:
                role_comp.append(exp.role)
            if exp.company:
                role_comp.append(f"at {exp.company}")
            
            line = " ".join(role_comp) if role_comp else "Professional Experience"
            
            dates = []
            if exp.start_date:
                dates.append(exp.start_date)
            if exp.end_date:
                dates.append(f"to {exp.end_date}")
            if exp.duration:
                dates.append(f"({exp.duration})")
            
            if dates:
                line += f" ({' '.join(dates)})"
                
            if exp.description:
                line += f"\nDescription: {exp.description}"
                
            exp_texts.append(line)
        
        sections.append("Experience:\n" + "\n\n".join(exp_texts))

    # 3. Projects
    if profile.projects:
        proj_texts = []
        for proj in profile.projects:
            line = proj.name
            if proj.technologies:
                line += f"\nTechnologies: {', '.join(proj.technologies)}"
            if proj.description:
                line += f"\nDescription: {proj.description}"
            proj_texts.append(line)
        
        sections.append("Projects:\n" + "\n\n".join(proj_texts))

    # 4. Education
    if profile.education:
        edu_texts = []
        for edu in profile.education:
            edu_parts = []
            if edu.degree:
                edu_parts.append(edu.degree)
            if edu.field:
                edu_parts.append(f"in {edu.field}")
            if edu.institution:
                edu_parts.append(f"from {edu.institution}")
            if edu.graduation_year:
                edu_parts.append(f"(Graduated: {edu.graduation_year})")
            
            if edu_parts:
                edu_texts.append(" ".join(edu_parts))
        
        if edu_texts:
            sections.append("Education:\n" + "\n".join(edu_texts))

    # 5. Certifications
    if profile.certifications:
        cert_texts = []
        for cert in profile.certifications:
            cert_parts = [cert.name]
            if cert.issuer:
                cert_parts.append(f"issued by {cert.issuer}")
            if cert.year:
                cert_parts.append(f"({cert.year})")
            cert_texts.append(" ".join(cert_parts))
        
        sections.append("Certifications:\n" + "\n".join(cert_texts))

    # 6. Achievements
    if profile.achievements:
        sections.append("Achievements:\n" + "\n".join(profile.achievements))

    result = "\n\n".join(sections)
    logger.info(f"Successfully built resume text for {profile.name or 'unknown candidate'}. Total length: {len(result)} characters.")
    return result


def build_job_text(job: JobProfile) -> str:
    """
    Converts a JobProfile object into a clean, semantic text representation.

    Args:
        job (JobProfile): The validated job profile model.

    Returns:
        str: A formatted text representation of the job description.

    Raises:
        TypeError: If the input is not a JobProfile instance.
        ValueError: If the resulting text is empty (profile has no usable content).
    """
    if not isinstance(job, JobProfile):
        logger.error(f"Invalid input type: expected JobProfile, got {type(job)}")
        raise TypeError("Input must be an instance of JobProfile")

    sections = []

    # 1. Job Summary
    if job.job_summary:
        sections.append(f"Job Summary:\n{job.job_summary}")

    # 2. Seniority level
    if job.seniority_level:
        sections.append(f"Seniority Level:\n{job.seniority_level}")

    # 3. Critical Skills
    if job.critical_skills:
        sections.append("Critical Skills:\n" + "\n".join(job.critical_skills))

    # 4. Required Skills
    if job.required_skills:
        sections.append("Required Skills:\n" + "\n".join(job.required_skills))

    # 5. Preferred Skills
    if job.preferred_skills:
        sections.append("Preferred Skills:\n" + "\n".join(job.preferred_skills))

    # 6. Responsibility Themes
    if job.responsibility_themes:
        sections.append("Responsibility Themes:\n" + "\n".join(job.responsibility_themes))

    # 7. Soft Skills
    if job.soft_skills:
        sections.append("Soft Skills:\n" + "\n".join(job.soft_skills))

    # 8. Domain Knowledge
    if job.domain_knowledge:
        sections.append("Domain Knowledge:\n" + "\n".join(job.domain_knowledge))

    # 9. Tools and Technologies
    if job.tools_and_technologies:
        sections.append("Tools and Technologies:\n" + "\n".join(job.tools_and_technologies))

    # 10. Future Potential Signals
    if job.future_potential_signals:
        sections.append("Future Potential Signals:\n" + "\n".join(job.future_potential_signals))

    # 11. Hidden Hiring Signals — convert boolean flags to descriptive text
    if job.hidden_hiring_signals:
        signal_labels = {
            "autonomy_required": "High autonomy required",
            "client_facing": "Client-facing role",
            "research_oriented": "Research-oriented work",
            "innovation_focused": "Innovation and R&D focused",
            "startup_environment": "Fast-paced startup environment",
            "high_ownership": "High personal ownership expected",
        }
        active_signals = [
            label
            for attr, label in signal_labels.items()
            if getattr(job.hidden_hiring_signals, attr, False)
        ]
        if active_signals:
            sections.append("Hiring Signals:\n" + "\n".join(active_signals))

    result = "\n\n".join(sections)

    if not result.strip():
        logger.warning(
            "build_job_text produced empty output — the extracted JobProfile has no "
            "usable content. Check that the LLM extraction succeeded for the job description."
        )
        raise ValueError(
            "Job profile text is empty. The LLM may have failed to extract meaningful content "
            "from the job description. Verify the JD text is non-trivial and re-run."
        )

    logger.info(f"Successfully built job text. Total length: {len(result)} characters.")
    return result
