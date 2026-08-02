import React from 'react'
import { motion } from 'framer-motion'

export default function AlertBanner({ alert }) {
  if (!alert) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`mb-6 rounded-3xl p-5 border ${
        alert.type === 'danger'
          ? 'bg-red-50 border-red-300'
          : 'bg-yellow-50 border-yellow-300'
      }`}
    >
      <h2 className="text-xl font-bold">{alert.title}</h2>
      <p className="text-gray-600 mt-1">{alert.message}</p>
    </motion.div>
  )
}