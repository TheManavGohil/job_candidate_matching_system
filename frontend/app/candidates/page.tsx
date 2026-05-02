"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  Upload,
  FileText,
  Plus,
  X,
  Loader2,
  CheckCircle2,
  CloudUpload,
  Table,
} from "lucide-react";
import { uploadCandidates } from "@/lib/api";
import { toast } from "@/components/Toast";

export default function CandidatesPage() {
  const router = useRouter();
  const [showModal, setShowModal] = useState(false);
  const [tab, setTab] = useState<"file" | "text" | "bulk">("file");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [lastResult, setLastResult] = useState<{ count: number; ids: string[] } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (tab === "text" && !text.trim()) {
      toast.error("Empty resume", "Paste the candidate's resume text first.");
      return;
    }
    if ((tab === "file" || tab === "bulk") && !file) {
      toast.error("No file selected", `Please select a ${tab === "bulk" ? "Excel or CSV" : "PDF or DOCX"} file.`);
      return;
    }
    setUploading(true);
    try {
      const result = await uploadCandidates(
        (tab === "file" || tab === "bulk") ? file! : undefined,
        tab === "text" ? text : undefined
      );
      setLastResult({ count: result.candidate_ids.length, ids: result.candidate_ids });
      toast.success(
        `${result.candidate_ids.length} candidate(s) uploaded`,
        "AI is extracting and embedding their profiles in the background."
      );
      setShowModal(false);
      setText("");
      setFile(null);
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
    if (f) {
      setFile(f);
      const ext = f.name.toLowerCase().split('.').pop();
      if (ext === 'csv' || ext === 'xlsx') {
        setTab("bulk");
      } else {
        setTab("file");
      }
    }
  };

  return (
    <div className="page fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Users size={22} color="var(--emerald)" />
            Candidates
          </h1>
          <p className="page-subtitle">Upload resumes individually or in bulk — AI extracts structured profiles automatically</p>
        </div>
        <button className="btn btn-primary btn-lg" onClick={() => setShowModal(true)}>
          <Plus size={16} />
          Upload Candidates
        </button>
      </div>

      {/* How it works */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 28 }}>
        {[
          {
            step: "1",
            color: "var(--cyan)",
            bg: "var(--cyan-dim)",
            title: "Upload Resumes",
            desc: "PDF, DOCX, or CSV with multiple candidates. Bulk upload supported.",
          },
          {
            step: "2",
            color: "var(--purple)",
            bg: "var(--purple-dim)",
            title: "AI Processing",
            desc: "LLM extracts skills, experience, education and builds structured JSON profiles.",
          },
          {
            step: "3",
            color: "var(--emerald)",
            bg: "var(--emerald-dim)",
            title: "Run Matching",
            desc: "Go to any Job Description and click 'Run Matching' to rank all candidates.",
          },
        ].map(({ step, color, bg, title, desc }) => (
          <div key={step} className="card card-p" style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: bg, display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, fontWeight: 800, color, flexShrink: 0
            }}>
              {step}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5 }}>{title}</div>
              <div style={{ fontSize: 12.5, color: "var(--text-muted)", lineHeight: 1.6 }}>{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Last upload success */}
      {lastResult && (
        <div className="card card-p fade-in" style={{ borderColor: "rgba(16,185,129,0.3)", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <CheckCircle2 size={22} color="var(--emerald)" />
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {lastResult.count} candidate(s) queued for processing
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 3 }}>
                Processing happens in the background (30–90s). Then head to a job description and run matching.
              </div>
            </div>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => router.push("/dashboard")}
              style={{ marginLeft: "auto" }}
            >
              Go to Jobs →
            </button>
          </div>
        </div>
      )}

      {/* Big upload CTA when no recent upload */}
      {!lastResult && (
        <div className="card" style={{ border: "2px dashed var(--border)" }}>
          <div className="empty-state">
            <div className="empty-state-icon" style={{ background: "var(--emerald-dim)", color: "var(--emerald)" }}>
              <Users size={28} />
            </div>
            <div className="empty-state-title">Upload candidate resumes</div>
            <div className="empty-state-sub">
              Upload individual resumes (PDF/DOCX) or a CSV file containing multiple candidates.
              The AI will parse and index each one automatically.
            </div>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              <CloudUpload size={16} />
              Upload Now
            </button>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => !uploading && setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <CloudUpload size={18} color="var(--emerald)" />
                Upload Candidates
              </div>
              {!uploading && (
                <button className="btn btn-ghost btn-sm" onClick={() => setShowModal(false)}>
                  <X size={16} />
                </button>
              )}
            </div>

            <div className="modal-body">
              <div className="tabs">
                <button className={`tab ${tab === "file" ? "active" : ""}`} onClick={() => { setTab("file"); setFile(null); }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Upload size={13} />Single Resume
                  </span>
                </button>
                <button className={`tab ${tab === "bulk" ? "active" : ""}`} onClick={() => { setTab("bulk"); setFile(null); }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Table size={13} />Bulk Upload
                  </span>
                </button>
                <button className={`tab ${tab === "text" ? "active" : ""}`} onClick={() => { setTab("text"); setFile(null); }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <FileText size={13} />Paste Text
                  </span>
                </button>
              </div>

               {tab === "file" && (
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
                  <div className="upload-zone-icon" style={{ background: "var(--emerald-dim)", color: "var(--emerald)", border: "1px solid rgba(16,185,129,0.2)" }}>
                    <Upload size={24} />
                  </div>
                  {file ? (
                    <>
                      <div className="upload-zone-title" style={{ color: "var(--emerald)" }}>{file.name}</div>
                      <div className="upload-zone-sub">{(file.size / 1024).toFixed(0)} KB · Click to change</div>
                    </>
                  ) : (
                    <>
                      <div className="upload-zone-title">Upload a single resume</div>
                      <div className="upload-zone-sub">PDF, DOCX, or TXT formats supported</div>
                    </>
                  )}
                </div>
              )}

              {tab === "bulk" && (
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
                    accept=".csv,.xlsx"
                    style={{ display: "none" }}
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                  <div className="upload-zone-icon" style={{ background: "var(--emerald-dim)", color: "var(--emerald)", border: "1px solid rgba(16,185,129,0.2)" }}>
                    <Table size={24} />
                  </div>
                  {file ? (
                    <>
                      <div className="upload-zone-title" style={{ color: "var(--emerald)" }}>{file.name}</div>
                      <div className="upload-zone-sub">{(file.size / 1024).toFixed(0)} KB · Click to change</div>
                    </>
                  ) : (
                    <>
                      <div className="upload-zone-title">Upload candidate data file</div>
                      <div className="upload-zone-sub">Excel (.xlsx) or CSV supported</div>
                    </>
                  )}
                </div>
              )}
              {tab === "text" && (
                <div className="input-group">
                  <label className="input-label">Candidate Resume Text</label>
                  <textarea
                    className="input"
                    style={{ minHeight: 200, fontSize: 13, lineHeight: 1.7 }}
                    placeholder={`Paste the resume here...

Example:
Alice Johnson
Skills: Python, FastAPI, PostgreSQL, Docker
Experience: 5 years backend at Stripe...`}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                  />
                </div>
              )}

              {uploading && (
                <div style={{ marginTop: 16, padding: "12px 16px", background: "var(--emerald-dim)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
                  <Loader2 size={15} color="var(--emerald)" style={{ animation: "spin 1s linear infinite" }} />
                  <span style={{ fontSize: 13, color: "var(--emerald)" }}>Uploading candidates…</span>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)} disabled={uploading}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmit} disabled={uploading} style={{ background: "linear-gradient(135deg, var(--emerald), #059669)" }}>
                {uploading ? (
                  <><Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />Uploading…</>
                ) : (
                  <><CloudUpload size={14} />Upload Candidates</>
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
