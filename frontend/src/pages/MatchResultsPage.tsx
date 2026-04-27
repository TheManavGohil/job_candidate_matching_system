import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Search, Users, Zap } from 'lucide-react';
import { useMatchResults, useJob } from '../hooks/useApi';
import MatchCard from '../components/MatchCard';
import { CardSkeleton } from '../components/Skeleton';

export default function MatchResultsPage() {
  const { jdId } = useParams<{ jdId: string }>();
  const [searchQuery, setSearchQuery] = useState('');
  const [topK] = useState(50);
  const [threshold] = useState(0);

  const { data: job } = useJob(jdId || '');
  const { data: results, isLoading, error } = useMatchResults(jdId || '', topK, threshold);

  const filtered = results?.candidates.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.name || '').toLowerCase().includes(q) ||
      c.short_summary.toLowerCase().includes(q) ||
      c.top_skills.some((s) => s.toLowerCase().includes(q))
    );
  }) || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-in">
      <Link to={jdId ? `/jobs/${jdId}` : '/jobs'} className="flex items-center gap-1 text-sm text-text-secondary hover:text-primary mb-4 no-underline">
        <ArrowLeft className="w-4 h-4" /> Back to Job
      </Link>

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-5 h-5 text-accent" />
            <h1 className="text-2xl font-bold text-text">Match Results</h1>
          </div>
          <p className="text-sm text-text-secondary">
            {job?.title || 'Job'} — {results?.total_candidates ?? '...'} candidates ranked
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-5">
        <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by name, skill, or summary..."
          className="input pl-9"
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card text-center py-8">
          <p className="text-sm text-danger">Failed to load results. Make sure the API is running and candidates are uploaded.</p>
        </div>
      )}

      {/* Empty */}
      {results && filtered.length === 0 && (
        <div className="card text-center py-12">
          <Users className="w-12 h-12 text-text-muted mx-auto mb-3" />
          <p className="text-sm text-text-secondary">
            {searchQuery ? 'No candidates match your search.' : 'No matching candidates found. Try uploading more candidates.'}
          </p>
        </div>
      )}

      {/* Results */}
      {filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((candidate, i) => (
            <MatchCard
              key={candidate.candidate_id}
              candidate={candidate}
              jdId={jdId || ''}
              index={i}
            />
          ))}
        </div>
      )}
    </div>
  );
}
