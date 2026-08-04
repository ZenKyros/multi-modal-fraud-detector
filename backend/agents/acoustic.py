# agents/acoustic.py
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AcousticAgent:
    """
    Extracts acoustic features from audio waveform.
    Requires numpy array of audio samples.
    """
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def analyze(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        audio_data: 1D numpy array of audio samples (16kHz mono)
        Returns: speech_rate, energy, pitch_variation, silence_ratio
        """
        if audio_data is None or len(audio_data) == 0:
            return self._empty_result()

        try:
            # Simple energy (RMS)
            rms = np.sqrt(np.mean(audio_data**2))
            # Zero-crossing rate (proxy for pitch)
            zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
            # Speech rate estimate: we need segments to compute, so here we just return raw features
            # In full pipeline, we might use VAD to get speech segments, but for simplicity:
            duration = len(audio_data) / self.sr
            # Count non-silent frames
            frame_len = int(0.02 * self.sr)
            energy = np.array([np.sum(audio_data[i:i+frame_len]**2) for i in range(0, len(audio_data)-frame_len, frame_len)])
            silent_frames = np.sum(energy < np.mean(energy)*0.1)
            total_frames = len(energy)
            silence_ratio = silent_frames / total_frames if total_frames > 0 else 0

            return {
                "duration_sec": round(duration, 2),
                "rms_energy": round(float(rms), 6),
                "zcr": round(float(zcr), 6),
                "silence_ratio": round(silence_ratio, 3),
                # Heuristic arousal score: high energy + low silence => urgency?
                "arousal_score": round(min(1.0, (rms*10 + (1-silence_ratio))), 3)
            }
        except Exception as e:
            logger.error(f"Acoustic analysis error: {e}")
            return self._empty_result()

    def _empty_result(self):
        return {
            "duration_sec": 0,
            "rms_energy": 0,
            "zcr": 0,
            "silence_ratio": 1.0,
            "arousal_score": 0.0
        }