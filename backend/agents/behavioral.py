"""
Pillar II: Behavioral Agent - Speaker Dominance & Conversational Pressure

Uses Librosa to extract audio features that signal aggressive call center behavior:
- Speaker dominance: duration of caller speech vs. pauses
- Volume pressure: consistent high energy indicating aggression/pressure
- Speech-to-pause ratios: minimal pause time (not letting user speak)
- Energy variability: sudden spikes indicating aggressive statements

All processing runs locally on CPU without GPU requirements.
"""

import numpy as np
import librosa
from typing import Dict, List, Optional, Tuple
from scipy import signal


class BehavioralAgent:
    """Speaker behavior analysis using local Librosa features."""

    def __init__(self):
        """Initialize the behavioral agent."""
        self.energy_history: List[float] = []
        self.dominance_history: List[float] = []

    def _extract_energy_features(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Extract short-time energy features to detect volume pressure.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with energy statistics
        """
        # Short-time energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = np.array([
            np.sum(frame ** 2) for frame in librosa.util.frame(
                audio_chunk, frame_length=frame_length, hop_length=hop_length
            )
        ])
        
        # Normalize energy
        if np.max(energy) > 0:
            energy_normalized = energy / np.max(energy)
        else:
            energy_normalized = energy
        
        # Detect speech frames (threshold at 0.02)
        speech_threshold = 0.02
        speech_frames = energy_normalized > speech_threshold
        
        if len(speech_frames) == 0:
            return {
                "mean_energy": 0.0,
                "max_energy": 0.0,
                "energy_std": 0.0,
                "energy_peaks": 0,
                "volume_pressure": 0.0,
            }
        
        # Energy statistics
        mean_energy = np.mean(energy_normalized[speech_frames]) if np.any(speech_frames) else 0.0
        max_energy = np.max(energy_normalized) if len(energy_normalized) > 0 else 0.0
        std_energy = np.std(energy_normalized[speech_frames]) if np.any(speech_frames) else 0.0
        
        # Detect energy peaks (sudden spikes)
        peaks, _ = signal.find_peaks(energy_normalized, height=np.mean(energy_normalized) + np.std(energy_normalized))
        energy_peaks = len(peaks)
        
        # Volume pressure: high mean energy + high peaks = aggressive
        volume_pressure = min((mean_energy * 0.5 + max_energy * 0.5), 1.0)
        
        return {
            "mean_energy": float(mean_energy),
            "max_energy": float(max_energy),
            "energy_std": float(std_energy),
            "energy_peaks": int(energy_peaks),
            "volume_pressure": float(volume_pressure),
        }

    def _extract_voice_activity(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Detect voice activity and speech-to-pause ratios.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with voice activity metrics
        """
        # Compute RMS energy for VAD
        rms = librosa.feature.rms(y=audio_chunk, frame_length=2048, hop_length=512)[0]
        
        # Threshold for voice activity (adaptive)
        threshold = np.mean(rms) + np.std(rms)
        voice_frames = rms > threshold
        
        if len(voice_frames) == 0:
            return {
                "voice_ratio": 0.0,
                "pause_count": 0,
                "avg_pause_duration": 0.0,
                "dominance_score": 0.0,
            }
        
        # Voice activity ratio
        voice_ratio = np.sum(voice_frames) / len(voice_frames) if len(voice_frames) > 0 else 0.0
        
        # Find pauses (consecutive frames without voice)
        voice_bool = voice_frames.astype(int)
        pause_starts = np.where(np.diff(voice_bool) == -1)[0]
        pause_ends = np.where(np.diff(voice_bool) == 1)[0]
        
        pause_count = len(pause_starts)
        
        if pause_count > 0:
            pause_durations = (pause_ends[:len(pause_starts)] - pause_starts) * 512 / sr
            avg_pause_duration = float(np.mean(pause_durations))
        else:
            avg_pause_duration = 0.0
        
        # Dominance score: high voice ratio + short pauses = dominating speaker
        # (Not letting the other person speak)
        dominance_score = min(voice_ratio * 0.7 + (1.0 - min(avg_pause_duration / 0.5, 1.0)) * 0.3, 1.0)
        
        self.dominance_history.append(dominance_score)
        if len(self.dominance_history) > 10:
            self.dominance_history.pop(0)
        
        return {
            "voice_ratio": float(voice_ratio),
            "pause_count": int(pause_count),
            "avg_pause_duration": float(avg_pause_duration),
            "dominance_score": float(dominance_score),
        }

    def _extract_spectral_features(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Extract spectral features indicating speech patterns.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with spectral metrics
        """
        # MFCC features for speech characterization
        mfcc = librosa.feature.mfcc(y=audio_chunk, sr=sr, n_mfcc=13)
        
        # Spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_chunk, sr=sr)[0]
        
        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_chunk, sr=sr)[0]
        
        # MFCC statistics
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        # Jitter-like metric: variability in energy
        energy_variance = np.std(librosa.feature.rms(y=audio_chunk, frame_length=2048, hop_length=512)[0])
        
        return {
            "spectral_centroid_mean": float(np.mean(spectral_centroid)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "mfcc_variance": float(np.mean(mfcc_std)),
            "energy_variance": float(energy_variance),
        }

    def _compute_aggression_index(
        self,
        energy_features: Dict,
        voice_features: Dict,
        spectral_features: Dict
    ) -> float:
        """
        Compute an overall aggression/pressure index from behavioral features.
        
        Args:
            energy_features: Output from _extract_energy_features
            voice_features: Output from _extract_voice_activity
            spectral_features: Output from _extract_spectral_features
            
        Returns:
            Aggression score from 0.0 to 1.0
        """
        # Weights for different behavioral indicators
        volume_weight = 0.35  # High volume suggests aggression
        dominance_weight = 0.40  # Not letting other person speak
        spectral_weight = 0.25  # Voice characteristics
        
        # Combine features
        volume_component = energy_features["volume_pressure"] * volume_weight
        dominance_component = voice_features["dominance_score"] * dominance_weight
        
        # Spectral pressure: high energy variance + low pause suggests stress
        spectral_pressure = (
            spectral_features["energy_variance"] / (1.0 + spectral_features["energy_variance"]) * 0.5 +
            (1.0 - min(voice_features["avg_pause_duration"] / 0.5, 1.0)) * 0.5
        )
        spectral_component = spectral_pressure * spectral_weight
        
        aggression_index = volume_component + dominance_component + spectral_component
        return float(np.clip(aggression_index, 0.0, 1.0))

    def get_behavioral_trend(self) -> float:
        """
        Get trend of behavioral aggression over recent chunks.
        
        Returns:
            Trend from -1.0 (improving) to 1.0 (worsening)
        """
        if len(self.dominance_history) < 2:
            return 0.0
        
        recent = self.dominance_history[-5:]
        if len(recent) < 2:
            return 0.0
        
        trend = (recent[-1] - recent[0]) / len(recent) * 10
        return float(np.clip(trend, -1.0, 1.0))

    async def process_chunk(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int,
        chunk_index: int
    ) -> Dict:
        """
        Full behavioral analysis pipeline for audio chunk.
        
        Args:
            audio_chunk: Audio samples
            sample_rate: Sample rate
            chunk_index: Chunk sequence number
            
        Returns:
            Dictionary with behavioral analysis results
        """
        energy_features = self._extract_energy_features(audio_chunk, sample_rate)
        voice_features = self._extract_voice_activity(audio_chunk, sample_rate)
        spectral_features = self._extract_spectral_features(audio_chunk, sample_rate)
        
        aggression_score = self._compute_aggression_index(
            energy_features, voice_features, spectral_features
        )
        
        return {
            "pillar": "behavioral",
            "chunk_index": chunk_index,
            "aggression_score": aggression_score,
            "behavioral_trend": float(self.get_behavioral_trend()),
            "energy_features": energy_features,
            "voice_features": voice_features,
            "spectral_features": spectral_features,
        }
