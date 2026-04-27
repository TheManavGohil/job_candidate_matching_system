import { getScoreColor } from './ScoreBadge';

interface ProgressBarProps {
  label: string;
  value: number;
  max?: number;
}

export default function ProgressBar({ label, value, max = 100 }: ProgressBarProps) {
  const pct = Math.min(100, (value / max) * 100);
  const color = getScoreColor(value);

  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-text">{label}</span>
        <span className="text-sm font-semibold" style={{ color }}>
          {value.toFixed(1)}
        </span>
      </div>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
