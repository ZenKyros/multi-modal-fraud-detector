"""
Ingestion Agent: Audio Stream Chunking & Segmentation

Handles the intake of audio files from the data directory, slicing them into
3-second segments based on client-requested offsets. Maintains chronological
order and returns raw numpy arrays for downstream pillar processing.
"""

import os
import numpy as np
import soundfile as sf
import librosa
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class AudioIngestionAgent:
    """Manages audio file ingestion and chunking operations."""

    CHUNK_DURATION = 3.0  # 3-second segments
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

    def __init__(self):
        """Initialize the ingestion agent with data directory scanning."""
        self.available_files = self._scan_data_directory()
        self.audio_cache: Dict[str, Dict] = {}

    def _scan_data_directory(self) -> Dict[str, str]:
        """
        Scan the data directory and index available audio files (WAV, MP3).
        
        Returns:
            Dictionary mapping filename to full file path
        """
        files = {}
        if os.path.exists(self.DATA_DIR):
            for file in os.listdir(self.DATA_DIR):
                if file.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
                    files[file] = os.path.join(self.DATA_DIR, file)
        return files

    def load_audio(self, filename: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file and cache it for repeated access.
        Supports WAV, MP3, M4A, FLAC formats.
        
        Args:
            filename: Name of the audio file (e.g., 'scam_call.wav', 'call.mp3')
            
        Returns:
            Tuple of (audio_data, sample_rate)
            
        Raises:
            FileNotFoundError: If file not found in data directory
        """
        if filename not in self.available_files:
            raise FileNotFoundError(
                f"Audio file '{filename}' not found. Available: {list(self.available_files.keys())}"
            )

        if filename not in self.audio_cache:
            filepath = self.available_files[filename]
            try:
                # Use librosa for flexible format support
                audio_data, sr = librosa.load(filepath, sr=None, mono=True)
                self.audio_cache[filename] = {"audio": audio_data, "sr": sr}
            except Exception as e:
                raise RuntimeError(f"Failed to load audio file: {str(e)}")

        cached = self.audio_cache[filename]
        return cached["audio"], cached["sr"]

    def get_audio_duration(self, filename: str) -> float:
        """
        Get total duration of an audio file in seconds.
        
        Args:
            filename: Name of the WAV file
            
        Returns:
            Duration in seconds
        """
        audio_data, sr = self.load_audio(filename)
        return len(audio_data) / sr

    def get_chunk(
        self,
        filename: str,
        chunk_index: int
    ) -> Tuple[np.ndarray, int, Dict]:
        """
        Extract a 3-second chunk from an audio file at the specified index.
        
        Args:
            filename: Name of the WAV file
            chunk_index: 0-based index of the chunk (0 = first 3 seconds, 1 = 3-6 seconds, etc.)
            
        Returns:
            Tuple of (chunk_audio, sample_rate, metadata_dict)
            
        Raises:
            IndexError: If chunk_index is out of range
        """
        audio_data, sr = self.load_audio(filename)
        chunk_samples = int(self.CHUNK_DURATION * sr)
        
        start_sample = chunk_index * chunk_samples
        end_sample = start_sample + chunk_samples
        
        if start_sample >= len(audio_data):
            raise IndexError(
                f"Chunk index {chunk_index} out of range for {filename} "
                f"(duration: {len(audio_data) / sr:.1f}s, ~{len(audio_data) // chunk_samples} chunks)"
            )
        
        # Handle partial final chunk
        chunk = audio_data[start_sample:end_sample]
        if len(chunk) < chunk_samples:
            # Pad with zeros if we're at the end
            chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode='constant')
        
        metadata = {
            "filename": filename,
            "chunk_index": chunk_index,
            "start_time": chunk_index * self.CHUNK_DURATION,
            "end_time": (chunk_index + 1) * self.CHUNK_DURATION,
            "sample_rate": sr,
            "chunk_samples": len(chunk),
            "duration": len(chunk) / sr
        }
        
        return chunk, sr, metadata

    def get_all_chunks(self, filename: str) -> List[Tuple[np.ndarray, int, Dict]]:
        """
        Extract all 3-second chunks from a file.
        
        Args:
            filename: Name of the WAV file
            
        Returns:
            List of (chunk_audio, sample_rate, metadata_dict) tuples
        """
        audio_data, sr = self.load_audio(filename)
        chunk_samples = int(self.CHUNK_DURATION * sr)
        num_chunks = (len(audio_data) + chunk_samples - 1) // chunk_samples
        
        chunks = []
        for i in range(num_chunks):
            try:
                chunk, sr_ret, metadata = self.get_chunk(filename, i)
                chunks.append((chunk, sr_ret, metadata))
            except IndexError:
                break
        
        return chunks

    def get_available_files(self) -> List[str]:
        """
        Get list of available audio files.
        
        Returns:
            List of available WAV filenames
        """
        return list(self.available_files.keys())

    def clear_cache(self) -> None:
        """Clear the audio cache to free memory."""
        self.audio_cache.clear()
