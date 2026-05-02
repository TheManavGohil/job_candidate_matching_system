"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Briefcase,
  Plus,
  Upload,
  FileText,
  ChevronRight,
  X,
  Loader2,
  Clock,
  CheckCircle2,
  AlertCircle,
  CloudUpload,
} from "lucide-react";
import { listJobs, uploadJob } from "@/lib/api";
import type { JobDescription } from "@/lib/types";
import { toast } from "@/components/Toast";

export default function DashboardPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [tab, setTab] = useState<"file" | "text">("file");
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadJobs(); }, []);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const data = await listJobs();
      setJobs(data);
    } catch {
      toast.error("Failed to load jobs", "Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (tab === "text" && !jdText.trim()) {
      toast.error("Empty description", "Paste your job description text first.");
      return;
    }
    if (tab === "file" && !file) {
      toast.error("No file selected", "Please select a PDF, DOCX, or TXT file.");
      return;
    }
    setUploading(true);
    try {
      const result = await uploadJob(tab === "file" ? file! : undefined, tab === "text" ? jdText : undefined);
      toast.success("Job uploaded!", "AI is processing the job description in the background.");
      setShowModal(false);
      setJdText("");
      setFile(null);
      router.push(`/jobs/${result.jd_id}`);
    } catch (e: unknown) {
      toast.error("Upload failed", e instanceof Error ? e.message : "Unknown error");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); setTab("file"); }
  };

  const getStatusInfo = (jd: JobDescription) => {
    const std = jd.standardised_json as unknown as Record<string, unknown>;
    const ready = std && Object.keys(std).length > 0 && std.title;
    return {
      ready,
      title: ready ? (std.title as string) : "Processing…",
    };
  };

  const readyCount = jobs.filter((j) => getStatusInfo(j).ready).length;

  return (
    <div className="page fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Briefcase size={22} color="var(--cyan)" />
            Job Descriptions
          </h1>
          <p className="page-subtitle">Upload and manage job descriptions to run candidate matching</p>
        </div>
        <button className="btn btn-primary btn-lg" onClick={() => setShowModal(true)}>
          <Plus size={16} />
          Upload New Job
        </button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Jobs</div>
          <div className="stat-value cyan">{loading ? "—" : jobs.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Ready to Match</div>
          <div className="stat-value emerald">{loading ? "—" : readyCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Processing</div>
          <div className="stat-value">{loading ? "—" : jobs.length - readyCount}</div>
        </div>
      </div>

      {/* Job List */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 72 }} />
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">
              <Briefcase size={28} />
            </div>
            <div className="empty-state-title">No job descriptions yet</div>
            <div className="empty-state-sub">
              Upload your first job description to start matching candidates with AI-powered semantic search.
            </div>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              <Plus size={16} />
              Upload Your First Job
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {jobs.map((jd, i) => {
            const { ready, title } = getStatusInfo(jd);
            return (
              <div
                key={String(jd.jd_id)}
                className="list-item fade-in"
                style={{ animationDelay: `${i * 40}ms` }}
                onClick={() => router.push(`/jobs/${jd.jd_id}`)}
              >
                <div className="list-icon" style={{ background: ready ? "var(--cyan-dim)" : "var(--amber-dim)" }}>
                  {ready ? (
                    <CheckCircle2 size={18} color="var(--cyan)" />
                  ) : (
                    <Loader2 size={18} color="var(--amber)" style={{ animation: "spin 1s linear infinite" }} />
                  )}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>{title}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span className={`badge ${ready ? "badge-emerald" : "badge-amber"}`}>
                      {ready ? "Ready" : "Processing…"}
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "var(--text-faint)" }}>
                      <Clock size={11} />
                      {jd.created_at ? new Date(jd.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : ""}
                    </span>
                  </div>
                </div>
                <ChevronRight size={16} color="var(--text-faint)" />
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => !uploading && setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <CloudUpload size={18} color="var(--cyan)" />
                Upload Job Description
              </div>
              {!uploading && (
                <button className="btn btn-ghost btn-sm" onClick={() => setShowModal(false)}>
                  <X size={16} />
                </button>
              )}
            </div>

            <div className="modal-body">
              {/* Tabs */}
              <div className="tabs">
                <button className={`tab ${tab === "file" ? "active" : ""}`} onClick={() => setTab("file")}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Upload size={13} />File Upload
                  </span>
                </button>
                <button className={`tab ${tab === "text" ? "active" : ""}`} onClick={() => setTab("text")}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <FileText size={13} />Paste Text
                  </span>
                </button>
              </div>

              {tab === "file" ? (
                <div>
                  <div
                    className={`upload-zone ${dragOver ? "drag-over" : ""} ${file ? "drag-over" : ""}`}
                    onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileRef.current?.click()}
                  >
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".pdf,.docx,.txt"
                      style={{ display: "none" }}
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                    <div className="upload-zone-icon">
                      <Upload size={24} />
                    </div>
                    {file ? (
                      <>
                        <div className="upload-zone-title" style={{ color: "var(--cyan)" }}>{file.name}</div>
                        <div className="upload-zone-sub">{(file.size / 1024).toFixed(0)} KB • Click to change</div>
                      </>
                    ) : (
                      <>
                        <div className="upload-zone-title">Drag & drop or click to browse</div>
                        <div className="upload-zone-sub">Supports PDF, DOCX, and TXT files</div>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="input-group">
                  <label className="input-label">Job Description Text</label>
                  <textarea
                    className="input"
                    style={{ minHeight: 200, fontSize: 13, lineHeight: 1.7 }}
                    placeholder={`Paste the full job description here...

Example:
Software Engineer – Python Backend
Required Skills: Python, FastAPI, PostgreSQL...`}
                    value={jdText}
                    onChange={(e) => setJdText(e.target.value)}
                  />
                  <div style={{ fontSize: 12, color: "var(--text-faint)", marginTop: 6 }}>
                    {jdText.length} characters · {jdText.split(/\s+/).filter(Boolean).length} words
                  </div>
                </div>
              )}

              {uploading && (
                <div style={{ marginTop: 16, padding: "12px 16px", background: "var(--cyan-dim)", border: "1px solid rgba(6,182,212,0.2)", borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
                  <Loader2 size={15} color="var(--cyan)" style={{ animation: "spin 1s linear infinite" }} />
                  <span style={{ fontSize: 13, color: "var(--cyan)" }}>Uploading and queueing AI processing…</span>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)} disabled={uploading}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={uploading}>
                {uploading ? (
                  <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />Processing…</>
                ) : (
                  <><CloudUpload size={14} />Upload & Process</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
