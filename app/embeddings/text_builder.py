import logging
from app.models.resume_schema import ResumeProfile
from app.models.job_schema import JobProfile

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
    """
    if not isinstance(job, JobProfile):
        logger.error(f"Invalid input type: expected JobProfile, got {type(job)}")
        raise TypeError("Input must be an instance of JobProfile")

    sections = []

    # 1. Job Summary
    if job.job_summary:
        sections.append(f"Job Summary:\n{job.job_summary}")

    # 2. Critical Skills
    if job.critical_skills:
        sections.append("Critical Skills:\n" + "\n".join(job.critical_skills))

    # 3. Required Skills
    if job.required_skills:
        sections.append("Required Skills:\n" + "\n".join(job.required_skills))

    # 4. Preferred Skills
    if job.preferred_skills:
        sections.append("Preferred Skills:\n" + "\n".join(job.preferred_skills))

    # 5. Responsibility Themes
    if job.responsibility_themes:
        sections.append("Responsibility Themes:\n" + "\n".join(job.responsibility_themes))

    # 6. Soft Skills
    if job.soft_skills:
        sections.append("Soft Skills:\n" + "\n".join(job.soft_skills))

    # 7. Domain Knowledge
    if job.domain_knowledge:
        sections.append("Domain Knowledge:\n" + "\n".join(job.domain_knowledge))

    # 8. Tools and Technologies
    if job.tools_and_technologies:
        sections.append("Tools and Technologies:\n" + "\n".join(job.tools_and_technologies))

    result = "\n\n".join(sections)
    logger.info(f"Successfully built job text. Total length: {len(result)} characters.")
    return result
