import React from 'react'
import { Zap, AlertCircle } from 'lucide-react'

/**
 * TelemetryCard Component
 * 
 * Displays individual pillar analysis with score gauge and key metrics
 * Used for Linguistic, Behavioral, and Acoustic pillar visualization
 */
function TelemetryCard({ title, score, label, subtitle, topKeywords = [] }) {
  // Determine threat color
  const getColor = () => {
    if (score < 0.3) return 'text-cyber-green'
    if (score < 0.55) return 'text-yellow-400'
    if (score < 0.8) return 'text-cyber-red'
    return 'text-cyber-purple'
  }

  const getBgColor = () => {
    if (score < 0.3) return 'bg-cyber-green/10'
    if (score < 0.55) return 'bg-yellow-500/10'
    if (score < 0.8) return 'bg-cyber-red/10'
    return 'bg-cyber-purple/10'
  }

  const getGradient = () => {
    if (score < 0.3) return 'from-cyber-green to-cyber-green/50'
    if (score < 0.55) return 'from-yellow-400 to-yellow-400/50'
    if (score < 0.8) return 'from-cyber-red to-cyber-red/50'
    return 'from-cyber-purple to-cyber-purple/50'
  }

  return (
    <div className={`cyber-card ${getBgColor()} border-2 ${getColor()}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-mono font-bold text-sm text-white">{title}</h3>
          <p className="text-xs text-gray-400 font-mono mt-1">{subtitle}</p>
        </div>
        <Zap size={20} className={getColor()} />
      </div>

      {/* Score gauge */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-mono text-gray-300">{label}</span>
          <span className={`font-mono font-bold text-sm ${getColor()}`}>
            {(score * 100).toFixed(0)}%
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full h-3 bg-cyber-darker rounded overflow-hidden border border-glass/30">
          <div
            className={`h-full bg-gradient-to-r ${getGradient()} transition-all duration-300 rounded`}
            style={{ width: `${score * 100}%` }}
          />
        </div>

        {/* Threat indicator */}
        {score > 0.55 && (
          <div className="flex items-center gap-1 mt-2 text-xs text-cyber-red font-mono">
            <AlertCircle size={12} />
            <span>Verification required</span>
          </div>
        )}
      </div>

      {/* Keywords or metrics */}
      {topKeywords && topKeywords.length > 0 && (
        <div className="pt-3 border-t border-glass/30">
          <p className="text-xs text-gray-400 font-mono mb-2">Top Indicators</p>
          <div className="flex flex-wrap gap-1">
            {topKeywords.slice(0, 3).map((item, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded bg-cyber-darker text-xs font-mono text-cyber-cyan border border-cyber-cyan/30"
              >
                {typeof item === 'string' ? item : item.keyword}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default TelemetryCard
