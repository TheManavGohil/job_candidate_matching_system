import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, Users, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import FileDropZone from '../components/FileDropZone';
import { useUploadJob, useUploadCandidates } from '../hooks/useApi';

type Tab = 'job' | 'candidate';

export default function UploadPage() {
  const [activeTab, setActiveTab] = useState<Tab>('job');
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [jobText, setJobText] = useState('');
  const [candFile, setCandFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const navigate = useNavigate();

  const uploadJob = useUploadJob();
  const uploadCandidates = useUploadCandidates();

  const handleJobUpload = async () => {
    setMessage(null);
    const formData = new FormData();
    if (jobFile) {
      formData.append('file', jobFile);
    } else if (jobText.trim()) {
      formData.append('raw_text', jobText);
    } else {
      setMessage({ type: 'error', text: 'Please provide a file or paste job description text.' });
      return;
    }

    try {
      const result = await uploadJob.mutateAsync(formData);
      setMessage({ type: 'success', text: `Job "${result.title || 'Untitled'}" uploaded successfully!` });
      setJobFile(null);
      setJobText('');
      setTimeout(() => navigate(`/jobs/${result.jd_id}`), 1500);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed' });
    }
  };

  const handleCandidateUpload = async () => {
    setMessage(null);
    if (!candFile) {
      setMessage({ type: 'error', text: 'Please select a file.' });
      return;
    }
    const formData = new FormData();
    formData.append('file', candFile);

    try {
      const result = await uploadCandidates.mutateAsync(formData);
      setMessage({ type: 'success', text: result.message });
      setCandFile(null);
      setTimeout(() => navigate('/candidates'), 1500);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed' });
    }
  };

  const isLoading = uploadJob.isPending || uploadCandidates.isPending;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 animate-fade-in">
      <h1 className="text-2xl font-bold text-text mb-6">Upload</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-bg-card border border-border rounded-lg p-1">
        <button
          onClick={() => { setActiveTab('job'); setMessage(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-sm font-medium transition-all ${
            activeTab === 'job'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          Job Description
        </button>
        <button
          onClick={() => { setActiveTab('candidate'); setMessage(null); }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md text-sm font-medium transition-all ${
            activeTab === 'candidate'
              ? 'bg-primary text-white shadow-sm'
              : 'text-text-secondary hover:text-text'
          }`}
        >
          <Users className="w-4 h-4" />
          Candidates
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`flex items-center gap-2 p-3 rounded-lg mb-4 text-sm ${
          message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* Job Upload */}
      {activeTab === 'job' && (
        <div className="card space-y-5">
          <div>
            <label className="block text-sm font-semibold text-text mb-2">Upload File (PDF/DOCX)</label>
            <FileDropZone
              onFileSelect={setJobFile}
              accept=".pdf,.docx,.txt"
              label="Drop job description file here"
              description="Supports PDF, DOCX, TXT"
              selectedFile={jobFile}
              onClear={() => setJobFile(null)}
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs text-text-muted font-medium">OR</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <div>
            <label className="block text-sm font-semibold text-text mb-2">Paste Job Description</label>
            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              placeholder="Paste the full job description here..."
              rows={8}
              className="input resize-y"
            />
          </div>

          <button
            onClick={handleJobUpload}
            disabled={isLoading || (!jobFile && !jobText.trim())}
            className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadJob.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Briefcase className="w-4 h-4" />}
            {uploadJob.isPending ? 'Processing...' : 'Upload Job Description'}
          </button>
        </div>
      )}

      {/* Candidate Upload */}
      {activeTab === 'candidate' && (
        <div className="card space-y-5">
          <div>
            <label className="block text-sm font-semibold text-text mb-2">Upload CSV or Resume</label>
            <FileDropZone
              onFileSelect={setCandFile}
              accept=".csv,.pdf,.docx,.txt"
              label="Drop candidate file here"
              description="CSV for bulk upload, or PDF/DOCX for single resume"
              selectedFile={candFile}
              onClear={() => setCandFile(null)}
            />
          </div>

          <div className="bg-bg rounded-lg p-3 text-xs text-text-secondary space-y-1">
            <p className="font-semibold text-text">CSV Format Tips:</p>
            <p>• Include columns: name, email, skills, years_of_experience, education, current_title</p>
            <p>• Skills can be comma-separated within a single column</p>
            <p>• Single resume files will be parsed automatically</p>
          </div>

          <button
            onClick={handleCandidateUpload}
            disabled={isLoading || !candFile}
            className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadCandidates.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Users className="w-4 h-4" />}
            {uploadCandidates.isPending ? 'Processing...' : 'Upload Candidates'}
          </button>
        </div>
      )}
    </div>
  );
}
