import React, { useEffect, useState } from 'react'

const AlertBanner = ({ alert }) => {
  const [isVisible, setIsVisible] = useState(true)

  // Reset visibility when alert changes
  useEffect(() => {
    setIsVisible(true)
  }, [alert])

  if (!alert || !isVisible) return null

  // Define styles per alert type
  const typeMap = {
    danger: {
      icon: '🚨',
      gradient: 'from-red-600/90 via-rose-600/80 to-red-700/90',
      border: 'border-red-400/30',
      glow: 'shadow-red-500/30',
      text: 'text-white',
      accent: 'bg-red-400/20'
    },
    warning: {
      icon: '⚠️',
      gradient: 'from-amber-500/90 via-orange-500/80 to-amber-600/90',
      border: 'border-amber-400/30',
      glow: 'shadow-amber-500/30',
      text: 'text-white',
      accent: 'bg-amber-400/20'
    },
    info: {
      icon: 'ℹ️',
      gradient: 'from-blue-500/90 via-cyan-500/80 to-blue-600/90',
      border: 'border-blue-400/30',
      glow: 'shadow-blue-500/30',
      text: 'text-white',
      accent: 'bg-blue-400/20'
    }
  }

  const styles = typeMap[alert.type] || typeMap.info

  const handleDismiss = () => {
    setIsVisible(false)
  }

  return (
    <div className={`
      mx-4 my-2 rounded-xl overflow-hidden backdrop-blur-xl
      bg-gradient-to-r ${styles.gradient} ${styles.border} border
      shadow-lg ${styles.glow} transition-all duration-500 ease-out
      animate-slideDown
    `}>
      <div className="flex items-center gap-4 px-5 py-4">
        {/* Icon */}
        <div className="text-3xl flex-shrink-0">
          {styles.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h4 className={`font-bold text-base ${styles.text}`}>
            {alert.message}
          </h4>
          {alert.details && (
            <p className={`text-sm ${styles.text} opacity-80 mt-0.5 line-clamp-2`}>
              {alert.details}
            </p>
          )}
        </div>

        {/* Dismiss button */}
        <button
          onClick={handleDismiss}
          className={`
            flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center
            ${styles.accent} hover:bg-white/20 transition-colors
            text-white/70 hover:text-white
          `}
          aria-label="Dismiss alert"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Animation keyframes (injected via style) */}
      <style>{`
        @keyframes slideDown {
          0% { opacity: 0; transform: translateY(-20px) scale(0.95); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-slideDown {
          animation: slideDown 0.4s ease-out forwards;
        }
      `}</style>
    </div>
  )
}

export default AlertBanner