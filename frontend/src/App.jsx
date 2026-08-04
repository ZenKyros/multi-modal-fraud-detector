import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";

import {
  FileText,
  Mic,
  Upload,
  AlertTriangle,
  ShieldCheck,
  Activity,
  ChevronDown,
  ArrowRight,
  X,
  Zap,
  Brain,
  BarChart3
} from "lucide-react";

const BASE_URL = "http://localhost:8000";

const decisionMeta = {
  CONTINUE:   { color: "emerald", text: "Safe",        icon: ShieldCheck },
  VERIFY:     { color: "yellow",  text: "Caution",     icon: AlertTriangle },
  WARN:       { color: "orange",  text: "Suspicious",  icon: AlertTriangle },
  HANG_UP:    { color: "red",     text: "Fraudulent",  icon: Zap },
  BLOCK:      { color: "red",     text: "Critical",    icon: AlertTriangle }   
};

function CircularGauge({ value, size = 160 }) {
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const color =
    value < 30 ? "#10b981" : value < 50 ? "#eab308" : value < 70 ? "#f97316" : "#ef4444";

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#1f2937" strokeWidth="12" />
        <motion.circle
          cx="80"
          cy="80"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <span className="absolute text-3xl font-bold text-white">{(value).toFixed(1)}%</span>
    </div>
  );
}

function App() {
  // input mode
  const [mode, setMode] = useState("text"); // text | live | upload

  // text input
  const [textTranscript, setTextTranscript] = useState("");

  // live audio state
  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscripts, setLiveTranscripts] = useState([]);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  // upload
  const [uploadedFile, setUploadedFile] = useState(null);

  // results
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  // accordion
  const [showDetails, setShowDetails] = useState(false);

  // cleanup websocket
  const cleanupWS = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const handleTextSubmit = async () => {
    if (!textTranscript.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const form = new FormData();
      form.append("transcript", textTranscript);
      const { data } = await axios.post(`${BASE_URL}/analyze-text`, form);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await axios.post(`${BASE_URL}/analyze-audio`, form);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const startLiveCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/ogg"
      });
      mediaRecorderRef.current = mediaRecorder;

      const ws = new WebSocket("ws://localhost:8000/ws/live-audio");
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected");
        mediaRecorder.start(300); // send chunk every 300ms
        setIsRecording(true);
      };

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
          ws.send(event.data);
        }
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "analysis" && data.result) {
          setResult(data.result);
          setLiveTranscripts(prev => [
            ...prev,
            { text: data.transcript, timestamp: Date.now() }
          ]);
        }
      };

      ws.onerror = (err) => console.error("WS error", err);
      ws.onclose = () => setIsRecording(false);
    } catch (err) {
      setError("Microphone access denied or not available.");
    }
  };

  const stopLiveCapture = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsRecording(false);
  };

  const toggleLiveAudio = () => {
    if (isRecording) {
      stopLiveCapture();
    } else {
      startLiveCapture();
    }
  };

  // clean up on unmount
  useEffect(() => {
    return () => cleanupWS();
  }, []);

  const riskScore = result?.analysis?.risk_score ? Math.round(result.analysis.risk_score * 100) : 0;
  const decision = result?.analysis?.decision || "CONTINUE";
  const meta = decisionMeta[decision] || decisionMeta.CONTINUE;
  const DecisionIcon = meta.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-white/10 bg-white/5 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="text-emerald-400" size={32} />
            <h1 className="text-xl font-bold">ScamCall <span className="text-emerald-400">Shield</span></h1>
          </div>
          <span className="text-sm text-gray-400">Real‑Time Fraud Detection</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Mode Selector */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white/5 p-1 rounded-xl backdrop-blur border border-white/10">
            {["text", "live", "upload"].map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${
                  mode === m ? "bg-emerald-500 text-white shadow-lg" : "text-gray-300 hover:text-white"
                }`}
              >
                {m === "text" && <FileText className="inline mr-2" size={16} />}
                {m === "live" && <Mic className="inline mr-2" size={16} />}
                {m === "upload" && <Upload className="inline mr-2" size={16} />}
                {m === "text" ? "Paste Transcript" : m === "live" ? "Live Audio" : "Upload File"}
              </button>
            ))}
          </div>
        </div>

        {/* Input Area */}
        <motion.div
          layout
          className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 mb-8 shadow-2xl"
        >
          <AnimatePresence mode="wait">
            {mode === "text" && (
              <motion.div
                key="text"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <textarea
                  value={textTranscript}
                  onChange={(e) => setTextTranscript(e.target.value)}
                  rows={6}
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-400 transition"
                  placeholder="Paste your conversation transcript here...&#10;e.g., Caller: Hello, I'm from HMRC..."
                />
                <button
                  onClick={handleTextSubmit}
                  disabled={loading}
                  className="mt-4 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 rounded-xl font-medium flex items-center gap-2 transition"
                >
                  {loading ? "Analyzing..." : "Analyze Transcript"}
                  <ArrowRight size={18} />
                </button>
              </motion.div>
            )}

            {mode === "live" && (
              <motion.div
                key="live"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-center"
              >
                <button
                  onClick={toggleLiveAudio}
                  disabled={loading}
                  className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto border-4 transition-all shadow-lg ${
                    isRecording
                      ? "bg-red-500 border-red-400 animate-pulse"
                      : "bg-emerald-500 border-emerald-400 hover:scale-105"
                  }`}
                >
                  <Mic size={36} className="text-white" />
                </button>
                <p className="mt-4 text-gray-300">
                  {isRecording ? "Recording... (speak now)" : "Click to start live audio demo"}
                </p>
                {liveTranscripts.length > 0 && (
                  <div className="mt-4 max-h-40 overflow-y-auto text-left">
                    {liveTranscripts.map((t, i) => (
                      <p key={i} className="text-gray-400 text-sm p-1 border-b border-white/5">{t.text}</p>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {mode === "upload" && (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <label className="flex flex-col items-center justify-center border-2 border-dashed border-white/20 rounded-xl p-12 cursor-pointer hover:border-emerald-400 transition">
                  <Upload size={40} className="text-gray-400 mb-2" />
                  <span className="text-gray-300">Click to upload audio file</span>
                  <span className="text-gray-500 text-sm">MP3, WAV, M4A supported</span>
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      setUploadedFile(file);
                      handleFileUpload(file);
                    }}
                  />
                </label>
                {uploadedFile && <p className="mt-2 text-gray-400 text-sm">{uploadedFile.name}</p>}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Results Section */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-400 mx-auto"></div>
              <p className="mt-4 text-gray-400">Analyzing conversation...</p>
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-500/20 border border-red-400 text-red-300 p-4 rounded-xl mb-8 flex items-center gap-2"
            >
              <AlertTriangle size={20} />
              {error}
            </motion.div>
          )}

          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Main Decision Card */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Risk Gauge */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 flex flex-col items-center justify-center shadow-2xl">
                  <CircularGauge value={riskScore} />
                  <p className="text-gray-400 mt-2 text-sm">Scam Probability</p>
                </div>

                {/* Decision */}
                <div className="col-span-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl flex flex-col justify-center">
                  <div className={`flex items-center gap-3 text-${meta.color}-400`}>
                    <DecisionIcon size={36} />
                    <h2 className="text-3xl font-bold capitalize">{decision.replace("_", " ")}</h2>
                  </div>
                  <p className="text-xl mt-2 text-gray-200">{meta.text}</p>
                  <p className="mt-4 text-gray-400">{result.analysis?.explanation}</p>
                  <div className="mt-4 flex gap-4">
                    <div className="bg-white/10 rounded-lg px-4 py-2">
                      <span className="text-sm text-gray-400">Scam Type</span>
                      <p className="font-semibold">{result.analysis?.scam_type || "none"}</p>
                    </div>
                    <div className="bg-white/10 rounded-lg px-4 py-2">
                      <span className="text-sm text-gray-400">Confidence</span>
                      <p className="font-semibold">{(result.analysis?.confidence * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Transcript Card */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <FileText size={18} /> Transcript
                </h3>
                <p className="text-gray-300 whitespace-pre-line max-h-60 overflow-y-auto">
                  {result.transcript || "No transcript available"}
                </p>
              </div>

              {/* Scam Indicators */}
              {result.analysis?.indicators?.length > 0 && (
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <AlertTriangle size={18} className="text-orange-400" /> Detected Indicators
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {result.analysis.indicators.map((ind, i) => (
                      <span
                        key={i}
                        className="bg-red-500/20 text-red-300 px-3 py-1 rounded-full text-sm border border-red-500/30"
                      >
                        {ind}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Analysis Accordion */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="w-full p-6 flex items-center justify-between text-left hover:bg-white/5 transition"
                >
                  <span className="font-semibold flex items-center gap-2">
                    <Activity size={18} /> Detailed Analysis
                  </span>
                  <motion.div animate={{ rotate: showDetails ? 180 : 0 }}>
                    <ChevronDown size={20} />
                  </motion.div>
                </button>
                <AnimatePresence>
                  {showDetails && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="px-6 pb-6 space-y-4"
                    >
                      {/* Rule Scanner */}
                      <div className="p-4 bg-white/5 rounded-xl">
                        <p className="font-medium text-emerald-400">Rule Scanner</p>
                        <p>Confidence: {result.details?.rule_scanner?.confidence}</p>
                        <p className="text-gray-400 text-sm">Matches: {result.details?.rule_scanner?.matched_rules?.join(", ") || "none"}</p>
                      </div>

                      {/* Linguistic */}
                      <div className="p-4 bg-white/5 rounded-xl">
                        <p className="font-medium text-emerald-400">Linguistic</p>
                        <p>Urgency Score: {result.details?.linguistic?.urgency_score}</p>
                        <p>Keywords: {result.details?.linguistic?.total_keyword_hits}</p>
                      </div>

                      {/* Acoustic */}
                      <div className="p-4 bg-white/5 rounded-xl">
                        <p className="font-medium text-emerald-400">Acoustic</p>
                        <p>Arousal: {result.details?.acoustic?.arousal_score}</p>
                        <p>Silence Ratio: {result.details?.acoustic?.silence_ratio}</p>
                      </div>

                      {/* Behavioral */}
                      <div className="p-4 bg-white/5 rounded-xl">
                        <p className="font-medium text-emerald-400">Behavioral</p>
                        <p>Dominance: {result.details?.behavioral?.dominance_ratio}</p>
                        <p>Interruptions: {result.details?.behavioral?.interruption_count}</p>
                      </div>

                      {/* LLM */}
                      <div className="p-4 bg-white/5 rounded-xl">
                        <p className="font-medium text-emerald-400">LLM Verifier</p>
                        <p>Probability: {result.details?.llm_raw?.scam_probability}</p>
                        <p>Type: {result.details?.llm_raw?.scam_type}</p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;