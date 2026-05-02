"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Play,
  Save,
  Loader2,
  CheckCircle2,
  Briefcase,
  ChevronRight,
} from "lucide-react";
import { getJob, updateWeights, triggerMatch } from "@/lib/api";
import type { JobDescription } from "@/lib/types";
import { toast } from "@/components/Toast";

const SECTION_LABELS: Record<string, string> = {
  required_skills: "Required Skills",
  preferred_skills: "Preferred Skills",
  responsibilities: "Responsibilities",
  qualifications: "Qualifications",
  context: "Context / Culture",
};

export default function JobDetailPage() {
  const { jdId } = useParams<{ jdId: string }>();
  const router = useRouter();

  const [jd, setJd] = useState<JobDescription | null>(null);
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [matching, setMatching] = useState(false);
  const [matchTriggered, setMatchTriggered] = useState(false);

  useEffect(() => { loadJob(); }, [jdId]);

  const loadJob = async () => {
    setLoading(true);
    try {
      const data = await getJob(jdId);
      setJd(data);
      setWeights(data.weights as Record<string, number>);
    } catch {
      toast.error("Failed to load job");
    } finally {
      setLoading(false);
    }
  };

  const saveWeights = async () => {
    setSaving(true);
    try {
      const updated = await updateWeights(jdId, weights);
      setJd(updated);
      setWeights(updated.weights as Record<string, number>);
      toast.success("Weights saved!", "Matching will use the updated section weights.");
    } catch {
      toast.error("Failed to save weights");
    } finally {
      setSaving(false);
    }
  };

  const runMatching = async () => {
    setMatching(true);
    try {
      await triggerMatch(jdId);
      setMatchTriggered(true);
      toast.success("Matching started!", "Results will be ready in ~30 seconds. Redirecting…");
      setTimeout(() => router.push(`/match/${jdId}`), 3000);
    } catch (e: unknown) {
      toast.error("Matching failed", e instanceof Error ? e.message : "Unknown error");
      setMatching(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[...Array(5)].map((_, i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
        </div>
      </div>
    );
  }

  if (!jd) {
    return (
      <div className="page">
        <div className="card card-p" style={{ textAlign: "center", padding: 60 }}>
          <p style={{ color: "var(--text-muted)" }}>Job not found.</p>
          <button className="btn btn-secondary" onClick={() => router.push("/dashboard")} style={{ marginTop: 16 }}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const std = (jd.standardised_json as unknown as Record<string, unknown>) ?? {};
  const isReady = std && Object.keys(std).length > 0 && std.title;
  const requiredSkills = Array.isArray(std.required_skills) ? (std.required_skills as string[]) : [];
  const preferredSkills = Array.isArray(std.preferred_skills) ? (std.preferred_skills as string[]) : [];
  const responsibilities = Array.isArray(std.responsibilities) ? (std.responsibilities as string[]) : [];
  const qualifications = (std.qualifications && typeof std.qualifications === "object")
    ? (std.qualifications as Record<string, unknown>)
    : null;

  return (
    <div className="page fade-in">
      {/* Back */}
      <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={() => router.push("/dashboard")}>
        <ArrowLeft size={14} /> Back to Dashboard
      </button>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 24, alignItems: "start" }}>
        {/* Left: Job Details */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Title card */}
          <div className="card card-p">
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12 }}>
              <div className="list-icon" style={{ width: 48, height: 48, borderRadius: 12, background: "var(--cyan-dim)" }}>
                <Briefcase size={22} color="var(--cyan)" />
              </div>
              <div>
                <h1 style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.02em" }}>
                  {isReady ? (std.title as string) : "Processing\u2026"}
                </h1>
                {std.company_context != null && (
                  <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 3 }}>{String(std.company_context)}</p>
                )}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <span className={`badge ${isReady ? "badge-emerald" : "badge-amber"}`}>
                {isReady ? "✓ Ready for matching" : "⟳ Processing…"}
              </span>
            </div>
          </div>

          {/* Not ready yet */}
          {!isReady && (
            <div className="card card-p" style={{ borderColor: "rgba(245,158,11,0.3)", background: "var(--amber-dim)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Loader2 size={18} color="var(--amber)" style={{ animation: "spin 1s linear infinite", flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13.5, color: "var(--amber)" }}>AI is processing this job description</div>
                  <div style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 3 }}>
                    Typically takes 15–45 seconds. Refresh this page to see results.
                  </div>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={loadJob} style={{ marginLeft: "auto" }}>
                  ↻ Refresh
                </button>
              </div>
            </div>
          )}

          {/* Required Skills */}
          {requiredSkills.length > 0 && (
            <div className="card card-p">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 12 }}>
                Required Skills
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                {requiredSkills.map((s, i) => (
                  <span key={i} className="badge badge-cyan">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Preferred Skills */}
          {preferredSkills.length > 0 && (
            <div className="card card-p">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 12 }}>
                Preferred Skills
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                {preferredSkills.map((s, i) => (
                  <span key={i} className="badge badge-gray">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Responsibilities */}
          {responsibilities.length > 0 && (
            <div className="card card-p">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 12 }}>
                Responsibilities
              </div>
              <ul style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {responsibilities.map((r, i) => (
                  <li key={i} style={{ display: "flex", gap: 10, fontSize: 13.5, lineHeight: 1.5 }}>
                    <span style={{ color: "var(--cyan)", marginTop: 4, fontSize: 10 }}>●</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Qualifications */}
          {qualifications && (
            <div className="card card-p">
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-faint)", marginBottom: 12 }}>
                Qualifications
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
                {Object.entries(qualifications).map(([k, v]) => (
                  <div key={k}>
                    <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 4 }}>{k}</div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{String(v) || "—"}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Actions + Weights */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "sticky", top: 24 }}>
          {/* Actions */}
          <div className="card card-p">
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14 }}>Actions</div>

            {matchTriggered ? (
              <div style={{ padding: "14px 16px", background: "var(--emerald-dim)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--emerald)", fontWeight: 600, fontSize: 13.5 }}>
                  <CheckCircle2 size={16} />
                  Matching in progress…
                </div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>Redirecting to results shortly</div>
              </div>
            ) : (
              <button
                className="btn btn-primary"
                style={{ width: "100%", marginBottom: 10 }}
                onClick={runMatching}
                disabled={matching || !isReady}
                title={!isReady ? "Wait for JD processing to complete" : ""}
              >
                {matching ? <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> : <Play size={15} />}
                {matching ? "Running…" : "Run Matching"}
              </button>
            )}

            <button
              className="btn btn-ghost"
              style={{ width: "100%", fontSize: 13 }}
              onClick={() => router.push(`/match/${jdId}`)}
            >
              <ChevronRight size={14} />
              View Results
            </button>
          </div>

          {/* Weights */}
          {Object.keys(weights).length > 0 && (
            <div className="card card-p">
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14 }}>Section Weights</div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 14, lineHeight: 1.6 }}>
                Adjust how much each section influences the final score.
              </p>
              {Object.entries(weights).map(([key, value]) => (
                <div key={key} className="slider-row">
                  <span className="slider-label">{SECTION_LABELS[key] || key}</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    step={1}
                    value={value}
                    onChange={(e) => setWeights((w) => ({ ...w, [key]: parseFloat(e.target.value) }))}
                  />
                  <span className="slider-value">{value.toFixed(0)}%</span>
                </div>
              ))}
              <button
                className="btn btn-secondary"
                style={{ width: "100%", marginTop: 10 }}
                onClick={saveWeights}
                disabled={saving}
              >
                {saving ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Save size={14} />}
                {saving ? "Saving…" : "Save Weights"}
              </button>
            </div>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
