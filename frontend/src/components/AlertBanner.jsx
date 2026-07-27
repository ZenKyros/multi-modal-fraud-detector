import React from 'react'
import { AlertTriangle, CheckCircle, XCircle, Shield } from 'lucide-react'

/**
 * AlertBanner Component
 * 
 * Displays:
 * 1. Flashing threat warnings based on threat index
 * 2. LLM verification results and confidence
 * 3. Fraud classification and recommendations
 */
function AlertBanner({ threatLevel, threatIndex, requiresVerification, verification }) {
  // Get color scheme based on threat level
  const getTheme = () => {
    if (threatLevel === 'safe')
      return {
        bg: 'bg-cyber-green/20',
        border: 'border-cyber-green',
        text: 'text-cyber-green',
        icon: 'text-cyber-green',
      }
    if (threatLevel === 'medium')
      return {
        bg: 'bg-yellow-500/20',
        border: 'border-yellow-500',
        text: 'text-yellow-400',
        icon: 'text-yellow-400',
      }
    if (threatLevel === 'high')
      return {
        bg: 'bg-cyber-red/20',
        border: 'border-cyber-red',
        text: 'text-cyber-red',
        icon: 'text-cyber-red',
      }
    return {
      bg: 'bg-cyber-purple/20',
      border: 'border-cyber-purple',
      text: 'text-cyber-purple',
      icon: 'text-cyber-purple animate-pulse',
    }
  }

  const theme = getTheme()

  // Get threat label
  const getThreatLabel = () => {
    if (threatLevel === 'safe') return '✓ SAFE'
    if (threatLevel === 'medium') return '⚠ MEDIUM RISK'
    if (threatLevel === 'high') return '⚠ HIGH THREAT'
    return '🚨 CRITICAL THREAT'
  }

  return (
    <div className={`${theme.bg} border-b-2 ${theme.border} px-6 py-4`}>
      {/* Main threat banner */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {threatLevel === 'critical' && (
            <div className={`${theme.icon}`}>
              <AlertTriangle size={24} className="animate-pulse" />
            </div>
          )}
          {threatLevel === 'high' && (
            <AlertTriangle size={24} className={theme.icon} />
          )}
          {threatLevel === 'medium' && <Shield size={24} className={theme.icon} />}
          {threatLevel === 'safe' && <CheckCircle size={24} className={theme.icon} />}

          <div>
            <h2 className={`font-mono font-bold text-lg ${theme.text}`}>
              {getThreatLabel()}
            </h2>
            <p className="text-xs text-gray-400 font-mono">
              Threat Index: {(threatIndex * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Threat meter */}
        <div className="hidden lg:block">
          <div className="w-40 h-2 bg-cyber-darker rounded overflow-hidden border border-glass/30">
            <div
              className={`h-full transition-all ${
                threatLevel === 'safe'
                  ? 'bg-cyber-green'
                  : threatLevel === 'medium'
                    ? 'bg-yellow-500'
                    : threatLevel === 'high'
                      ? 'bg-cyber-red'
                      : 'bg-cyber-purple'
              }`}
              style={{ width: `${threatIndex * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Verification results */}
      {requiresVerification && verification && (
        <div className="mt-4 pt-3 border-t border-glass/30">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Verification status */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                {verification.is_fraud ? (
                  <XCircle size={18} className="text-cyber-red" />
                ) : (
                  <CheckCircle size={18} className="text-cyber-green" />
                )}
                <span className="font-mono font-bold text-sm">
                  LLM Verification Result
                </span>
              </div>

              <div className="ml-6 space-y-1 text-xs font-mono">
                <p>
                  <span className="text-gray-400">Status:</span>{' '}
                  <span className={verification.is_fraud ? 'text-cyber-red' : 'text-cyber-green'}>
                    {verification.is_fraud ? 'FRAUD DETECTED' : 'LEGITIMATE'}
                  </span>
                </p>
                <p>
                  <span className="text-gray-400">Confidence:</span>{' '}
                  <span className="text-cyber-blue">
                    {(verification.confidence * 100).toFixed(0)}%
                  </span>
                </p>
                <p>
                  <span className="text-gray-400">Type:</span>{' '}
                  <span className="text-cyber-cyan capitalize">
                    {verification.fraud_type}
                  </span>
                </p>
              </div>
            </div>

            {/* Key indicators and recommendations */}
            <div>
              {verification.key_indicators && verification.key_indicators.length > 0 && (
                <div className="mb-3">
                  <p className="font-mono font-bold text-sm text-gray-300 mb-2">Key Indicators</p>
                  <div className="flex flex-wrap gap-1">
                    {verification.key_indicators.slice(0, 4).map((indicator, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-cyber-darker text-xs font-mono text-cyber-cyan border border-cyber-cyan/30"
                      >
                        {indicator}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {verification.recommendations && verification.recommendations.length > 0 && (
                <div>
                  <p className="font-mono font-bold text-sm text-gray-300 mb-2">
                    Recommended Actions
                  </p>
                  <ul className="text-xs font-mono space-y-1">
                    {verification.recommendations.slice(0, 2).map((rec, idx) => (
                      <li key={idx} className="text-gray-300">
                        • {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Reasoning */}
          {verification.reasoning && (
            <div className="mt-3 pt-3 border-t border-glass/30">
              <p className="text-xs font-mono text-gray-400 italic">
                "{verification.reasoning}"
              </p>
            </div>
          )}
        </div>
      )}

      {/* Loading state for verification */}
      {requiresVerification && !verification && (
        <div className="mt-3 text-xs font-mono text-gray-400 flex items-center gap-2">
          <div className="w-2 h-2 bg-cyber-blue rounded-full animate-pulse" />
          Running LLM verification...
        </div>
      )}
    </div>
  )
}

export default AlertBanner
