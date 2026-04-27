import { Link } from 'react-router-dom';
import { Users, Plus, Mail, Clock, Briefcase } from 'lucide-react';
import { useCandidates } from '../hooks/useApi';
import { CardSkeleton } from '../components/Skeleton';

export default function CandidatesPage() {
  const { data: candidates, isLoading, error } = useCandidates();

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Candidates</h1>
        <Link to="/upload" className="btn btn-primary btn-sm no-underline">
          <Plus className="w-3.5 h-3.5" /> Add Candidates
        </Link>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      )}

      {error && (
        <div className="card text-center py-8">
          <p className="text-sm text-danger">Failed to load candidates. Is the API running?</p>
        </div>
      )}

      {candidates && candidates.length === 0 && (
        <div className="card text-center py-12">
          <Users className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-secondary mb-3">No candidates uploaded yet.</p>
          <Link to="/upload" className="btn btn-primary btn-sm no-underline">Upload candidates</Link>
        </div>
      )}

      {candidates && candidates.length > 0 && (
        <div className="space-y-3">
          {candidates.map((c, i) => (
            <div
              key={c.candidate_id}
              className="card animate-fade-in"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-text truncate">
                    {c.name || 'Unknown Candidate'}
                  </h3>
                  <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-text-secondary">
                    {c.email && (
                      <span className="flex items-center gap-1">
                        <Mail className="w-3 h-3" /> {c.email}
                      </span>
                    )}
                    {c.current_title && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="w-3 h-3" /> {c.current_title}
                      </span>
                    )}
                    {c.years_of_experience != null && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {c.years_of_experience}y
                      </span>
                    )}
                  </div>
                  {c.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {c.skills.slice(0, 6).map((s) => (
                        <span key={s} className="badge badge-neutral text-[11px]">{s}</span>
                      ))}
                      {c.skills.length > 6 && (
                        <span className="badge badge-neutral text-[11px]">+{c.skills.length - 6}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
