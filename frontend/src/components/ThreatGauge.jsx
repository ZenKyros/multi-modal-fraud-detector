import React from 'react'

export default function ThreatGauge({ value }) {
  const color = value > 0.55 ? '#ef4444' : value > 0.35 ? '#f59e0b' : '#10b981'
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference * (1 - value)

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="transparent"
          stroke="rgba(0,0,0,0.05)"
          strokeWidth="10"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          className="transition-all duration-700 ease-out"
        />
        <text x="70" y="80" textAnchor="middle" fontSize="28" fill="#1e293b" fontWeight="bold" fontFamily="Inter">
          {(value * 100).toFixed(0)}%
        </text>
      </svg>
      <span className="text-sm font-medium text-gray-500 mt-2">Threat Level</span>
    </div>
  )
}