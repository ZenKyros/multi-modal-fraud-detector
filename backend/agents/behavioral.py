import librosa
import numpy as np
from typing import Dict, Any, Optional
import logging
import os
import tempfile
import subprocess

logger = logging.getLogger(__name__)

class BehavioralPillar:
    """
    Behavioral analysis pillar – extracts speaker dynamics:
    - Speaker dominance (energy consistency and high-energy ratio)
    - Volume pressure (dynamic range)
    - Speech/pause ratio (stress indicator)
    - Speaking rate (proxy for nervousness)
    """
    
    def __init__(self, sample_rate: int = 16000, frame_length: int = 2048, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length

    async def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze audio file for behavioral patterns.
        Returns:
            - speaker_dominance (float 0-1)
            - volume_pressure (float 0-1)
            - speech_pause_ratio (float 0-1)
            - speaking_rate (float 0-1)
            - pillar_score (float 0-1)
        """
        try:
            # Robust audio loading (same as acoustic)
            audio = self._load_audio(audio_path)
            if audio is None:
                return self._fallback_result("audio loading failed")
            if len(audio) == 0:
                return self._fallback_result("empty audio")

            # Compute metrics
            speaker_dominance = self._compute_speaker_dominance(audio)
            volume_pressure = self._compute_volume_pressure(audio)
            speech_pause_ratio = self._compute_speech_pause_ratio(audio)
            speaking_rate = self._compute_speaking_rate(audio)

            # Combine into pillar score (weighted)
            pillar_score = (
                0.3 * speaker_dominance +
                0.2 * volume_pressure +
                0.3 * speech_pause_ratio +
                0.2 * speaking_rate
            )
            pillar_score = max(0.0, min(1.0, pillar_score))

            return {
                "speaker_dominance": speaker_dominance,
                "volume_pressure": volume_pressure,
                "speech_pause_ratio": speech_pause_ratio,
                "speaking_rate": speaking_rate,
                "pillar_score": pillar_score,
            }

        except Exception as e:
            logger.error(f"Behavioral analysis error: {str(e)}")
            return self._fallback_result(f"analysis error: {str(e)}")

    # ----------------------------------------------------------------------
    # AUDIO LOADING (same as acoustic.py)
    # ----------------------------------------------------------------------
    def _load_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """Load audio with multiple fallback methods."""
        if not os.path.exists(audio_path):
            logger.error(f"File not found: {audio_path}")
            return None

        # Method 1: librosa
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with librosa: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.warning(f"librosa load failed: {e}")

        # Method 2: pydub + ffmpeg
        try:
            from pydub import AudioSegment
            import io
            audio_seg = AudioSegment.from_file(audio_path)
            audio_seg = audio_seg.set_frame_rate(self.sample_rate).set_channels(1)
            wav_io = io.BytesIO()
            audio_seg.export(wav_io, format='wav')
            wav_io.seek(0)
            audio, sr = librosa.load(wav_io, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with pydub: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.warning(f"pydub load failed: {e}")

        # Method 3: ffmpeg direct conversion
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', '1',
                tmp_path,
                '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise Exception(f"ffmpeg error: {result.stderr}")
            audio, sr = librosa.load(tmp_path, sr=self.sample_rate, mono=True)
            os.unlink(tmp_path)
            logger.info(f"Loaded with ffmpeg: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.error(f"All audio loading methods failed: {e}")
            return None

    # ----------------------------------------------------------------------
    # BEHAVIORAL METRICS
    # ----------------------------------------------------------------------
    def _compute_speaker_dominance(self, audio: np.ndarray) -> float:
        """
        Speaker dominance: energy consistency and high-energy ratio.
        """
        try:
            energy = librosa.feature.rms(y=audio, frame_length=self.frame_length,
                                         hop_length=self.hop_length)
            energy_flat = energy.flatten()
            if len(energy_flat) == 0:
                return 0.0
            mean_energy = np.mean(energy_flat)
            std_energy = np.std(energy_flat)
            # High-energy ratio (energy > mean+0.5*std)
            high_energy_ratio = np.sum(energy_flat > (mean_energy + 0.5 * std_energy)) / len(energy_flat)
            dominance = min(1.0, high_energy_ratio * 2.0)
            return float(dominance)
        except Exception as e:
            logger.warning(f"Speaker dominance error: {e}")
            return 0.0

    def _compute_volume_pressure(self, audio: np.ndarray) -> float:
        """
        Volume pressure: dynamic range of RMS (in dB).
        """
        try:
            rms = librosa.feature.rms(y=audio, frame_length=self.frame_length,
                                      hop_length=self.hop_length)
            rms_flat = rms.flatten()
            if len(rms_flat) == 0:
                return 0.0
            # Convert to dB
            rms_db = librosa.amplitude_to_db(rms_flat, ref=np.max)
            dynamic_range = np.max(rms_db) - np.min(rms_db)
            # Normalise: typical range 0-60 dB
            pressure = min(1.0, dynamic_range / 60.0)
            return float(pressure)
        except Exception as e:
            logger.warning(f"Volume pressure error: {e}")
            return 0.0

    def _compute_speech_pause_ratio(self, audio: np.ndarray) -> float:
        """
        Speech/pause ratio: detects silence via energy threshold.
        Returns stress indicator (0-1) where high values mean unusual pause pattern.
        """
        try:
            energy = librosa.feature.rms(y=audio, frame_length=self.frame_length,
                                         hop_length=self.hop_length)
            energy_flat = energy.flatten()
            if len(energy_flat) == 0:
                return 0.0
            threshold = np.max(energy_flat) * 0.15
            speech_frames = energy_flat > threshold
            if len(speech_frames) == 0:
                return 0.0
            speech_ratio = np.sum(speech_frames) / len(speech_frames)
            pause_ratio = 1.0 - speech_ratio

            # Stress: too much speech (aggressive) or too many pauses (nervous)
            if pause_ratio < 0.1:
                stress = 0.8
            elif pause_ratio > 0.5:
                stress = 0.6
            else:
                stress = 0.2
            return float(stress)
        except Exception as e:
            logger.warning(f"Speech/pause ratio error: {e}")
            return 0.0

    def _compute_speaking_rate(self, audio: np.ndarray) -> float:
        """
        Speaking rate estimate via zero‑crossing rate (higher ZCR => faster speech).
        Normalized to 0-1.
        """
        try:
            zcr = librosa.feature.zero_crossing_rate(audio, frame_length=self.frame_length,
                                                     hop_length=self.hop_length)
            zcr_mean = np.mean(zcr)
            # Typical ZCR for speech: 0.02-0.2; normalize to 0-1
            rate = min(1.0, zcr_mean * 5.0)
            return float(rate)
        except Exception as e:
            logger.warning(f"Speaking rate error: {e}")
            return 0.0

    def _fallback_result(self, error_msg: str = "unknown error") -> Dict[str, Any]:
        """Return safe fallback values when analysis fails."""
        return {
            "speaker_dominance": 0.0,
            "volume_pressure": 0.0,
            "speech_pause_ratio": 0.0,
            "speaking_rate": 0.0,
            "pillar_score": 0.0,
            "error": error_msg
        }