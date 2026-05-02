"use client";

import { useState } from "react";
import type { WeightsMap } from "@/lib/types";

interface WeightSlidersProps {
  weights: WeightsMap;
  onChange: (weights: WeightsMap) => void;
  disabled?: boolean;
}

const sectionLabels: Record<string, string> = {
  required_skills: "Required Skills",
  preferred_skills: "Preferred Skills",
  responsibilities: "Responsibilities",
  qualifications: "Qualifications",
  context: "Industry Context",
};

export default function WeightSliders({
  weights,
  onChange,
  disabled = false,
}: WeightSlidersProps) {
  const [local, setLocal] = useState<WeightsMap>({ ...weights });

  const handleChange = (key: string, value: number) => {
    const updated = { ...local, [key]: value };
    // Normalise to sum=100
    const total = Object.values(updated).reduce((a, b) => a + b, 0) || 1;
    const normalised: WeightsMap = {} as WeightsMap;
    for (const [k, v] of Object.entries(updated)) {
      normalised[k] = Math.round((v / total) * 100 * 10) / 10;
    }
    setLocal(updated);
    onChange(normalised);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-[var(--muted-foreground)] uppercase tracking-wider">
        Section Weights
      </h3>
      {Object.entries(local).map(([key, value]) => (
        <div key={key} className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">
              {sectionLabels[key] || key}
            </label>
            <span className="text-sm font-mono text-cyan-400 tabular-nums">
              {Math.round(value)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            step={1}
            value={value}
            onChange={(e) => handleChange(key, parseFloat(e.target.value))}
            disabled={disabled}
            className="w-full"
          />
        </div>
      ))}
    </div>
  );
}
