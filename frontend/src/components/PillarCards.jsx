import React from 'react'
import GlassCard from './GlassCard'

export default function PillarCards({ scores }) {
  const items = [
    { key: 'linguistic', label: '🎙️ Linguistic', color: 'cyan-500' },
    { key: 'behavioral', label: '🧠 Behavioral', color: 'emerald-500' },
    { key: 'acoustic', label: '🎵 Acoustic', color: 'purple-500' },
  ]

  return (
    <div className="space-y-3">
      {items.map(({ key, label, color }) => (
        <GlassCard key={key}>
          <div className="flex justify-between items-center">
            <span className="text-gray-600">{label}</span>
            <span className={`text-xl font-bold text-${color}`}>
              {(scores[key] * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full bg-${color} transition-all duration-500`}
              style={{ width: `${scores[key] * 100}%` }}
            />
          </div>
        </GlassCard>
      ))}
    </div>
  )
}