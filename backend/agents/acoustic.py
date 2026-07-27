"""
Pillar III: Acoustic Agent - Background Noise & Environment Signature

Detects acoustic signatures that distinguish high-density fraud call centers
from domestic/legitimate call environments:

- Noise uniformity: Constant ambient noise (HVAC, room tone) typical of call centers
- Spectral flatness: Distinguishes white-noise-like artifacts from natural speech
- Multi-speaker echo: Overlapping speech patterns from call center density
- Baseline noise floor: Elevation above typical home environments

All processing runs locally on CPU via Librosa.
"""

import numpy as np
import librosa
from scipy import signal
from typing import Dict, List, Optional


class AcousticAgent:
    """Environment acoustic analysis for fraud center detection."""

    def __init__(self):
        """Initialize the acoustic agent."""
        self.noise_floor_history: List[float] = []
        self.environment_consistency: List[float] = []

    def _extract_noise_floor(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Estimate the background noise floor.
        
        Fraud call centers typically have elevated, consistent noise floors
        from HVAC, multiple speakers, background chatter.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with noise floor metrics
        """
        # Compute RMS energy in 100ms windows
        frame_length = int(0.1 * sr)
        rms = librosa.feature.rms(y=audio_chunk, frame_length=frame_length, hop_length=frame_length // 2)[0]
        
        if len(rms) == 0:
            return {
                "noise_floor": 0.0,
                "noise_floor_std": 0.0,
                "noise_elevation": 0.0,
            }
        
        # Noise floor is approximately the minimum energy level (quietest parts)
        noise_floor = float(np.percentile(rms, 25))  # Lower quartile as noise estimate
        noise_floor_std = float(np.std(rms))
        
        # Elevation: how much above the typical home environment baseline (~0.001 for silence)
        home_baseline = 0.01
        noise_elevation = max((noise_floor - home_baseline) / home_baseline, 0.0)
        noise_elevation = float(np.clip(noise_elevation, 0.0, 1.0))
        
        self.noise_floor_history.append(noise_floor)
        if len(self.noise_floor_history) > 10:
            self.noise_floor_history.pop(0)
        
        return {
            "noise_floor": noise_floor,
            "noise_floor_std": noise_floor_std,
            "noise_elevation": noise_elevation,
        }

    def _extract_spectral_flatness(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Compute spectral flatness to detect uniform noise vs. tonal speech.
        
        High spectral flatness indicates noise-like signal (fraud center background).
        Low spectral flatness indicates tonal content (normal speech).
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with spectral flatness metrics
        """
        # Compute Short-Time Fourier Transform
        D = librosa.stft(audio_chunk)
        S = np.abs(D)
        
        # Spectral flatness: ratio of geometric mean to arithmetic mean
        # High value = flat spectrum (noise-like)
        # Low value = peaked spectrum (speech-like)
        
        eps = 1e-10
        geometric_mean = np.exp(np.mean(np.log(S + eps), axis=0))
        arithmetic_mean = np.mean(S, axis=0)
        
        spectral_flatness = geometric_mean / (arithmetic_mean + eps)
        spectral_flatness = np.clip(spectral_flatness, 0.0, 1.0)
        
        # Statistics
        mean_flatness = float(np.mean(spectral_flatness))
        max_flatness = float(np.max(spectral_flatness))
        high_flatness_ratio = float(np.sum(spectral_flatness > 0.5) / len(spectral_flatness))
        
        return {
            "mean_spectral_flatness": mean_flatness,
            "max_spectral_flatness": max_flatness,
            "high_flatness_ratio": high_flatness_ratio,
        }

    def _extract_zero_crossing_rate(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Compute zero-crossing rate to detect noise characteristics.
        
        Fraud call centers have elevated ZCR from background noise and overlapping speakers.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with ZCR metrics
        """
        zcr = librosa.feature.zero_crossing_rate(audio_chunk)[0]
        
        mean_zcr = float(np.mean(zcr))
        std_zcr = float(np.std(zcr))
        max_zcr = float(np.max(zcr)) if len(zcr) > 0 else 0.0
        
        # Normalize for interpretation
        # Typical speech: ~0.1, noise: ~0.3-0.5
        normalized_zcr = float(np.clip(mean_zcr / 0.3, 0.0, 1.0))
        
        return {
            "mean_zcr": mean_zcr,
            "std_zcr": std_zcr,
            "max_zcr": max_zcr,
            "normalized_zcr": normalized_zcr,
        }

    def _detect_overlapping_speech(self, audio_chunk: np.ndarray, sr: int) -> Dict:
        """
        Detect signatures of overlapping speech (multiple speakers simultaneously).
        
        Call center environments often have background speech/chatter.
        
        Args:
            audio_chunk: Audio samples
            sr: Sample rate
            
        Returns:
            Dictionary with overlapping speech indicators
        """
        # Compute MFCC to characterize spectral content
        mfcc = librosa.feature.mfcc(y=audio_chunk, sr=sr, n_mfcc=13)
        
        # Compute spectral entropy: high entropy suggests complex/overlapping signals
        S = np.abs(librosa.stft(audio_chunk))
        S_norm = S / (np.sum(S, axis=0, keepdims=True) + 1e-10)
        
        entropy = -np.sum(S_norm * np.log2(S_norm + 1e-10), axis=0)
        mean_entropy = float(np.mean(entropy))
        max_entropy = float(np.max(entropy)) if len(entropy) > 0 else 0.0
        
        # Normalized entropy (0-1 scale, higher = more complex/overlapping)
        max_theoretical_entropy = np.log2(S.shape[0])
        normalized_entropy = float(mean_entropy / max_theoretical_entropy) if max_theoretical_entropy > 0 else 0.0
        normalized_entropy = float(np.clip(normalized_entropy, 0.0, 1.0))
        
        # Chroma features: tonal consistency
        chroma = librosa.feature.chroma_stft(y=audio_chunk, sr=sr)
        chroma_std = float(np.std(chroma))
        
        return {
            "mean_entropy": mean_entropy,
            "max_entropy": max_entropy,
            "normalized_entropy": normalized_entropy,
            "chroma_std": chroma_std,
        }

    def _compute_environment_index(
        self,
        noise_floor_features: Dict,
        spectral_flatness: Dict,
        zcr_features: Dict,
        speech_overlap: Dict
    ) -> float:
        """
        Compute an overall environment (call center vs. home) index.
        
        Higher score indicates fraud call center environment characteristics.
        
        Args:
            noise_floor_features: From _extract_noise_floor
            spectral_flatness: From _extract_spectral_flatness
            zcr_features: From _extract_zero_crossing_rate
            speech_overlap: From _detect_overlapping_speech
            
        Returns:
            Environment score from 0.0 (home) to 1.0 (call center)
        """
        # Weight different indicators
        noise_weight = 0.25        # Elevated noise floor
        flatness_weight = 0.25     # Uniform spectral content
        zcr_weight = 0.20          # High ZCR from background chatter
        entropy_weight = 0.30      # Complex overlapping signals
        
        noise_component = noise_floor_features["noise_elevation"] * noise_weight
        flatness_component = spectral_flatness["high_flatness_ratio"] * flatness_weight
        zcr_component = zcr_features["normalized_zcr"] * zcr_weight
        entropy_component = speech_overlap["normalized_entropy"] * entropy_weight
        
        environment_index = noise_component + flatness_component + zcr_component + entropy_component
        environment_index = float(np.clip(environment_index, 0.0, 1.0))
        
        self.environment_consistency.append(environment_index)
        if len(self.environment_consistency) > 10:
            self.environment_consistency.pop(0)
        
        return environment_index

    def get_environment_trend(self) -> float:
        """
        Get trend of environment characteristics over recent chunks.
        
        Returns:
            Trend from -1.0 (improving) to 1.0 (worsening toward call center)
        """
        if len(self.environment_consistency) < 2:
            return 0.0
        
        recent = self.environment_consistency[-5:]
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
        Full acoustic analysis pipeline for audio chunk.
        
        Args:
            audio_chunk: Audio samples
            sample_rate: Sample rate
            chunk_index: Chunk sequence number
            
        Returns:
            Dictionary with acoustic analysis results
        """
        noise_floor_features = self._extract_noise_floor(audio_chunk, sample_rate)
        spectral_flatness = self._extract_spectral_flatness(audio_chunk, sample_rate)
        zcr_features = self._extract_zero_crossing_rate(audio_chunk, sample_rate)
        speech_overlap = self._detect_overlapping_speech(audio_chunk, sample_rate)
        
        environment_index = self._compute_environment_index(
            noise_floor_features, spectral_flatness, zcr_features, speech_overlap
        )
        
        return {
            "pillar": "acoustic",
            "chunk_index": chunk_index,
            "environment_index": environment_index,
            "environment_trend": float(self.get_environment_trend()),
            "noise_floor_features": noise_floor_features,
            "spectral_flatness": spectral_flatness,
            "zcr_features": zcr_features,
            "speech_overlap": speech_overlap,
        }
