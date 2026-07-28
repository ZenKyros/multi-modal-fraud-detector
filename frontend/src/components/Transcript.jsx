import React, { useRef, useEffect } from 'react'

const Transcript = ({ transcripts }) => {
  const containerRef = useRef(null)

  // Auto-scroll to bottom when new transcripts arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [transcripts])

  const clearTranscripts = () => {
    // We'll call a parent callback if needed – but for now we'll just clear local state.
    // In a real app, you'd pass a setter from parent.
    // We'll handle it by resetting the array in the parent or using a callback.
    // For now, we'll just show a placeholder.
    // We'll implement a proper clear function with a callback prop.
  }

  return (
    <div className="glass-card p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider">
          📝 Live Transcript
        </h3>
        {transcripts.length > 0 && (
          <button
            onClick={() => {
              // This will clear transcripts in parent – we'll pass a callback
              // For now, we'll just log
              console.log('Clear transcripts – implement callback from parent')
            }}
            className="text-xs text-white/30 hover:text-white/70 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Transcript list */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scroll"
      >
        {transcripts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-white/20 text-sm">
            <span className="text-3xl mb-2">🎙️</span>
            <p>No transcripts yet</p>
            <p className="text-xs mt-1">Start recording or upload a file</p>
          </div>
        ) : (
          transcripts.map((item, index) => (
            <div
              key={index}
              className={`
                group flex items-start gap-2 p-2 rounded-lg transition-all duration-200
                ${item.isFraud
                  ? 'bg-red-500/10 border-l-2 border-red-500'
                  : 'bg-white/5 hover:bg-white/10 border-l-2 border-transparent'
                }
              `}
            >
              <div className="flex-1 min-w-0">
                <p className={`text-sm break-words ${item.isFraud ? 'text-red-300' : 'text-white/80'}`}>
                  {item.text}
                </p>
                <span className="text-[10px] text-white/20">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
              {item.isFraud && (
                <span className="flex-shrink-0 text-red-400 text-xs bg-red-500/20 px-2 py-0.5 rounded-full">
                  ⚠️ Fraud
                </span>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer count */}
      {transcripts.length > 0 && (
        <div className="mt-3 text-[10px] text-white/20 border-t border-white/5 pt-2 flex justify-between">
          <span>{transcripts.length} segments</span>
          <span>•</span>
          <span>Live</span>
        </div>
      )}

      {/* Custom scrollbar style */}
      <style>{`
        .custom-scroll::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: rgba(255,255,255,0.05);
          border-radius: 10px;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.15);
          border-radius: 10px;
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: rgba(255,255,255,0.25);
        }
      `}</style>
    </div>
  )
}

export default Transcript