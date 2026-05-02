"use client";

import Link from "next/link";
import { ChevronRight, Zap, AlertTriangle } from "lucide-react";
import ScoreBar from "./ScoreBar";
import GradeBadge from "./GradeBadge";
import type { MatchResult } from "@/lib/types";

interface CandidateCardProps {
  match: MatchResult;
  jdId: string;
  index: number;
}

export default function CandidateCard({ match, jdId, index }: CandidateCardProps) {
  const xai = match.xai_explanation;
  const grade = xai?.overall_grade || "Potential";
  const topStrengths = xai?.strengths?.slice(0, 3) || [];

  return (
    <Link href={`/match/${jdId}/${match.candidate_id}`}>
      <div
        className="glass-card p-5 cursor-pointer fade-in group"
        style={{ animationDelay: `${index * 60}ms` }}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-1">
              <h3 className="text-base font-semibold truncate">
                {match.candidate_name || "Unknown Candidate"}
              </h3>
              <GradeBadge grade={grade} />
            </div>
            {match.candidate_summary && (
              <p className="text-sm text-[var(--muted-foreground)] line-clamp-1">
                {match.candidate_summary}
              </p>
            )}
          </div>
          <ChevronRight
            size={18}
            className="text-[var(--muted)] group-hover:text-cyan-400 transition-colors ml-3 mt-1 shrink-0"
          />
        </div>

        <div className="mb-3">
          <ScoreBar score={match.total_score} />
        </div>

        {topStrengths.length > 0 && (
          <div className="space-y-1.5">
            {topStrengths.map((s, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-xs text-[var(--muted-foreground)]"
              >
                <Zap size={12} className="text-emerald-400 mt-0.5 shrink-0" />
                <span className="line-clamp-1">{s.point}</span>
              </div>
            ))}
          </div>
        )}

        {match.recruiter_feedback && (
          <div className="mt-3 flex items-center gap-1.5 text-xs">
            {match.recruiter_feedback === "positive" ? (
              <span className="text-emerald-400">👍 Positive feedback</span>
            ) : (
              <span className="text-red-400">👎 Negative feedback</span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}
