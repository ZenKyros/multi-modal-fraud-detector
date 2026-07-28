import os
import tempfile
import subprocess
import numpy as np
import librosa
from typing import List, Optional, Callable, Any, Dict
import logging

logger = logging.getLogger(__name__)

class AudioIngestionAgent:
    """
    Handles loading, chunking, and processing of audio files.
    Supports MP3, WAV, M4A, etc. via ffmpeg fallback.
    """

    def __init__(self, chunk_duration: int = 3, sample_rate: int = 16000):
        self.chunk_duration = chunk_duration  # seconds
        self.sample_rate = sample_rate
        self.buffer = []  # for streaming chunks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_audio(self, file_path: str) -> Optional[np.ndarray]:
        """
        Load audio from any format (MP3, WAV, etc.) into a numpy array.
        Returns float32 array (mono, sample_rate=16000) or None on failure.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Try direct librosa (WAV, FLAC)
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with librosa: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.warning(f"librosa load failed: {e}")

        # Try pydub + ffmpeg
        try:
            from pydub import AudioSegment
            import io
            audio_seg = AudioSegment.from_file(file_path)
            audio_seg = audio_seg.set_frame_rate(self.sample_rate).set_channels(1)
            wav_io = io.BytesIO()
            audio_seg.export(wav_io, format='wav')
            wav_io.seek(0)
            audio, sr = librosa.load(wav_io, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded with pydub: {len(audio)} samples")
            return audio
        except Exception as e:
            logger.warning(f"pydub load failed: {e}")

        # Fallback: ffmpeg direct conversion to temp WAV
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            cmd = [
                'ffmpeg', '-i', file_path,
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
            logger.error(f"All loading methods failed: {e}")
            return None

    def chunk_audio(self, audio: np.ndarray, chunk_duration: Optional[int] = None) -> List[np.ndarray]:
        """
        Split audio array into chunks of specified duration (seconds).
        """
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
        chunk_size = chunk_duration * self.sample_rate
        chunks = []
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i + chunk_size]
            if len(chunk) > 0:
                chunks.append(chunk)
        return chunks

    def process_file(self, file_path: str, chunk_callback: Callable[[np.ndarray, int], Any]) -> List[Any]:
        """
        Load audio, split into chunks, and call callback for each chunk.
        Returns list of results from callback.
        """
        audio = self.load_audio(file_path)
        if audio is None:
            return []
        chunks = self.chunk_audio(audio)
        results = []
        for idx, chunk in enumerate(chunks):
            # Save chunk to temporary WAV for processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            # Write WAV header
            import wave
            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                # Convert float32 to int16
                chunk_int16 = (chunk * 32767).astype(np.int16)
                wf.writeframes(chunk_int16.tobytes())
            # Process chunk
            try:
                result = chunk_callback(tmp_path, idx)
                results.append(result)
            finally:
                os.unlink(tmp_path)
        return results

    # ------------------------------------------------------------------
    # Streaming support (for WebSocket)
    # ------------------------------------------------------------------
    def feed_stream(self, audio_chunk: np.ndarray) -> List[np.ndarray]:
        """
        Feed a chunk of audio data (from browser) into the buffer.
        Returns a list of full 3-second chunks if enough data accumulated.
        """
        self.buffer.extend(audio_chunk.tolist())
        chunk_size = self.chunk_duration * self.sample_rate
        chunks = []
        while len(self.buffer) >= chunk_size:
            chunk = np.array(self.buffer[:chunk_size], dtype=np.float32)
            chunks.append(chunk)
            self.buffer = self.buffer[chunk_size:]
        return chunks