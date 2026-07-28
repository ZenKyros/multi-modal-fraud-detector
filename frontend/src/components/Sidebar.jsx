import React, { useRef } from 'react'

const Sidebar = ({ isRecording, isConnected, onToggleRecording, onFileUpload, isProcessing }) => {
  const fileInputRef = useRef(null)

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      onFileUpload(file)
    }
    event.target.value = null
  }

  return (
    <div className="w-72 min-h-screen bg-gradient-to-b from-slate-900/95 via-purple-900/40 to-slate-900/95 backdrop-blur-xl border-r border-white/10 shadow-2xl flex flex-col p-6">
      {/* Brand */}
      <div className="mb-8">
        <h1 className="text-2xl font-extrabold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
          FraudDetect
        </h1>
        <p className="text-xs text-white/40 mt-1 tracking-widest">GAME‑THEORETIC FUSION</p>
      </div>

      {/* Connection status */}
      <div className="flex items-center gap-2 mb-6 bg-white/5 rounded-full px-4 py-2 border border-white/10">
        <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
        <span className="text-sm text-white/70">{isConnected ? 'Connected' : 'Disconnected'}</span>
        <span className="ml-auto text-xs text-white/30">{isConnected ? '● Live' : '● Offline'}</span>
      </div>

      {/* Record button */}
      <button
        onClick={onToggleRecording}
        disabled={!isConnected}
        className={`
          w-full py-3.5 rounded-xl font-semibold text-white transition-all duration-300
          ${isRecording 
            ? 'bg-gradient-to-r from-red-500 to-rose-500 shadow-lg shadow-red-500/30 hover:shadow-red-500/50' 
            : 'bg-gradient-to-r from-cyan-500 to-blue-500 shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50'
          }
          ${!isConnected && 'opacity-50 cursor-not-allowed grayscale'}
        `}
      >
        {isRecording ? '⏹ Stop Analysis' : '🎤 Start Analysis'}
      </button>

      {/* File upload */}
      <div className="mt-6 border-t border-white/10 pt-6">
        <p className="text-xs text-white/40 uppercase tracking-wider mb-3">Upload Audio</p>
        <label
          className={`
            flex flex-col items-center justify-center w-full p-4 border-2 border-dashed rounded-xl cursor-pointer
            transition-all duration-200
            ${isProcessing ? 'border-amber-400/50 bg-amber-400/10' : 'border-white/20 hover:border-cyan-400/50 hover:bg-white/5'}
            ${(isRecording || !isConnected) && 'opacity-50 pointer-events-none'}
          `}
        >
          <div className="text-2xl mb-1">📁</div>
          <span className="text-xs text-white/60 text-center">
            {isProcessing ? 'Processing...' : 'Click or drag MP3, WAV'}
          </span>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".wav,.mp3,.m4a,.webm,.flac,.ogg"
            className="hidden"
            disabled={isRecording || !isConnected || isProcessing}
          />
        </label>
        {isProcessing && (
          <div className="mt-2 flex items-center gap-2 text-amber-400 text-xs">
            <span className="animate-spin">⏳</span> Analysing audio...
          </div>
        )}
      </div>

      {/* Status panel */}
      <div className="mt-auto pt-6 border-t border-white/10">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-white/5 rounded-lg p-3">
            <span className="text-white/40 block">Analysis</span>
            <span className={isRecording ? 'text-emerald-400' : 'text-white/60'}>
              {isRecording ? '● Active' : '○ Idle'}
            </span>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <span className="text-white/40 block">Upload</span>
            <span className={isProcessing ? 'text-amber-400' : 'text-white/60'}>
              {isProcessing ? '⏳ Processing' : '✓ Ready'}
            </span>
          </div>
        </div>
        <div className="mt-4 text-[10px] text-white/20 text-center">
          v1.0.0 · 3‑Pillar Fusion · Nash Equilibrium
        </div>
      </div>
    </div>
  )
}

export default Sidebar