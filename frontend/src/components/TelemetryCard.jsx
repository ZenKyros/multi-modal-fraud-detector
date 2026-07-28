import React from 'react'

const TelemetryCard = ({ title, score, details, color }) => {
  // Define color schemes for each pillar
  const colorMap = {
    blue: {
      gradient: 'from-blue-500 to-cyan-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      icon: '🎙️',
      progress: 'bg-gradient-to-r from-blue-500 to-cyan-400',
      glow: 'shadow-blue-500/20'
    },
    green: {
      gradient: 'from-emerald-500 to-teal-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      icon: '🧠',
      progress: 'bg-gradient-to-r from-emerald-500 to-teal-400',
      glow: 'shadow-emerald-500/20'
    },
    purple: {
      gradient: 'from-purple-500 to-pink-400',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/30',
      icon: '🎵',
      progress: 'bg-gradient-to-r from-purple-500 to-pink-400',
      glow: 'shadow-purple-500/20'
    }
  }

  const styles = colorMap[color] || colorMap.blue

  // Determine status based on score
  const getStatus = (score) => {
    if (score > 0.6) return { label: 'High', color: 'text-red-400' }
    if (score > 0.3) return { label: 'Moderate', color: 'text-amber-400' }
    return { label: 'Low', color: 'text-emerald-400' }
  }

  const status = getStatus(score)

  return (
    <div className={`
      glass-card p-5 hover:scale-[1.02] transition-all duration-300
      border-t-2 ${styles.border} shadow-lg ${styles.glow}
      ${styles.bg} backdrop-blur-xl
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-2xl mr-2">{styles.icon}</span>
          <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider inline-block">
            {title}
          </h3>
        </div>
        <span className={`text-xs font-medium ${status.color} bg-white/10 px-2.5 py-1 rounded-full`}>
          {status.label}
        </span>
      </div>

      {/* Score */}
      <div className="flex items-end gap-3 mb-4">
        <span className="text-4xl font-extrabold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
          {(score * 100).toFixed(0)}%
        </span>
        <span className="text-xs text-white/30 mb-1">pillar score</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden mb-4">
        <div
          className={`h-full rounded-full ${styles.progress} transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(100, score * 100)}%` }}
        />
      </div>

      {/* Details */}
      {details && (
        <div className="grid grid-cols-2 gap-1.5 text-xs">
          {Object.entries(details)
            .filter(([key]) => !['pillar_score', 'error', 'transcript'].includes(key))
            .slice(0, 4)
            .map(([key, value]) => (
              <div key={key} className="bg-white/5 rounded-lg px-2.5 py-1.5 flex justify-between">
                <span className="text-white/40 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="text-white/80 font-medium">
                  {typeof value === 'number' ? (value * 100).toFixed(0) + '%' : String(value).slice(0, 20)}
                </span>
              </div>
            ))}
        </div>
      )}

      {/* Error state */}
      {details?.error && (
        <div className="mt-3 text-xs text-red-400/80 bg-red-500/10 rounded-lg px-3 py-2 border border-red-500/20">
          ⚠️ {details.error}
        </div>
      )}

      {/* Live indicator */}
      <div className="mt-3 flex items-center gap-1.5">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
        </span>
        <span className="text-[10px] text-white/30">Live</span>
      </div>
    </div>
  )
}

export default TelemetryCard