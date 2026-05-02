"use client";

interface ScoreBarProps {
  score: number;  // 0–100
  height?: number;
  showLabel?: boolean;
}

export default function ScoreBar({ score, height = 8, showLabel = true }: ScoreBarProps) {
  const clampedScore = Math.max(0, Math.min(100, score));

  // Color gradient based on score
  const getColor = (s: number) => {
    if (s >= 75) return "from-emerald-500 to-emerald-400";
    if (s >= 50) return "from-cyan-500 to-cyan-400";
    if (s >= 30) return "from-amber-500 to-amber-400";
    return "from-red-500 to-red-400";
  };

  return (
    <div className="flex items-center gap-3 w-full">
      <div
        className="flex-1 rounded-full overflow-hidden"
        style={{
          height,
          backgroundColor: "var(--card-border)",
        }}
      >
        <div
          className={`h-full rounded-full bg-gradient-to-r ${getColor(clampedScore)} transition-all duration-1000 ease-out`}
          style={{ width: `${clampedScore}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-semibold tabular-nums min-w-[3rem] text-right">
          {clampedScore.toFixed(1)}
        </span>
      )}
    </div>
  );
}
