interface ScoreBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 85) return '#10B981';
  if (score >= 70) return '#3B82F6';
  if (score >= 55) return '#F59E0B';
  if (score >= 40) return '#F97316';
  return '#EF4444';
}

function getScoreGradient(score: number): string {
  if (score >= 85) return 'from-emerald-500 to-teal-500';
  if (score >= 70) return 'from-blue-500 to-indigo-500';
  if (score >= 55) return 'from-amber-500 to-orange-500';
  if (score >= 40) return 'from-orange-500 to-red-400';
  return 'from-red-500 to-rose-600';
}

const SIZES = {
  sm: { outer: 48, stroke: 4, text: 'text-xs', label: 'text-[9px]' },
  md: { outer: 64, stroke: 5, text: 'text-base', label: 'text-[10px]' },
  lg: { outer: 88, stroke: 6, text: 'text-xl', label: 'text-xs' },
};

export default function ScoreBadge({ score, size = 'md', showLabel = false }: ScoreBadgeProps) {
  const { outer, stroke, text } = SIZES[size];
  const radius = (outer - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: outer, height: outer }}>
        <svg width={outer} height={outer} className="-rotate-90">
          <circle
            cx={outer / 2}
            cy={outer / 2}
            r={radius}
            fill="none"
            stroke="#E2E8F0"
            strokeWidth={stroke}
          />
          <circle
            cx={outer / 2}
            cy={outer / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className={`absolute inset-0 flex items-center justify-center font-bold ${text}`}>
          {Math.round(score)}
        </div>
      </div>
      {showLabel && (
        <span className={`font-semibold ${SIZES[size].label}`} style={{ color }}>
          {score >= 85 ? 'Top' : score >= 70 ? 'Strong' : score >= 55 ? 'Potential' : score >= 40 ? 'Weak' : 'Low'}
        </span>
      )}
    </div>
  );
}

export { getScoreColor, getScoreGradient };
