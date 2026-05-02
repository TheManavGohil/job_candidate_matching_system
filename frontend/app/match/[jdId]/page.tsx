"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  Play,
  Loader2,
  Users,
  ChevronRight,
  Zap,
  AlertTriangle,
  Trophy,
} from "lucide-react";
import { getMatchResults, triggerMatch } from "@/lib/api";
import type { MatchResult, XAIExplanation } from "@/lib/types";
import { toast } from "@/components/Toast";

const GRADE_STYLES: Record<string, { label: string; cls: string }> = {
  "Strong Match": { label: "Strong Match", cls: "badge-emerald" },
  "Good Fit": { label: "Good Fit", cls: "badge-cyan" },
  "Potential": { label: "Potential", cls: "badge-amber" },
  "Not Recommended": { label: "Not Recommended", cls: "badge-red" },
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? "var(--emerald)" : pct >= 40 ? "var(--cyan)" : "var(--amber)";
  return (
    <div className="score-bar-track">
      <div
        className="score-bar-fill"
        style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}, var(--cyan))` }}
      />
    </div>
  );
}

export default function MatchResultsPage() {
  const { jdId } = useParams<{ jdId: string }>();
  const router = useRouter();

  const [results, setResults] = useState<MatchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [topK, setTopK] = useState(50);

  useEffect(() => { loadResults(); }, [jdId]);

  const loadResults = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getMatchResults(jdId, topK, 0);
      setResults(data.results as MatchResult[]);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load results");
    } finally {
      setLoading(false);
    }
  }, [jdId, topK]);

  const rerunMatch = async () => {
    setTriggering(true);
    try {
      await triggerMatch(jdId);
      toast.info("Matching triggered", "Results will update in ~30 seconds. Click Refresh to see them.");
      setTimeout(() => { loadResults(); setTriggering(false); }, 5000);
    } catch {
      toast.error("Failed to trigger matching");
      setTriggering(false);
    }
  };

  return (
    <div className="page fade-in">
      {/* Header */}
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={() => router.push(`/jobs/${jdId}`)}>
        <ArrowLeft size={14} /> Back to Job
      </button>

      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Trophy size={22} color="var(--cyan)" />
            Match Results
          </h1>
          <p className="page-subtitle">
            {loading ? "Loading…" : `${total} candidate${total !== 1 ? "s" : ""} ranked by AI semantic matching`}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <select
            className="input"
            style={{ width: "auto", fontSize: 13, padding: "8px 12px" }}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
          >
            {[10, 25, 50, 100, 200].map((v) => (
              <option key={v} value={v}>Top {v}</option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={loadResults} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={rerunMatch} disabled={triggering}>
            {triggering ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={14} />}
            {triggering ? "Running…" : "Re-run Match"}
          </button>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
      ) : results.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon"><Users size={28} /></div>
            <div className="empty-state-title">No results yet</div>
            <div className="empty-state-sub">
              Click "Re-run Match" to start the AI matching pipeline. Make sure you've uploaded candidates first.
            </div>
            <button className="btn btn-primary" onClick={rerunMatch} disabled={triggering}>
              {triggering ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={16} />}
              {triggering ? "Matching…" : "Run Matching Now"}
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {results.map((match, i) => {
            const xai = match.xai_explanation as XAIExplanation | null;
            const grade = xai?.overall_grade || "Potential";
            const gradeStyle = GRADE_STYLES[grade] || GRADE_STYLES["Potential"];
            const topStrengths = xai?.strengths?.slice(0, 2) || [];

            return (
              <div
                key={match.candidate_id}
                className="list-item fade-in"
                style={{ flexDirection: "column", alignItems: "stretch", gap: 12, animationDelay: `${i * 40}ms`, cursor: "pointer" }}
                onClick={() => router.push(`/match/${jdId}/${match.candidate_id}`)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  {/* Rank */}
                  <div style={{
                    width: 36, height: 36, borderRadius: 10,
                    background: i === 0 ? "var(--amber-dim)" : i === 1 ? "var(--surface-2)" : "var(--surface-2)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 12, fontWeight: 800,
                    color: i === 0 ? "var(--amber)" : "var(--text-faint)",
                    border: `1px solid ${i === 0 ? "rgba(245,158,11,0.2)" : "var(--border)"}`,
                    flexShrink: 0,
                  }}>
                    #{i + 1}
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 700, fontSize: 14 }}>{match.candidate_name || "Unknown Candidate"}</span>
                      <span className={`badge ${gradeStyle.cls}`}>{gradeStyle.label}</span>
                    </div>
                    {match.candidate_summary && (
                      <div style={{ fontSize: 12.5, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {match.candidate_summary}
                      </div>
                    )}
                  </div>

                  {/* Score */}
                  <div style={{ textAlign: "right", flexShrink: 0, marginRight: 4 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.04em", color: "var(--cyan)" }}>
                      {match.total_score.toFixed(1)}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-faint)" }}>score</div>
                  </div>

                  <ChevronRight size={16} color="var(--text-faint)" />
                </div>

                {/* Score bar */}
                <ScoreBar score={match.total_score} />

                {/* Top strengths */}
                {topStrengths.length > 0 && (
                  <div style={{ display: "flex", gap: 16 }}>
                    {topStrengths.map((s, si) => (
                      <div key={si} style={{ display: "flex", alignItems: "flex-start", gap: 5, fontSize: 12, color: "var(--text-muted)" }}>
                        <Zap size={11} color="var(--emerald)" style={{ marginTop: 2, flexShrink: 0 }} />
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 200 }}>{s.point}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } } .spin { animation: spin 1s linear infinite; }`}</style>
    </div>
  );
}
