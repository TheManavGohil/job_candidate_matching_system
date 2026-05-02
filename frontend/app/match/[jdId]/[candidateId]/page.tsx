"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  User,
  Zap,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
} from "lucide-react";
import { getMatchDetail, submitFeedback } from "@/lib/api";
import type { MatchResult, XAIExplanation } from "@/lib/types";
import { toast } from "@/components/Toast";

const GRADE_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  "Strong Match":    { label: "Strong Match",    color: "var(--emerald)", bg: "var(--emerald-dim)", border: "rgba(16,185,129,0.3)" },
  "Good Fit":        { label: "Good Fit",         color: "var(--cyan)",    bg: "var(--cyan-dim)",    border: "rgba(6,182,212,0.3)" },
  "Potential":       { label: "Potential",        color: "var(--amber)",   bg: "var(--amber-dim)",   border: "rgba(245,158,11,0.3)" },
  "Not Recommended": { label: "Not Recommended", color: "var(--red)",     bg: "var(--red-dim)",     border: "rgba(239,68,68,0.3)" },
};

const SECTION_LABELS: Record<string, string> = {
  required_skills: "Required Skills",
  preferred_skills: "Preferred Skills",
  responsibilities: "Responsibilities",
  qualifications: "Qualifications",
  context: "Context",
};

function ScoreBar({ score, label }: { score: number; label?: string }) {
  const pct = Math.min(100, Math.max(0, score * 100));
  const color = pct >= 70 ? "var(--emerald)" : pct >= 40 ? "var(--cyan)" : "var(--amber)";
  return (
    <div>
      {label && (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>
            {pct.toFixed(0)}%
          </span>
        </div>
      )}
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, var(--cyan))` }}
        />
      </div>
    </div>
  );
}

export default function MatchDetailPage() {
  const { jdId, candidateId } = useParams<{ jdId: string; candidateId: string }>();
  const router = useRouter();

  const [match, setMatch] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackSending, setFeedbackSending] = useState(false);

  useEffect(() => { loadDetail(); }, [jdId, candidateId]);

  const loadDetail = async () => {
    setLoading(true);
    try {
      const data = await getMatchDetail(jdId, candidateId);
      setMatch(data);
    } catch {
      toast.error("Failed to load match detail");
    } finally {
      setLoading(false);
    }
  };

  const sendFeedback = async (type: "positive" | "negative") => {
    setFeedbackSending(true);
    try {
      await submitFeedback(jdId, candidateId, type);
      setMatch((prev) => prev ? { ...prev, recruiter_feedback: type } : prev);
      toast.success(type === "positive" ? "Positive feedback recorded" : "Feedback recorded");
    } catch {
      toast.error("Failed to submit feedback");
    } finally {
      setFeedbackSending(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
        </div>
      </div>
    );
  }

  if (!match) {
    return (
      <div className="page">
        <div className="card card-p" style={{ textAlign: "center", padding: 60 }}>
          <p style={{ color: "var(--text-muted)" }}>Match detail not found.</p>
          <button className="btn btn-secondary" onClick={() => router.push(`/match/${jdId}`)} style={{ marginTop: 16 }}>
            Back to Results
          </button>
        </div>
      </div>
    );
  }

  const xai = match.xai_explanation as XAIExplanation | null;
  const grade = xai?.overall_grade || "Potential";
  const gradeConf = GRADE_CONFIG[grade] || GRADE_CONFIG["Potential"];

  return (
    <div className="page fade-in">
      {/* Back */}
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={() => router.push(`/match/${jdId}`)}>
        <ArrowLeft size={14} /> Back to Results
      </button>

      {/* Hero card */}
      <div className="card card-p" style={{ marginBottom: 20, borderColor: gradeConf.border }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* Avatar */}
            <div style={{
              width: 56, height: 56, borderRadius: 14,
              background: "linear-gradient(135deg, rgba(6,182,212,0.15), rgba(16,185,129,0.15))",
              border: "1px solid rgba(6,182,212,0.2)",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
            }}>
              <User size={24} color="var(--cyan)" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <h1 style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.02em" }}>
                  {match.candidate_name || "Unknown Candidate"}
                </h1>
                <span
                  className="badge"
                  style={{ background: gradeConf.bg, color: gradeConf.color, border: `1px solid ${gradeConf.border}` }}
                >
                  {gradeConf.label}
                </span>
              </div>
              {match.candidate_summary && (
                <p style={{ fontSize: 13.5, color: "var(--text-muted)" }}>{match.candidate_summary}</p>
              )}
            </div>
          </div>

          {/* Overall score + feedback */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 12, flexShrink: 0 }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 36, fontWeight: 900, letterSpacing: "-0.05em", color: gradeConf.color }}>
                {match.total_score.toFixed(1)}
              </div>
              <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: -2 }}>Overall Score</div>
            </div>
            {/* Feedback */}
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => sendFeedback("positive")}
                disabled={feedbackSending}
                style={{
                  padding: "7px 12px", borderRadius: 8, border: "none", cursor: "pointer",
                  background: match.recruiter_feedback === "positive" ? "var(--emerald-dim)" : "var(--surface-2)",
                  color: match.recruiter_feedback === "positive" ? "var(--emerald)" : "var(--text-faint)",
                  display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600,
                  transition: "all 0.15s",
                }}
              >
                <ThumbsUp size={14} /> Good fit
              </button>
              <button
                onClick={() => sendFeedback("negative")}
                disabled={feedbackSending}
                style={{
                  padding: "7px 12px", borderRadius: 8, border: "none", cursor: "pointer",
                  background: match.recruiter_feedback === "negative" ? "var(--red-dim)" : "var(--surface-2)",
                  color: match.recruiter_feedback === "negative" ? "var(--red)" : "var(--text-faint)",
                  display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600,
                  transition: "all 0.15s",
                }}
              >
                <ThumbsDown size={14} /> Not a fit
              </button>
            </div>
          </div>
        </div>

        {/* Overall score bar */}
        <div style={{ marginTop: 20 }}>
          <ScoreBar score={match.total_score / 100} />
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20 }}>
        {/* Section scores */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card card-p">
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}>
              <BarChart3 size={13} /> Section Scores
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {Object.entries(match.section_scores).map(([key, val]) => (
                <ScoreBar
                  key={key}
                  score={val}
                  label={SECTION_LABELS[key] || key}
                />
              ))}
            </div>
          </div>

          {/* Feedback confirmation */}
          {match.recruiter_feedback && (
            <div
              className="card card-p"
              style={{
                borderColor: match.recruiter_feedback === "positive" ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13.5, fontWeight: 600 }}>
                {match.recruiter_feedback === "positive" ? (
                  <><CheckCircle2 size={16} color="var(--emerald)" /> Marked as Good Fit</>
                ) : (
                  <><AlertTriangle size={16} color="var(--red)" /> Marked as Not a Fit</>
                )}
              </div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                Your feedback helps improve future rankings.
              </div>
            </div>
          )}
        </div>

        {/* XAI explanation */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {xai ? (
            <>
              {/* Recommendation */}
              <div className="card card-p" style={{ borderColor: gradeConf.border, background: gradeConf.bg }}>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: gradeConf.color, marginBottom: 10 }}>
                  AI Recommendation
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--text)" }}>
                  {xai.recommendation}
                </p>
              </div>

              {/* Strengths */}
              {xai.strengths.length > 0 && (
                <div className="card card-p">
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>
                    <Zap size={13} color="var(--emerald)" /> Strengths ({xai.strengths.length})
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {xai.strengths.map((s, i) => (
                      <div key={i} style={{ display: "flex", gap: 12, padding: "12px 14px", background: "var(--emerald-dim)", borderRadius: 8, border: "1px solid rgba(16,185,129,0.15)" }}>
                        <Zap size={14} color="var(--emerald)" style={{ marginTop: 2, flexShrink: 0 }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 3 }}>{s.point}</div>
                          <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>{s.evidence}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Weaknesses */}
              {xai.weaknesses.length > 0 && (
                <div className="card card-p">
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>
                    <AlertTriangle size={13} color="var(--amber)" /> Gaps & Concerns ({xai.weaknesses.length})
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {xai.weaknesses.map((w, i) => (
                      <div key={i} style={{ display: "flex", gap: 12, padding: "12px 14px", background: "var(--amber-dim)", borderRadius: 8, border: "1px solid rgba(245,158,11,0.15)" }}>
                        <AlertTriangle size={14} color="var(--amber)" style={{ marginTop: 2, flexShrink: 0 }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 3 }}>{w.point}</div>
                          <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>{w.evidence}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card card-p" style={{ textAlign: "center", padding: 48 }}>
              <Loader2 size={28} color="var(--cyan)" style={{ animation: "spin 1s linear infinite", margin: "0 auto 16px" }} />
              <div style={{ fontWeight: 600, marginBottom: 6 }}>XAI explanation is generating…</div>
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>
                This typically takes 15–30 seconds after matching completes. Refresh the page to check.
              </div>
              <button className="btn btn-secondary" style={{ marginTop: 16 }} onClick={loadDetail}>
                ↻ Refresh
              </button>
            </div>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
