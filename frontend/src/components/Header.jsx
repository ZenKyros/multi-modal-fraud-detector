import React from 'react'
import { motion } from 'framer-motion'
import { Wifi, WifiOff } from 'lucide-react'
import GlassCard from './GlassCard'

export default function Header({ connected }) {
  return (
    <motion.div
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="flex justify-between items-center mb-8"
    >
      <div>
        <h1 className="text-5xl font-black tracking-tight bg-gradient-to-r from-purple-600 to-cyan-500 bg-clip-text text-transparent">
          FraudDetect AI
        </h1>
        <p className="text-gray-500 mt-2">Bayesian Multi-Modal Fraud Intelligence</p>
      </div>
      <GlassCard className="px-6 py-4">
        <div className="flex items-center gap-3">
          {connected ? (
            <Wifi className="text-green-500 animate-pulse" />
          ) : (
            <WifiOff className="text-red-500" />
          )}
          <div>
            <p className="text-xs uppercase text-gray-500">Status</p>
            <h3 className="font-bold">{connected ? 'LIVE' : 'OFFLINE'}</h3>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  )
}