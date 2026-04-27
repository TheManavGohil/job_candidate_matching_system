import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import ScoreBadge from './ScoreBadge';
import type { MatchCandidate } from '../api/client';

interface MatchCardProps {
  candidate: MatchCandidate;
  jdId: string;
  index: number;
}

function getLabelBadge(label: string) {
  switch (label) {
    case 'Top Match': return 'badge-success';
    case 'Strong Match': return 'badge-primary';
    case 'Potential Fit': return 'badge-warning';
    default: return 'badge-danger';
  }
}

export default function MatchCard({ candidate, jdId, index }: MatchCardProps) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/match/${jdId}/${candidate.candidate_id}`)}
      className="card cursor-pointer group animate-fade-in hover:border-primary/30"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-4">
        {/* Score Badge */}
        <ScoreBadge score={candidate.total_score} size="md" />

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-text truncate">
              {candidate.name || 'Unknown Candidate'}
            </h3>
            <span className={`badge ${getLabelBadge(candidate.label)}`}>
              {candidate.label}
            </span>
          </div>

          <p className="text-xs text-text-secondary line-clamp-2 mb-2">
            {candidate.short_summary}
          </p>

          {/* Top Skills */}
          {candidate.top_skills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {candidate.top_skills.map((skill) => (
                <span key={skill} className="badge badge-neutral text-[11px]">
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Arrow */}
        <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-primary transition-colors shrink-0 mt-1" />
      </div>
    </div>
  );
}
