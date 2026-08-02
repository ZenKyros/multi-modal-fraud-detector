import React from 'react'
import GlassCard from './GlassCard'

export default function TranscriptTimeline({ transcripts }) {
  return (
    <GlassCard>
      <h3 className="font-bold text-lg mb-3">📝 Live Transcript</h3>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {transcripts.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No transcripts yet</p>
        ) : (
          transcripts.slice(-20).map((item, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg text-sm ${
                item.fraud
                  ? 'bg-red-50 border-l-4 border-red-500'
                  : 'bg-gray-50 border-l-4 border-gray-300'
              }`}
            >
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">
                  {item.speaker || 'Caller'}:
                </span>
                <span className="text-gray-400 text-xs">
                  {new Date().toLocaleTimeString()}
                </span>
              </div>
              <p className={`mt-1 ${item.fraud ? 'text-red-600' : 'text-gray-700'}`}>
                {item.text}
              </p>
            </div>
          ))
        )}
      </div>
    </GlassCard>
  )
}