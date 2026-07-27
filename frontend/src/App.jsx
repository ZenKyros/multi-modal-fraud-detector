import React, { useState, useCallback, useEffect } from 'react'
import { AlertCircle, Activity } from 'lucide-react'
import Sidebar from './components/Sidebar'
import TelemetryCard from './components/TelemetryCard'
import StrategyChart from './components/StrategyChart'
import Transcript from './components/Transcript'
import AlertBanner from './components/AlertBanner'
import { useWebSocket } from './hooks/useWebSocket'

/**
 * Root Application Component
 * 
 * Multi-Modal Fraud Detector Dashboard
 * Orchestrates real-time analysis visualization with parallel pillar monitoring
 */
function App() {
  // WebSocket configuration
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

  // State management
  const [selectedFile, setSelectedFile] = useState('scam_call.wav')
  const [currentChunk, setCurrentChunk] = useState(0)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [autoPlay, setAutoPlay] = useState(true)

  // Analysis results
  const [latestResult, setLatestResult] = useState(null)
  const [transcripts, setTranscripts] = useState([])
  const [threatHistory, setThreatHistory] = useState([])
  const [strategyMetrics, setStrategyMetrics] = useState(null)
  const [verificationResult, setVerificationResult] = useState(null)

  // UI state
  const [error, setError] = useState(null)
  const [maxChunks, setMaxChunks] = useState(0)

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((message) => {
    if (message.type === 'analysis_result') {
      const data = message.data

      // Update threat history
      setThreatHistory((prev) => {
        const updated = [...prev, data.threat_index]
        return updated.slice(-50) // Keep last 50
      })

      // Update transcript
      if (data.transcript) {
        setTranscripts((prev) => [
          ...prev,
          {
            chunk: data.chunk_index,
            text: data.transcript,
            timestamp: data.timestamp,
          },
        ])
      }

      // Update latest result
      setLatestResult(data)

      // Update strategy
      if (data.game_state) {
        setStrategyMetrics(data.game_state)
      }

      // Update verification if present
      if (data.verification) {
        setVerificationResult(data.verification)
      }

      // Auto-advance to next chunk
      if (autoPlay && currentChunk < maxChunks - 1) {
        setTimeout(() => {
          setCurrentChunk((prev) => prev + 1)
        }, 1000)
      }

      setError(null)
      setIsAnalyzing(false)
    } else if (message.type === 'error') {
      setError(message.message)
      setIsAnalyzing(false)
    } else if (message.type === 'strategy_update') {
      setStrategyMetrics(message.data)
    }
  }, [currentChunk, maxChunks, autoPlay])

  // Initialize WebSocket connection
  const { isConnected, send: sendWS } = useWebSocket(wsUrl, handleWebSocketMessage)

  // Fetch file metadata
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/files/${selectedFile}/metadata`
        )
        const data = await response.json()
        setMaxChunks(data.chunk_count)
        setCurrentChunk(0)
      } catch (err) {
        console.error('Failed to fetch file metadata:', err)
      }
    }

    if (selectedFile) {
      fetchMetadata()
    }
  }, [selectedFile])

  // Handle chunk analysis
  const handleAnalyzeChunk = useCallback(() => {
    if (!isConnected) {
      setError('WebSocket not connected')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    sendWS({
      action: 'analyze',
      audio_file: selectedFile,
      chunk_index: currentChunk,
    })
  }, [isConnected, sendWS, selectedFile, currentChunk])

  // Handle file selection
  const handleFileSelect = (file) => {
    setSelectedFile(file)
    setCurrentChunk(0)
    setLatestResult(null)
    setTranscripts([])
    setThreatHistory([])
    setVerificationResult(null)
  }

  // Handle live recording
  const handleLiveRecording = useCallback((recordingData) => {
    if (!isConnected) {
      setError('WebSocket not connected')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    // Convert audio data to base64 for transmission
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64Audio = btoa(
        new Uint8Array(e.target.result).reduce((data, byte) => data + String.fromCharCode(byte), '')
      )

      sendWS({
        action: 'analyze_live',
        audio_data: base64Audio,
        format: recordingData.format,
        timestamp: recordingData.timestamp,
      })
    }
    reader.readAsArrayBuffer(recordingData.audio)
  }, [isConnected, sendWS])

  // Handle recording error
  const handleRecordingError = useCallback((errorMsg) => {
    setError(errorMsg)
  }, [])

  // Get threat level
  const getThreatLevel = () => {
    if (!latestResult) return 'safe'
    const ti = latestResult.threat_index
    if (ti < 0.3) return 'safe'
    if (ti < 0.55) return 'medium'
    if (ti < 0.8) return 'high'
    return 'critical'
  }

  return (
    <div className="min-h-screen bg-cyber-darker text-white overflow-hidden">
      {/* Background scan effect */}
      <div className="fixed inset-0 scan-line pointer-events-none opacity-5 z-0" />

      {/* Main container */}
      <div className="relative z-10 flex h-screen flex-col lg:flex-row">
        {/* Sidebar */}
        <div className="w-full lg:w-80 border-r border-glass overflow-y-auto bg-cyber-darker/50 backdrop-blur">
          <Sidebar
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            currentChunk={currentChunk}
            maxChunks={maxChunks}
            onChunkChange={setCurrentChunk}
            onAnalyze={handleAnalyzeChunk}
            isAnalyzing={isAnalyzing}
            isConnected={isConnected}
            autoPlay={autoPlay}
            onAutoPlayChange={setAutoPlay}
            onLiveRecording={handleLiveRecording}
            onRecordingError={handleRecordingError}
          />
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Alert Banner */}
          {latestResult && (
            <AlertBanner
              threatLevel={getThreatLevel()}
              threatIndex={latestResult.threat_index}
              requiresVerification={latestResult.requires_verification}
              verification={verificationResult}
            />
          )}

          {/* Error display */}
          {error && (
            <div className="px-6 py-3 bg-cyber-red/20 border-b border-cyber-red text-cyber-red flex items-center gap-2 font-mono text-sm">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          {/* Grid layout for metrics and charts */}
          <div className="flex-1 overflow-y-auto p-6">
            {!latestResult ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                <Activity size={48} className="mb-4 opacity-50" />
                <p className="text-lg font-mono">Select audio file and click analyze to begin</p>
                <p className="text-sm mt-2">Current WebSocket status: {isConnected ? '✓ Connected' : '✗ Disconnected'}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-fit">
                {/* Telemetry Cards */}
                <TelemetryCard
                  title="Linguistic (Pillar I)"
                  score={latestResult.pillar_scores[0]}
                  label="Urgency Score"
                  subtitle={`${latestResult.linguistic_data.keywords.length} keywords detected`}
                  topKeywords={latestResult.linguistic_data.keywords.slice(0, 3)}
                />

                <TelemetryCard
                  title="Behavioral (Pillar II)"
                  score={latestResult.pillar_scores[1]}
                  label="Aggression Score"
                  subtitle={`Dominance: ${(latestResult.behavioral_data.dominance_score * 100).toFixed(0)}%`}
                />

                <TelemetryCard
                  title="Acoustic (Pillar III)"
                  score={latestResult.pillar_scores[2]}
                  label="Environment Index"
                  subtitle={`Noise Elevation: ${(latestResult.acoustic_data.noise_elevation * 100).toFixed(0)}%`}
                />

                {/* Strategy Chart */}
                <div className="lg:col-span-3">
                  <StrategyChart
                    weights={latestResult.weights}
                    threatHistory={threatHistory}
                    strategyMetrics={strategyMetrics}
                  />
                </div>

                {/* Transcript */}
                <div className="lg:col-span-3">
                  <Transcript
                    transcripts={transcripts}
                    currentChunk={currentChunk}
                    threatLevel={getThreatLevel()}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
