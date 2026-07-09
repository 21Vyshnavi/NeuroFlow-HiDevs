'use client';

import React, { useEffect, useState } from 'react';

interface MetricGaugeProps {
  label: string;
  value: number;
  color?: string;
}

export default function MetricGauge({ label, value, color }: MetricGaugeProps) {
  const [offset, setOffset] = useState(226.2); // 2 * PI * 36

  useEffect(() => {
    // Animate to target value
    const targetOffset = 226.2 * (1 - value);
    // Use timeout to allow initial render to happen before animation starts
    const timer = setTimeout(() => {
      setOffset(targetOffset);
    }, 100);
    return () => clearTimeout(timer);
  }, [value]);

  const defaultColor = value >= 0.8 ? '#22c55e' : value >= 0.6 ? '#eab308' : '#ef4444';
  const strokeColor = color || defaultColor;

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative w-20 h-20">
        <svg viewBox="0 0 80 80" className="w-full h-full transform -rotate-90">
          <circle
            cx="40"
            cy="40"
            r="36"
            fill="transparent"
            stroke="#1e293b"
            strokeWidth="6"
          />
          <circle
            cx="40"
            cy="40"
            r="36"
            fill="transparent"
            stroke={strokeColor}
            strokeWidth="6"
            strokeDasharray="226.2"
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-semibold text-white">{Math.round(value * 100)}%</span>
        </div>
      </div>
      <span className="mt-2 text-xs text-gray-400">{label}</span>
    </div>
  );
}
