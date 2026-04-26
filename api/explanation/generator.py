"""
Explanation generator — builds human-readable strengths, weaknesses,
and recommendation from match scores. Template-based, no LLM.
"""

from typing import Dict, Any, List


class ExplanationGenerator:
    """Generate structured explanations from match score dicts."""

    def __init__(self, match_result: Dict[str, Any], jd: Dict, candidate: Dict):
        self.result = match_result
        self.jd = jd
        self.candidate = candidate
        self.facets = match_result.get("facet_scores", {})
        self.details = match_result.get("details", {})
        self.total = match_result.get("total_score", 0)

    def generate(self) -> Dict[str, Any]:
        return {
            "strengths": self._build_strengths(),
            "weaknesses": self._build_weaknesses(),
            "recommendation": self._build_recommendation(),
        }

    def _build_strengths(self) -> List[str]:
        strengths = []
        matched = self.details.get("matched_skills", [])
        if matched:
            top = matched[:5]
            strengths.append(f"Matches key required skills: {', '.join(top)}")
            if len(matched) > 5:
                strengths.append(f"Plus {len(matched) - 5} additional matching skills")

        years_score = self.details.get("years_score", 0)
        cand_years = self.candidate.get("years_of_experience")
        req_years = self.jd.get("min_years")
        if years_score >= 1.0 and cand_years:
            if req_years:
                strengths.append(
                    f"Meets/exceeds required experience ({cand_years} years vs {req_years} required)"
                )
            else:
                strengths.append(f"Brings {cand_years} years of experience")

        domain_score = self.details.get("domain_score", 0)
        if domain_score > 0.7:
            strengths.append("Strong relevance of recent work to the role")

        role_score = self.details.get("role_score", 0)
        if role_score > 0.7 and self.candidate.get("current_title"):
            strengths.append(
                f"Current role ({self.candidate['current_title']}) aligns well with position"
            )

        edu_req = self.details.get("education_level_required", "None")
        edu_cand = self.details.get("education_level_candidate", "Unknown")
        if edu_req != "None" and edu_cand != "Unknown":
            if self.facets.get("education_match", 0) >= 100:
                strengths.append(f"Meets education requirement ({edu_cand})")

        if self.facets.get("contextual_fit", 0) > 70:
            strengths.append("Overall profile strongly aligns with the job description")

        if self.facets.get("skill_match", 0) > 80:
            strengths.append("Excellent technical skill coverage")

        extra = self.details.get("extra_skills", [])
        if extra:
            top_extra = extra[:3]
            strengths.append(f"Additional relevant skills: {', '.join(top_extra)}")

        return strengths if strengths else ["Profile has some relevant background"]

    def _build_weaknesses(self) -> List[str]:
        weaknesses = []
        missing = self.details.get("missing_skills", [])
        if missing:
            weaknesses.append(f"Missing required skills: {', '.join(missing)}")

        years_score = self.details.get("years_score", 0)
        cand_years = self.candidate.get("years_of_experience") or 0
        req_years = self.jd.get("min_years") or 0
        if years_score < 1.0 and req_years > 0:
            gap = req_years - cand_years
            weaknesses.append(
                f"Has {cand_years} years vs required {req_years} — gap of {gap:.1f} years"
            )

        edu_req = self.details.get("education_level_required", "None")
        edu_cand = self.details.get("education_level_candidate", "Unknown")
        if edu_req != "None" and self.facets.get("education_match", 100) < 100:
            weaknesses.append(f"Education: required {edu_req}, candidate has {edu_cand}")

        if self.facets.get("contextual_fit", 100) < 40:
            weaknesses.append(
                "Overall experience may not align closely with the job description"
            )

        role_score = self.details.get("role_score", 1)
        if role_score < 0.4:
            weaknesses.append("Current role title differs significantly from the position")

        if self.facets.get("skill_match", 100) < 30:
            weaknesses.append("Limited overlap in technical skills")

        return weaknesses if weaknesses else ["No significant weaknesses identified"]

    def _build_recommendation(self) -> str:
        if self.total >= 85:
            return (
                "Top match — this candidate's skills, experience, and background "
                "are an excellent fit for this role. Highly recommended for interview."
            )
        elif self.total >= 70:
            return (
                "Strong match — candidate meets most requirements with some gaps. "
                "Recommended for further evaluation."
            )
        elif self.total >= 55:
            return (
                "Potential fit — candidate has relevant skills but notable gaps exist. "
                "Consider if gaps can be addressed through training."
            )
        elif self.total >= 40:
            return (
                "Weak match — significant gaps in required skills or experience. "
                "May be suitable for a more junior role or different position."
            )
        else:
            return (
                "Not recommended — candidate's profile does not align well with "
                "this role's requirements."
            )


def generate_explanation(
    match_result: Dict[str, Any], jd: Dict, candidate: Dict
) -> Dict[str, Any]:
    """Convenience function to generate explanation."""
    gen = ExplanationGenerator(match_result, jd, candidate)
    return gen.generate()
