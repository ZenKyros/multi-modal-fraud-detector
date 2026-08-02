import React, { useState, useRef } from 'react'
import { Mic, Upload, Square } from 'lucide-react'
import { uploadAudio, analyzeText } from '../services/api'
import GlassCard from './GlassCard'

export default function ControlPanel({
  connected,
  sendMessage,
  setTranscripts,
  setThreat,
  setHistory,
  setPosterior,
  setPillarScores,
  setAlert,
}) {
  const [recording, setRecording] = useState(false)
  const [processing, setProcessing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const wsRef = useRef(null) // we'll keep local ref to send chunks

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1]
            if (sendMessage) {
              sendMessage({
                type: 'audio_chunk',
                data: base64Audio,
              })
            }
          }
          reader.readAsDataURL(event.data)
        }
      }

      mediaRecorder.start(3000)
      setRecording(true)
    } catch (error) {
      console.error('Microphone error:', error)
      alert('Could not access microphone.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setRecording(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    setProcessing(true)
    try {
      const response = await uploadAudio(file)
      const data = response.data
      // Update parent state
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
      console.error('Upload error:', error)
      alert('Upload failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setProcessing(false)
      event.target.value = ''
    }
  }

  const handleTextAnalysis = async (e) => {
    const text = e.target.value
    if (!text.trim()) return
    setProcessing(true)
    try {
      const response = await analyzeText(text)
      const data = response.data
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
            speaker: 'User',
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
      console.error('Text analysis error:', error)
      alert('Analysis failed: ' + (error.response?.data?.detail || error.message))
    } finally {
      setProcessing(false)
      e.target.value = ''
    }
  }

  return (
    <GlassCard>
      <h2 className="font-bold text-xl mb-5">🎯 Input Center</h2>

      <button
        onClick={recording ? stopRecording : startRecording}
        disabled={!connected || processing}
        className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:shadow-2xl mb-4 ${
          recording
            ? 'bg-gradient-to-r from-red-500 to-rose-600 text-white'
            : 'bg-gradient-to-r from-purple-500 to-cyan-500 text-white'
        } ${(!connected || processing) && 'opacity-50 cursor-not-allowed'}`}
      >
        {recording ? <Square size={20} /> : <Mic size={20} />}
        {recording ? 'Stop Analysis' : 'Start Analysis'}
      </button>

      <label className={`w-full py-4 px-6 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg hover:shadow-2xl mb-4 ${processing && 'opacity-50 cursor-not-allowed'}`}>
        <Upload size={20} />
        {processing ? 'Processing...' : 'Upload Audio'}
        <input
          type="file"
          accept=".wav,.mp3,.m4a,.webm,.flac,.ogg"
          onChange={handleFileUpload}
          className="hidden"
          disabled={processing}
        />
      </label>

      <textarea
        placeholder="Paste conversation text here..."
        className="w-full h-24 bg-gray-50 border border-gray-200 rounded-xl p-3 text-sm text-gray-700 placeholder-gray-400 resize-none focus:outline-none focus:border-purple-500 transition-all"
        onBlur={handleTextAnalysis}
        disabled={processing}
      />
      <p className="text-xs text-gray-400 mt-1">Press Enter or click away to analyse</p>
    </GlassCard>
  )
}