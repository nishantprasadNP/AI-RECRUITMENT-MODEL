from app.role_classification.role_classifier import RoleClassifier
from app.schemas.job_schema import JobProfile, HiddenHiringSignals


def create_job(
    title,
    skills,
    exp,
    expected_family,
    expected_specialization,
    expected_seniority,
):
    return {
        "job": JobProfile(
            title=title,
            required_skills=skills,
            preferred_skills=[],
            critical_skills=[],
            experience_required=exp,
            education=None,
            leadership=False,
            seniority_level="",
            responsibility_themes=[],
            domain_knowledge=[],
            soft_skills=[],
            tools_and_technologies=[],
            hidden_hiring_signals=HiddenHiringSignals(),
            role_complexity_score=5,
            future_potential_signals=[],
            job_summary=title,
        ),
        "expected_family": expected_family,
        "expected_specialization": expected_specialization,
        "expected_seniority": expected_seniority,
    }


def print_separator():
    print("=" * 80)


def main():

    classifier = RoleClassifier()

    test_cases = [
        create_job(
            "Backend Software Engineer",
            ["Python", "Kafka", "AWS"],
            3,
            "software_engineering",
            "backend_engineer",
            "mid_level",
        ),
        create_job(
            "Frontend Engineer",
            ["React", "TypeScript"],
            2,
            "software_engineering",
            "frontend_engineer",
            "mid_level",
        ),
        create_job(
            "Full Stack Engineer",
            ["React", "Node.js", "MongoDB"],
            4,
            "software_engineering",
            "fullstack_engineer",
            "senior",
        ),
        create_job(
            "Mobile Engineer",
            ["Android", "Kotlin"],
            2,
            "software_engineering",
            "mobile_engineer",
            "mid_level",
        ),
        create_job(
            "Machine Learning Engineer",
            ["Python", "TensorFlow", "PyTorch"],
            5,
            "data_ai",
            "ml_engineer",
            "senior",
        ),
        create_job(
            "Data Engineer",
            ["Spark", "Airflow", "Kafka"],
            5,
            "data_ai",
            "data_engineer",
            "senior",
        ),
        create_job(
            "Data Scientist",
            ["Python", "Pandas", "Scikit-learn"],
            4,
            "data_ai",
            "data_scientist",
            "senior",
        ),
        create_job(
            "AI Research Engineer",
            ["Transformers", "LLMs", "PyTorch"],
            8,
            "data_ai",
            "ai_research_engineer",
            "staff",
        ),
        create_job(
            "DevOps Engineer",
            ["Docker", "Kubernetes", "Terraform"],
            8,
            "cloud_engineering",
            "devops_engineer",
            "staff",
        ),
        create_job(
            "Cloud Engineer",
            ["AWS", "Terraform"],
            5,
            "cloud_engineering",
            "cloud_engineer",
            "senior",
        ),
        create_job(
            "Security Engineer",
            ["SIEM", "Penetration Testing"],
            5,
            "security_engineering",
            "security_engineer",
            "senior",
        ),
        create_job(
            "Technical Product Manager",
            ["Agile", "Roadmap"],
            6,
            "product_management",
            "product_manager",
            "senior",
        ),
    ]

    passed = 0
    failed = 0

    print_separator()
    print("ARIS PHASE 3 VALIDATION SUITE")
    print_separator()

    for idx, test in enumerate(test_cases, start=1):

        role_profile = classifier.classify(test["job"])

        family_ok = (
            role_profile.role_family
            == test["expected_family"]
        )

        specialization_ok = (
            role_profile.specialization
            == test["expected_specialization"]
        )

        seniority_ok = (
            role_profile.seniority
            == test["expected_seniority"]
        )

        result = (
            family_ok
            and specialization_ok
            and seniority_ok
        )

        print_separator()

        print(f"TEST #{idx}")
        print(f"TITLE: {test['job'].title}")

        print()

        print(
            f"Family Expected   : {test['expected_family']}"
        )
        print(
            f"Family Predicted  : {role_profile.role_family}"
        )

        print()

        print(
            f"Spec Expected     : {test['expected_specialization']}"
        )
        print(
            f"Spec Predicted    : {role_profile.specialization}"
        )

        print()

        print(
            f"Seniority Expected: {test['expected_seniority']}"
        )
        print(
            f"Seniority Actual  : {role_profile.seniority}"
        )

        print()

        if result:
            print("RESULT: PASS")
            passed += 1
        else:
            print("RESULT: FAIL")
            failed += 1

    print_separator()
    print("FINAL SUMMARY")
    print_separator()

    total = passed + failed

    accuracy = (
        (passed / total) * 100
        if total > 0
        else 0
    )

    print(f"Passed : {passed}")
    print(f"Failed : {failed}")
    print(f"Accuracy : {accuracy:.2f}%")

    print_separator()


if __name__ == "__main__":
    main()