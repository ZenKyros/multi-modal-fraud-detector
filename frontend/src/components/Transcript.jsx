import React, { useEffect, useRef } from 'react'
import { MessageCircle } from 'lucide-react'

/**
 * Transcript Component
 * 
 * Live scrolling text subtitle box showing transcribed audio
 * Color-coded based on threat level
 */
function Transcript({ transcripts, currentChunk, threatLevel }) {
  const scrollContainerRef = useRef(null)

  // Auto-scroll to bottom when new transcripts arrive
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
    }
  }, [transcripts])

  // Get threat color
  const getThreatColor = () => {
    if (threatLevel === 'safe') return 'text-cyber-green border-cyber-green'
    if (threatLevel === 'medium') return 'text-yellow-400 border-yellow-400'
    if (threatLevel === 'high') return 'text-cyber-red border-cyber-red'
    return 'text-cyber-purple border-cyber-purple'
  }

  return (
    <div className="cyber-card">
      <div className="flex items-center gap-2 mb-4">
        <MessageCircle size={18} className="text-cyber-cyan" />
        <h3 className="font-mono font-bold text-sm text-cyber-cyan">Live Transcript</h3>
        <span className={`text-xs font-mono ${getThreatColor()}`}>
          [{threatLevel.toUpperCase()}]
        </span>
      </div>

      {/* Transcript display */}
      <div
        ref={scrollContainerRef}
        className="bg-cyber-darker rounded h-64 p-4 overflow-y-auto space-y-3 border border-glass/20"
      >
        {transcripts.length > 0 ? (
          transcripts.map((item, idx) => (
            <div key={idx} className="animate-fade-in">
              <div className="text-xs text-gray-500 font-mono mb-1">
                [{item.chunk}] {new Date(item.timestamp).toLocaleTimeString()}
              </div>
              <p className="text-sm font-mono text-gray-200 leading-relaxed">
                "{item.text || '(empty)'}"
              </p>
              {idx < transcripts.length - 1 && (
                <div className="mt-3 border-t border-glass/10" />
              )}
            </div>
          ))
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500 font-mono text-sm">
            No transcripts yet
          </div>
        )}
      </div>

      {/* Chunk indicator */}
      <div className="mt-3 text-xs text-gray-400 font-mono">
        Current: Chunk {currentChunk + 1} • Total: {transcripts.length}
      </div>
    </div>
  )
}

export default Transcript
