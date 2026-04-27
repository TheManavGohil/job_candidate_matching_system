import { Link } from 'react-router-dom';
import { Briefcase, Calendar, Zap, Plus } from 'lucide-react';
import { useJobs } from '../hooks/useApi';
import { CardSkeleton } from '../components/Skeleton';

export default function JobsPage() {
  const { data: jobs, isLoading, error } = useJobs();

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Job Descriptions</h1>
        <Link to="/upload" className="btn btn-primary btn-sm">
          <Plus className="w-3.5 h-3.5" /> Add JD
        </Link>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      )}

      {error && (
        <div className="card text-center py-8">
          <p className="text-sm text-danger">Failed to load jobs. Is the API running?</p>
        </div>
      )}

      {jobs && jobs.length === 0 && (
        <div className="card text-center py-12">
          <Briefcase className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-secondary mb-3">No job descriptions uploaded yet.</p>
          <Link to="/upload" className="btn btn-primary btn-sm">Upload your first JD</Link>
        </div>
      )}

      {jobs && jobs.length > 0 && (
        <div className="space-y-3">
          {jobs.map((job, i) => (
            <Link
              key={job.jd_id}
              to={`/jobs/${job.jd_id}`}
              className="card block no-underline group hover:border-primary/30 animate-fade-in"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-text truncate">
                      {job.title || 'Untitled Job'}
                    </h3>
                    {job.role_type && (
                      <span className="badge badge-primary">{job.role_type}</span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-1 mt-2">
                    {(job.required_skills || []).slice(0, 5).map((s) => (
                      <span key={s} className="badge badge-neutral text-[11px]">{s}</span>
                    ))}
                    {(job.required_skills || []).length > 5 && (
                      <span className="badge badge-neutral text-[11px]">
                        +{job.required_skills.length - 5} more
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Link
                    to={`/match/${job.jd_id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="btn btn-accent btn-sm no-underline"
                  >
                    <Zap className="w-3 h-3" /> Match
                  </Link>
                  {job.created_at && (
                    <span className="flex items-center gap-1 text-[11px] text-text-muted">
                      <Calendar className="w-3 h-3" />
                      {new Date(job.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
