"use client";

import { CheckCircle, XCircle, Quote } from "lucide-react";
import type { XAIExplanation } from "@/lib/types";

interface ExplanationCardProps {
  explanation: XAIExplanation;
}

export default function ExplanationCard({ explanation }: ExplanationCardProps) {
  return (
    <div className="space-y-6">
      {/* Recommendation */}
      {explanation.recommendation && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-[var(--muted-foreground)] uppercase tracking-wider mb-2">
            Recommendation
          </h3>
          <p className="text-base leading-relaxed">{explanation.recommendation}</p>
        </div>
      )}

      {/* Strengths */}
      {explanation.strengths.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <CheckCircle size={16} />
            Strengths
          </h3>
          {explanation.strengths.map((s, i) => (
            <div key={i} className="glass-card p-4 space-y-2">
              <p className="text-sm font-medium">{s.point}</p>
              {s.evidence && (
                <div className="flex items-start gap-2 text-xs text-[var(--muted-foreground)] bg-[var(--input-bg)] rounded-lg p-3">
                  <Quote size={12} className="text-cyan-400 mt-0.5 shrink-0" />
                  <span className="italic">{s.evidence}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Weaknesses */}
      {explanation.weaknesses.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-2">
            <XCircle size={16} />
            Areas of Concern
          </h3>
          {explanation.weaknesses.map((w, i) => (
            <div key={i} className="glass-card p-4 space-y-2">
              <p className="text-sm font-medium">{w.point}</p>
              {w.evidence && (
                <div className="flex items-start gap-2 text-xs text-[var(--muted-foreground)] bg-[var(--input-bg)] rounded-lg p-3">
                  <Quote size={12} className="text-amber-400 mt-0.5 shrink-0" />
                  <span className="italic">{w.evidence}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
