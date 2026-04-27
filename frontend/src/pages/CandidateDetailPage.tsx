import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, Lightbulb, User, Mail, GraduationCap, Clock } from 'lucide-react';
import { useDetailedMatch } from '../hooks/useApi';
import ScoreBadge from '../components/ScoreBadge';
import ProgressBar from '../components/ProgressBar';
import { PageSkeleton } from '../components/Skeleton';

export default function CandidateDetailPage() {
  const { jdId, candidateId } = useParams<{ jdId: string; candidateId: string }>();
  const { data, isLoading, error } = useDetailedMatch(jdId || '', candidateId || '');

  if (isLoading) return <div className="max-w-3xl mx-auto px-4 py-8"><PageSkeleton /></div>;
  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8 text-center">
        <p className="text-danger">Match data not found.</p>
        <Link to={`/match/${jdId}`} className="btn btn-secondary btn-sm mt-4 no-underline">Back to Results</Link>
      </div>
    );
  }

  const { candidate, total_score, label, facet_scores, details, explanation } = data;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <Link to={`/match/${jdId}`} className="flex items-center gap-1 text-sm text-text-secondary hover:text-primary mb-4 no-underline">
        <ArrowLeft className="w-4 h-4" /> Back to Results
      </Link>

      {/* Header */}
      <div className="card mb-4">
        <div className="flex items-center gap-5">
          <ScoreBadge score={total_score} size="lg" showLabel />
          <div className="flex-1">
            <h1 className="text-xl font-bold text-text">{candidate.name || 'Unknown'}</h1>
            <div className="flex flex-wrap gap-3 mt-2 text-sm text-text-secondary">
              {candidate.email && (
                <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {candidate.email}</span>
              )}
              {candidate.current_title && (
                <span className="flex items-center gap-1"><User className="w-3.5 h-3.5" /> {candidate.current_title}</span>
              )}
              {candidate.years_of_experience != null && (
                <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {candidate.years_of_experience}y exp</span>
              )}
              {candidate.education && (
                <span className="flex items-center gap-1"><GraduationCap className="w-3.5 h-3.5" /> {candidate.education}</span>
              )}
            </div>
            <span className={`badge mt-2 ${
              label === 'Top Match' ? 'badge-success' :
              label === 'Strong Match' ? 'badge-primary' :
              label === 'Potential Fit' ? 'badge-warning' : 'badge-danger'
            }`}>{label}</span>
          </div>
        </div>
      </div>

      {/* Facet Scores */}
      <div className="card mb-4">
        <h2 className="text-sm font-semibold text-text mb-4">Score Breakdown</h2>
        <ProgressBar label="Skill Match" value={facet_scores.skill_match} />
        <ProgressBar label="Experience Match" value={facet_scores.experience_match} />
        <ProgressBar label="Education Match" value={facet_scores.education_match} />
        <ProgressBar label="Contextual Fit" value={facet_scores.contextual_fit} />
      </div>

      {/* Skills */}
      <div className="card mb-4">
        <h2 className="text-sm font-semibold text-text mb-3">Skills Analysis</h2>
        {details.matched_skills.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-medium text-text-secondary mb-1.5">Matched Skills</p>
            <div className="flex flex-wrap gap-1">
              {details.matched_skills.map((s) => (
                <span key={s} className="badge badge-success">{s}</span>
              ))}
            </div>
          </div>
        )}
        {details.missing_skills.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-medium text-text-secondary mb-1.5">Missing Required Skills</p>
            <div className="flex flex-wrap gap-1">
              {details.missing_skills.map((s) => (
                <span key={s} className="badge badge-danger">{s}</span>
              ))}
            </div>
          </div>
        )}
        {details.extra_skills.length > 0 && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1.5">Additional Skills</p>
            <div className="flex flex-wrap gap-1">
              {details.extra_skills.map((s) => (
                <span key={s} className="badge badge-neutral">{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Explanation */}
      <div className="card mb-4">
        <h2 className="text-sm font-semibold text-text mb-4">Explanation</h2>

        {/* Strengths */}
        {explanation.strengths.length > 0 && (
          <div className="mb-4">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 mb-2">
              <CheckCircle className="w-3.5 h-3.5" /> Strengths
            </p>
            <ul className="space-y-1.5">
              {explanation.strengths.map((s, i) => (
                <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Weaknesses */}
        {explanation.weaknesses.length > 0 && (
          <div className="mb-4">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-red-700 mb-2">
              <XCircle className="w-3.5 h-3.5" /> Weaknesses
            </p>
            <ul className="space-y-1.5">
              {explanation.weaknesses.map((s, i) => (
                <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendation */}
        <div className="bg-bg rounded-lg p-3 flex items-start gap-2">
          <Lightbulb className="w-4 h-4 text-accent mt-0.5 shrink-0" />
          <p className="text-sm text-text">{explanation.recommendation}</p>
        </div>
      </div>

      {/* Work Summary */}
      {candidate.work_summary && (
        <div className="card">
          <h2 className="text-sm font-semibold text-text mb-3">Work Summary</h2>
          <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
            {candidate.work_summary.slice(0, 2000)}
          </p>
        </div>
      )}
    </div>
  );
}
