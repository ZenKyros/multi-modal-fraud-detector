import React, { useState, useEffect } from 'react'
import { Play, Pause, SkipBack, SkipForward, Zap } from 'lucide-react'
import axios from 'axios'
import LiveRecorder from './LiveRecorder'

/**
 * Sidebar Component
 * 
 * Controls for scenario selection, chunk navigation, and stream controls
 * Displays available audio files and allows manual chunk selection
 */
function Sidebar({
  selectedFile,
  onFileSelect,
  currentChunk,
  maxChunks,
  onChunkChange,
  onAnalyze,
  isAnalyzing,
  isConnected,
  autoPlay,
  onAutoPlayChange,
  onLiveRecording,
  onRecordingError,
}) {
  const [files, setFiles] = useState([])
  const [loadingFiles, setLoadingFiles] = useState(true)

  // Fetch available audio files
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/files`)
        setFiles(response.data.files || [])
      } catch (err) {
        console.error('Failed to fetch files:', err)
        setFiles([])
      } finally {
        setLoadingFiles(false)
      }
    }

    fetchFiles()
  }, [])

  return (
    <div className="flex flex-col h-full p-6 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-cyber-cyan mb-2">FRAUD DETECTOR</h1>
        <p className="text-xs text-gray-500 font-mono">Multi-Modal Real-Time Analysis Engine</p>

        {/* Connection Status */}
        <div className="mt-4 px-3 py-2 rounded bg-glass border border-glass flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-cyber-green animate-pulse' : 'bg-cyber-red'}`} />
          <span className="text-xs font-mono text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Live Recording */}
      <LiveRecorder 
        onDataAvailable={onLiveRecording}
        onError={onRecordingError}
        isAnalyzing={isAnalyzing}
      />

      {/* Scenarios / File Selection */}
      <div>
        <h2 className="text-sm font-mono font-bold text-cyber-cyan mb-3 uppercase">Scenarios</h2>
        <div className="space-y-2">
          {loadingFiles ? (
            <div className="text-xs text-gray-500 font-mono">Loading...</div>
          ) : files.length > 0 ? (
            files.map((file) => (
              <button
                key={file}
                onClick={() => onFileSelect(file)}
                className={`w-full text-left px-3 py-2 rounded font-mono text-sm transition-all ${
                  selectedFile === file
                    ? 'bg-cyber-blue text-white border border-cyber-blue'
                    : 'bg-glass text-gray-300 border border-glass hover:border-cyber-cyan hover:text-cyber-cyan'
                }`}
              >
                {file}
              </button>
            ))
          ) : (
            <div className="text-xs text-gray-500 font-mono">No audio files found</div>
          )}
        </div>
      </div>

      {/* Chunk Navigation */}
      <div>
        <h2 className="text-sm font-mono font-bold text-cyber-cyan mb-3 uppercase">
          Chunk Progress
        </h2>

        {/* Current chunk display */}
        <div className="px-3 py-2 rounded bg-glass border border-glass mb-3">
          <p className="text-xs text-gray-400 font-mono">
            Chunk {currentChunk + 1} / {maxChunks}
          </p>
          <div className="mt-2 w-full h-2 bg-cyber-darker rounded overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyber-blue to-cyber-cyan transition-all"
              style={{ width: `${maxChunks > 0 ? ((currentChunk + 1) / maxChunks) * 100 : 0}%` }}
            />
          </div>
        </div>

        {/* Chunk input */}
        <div className="flex gap-2 mb-3">
          <input
            type="number"
            min="0"
            max={Math.max(0, maxChunks - 1)}
            value={currentChunk}
            onChange={(e) => onChunkChange(Math.min(maxChunks - 1, Math.max(0, parseInt(e.target.value) || 0)))}
            className="cyber-input flex-1 text-center"
          />
          <button
            onClick={() => onChunkChange(Math.max(0, currentChunk - 1))}
            disabled={currentChunk === 0 || maxChunks === 0}
            className={`p-2 rounded transition-all ${
              currentChunk === 0 || maxChunks === 0
                ? 'bg-glass text-gray-500 cursor-not-allowed'
                : 'bg-glass hover:bg-cyber-blue hover:text-white text-gray-300'
            }`}
          >
            <SkipBack size={18} />
          </button>
          <button
            onClick={() => onChunkChange(Math.min(maxChunks - 1, currentChunk + 1))}
            disabled={currentChunk >= maxChunks - 1 || maxChunks === 0}
            className={`p-2 rounded transition-all ${
              currentChunk >= maxChunks - 1 || maxChunks === 0
                ? 'bg-glass text-gray-500 cursor-not-allowed'
                : 'bg-glass hover:bg-cyber-blue hover:text-white text-gray-300'
            }`}
          >
            <SkipForward size={18} />
          </button>
        </div>

        {/* Auto-play toggle */}
        <button
          onClick={() => onAutoPlayChange(!autoPlay)}
          className={`w-full px-3 py-2 rounded font-mono text-sm transition-all flex items-center justify-center gap-2 ${
            autoPlay
              ? 'bg-cyber-green/20 text-cyber-green border border-cyber-green'
              : 'bg-glass text-gray-400 border border-glass hover:border-cyber-cyan'
          }`}
        >
          {autoPlay ? <Pause size={16} /> : <Play size={16} />}
          {autoPlay ? 'Auto-play: ON' : 'Auto-play: OFF'}
        </button>
      </div>

      {/* Analysis Controls */}
      <div>
        <h2 className="text-sm font-mono font-bold text-cyber-cyan mb-3 uppercase">Analysis</h2>

        <button
          onClick={onAnalyze}
          disabled={!isConnected || isAnalyzing || maxChunks === 0}
          className={`w-full px-4 py-3 rounded font-mono font-bold text-base transition-all flex items-center justify-center gap-2 ${
            !isConnected || isAnalyzing || maxChunks === 0
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'cyber-button-primary hover:shadow-lg hover:shadow-cyber-blue'
          }`}
        >
          <Zap size={18} />
          {isAnalyzing ? 'ANALYZING...' : 'ANALYZE CHUNK'}
        </button>

        <p className="text-xs text-gray-500 font-mono mt-3 text-center">
          {maxChunks > 0
            ? `${maxChunks} total chunks (~${(maxChunks * 3).toFixed(0)}s duration)`
            : 'No audio file selected'}
        </p>
      </div>

      {/* Legend */}
      <div className="mt-auto pt-6 border-t border-glass">
        <h3 className="text-xs font-mono font-bold text-cyber-cyan mb-3 uppercase">Threat Levels</h3>
        <div className="space-y-2 text-xs font-mono">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-cyber-green" />
            <span className="text-gray-400">Safe (0 - 0.3)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-yellow-500" />
            <span className="text-gray-400">Medium (0.3 - 0.55)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-cyber-red" />
            <span className="text-gray-400">High (0.55 - 0.8)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-cyber-purple animate-pulse" />
            <span className="text-gray-400">Critical (0.8 - 1.0)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
