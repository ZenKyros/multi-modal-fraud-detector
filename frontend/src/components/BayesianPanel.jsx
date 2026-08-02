import React from 'react'
import GlassCard from './GlassCard'

export default function BayesianPanel({ posterior }) {
  return (
    <GlassCard>
      <h3 className="font-bold text-lg mb-3">🧠 Call Type Probabilities</h3>
      {Object.keys(posterior).length > 0 ? (
        <div className="space-y-2">
          {Object.entries(posterior).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-sm text-gray-600 capitalize w-24">
                {key.replace('_', ' ')}
              </span>
              <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${value * 100}%` }}
                />
              </div>
              <span className="text-sm font-bold">{(value * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-sm">No data yet</p>
      )}
    </GlassCard>
  )
}