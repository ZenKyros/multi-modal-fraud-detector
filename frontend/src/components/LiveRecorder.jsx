import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Play, AlertCircle } from 'lucide-react';

const LiveRecorder = ({ onDataAvailable, onError, isAnalyzing }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [error, setError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: false,
        },
      });
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4';
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const reader = new FileReader();
        reader.onload = () => {
          const audioData = reader.result;
          onDataAvailable({
            audio: audioData,
            duration: recordingDuration,
            timestamp: new Date().toISOString(),
            format: mimeType,
          });
        };
        reader.readAsArrayBuffer(blob);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.onerror = (event) => {
        const errorMsg = `Recording error: ${event.error}`;
        setError(errorMsg);
        onError?.(errorMsg);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingDuration(0);

      // Timer for recording duration
      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 0.1);
      }, 100);
    } catch (err) {
      const errorMsg =
        err.name === 'NotAllowedError'
          ? 'Microphone access denied. Please allow microphone permissions.'
          : `Failed to access microphone: ${err.message}`;
      setError(errorMsg);
      onError?.(errorMsg);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="cyber-card p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-cyan-400 font-mono font-bold text-sm">
          📡 LIVE RECORDING
        </h3>
        {isRecording && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-red-400 font-mono text-xs">
              {formatTime(recordingDuration)}
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-500 rounded px-3 py-2 mb-3 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-300 text-xs font-mono">{error}</p>
        </div>
      )}

      <div className="flex gap-2">
        {!isRecording ? (
          <button
            onClick={startRecording}
            disabled={isAnalyzing}
            className="flex-1 cyber-button bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Mic className="w-4 h-4" />
            <span>Start Recording</span>
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex-1 cyber-button bg-gradient-to-r from-red-500 to-orange-600 hover:from-red-400 hover:to-orange-500 flex items-center justify-center gap-2"
          >
            <Square className="w-4 h-4" />
            <span>Stop Recording</span>
          </button>
        )}
      </div>

      <div className="mt-3 text-xs text-gray-400 font-mono">
        <p>💡 Tip: Click "Start Recording" to capture live audio from your microphone</p>
        <p>Once stopped, recording will be automatically queued for analysis</p>
      </div>
    </div>
  );
};

export default LiveRecorder;
