import { useParams, Link } from 'react-router-dom';
import { Zap, ArrowLeft, Clock, Tag } from 'lucide-react';
import { useJob } from '../hooks/useApi';
import { PageSkeleton } from '../components/Skeleton';

export default function JobDetailPage() {
  const { jdId } = useParams<{ jdId: string }>();
  const { data: job, isLoading, error } = useJob(jdId || '');

  if (isLoading) return <div className="max-w-3xl mx-auto px-4 py-8"><PageSkeleton /></div>;
  if (error || !job) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center">
        <p className="text-danger">Job not found.</p>
        <Link to="/jobs" className="btn btn-secondary btn-sm mt-4">Back to Jobs</Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <Link to="/jobs" className="flex items-center gap-1 text-sm text-text-secondary hover:text-primary mb-4 no-underline">
        <ArrowLeft className="w-4 h-4" /> Back to Jobs
      </Link>

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text">{job.title || 'Untitled Job'}</h1>
          <div className="flex items-center gap-3 mt-2 text-sm text-text-secondary">
            {job.role_type && (
              <span className="flex items-center gap-1">
                <Tag className="w-3.5 h-3.5" /> {job.role_type}
              </span>
            )}
            {job.min_years && (
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> {job.min_years}+ years
              </span>
            )}
          </div>
        </div>
        <Link to={`/match/${jdId}`} className="btn btn-accent no-underline">
          <Zap className="w-4 h-4" /> Run Matching
        </Link>
      </div>

      {/* Skills */}
      <div className="card mb-4">
        <h2 className="text-sm font-semibold text-text mb-3">Required Skills</h2>
        <div className="flex flex-wrap gap-1.5">
          {(job.required_skills || []).length > 0 ? (
            job.required_skills.map((s) => (
              <span key={s} className="badge badge-primary">{s}</span>
            ))
          ) : (
            <span className="text-sm text-text-muted">None extracted</span>
          )}
        </div>

        {(job.preferred_skills || []).length > 0 && (
          <>
            <h2 className="text-sm font-semibold text-text mt-5 mb-3">Preferred Skills</h2>
            <div className="flex flex-wrap gap-1.5">
              {job.preferred_skills.map((s) => (
                <span key={s} className="badge badge-neutral">{s}</span>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Core Requirements */}
      {job.core_requirements_text && (
        <div className="card">
          <h2 className="text-sm font-semibold text-text mb-3">Core Requirements</h2>
          <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
            {job.core_requirements_text}
          </p>
        </div>
      )}
    </div>
  );
}
