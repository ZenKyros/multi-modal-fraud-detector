import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Wifi, WifiOff } from 'lucide-react'

import { WS_URL } from './utils/constants'
import { useWebSocket } from './services/websocket'

import GlassCard from './components/GlassCard'
import Background3D from './components/Background3D'
import Header from './components/Header'
import ControlPanel from './components/ControlPanel'
import ThreatGauge from './components/ThreatGauge'
import ThreatHistory from './components/ThreatHistory'
import PillarCards from './components/PillarCards'
import BayesianPanel from './components/BayesianPanel'
import TranscriptTimeline from './components/TranscriptTimeline'
import AlertBanner from './components/AlertBanner'

export default function App() {
  // ─── State ──────────────────────────────────────────────
  const [connected, setConnected] = useState(false)
  const [threat, setThreat] = useState(0)
  const [pillarScores, setPillarScores] = useState({
    linguistic: 0,
    behavioral: 0,
    acoustic: 0,
  })
  const [posterior, setPosterior] = useState({})
  const [transcripts, setTranscripts] = useState([])
  const [history, setHistory] = useState([])
  const [alert, setAlert] = useState(null)

  // ─── WebSocket ────────────────────────────────────────────
  const { sendMessage, lastMessage, isConnected } = useWebSocket(WS_URL)

  useEffect(() => {
    setConnected(isConnected)
  }, [isConnected])

  useEffect(() => {
    if (lastMessage) {
      try {
        const result = JSON.parse(lastMessage)
        if (result.type !== 'analysis_result') return

        const data = result.data

        setThreat(data.threat_index || 0)

        setHistory(prev => [
          ...prev.slice(-40),
          { time: new Date().toLocaleTimeString(), value: data.threat_index || 0 },
        ])

        if (data.posterior) setPosterior(data.posterior)

        if (data.pillar_results) {
          setPillarScores({
            linguistic: data.pillar_results.linguistic?.pillar_score || 0,
            behavioral: data.pillar_results.behavioral?.pillar_score || 0,
            acoustic: data.pillar_results.acoustic?.pillar_score || 0,
          })
        }

        if (data.transcripts) {
          setTranscripts(prev => [
            ...prev,
            ...data.transcripts.map(t => ({
              speaker: 'Caller',
              text: t,
              fraud: data.is_fraud,
            })),
          ])
        }

        if (data.is_fraud) {
          setAlert({
            type: 'danger',
            title: '🚨 Fraud Detected',
            message: data.verification?.reasons?.join(', ') || 'High confidence fraud',
          })
        } else if ((data.threat_index || 0) > 0.4) {
          setAlert({
            type: 'warning',
            title: '⚠️ Suspicious Behaviour',
            message: 'Threat score increasing',
          })
        } else {
          setAlert(null)
        }
      } catch (error) {
        console.error('WebSocket parse error:', error)
      }
    }
  }, [lastMessage])

  return (
    <div className="min-h-screen bg-slate-50 relative overflow-hidden">
      <Background3D />

      <main className="relative z-10 max-w-[1700px] mx-auto p-8">
        {/* Header */}
        <Header connected={connected} />

        {/* Alert Banner */}
        {alert && <AlertBanner alert={alert} />}

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column */}
          <div className="col-span-3 space-y-6">
            <ControlPanel
              connected={connected}
              sendMessage={sendMessage}
              setTranscripts={setTranscripts}
              setThreat={setThreat}
              setHistory={setHistory}
              setPosterior={setPosterior}
              setPillarScores={setPillarScores}
              setAlert={setAlert}
            />
            <PillarCards scores={pillarScores} />
          </div>

          {/* Centre Column */}
          <div className="col-span-6 space-y-6">
            <GlassCard className="flex justify-center py-8">
              <ThreatGauge value={threat} />
            </GlassCard>
            <ThreatHistory history={history} />
          </div>

          {/* Right Column */}
          <div className="col-span-3 space-y-6">
            <BayesianPanel posterior={posterior} />
          </div>
        </div>

        {/* Transcript Timeline */}
        <div className="mt-8">
          <TranscriptTimeline transcripts={transcripts} />
        </div>
      </main>
    </div>
  )
}