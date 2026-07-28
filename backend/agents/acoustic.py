import librosa
import numpy as np
from typing import Dict, Any, Optional
import logging
import os
import tempfile
import subprocess

logger = logging.getLogger(__name__)

class AcousticPillar:
    """
    Acoustic analysis pillar – classifies background environment,
    extracts spectral features, and estimates noise characteristics.
    """
    
    def __init__(self, sample_rate: int = 16000, frame_length: int = 2048, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length
        
        # Thresholds for fraud detection (tunable)
        self.fraud_call_center_noise_floor_threshold = 0.15
        self.fraud_spectral_variance_threshold = 0.3
        self.fraud_background_complexity_threshold = 0.4
        
    async def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze audio file for acoustic features and background classification.
        Returns:
            - noise_floor (float 0-1)
            - spectral_features (float 0-1)
            - background_classification (float 0-1)
            - environment_type (str)
            - pillar_score (float 0-1)
        """
        try:
            # Load audio with robust fallback
            audio = self._load_audio(audio_path)
            if audio is None:
                return self._fallback_result("audio loading failed")
            
            if len(audio) == 0:
                logger.warning("Audio file is empty")
                return self._fallback_result("empty audio")

            # Extract features
            features = self._extract_features(audio)
            
            # Calculate noise floor
            noise_floor = self._compute_noise_floor(audio)
            
            # Compute spectral features
            spectral_score = self._compute_spectral_score(features)
            
            # Background classification
            background_score = self._classify_background(audio, features, noise_floor)
            
            # Determine environment type
            environment_type = "fraud_center" if background_score > 0.5 else "domestic"
            
            # Combine into pillar score (weighted)
            pillar_score = (
                0.4 * background_score +
                0.3 * spectral_score +
                0.3 * noise_floor
            )
            pillar_score = max(0.0, min(1.0, pillar_score))
            
            return {
                "noise_floor": noise_floor,
                "spectral_features": spectral_score,
                "background_classification": background_score,
                "environment_type": environment_type,
                "pillar_score": pillar_score,
                "feature_details": features
            }
            
        except Exception as e:
            logger.error(f"Acoustic analysis error: {str(e)}")
            return self._fallback_result(f"analysis error: {str(e)}")
    
    def _load_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Load audio with multiple fallback methods.
        Returns numpy array (float32) or None on failure.
        """
        # Check if file exists
        if not os.path.exists(audio_path):
            logger.error(f"File not found: {audio_path}")
            return None
        
        # Method 1: Direct librosa (works for WAV, FLAC)
        try:
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with librosa: {len(audio)} samples, sr={sr}")
            return audio
        except Exception as e:
            logger.warning(f"librosa load failed: {e}")
        
        # Method 2: Try pydub (requires ffmpeg, works for MP3, M4A, etc.)
        try:
            from pydub import AudioSegment
            import io
            audio_seg = AudioSegment.from_file(audio_path)
            audio_seg = audio_seg.set_frame_rate(self.sample_rate).set_channels(1)
            # Export to in-memory WAV
            wav_io = io.BytesIO()
            audio_seg.export(wav_io, format='wav')
            wav_io.seek(0)
            audio, sr = librosa.load(wav_io, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with pydub: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.warning(f"pydub load failed: {e}")
        
        # Method 3: Use ffmpeg directly to convert to temp WAV
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
    
    def _extract_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract a comprehensive set of acoustic features."""
        features = {}
        try:
            # Zero-crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio, frame_length=self.frame_length, hop_length=self.hop_length)
            features['zcr_mean'] = float(np.mean(zcr))
            features['zcr_std'] = float(np.std(zcr))
            
            # Spectral centroid
            centroid = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate, 
                                                         n_fft=self.frame_length, hop_length=self.hop_length)
            features['spectral_centroid_mean'] = float(np.mean(centroid))
            features['spectral_centroid_std'] = float(np.std(centroid))
            
            # Spectral bandwidth
            bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate,
                                                           n_fft=self.frame_length, hop_length=self.hop_length)
            features['spectral_bandwidth_mean'] = float(np.mean(bandwidth))
            
            # Spectral rolloff
            rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate,
                                                       n_fft=self.frame_length, hop_length=self.hop_length)
            features['spectral_rolloff_mean'] = float(np.mean(rolloff))
            
            # MFCCs (13 coefficients)
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13,
                                         n_fft=self.frame_length, hop_length=self.hop_length)
            features['mfcc_mean'] = float(np.mean(mfccs))
            features['mfcc_std'] = float(np.std(mfccs))
            
            # Spectral flatness
            flatness = librosa.feature.spectral_flatness(y=audio, n_fft=self.frame_length, hop_length=self.hop_length)
            features['spectral_flatness_mean'] = float(np.mean(flatness))
            
            # RMS energy
            rms = librosa.feature.rms(y=audio, frame_length=self.frame_length, hop_length=self.hop_length)
            features['rms_mean'] = float(np.mean(rms))
            features['rms_std'] = float(np.std(rms))
            
            features['noise_likelihood'] = features['spectral_flatness_mean'] * 2.0
            
        except Exception as e:
            logger.warning(f"Feature extraction error: {e}")
            features = {
                'zcr_mean': 0.05,
                'spectral_centroid_mean': 2000,
                'spectral_bandwidth_mean': 1500,
                'spectral_rolloff_mean': 3000,
                'mfcc_mean': 0.0,
                'mfcc_std': 1.0,
                'spectral_flatness_mean': 0.5,
                'rms_mean': 0.1,
                'rms_std': 0.05,
                'noise_likelihood': 0.5
            }
        return features
    
    def _compute_noise_floor(self, audio: np.ndarray) -> float:
        try:
            rms = librosa.feature.rms(y=audio, frame_length=self.frame_length, hop_length=self.hop_length)
            rms_flat = rms.flatten()
            if len(rms_flat) == 0:
                return 0.0
            noise_rms = np.percentile(rms_flat, 10)
            noise_floor = min(1.0, noise_rms * 5.0)
            return float(noise_floor)
        except Exception:
            return 0.1
    
    def _compute_spectral_score(self, features: Dict[str, float]) -> float:
        try:
            centroid_norm = min(1.0, features.get('spectral_centroid_mean', 2000) / 4000)
            bandwidth_norm = min(1.0, features.get('spectral_bandwidth_mean', 1500) / 5000)
            rolloff_norm = min(1.0, features.get('spectral_rolloff_mean', 3000) / 5000)
            flatness = features.get('spectral_flatness_mean', 0.5)
            score = (centroid_norm * 0.3 + bandwidth_norm * 0.3 + rolloff_norm * 0.2 + flatness * 0.2)
            return float(min(1.0, score))
        except Exception:
            return 0.3
    
    def _classify_background(self, audio: np.ndarray, features: Dict[str, float], noise_floor: float) -> float:
        try:
            mfcc_std = features.get('mfcc_std', 1.0)
            mfcc_var_norm = min(1.0, mfcc_std / 3.0)
            zcr_std = features.get('zcr_std', 0.02)
            zcr_var_norm = min(1.0, zcr_std * 50.0)
            flatness = features.get('spectral_flatness_mean', 0.5)
            background_score = (
                0.3 * noise_floor +
                0.3 * mfcc_var_norm +
                0.2 * zcr_var_norm +
                0.2 * flatness
            )
            return float(min(1.0, background_score))
        except Exception:
            return 0.3
    
    def _fallback_result(self, error_msg: str = "unknown error") -> Dict[str, Any]:
        return {
            "noise_floor": 0.0,
            "spectral_features": 0.0,
            "background_classification": 0.0,
            "environment_type": "unknown",
            "pillar_score": 0.0,
            "error": error_msg
        }