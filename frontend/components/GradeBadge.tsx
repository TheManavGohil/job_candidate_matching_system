"use client";

interface GradeBadgeProps {
  grade: string;
}

const gradeConfig: Record<string, string> = {
  "Strong Match": "badge-strong",
  "Good Fit": "badge-good",
  "Potential": "badge-potential",
  "Not Recommended": "badge-not-recommended",
};

export default function GradeBadge({ grade }: GradeBadgeProps) {
  const className = gradeConfig[grade] || "badge-potential";
  return <span className={`badge ${className}`}>{grade}</span>;
}
