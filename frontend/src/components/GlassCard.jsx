import React from 'react'

export default function GlassCard({ children, className = '' }) {
  return (
    <div className={`bg-white/80 backdrop-blur-xl border border-white/30 shadow-xl rounded-3xl p-6 hover:shadow-2xl transition-all duration-300 ${className}`}>
      {children}
    </div>
  )
}