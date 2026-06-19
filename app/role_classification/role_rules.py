"""
Rule-based constants and helper mappings for role classification in ARIS.
Provides deterministic, static rules mapping job titles and skill indicators
to role families and specializations without using LLMs or embeddings.
"""

from typing import Dict, List

# --- Helper Skill Set Constants ---

BACKEND_SKILLS: List[str] = [
    "python", "django", "flask", "fastapi", "java", "spring boot", "spring", "go",
    "golang", "node.js", "nodejs", "express", "ruby", "rails", "c#", ".net", "php",
    "laravel", "sql", "postgresql", "mysql", "mongodb", "redis", "kafka", "rabbitmq",
    "api design", "rest api", "graphql", "microservices", "grpc"
]

FRONTEND_SKILLS: List[str] = [
    "react", "react.js", "reactjs", "angular", "vue", "vue.js", "vuejs", "typescript",
    "javascript", "html", "css", "sass", "next.js", "nextjs", "tailwind", "redux",
    "webpack", "vite", "bootstrap"
]

ML_SKILLS: List[str] = [
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "computer vision", "transformers", "llm",
    "langchain", "huggingface", "jax", "spacy", "nltk", "opencv"
]

DATA_ENGINEERING_SKILLS: List[str] = [
    "airflow", "spark", "hadoop", "flink", "hive", "snowflake", "bigquery", "redshift",
    "databricks", "dbt", "etl", "data pipeline", "kafka", "glue", "luigi", "presto"
]

DEVOPS_SKILLS: List[str] = [
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "helm", "prometheus", "grafana",
    "linux", "bash", "shell", "terraform", "cloudformation"
]

SECURITY_SKILLS: List[str] = [
    "cybersecurity", "cryptography", "oauth", "saml", "penetration testing", "owasp",
    "iam", "siem", "firewall", "tls", "ssl", "vulnerability scan", "soc2", "iso27001",
    "encryption", "decryption"
]

# --- Role Family Mappings ---

ROLE_FAMILY_KEYWORDS: Dict[str, List[str]] = {
    "software_engineering": [
        "software engineer",
        "software developer",
        "backend engineer",
        "backend developer",
        "frontend engineer",
        "frontend developer",
        "full stack engineer",
        "full stack developer",
        "fullstack engineer",
        "fullstack developer",
        "mobile engineer",
        "mobile developer",
        "ios engineer",
        "ios developer",
        "android engineer",
        "android developer",
        "application engineer",
        "systems engineer",
    ],
    "data_ai": [
        "machine learning",
        "ml engineer",
        "ml developer",
        "data scientist",
        "data science",
        "data engineer",
        "ai engineer",
        "ai developer",
        "deep learning",
        "nlp engineer",
        "computer vision",
        "ai research",
        "data analyst",
        "analytics engineer",
    ],
    "cloud_engineering": [
        "cloud engineer",
        "devops",
        "sre",
        "site reliability",
        "platform engineer",
        "infrastructure engineer",
        "cloud architect",
        "cloud developer",
    ],
    "security_engineering": [
        "security engineer",
        "cybersecurity",
        "information security",
        "secops",
        "application security",
        "network security",
        "security analyst",
    ],
    "product_management": [
        "product manager",
        "technical product manager",
        "pm",
        "product owner",
    ],
}

# --- Specialization Mappings ---

SPECIALIZATION_KEYWORDS: Dict[str, List[str]] = {
    "backend_engineer": [
        "backend",
        "back-end",
        "api",
        "microservices",
        "backend engineer",
        "backend developer",
    ],
    "frontend_engineer": [
        "frontend",
        "front-end",
        "ui",
        "ux",
        "web developer",
        "frontend engineer",
        "frontend developer",
    ],
    "fullstack_engineer": [
        "fullstack",
        "full stack",
        "full-stack",
        "full stack engineer",
        "fullstack developer",
    ],
    "mobile_engineer": [
        "mobile",
        "ios",
        "android",
        "swift",
        "kotlin",
        "flutter",
        "react native",
        "mobile engineer",
        "mobile developer",
    ],
    "ml_engineer": [
        "machine learning",
        "ml",
        "deep learning",
        "computer vision",
        "nlp",
        "reinforcement learning",
        "ml engineer",
        "machine learning engineer",
    ],
    "data_engineer": [
        "data engineer",
        "data pipeline",
        "etl",
        "data warehousing",
        "data engineering",
    ],
    "data_scientist": [
        "data scientist",
        "data science",
        "statistical modeling",
        "analytics",
    ],
    "ai_research_engineer": [
        "ai research",
        "research scientist",
        "llm research",
        "ai researcher",
        "research engineer",
    ],
    "devops_engineer": [
        "devops",
        "sre",
        "site reliability",
        "ci/cd",
        "devops engineer",
        "site reliability engineer",
    ],
    "cloud_engineer": [
        "cloud engineer",
        "cloud architect",
        "aws engineer",
        "azure engineer",
        "gcp engineer",
        "infrastructure engineer",
    ],
    "security_engineer": [
        "security engineer",
        "cybersecurity",
        "infosec",
        "application security",
        "security analyst",
    ],
    "product_manager": [
        "product manager",
        "pm",
        "product owner",
        "technical product manager",
    ],
}
