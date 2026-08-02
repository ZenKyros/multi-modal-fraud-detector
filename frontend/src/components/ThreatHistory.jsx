import React from 'react'
import GlassCard from './GlassCard'

export default function ThreatHistory({ history }) {
  return (
    <GlassCard>
      <h3 className="font-bold text-lg mb-3">📈 Threat History</h3>
      {history.length > 0 ? (
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {history.slice(-10).map((item, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span className="text-gray-500">{item.time}</span>
              <span className={`font-bold ${
                item.value > 0.55 ? 'text-red-500' : 
                item.value > 0.35 ? 'text-yellow-500' : 'text-green-500'
              }`}>
                {(item.value * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-sm">No history yet</p>
      )}
    </GlassCard>
  )
}