# agents/ingestion.py
import os
import tempfile
import subprocess
import logging
import numpy as np
import soundfile as sf
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class IngestionAgent:
    """
    Handles audio loading, conversion to 16kHz mono WAV,
    and transcription using Faster Whisper.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.sample_rate = 16000
        self.model_size = model_size
        self.device = device
        self._load_model()

    def _load_model(self):
        try:
            from faster_whisper import WhisperModel
            self.whisper = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8"
            )
            logger.info(f"Faster Whisper '{self.model_size}' loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            self.whisper = None

    def convert_to_wav(self, audio_path: str) -> Optional[str]:
        """Convert any audio file to 16kHz mono WAV using ffmpeg."""
        if not os.path.exists(audio_path):
            return None
        # If already proper WAV, return as-is
        if audio_path.lower().endswith('.wav'):
            try:
                info = sf.info(audio_path)
                if info.samplerate == self.sample_rate and info.channels == 1:
                    return audio_path
            except:
                pass

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            wav_path = tmp.name

        cmd = [
            'ffmpeg', '-i', audio_path,
            '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate),
            '-ac', '1',
            '-y', wav_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffmpeg error: {result.stderr}")
            return None
        return wav_path

    def transcribe(self, wav_path: str) -> Dict[str, Any]:
        """
        Transcribe WAV file with Faster Whisper.
        Returns: {
            "text": full transcript,
            "segments": [{"start": float, "end": float, "text": str}, ...],
            "language": str,
            "duration": float
        }
        """
        if not self.whisper:
            return {"text": "", "segments": [], "error": "Whisper not loaded"}

        try:
            segments, info = self.whisper.transcribe(
                wav_path,
                beam_size=5,
                word_timestamps=True
            )
            full_text = []
            seg_list = []
            for seg in segments:
                full_text.append(seg.text.strip())
                seg_list.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip()
                })

            return {
                "text": " ".join(full_text),
                "segments": seg_list,
                "language": info.language,
                "duration": seg_list[-1]["end"] if seg_list else 0.0
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"text": "", "segments": [], "error": str(e)}

    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Complete pipeline: convert -> transcribe.
        Returns combined result.
        """
        wav_path = self.convert_to_wav(file_path)
        if not wav_path:
            return {"error": "Audio conversion failed"}

        result = self.transcribe(wav_path)

        # Clean temp file if created
        if wav_path != file_path and os.path.exists(wav_path):
            os.remove(wav_path)

        return result

    def process_text(self, raw_text: str) -> Dict[str, Any]:
        """
        Process pasted text: parse into segments (one per line).
        Assumes alternating speakers if lines are separated by newline.
        """
        lines = [l.strip() for l in raw_text.strip().split('\n') if l.strip()]
        segments = []
        for i, line in enumerate(lines):
            # Try to detect speaker labels like "Caller: ..." or "Recipient: ..."
            if ':' in line:
                parts = line.split(':', 1)
                speaker = parts[0].strip()
                text = parts[1].strip()
            else:
                speaker = "SPEAKER_1" if i % 2 == 0 else "SPEAKER_2"
                text = line
            segments.append({
                "speaker": speaker,
                "text": text,
                "start": i * 5.0,   # fake timestamps
                "end": (i+1) * 5.0
            })

        full_text = " ".join([s["text"] for s in segments])
        return {
            "text": full_text,
            "segments": segments,
            "language": "en",
            "duration": segments[-1]["end"] if segments else 0.0
        }