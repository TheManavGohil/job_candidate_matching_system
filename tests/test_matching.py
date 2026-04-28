"""
Unit tests for the matching engine and parsing functions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ── Synonym Map Tests ────────────────────────────────────────────────────────

class TestSynonymMap:
    def test_normalize_skill(self):
        from api.utils.synonym_map import normalize_skill
        assert normalize_skill("Python3") == "python"
        assert normalize_skill("React.js") == "react"
        assert normalize_skill("k8s") == "kubernetes"
        assert normalize_skill("JS") == "javascript"
        assert normalize_skill("unknown_skill") == "unknown_skill"

    def test_normalize_skills_dedup(self):
        from api.utils.synonym_map import normalize_skills
        result = normalize_skills(["Python", "python3", "Py", "JavaScript"])
        assert "python" in result
        assert "javascript" in result
        assert len(result) == 2

    def test_extract_skills_from_text(self):
        from api.utils.synonym_map import extract_skills_from_text
        text = "We need someone with Python, React, and Docker experience"
        skills = extract_skills_from_text(text)
        assert "python" in skills
        assert "react" in skills
        assert "docker" in skills


# ── JD Parser Tests ──────────────────────────────────────────────────────────

class TestJDParser:
    def test_parse_basic_jd(self):
        from api.preprocessing.jd_parser import parse_jd
        jd_text = """Senior Python Developer

        Requirements:
        - 5+ years of experience with Python
        - Experience with Django or FastAPI
        - Knowledge of PostgreSQL

        Nice to have:
        - Docker experience
        - AWS knowledge
        """
        result = parse_jd(jd_text)
        assert result["title"] is not None
        assert result["min_years"] == 5.0
        assert isinstance(result["required_skills"], list)
        assert isinstance(result["preferred_skills"], list)
        assert result["raw_text"] == jd_text.strip()

    def test_empty_jd_raises(self):
        from api.preprocessing.jd_parser import parse_jd
        with pytest.raises(ValueError):
            parse_jd("")

    def test_years_extraction(self):
        from api.preprocessing.jd_parser import parse_jd
        result = parse_jd("Software Engineer\nMinimum 3 years of experience required.")
        assert result["min_years"] == 3.0


# ── Resume Parser Tests ─────────────────────────────────────────────────────

class TestResumeParser:
    def test_parse_basic_resume(self):
        from api.preprocessing.resume_parser import parse_resume
        resume_text = """John Doe
        john.doe@example.com

        Experience:
        Senior Software Engineer at Google
        June 2019 - Present
        - Developed microservices using Python and Go
        - Managed Kubernetes clusters on GCP

        Education:
        Master of Computer Science, Stanford University

        Skills:
        Python, Go, Kubernetes, Docker, GCP, PostgreSQL
        """
        result = parse_resume(resume_text)
        assert result["email"] == "john.doe@example.com"
        assert isinstance(result["skills"], list)
        assert len(result["skills"]) > 0
        assert result["education"] is not None

    def test_empty_resume_raises(self):
        from api.preprocessing.resume_parser import parse_resume
        with pytest.raises(ValueError):
            parse_resume("")


# ── Matching Weights Tests ───────────────────────────────────────────────────

class TestWeights:
    def test_weights_sum(self):
        from api.matching.weights import WEIGHTS
        total = (
            WEIGHTS["skill_match"]
            + WEIGHTS["experience_match"]
            + WEIGHTS["education_match"]
            + WEIGHTS["contextual_fit"]
        )
        assert abs(total - 1.0) < 0.01

    def test_get_label(self):
        from api.matching.weights import get_label
        assert get_label(90) == "Top Match"
        assert get_label(75) == "Strong Match"
        assert get_label(60) == "Potential Fit"
        assert get_label(45) == "Weak Match"
        assert get_label(20) == "Not Recommended"


# ── Matching Engine Tests ────────────────────────────────────────────────────

class TestMatchingEngine:
    def test_compute_skill_match_exact(self):
        from api.matching.engine import compute_skill_match
        jd = {"required_skills": ["python", "docker", "react"], "preferred_skills": ["aws"]}
        candidate = {"skills": ["python", "docker", "react", "aws"]}
        result = compute_skill_match(jd, candidate)
        assert result["score"] > 0
        assert "python" in result["matched_required"]
        assert len(result["missing_required"]) == 0

    def test_compute_education_match(self):
        from api.matching.engine import compute_education_match
        jd = {"raw_text": "Requires a Bachelor's degree", "core_requirements_text": ""}
        cand = {"education": "Master of Science"}
        result = compute_education_match(jd, cand)
        assert result["score"] == 100.0

    def test_compute_education_no_requirement(self):
        from api.matching.engine import compute_education_match
        jd = {"raw_text": "No specific degree needed", "core_requirements_text": ""}
        cand = {"education": None}
        result = compute_education_match(jd, cand)
        assert result["score"] == 100.0


# ── Explanation Generator Tests ──────────────────────────────────────────────

class TestExplanationGenerator:
    def test_generate_explanation(self):
        from api.explanation.generator import generate_explanation
        match_result = {
            "total_score": 82,
            "facet_scores": {
                "skill_match": 85, "experience_match": 80,
                "education_match": 100, "contextual_fit": 70,
            },
            "details": {
                "matched_skills": ["python", "docker"],
                "missing_skills": ["react"],
                "extra_skills": ["go"],
                "years_score": 1.0, "role_score": 0.8,
                "domain_score": 0.75,
                "education_level_required": "Bachelor",
                "education_level_candidate": "Master",
            },
        }
        jd = {"min_years": 3}
        candidate = {"years_of_experience": 5, "current_title": "Senior Engineer"}
        result = generate_explanation(match_result, jd, candidate)
        assert len(result["strengths"]) > 0
        assert len(result["weaknesses"]) > 0
        assert "recommendation" in result
        assert len(result["recommendation"]) > 0


# ── CSV Parser Tests ─────────────────────────────────────────────────────────

class TestCSVParser:
    def test_parse_csv(self):
        from api.preprocessing.candidate_parser import parse_csv
        csv_content = b"""name,email,skills,years_of_experience,education,current_title
Alice,alice@test.com,"Python, React, Docker",5,Master,Software Engineer
Bob,bob@test.com,"Java, Spring Boot",3,Bachelor,Backend Developer
"""
        result = parse_csv(csv_content)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["email"] == "alice@test.com"
        assert len(result[0]["skills"]) > 0

    def test_empty_csv_raises(self):
        from api.preprocessing.candidate_parser import parse_csv
        with pytest.raises(ValueError):
            parse_csv(b"")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
