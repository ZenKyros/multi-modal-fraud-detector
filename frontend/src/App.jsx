import React, { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import TelemetryCard from './components/TelemetryCard'
import StrategyChart from './components/StrategyChart'
import Transcript from './components/Transcript'
import AlertBanner from './components/AlertBanner'
import useWebSocket from './hooks/useWebSocket'

function App() {
  // ─── State ─────────────────────────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [threatIndex, setThreatIndex] = useState(0)
  const [pillarData, setPillarData] = useState({
    linguistic: { score: 0, details: {} },
    behavioral: { score: 0, details: {} },
    acoustic: { score: 0, details: {} }
  })
  const [strategyWeights, setStrategyWeights] = useState({
    linguistic: 0.33,
    behavioral: 0.33,
    acoustic: 0.33
  })
  const [transcripts, setTranscripts] = useState([])
  const [alert, setAlert] = useState(null)

  // ─── Refs ──────────────────────────────────────────────────────────────
  const mediaRecorderRef = useRef(null)

  // ─── WebSocket ─────────────────────────────────────────────────────────
  const wsUrl = import.meta.env.VITE_API_URL
    ? `ws://${new URL(import.meta.env.VITE_API_URL).host}/ws/analyze`
    : 'ws://localhost:8000/ws/analyze'

  const { sendMessage, lastMessage, isConnected: wsConnected } = useWebSocket(wsUrl)

  // ─── Effects ──────────────────────────────────────────────────────────
  useEffect(() => {
    setIsConnected(wsConnected)
  }, [wsConnected])

  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage)
        if (data.type === 'analysis_result') {
          updateDashboard(data.data)
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.message)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
  }, [lastMessage])

  // ─── Dashboard Update ────────────────────────────────────────────────
  const updateDashboard = (data) => {
    if (data.pillar_results) {
      const results = data.pillar_results
      setPillarData({
        linguistic: {
          score: results.linguistic?.pillar_score || 0,
          details: results.linguistic || {}
        },
        behavioral: {
          score: results.behavioral?.pillar_score || 0,
          details: results.behavioral || {}
        },
        acoustic: {
          score: results.acoustic?.pillar_score || 0,
          details: results.acoustic || {}
        }
      })
    }

    if (data.threat_index !== undefined) {
      setThreatIndex(data.threat_index)
    }

    if (data.strategy_weights) {
      setStrategyWeights(data.strategy_weights)
    }

    if (data.pillar_results?.linguistic?.transcript) {
      setTranscripts(prev => [
        ...prev,
        {
          text: data.pillar_results.linguistic.transcript,
          timestamp: data.timestamp || Date.now(),
          isFraud: data.is_fraud || false
        }
      ].slice(-50)) // Keep last 50 entries
    }

    // Update alert
    if (data.is_fraud) {
      setAlert({
        type: 'danger',
        message: '🚨 Fraud Detected!',
        details: data.verification?.reasons?.join(', ') || 'Multiple fraud indicators detected'
      })
    } else if (data.threat_index > 0.4) {
      setAlert({
        type: 'warning',
        message: '⚠️ Suspicious Activity',
        details: 'Threat index approaching threshold'
      })
    } else {
      setAlert(null)
    }
  }

  // ─── Recording ────────────────────────────────────────────────────────
  const processAudioChunk = async (blob) => {
    if (!wsConnected) return
    try {
      const reader = new FileReader()
      reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1]
        sendMessage(JSON.stringify({
          type: 'audio_chunk',
          data: base64Audio
        }))
      }
      reader.readAsDataURL(blob)
    } catch (error) {
      console.error('Error processing audio chunk:', error)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 1000) {
          processAudioChunk(event.data)
        }
      }

      mediaRecorder.start(5000) // 5-second chunks
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  // ─── File Upload ─────────────────────────────────────────────────────
  const handleFileUpload = async (file) => {
    if (!isConnected) {
      alert('Not connected to backend')
      return
    }
    setIsProcessing(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/upload`, {
        method: 'POST',
        body: formData
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }
      const data = await response.json()
      updateDashboard(data)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed: ' + error.message)
    } finally {
      setIsProcessing(false)
    }
  }

  // ─── Clear Transcripts ─────────────────────────────────────────────
  const clearTranscripts = () => {
    setTranscripts([])
  }

  // ─── Render ───────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900/80 to-slate-900">
      {/* Sidebar */}
      <Sidebar
        isRecording={isRecording}
        isConnected={isConnected}
        onToggleRecording={toggleRecording}
        onFileUpload={handleFileUpload}
        isProcessing={isProcessing}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="glass m-4 rounded-2xl px-6 py-4 flex items-center justify-between border border-white/10">
          <div>
            <h1 className="text-2xl font-extrabold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Multi‑Modal Fraud Detector
            </h1>
            <p className="text-xs text-white/40 tracking-widest mt-0.5">
              GAME‑THEORETIC FUSION · 3‑PILLAR ANALYSIS
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-full px-3 py-1.5 border border-white/10">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-xs text-white/60">{isConnected ? 'Live' : 'Offline'}</span>
            </div>
            {isRecording && (
              <span className="text-xs text-red-400 animate-pulse">● Recording</span>
            )}
          </div>
        </header>

        {/* Alert Banner */}
        <div className="px-4">
          {alert && <AlertBanner alert={alert} />}
        </div>

        {/* Dashboard Grid */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Pillar Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TelemetryCard
              title="Linguistic Analysis"
              score={pillarData.linguistic.score}
              details={pillarData.linguistic.details}
              color="blue"
            />
            <TelemetryCard
              title="Behavioral Analysis"
              score={pillarData.behavioral.score}
              details={pillarData.behavioral.details}
              color="green"
            />
            <TelemetryCard
              title="Acoustic Analysis"
              score={pillarData.acoustic.score}
              details={pillarData.acoustic.details}
              color="purple"
            />
          </div>

          {/* Strategy Chart + Transcript */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <StrategyChart weights={strategyWeights} threatIndex={threatIndex} />
            </div>
            <div>
              <Transcript transcripts={transcripts} onClear={clearTranscripts} />
            </div>
          </div>

          {/* Threat Level Bar */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider">
                Current Threat Level
              </h3>
              <span className={`text-lg font-extrabold ${
                threatIndex > 0.55 ? 'text-red-400' :
                threatIndex > 0.35 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {(threatIndex * 100).toFixed(1)}%
              </span>
            </div>
            <div className="relative w-full h-3 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-out ${
                  threatIndex > 0.55 ? 'bg-gradient-to-r from-red-500 to-rose-500' :
                  threatIndex > 0.35 ? 'bg-gradient-to-r from-amber-500 to-orange-500' :
                  'bg-gradient-to-r from-emerald-500 to-teal-400'
                }`}
                style={{ width: `${Math.min(100, threatIndex * 100)}%` }}
              />
              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse" />
            </div>
            <p className="text-xs text-white/30 mt-2 text-center">
              {threatIndex > 0.55 ? '⚠️ High Threat – Fraud Detected' :
               threatIndex > 0.35 ? '⚡ Medium Threat – Monitor' :
               '✅ Low Threat – Normal Call'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App