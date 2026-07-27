"""
Pillar I: Linguistic Agent - Semantic & Urgency Analysis

Uses Groq API (Whisper Large-v3) for real-time audio transcription and scans
transcribed text for high-urgency fraud keywords that indicate immediate action
pressure (payment demanded, account compromised, legal threat, etc.).

Maintains a dynamic keyword urgency scoring system that feeds into the game
theory fusion engine.
"""

import os
import numpy as np
import soundfile as sf
from typing import Dict, List, Optional, Tuple
from groq import Groq
import asyncio
from functools import lru_cache


class LinguisticAgent:
    """Semantic analysis using Groq Whisper and urgency keyword detection."""

    # High-urgency fraud keywords with risk weights
    URGENCY_KEYWORDS = {
        # Payment/Financial Pressure
        "payment": 0.8,
        "pay now": 0.95,
        "transfer": 0.85,
        "urgent": 0.8,
        "immediately": 0.85,
        "right now": 0.9,
        "bitcoin": 0.9,
        "wire transfer": 0.9,
        "money": 0.6,
        "fee": 0.7,
        "billing": 0.65,
        
        # Legal/Authority Threats
        "irs": 0.95,
        "court": 0.85,
        "lawsuit": 0.85,
        "legal": 0.7,
        "arrest": 0.95,
        "prison": 0.95,
        "warrant": 0.9,
        "police": 0.8,
        
        # Account Compromise
        "account": 0.6,
        "compromised": 0.85,
        "hacked": 0.85,
        "breach": 0.85,
        "unauthorized": 0.75,
        "suspicious activity": 0.8,
        "locked": 0.7,
        
        # Identity/Social Engineering
        "verify": 0.65,
        "confirm": 0.6,
        "password": 0.8,
        "ssn": 0.9,
        "social security": 0.9,
        "credit card": 0.85,
        "personal information": 0.75,
        
        # Generic Pressure
        "don't hang up": 0.8,
        "limited time": 0.85,
        "act now": 0.85,
        "don't tell anyone": 0.9,
        "keep it quiet": 0.9,
        "secret": 0.75,
    }

    def __init__(self):
        """Initialize Groq client with API key from environment."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=self.api_key)
        self.transcription_cache: Dict[str, str] = {}
        self.urgency_history: List[float] = []

    async def transcribe_audio(self, audio_chunk: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio chunk using Groq Whisper API.
        
        Args:
            audio_chunk: Numpy array of audio samples
            sample_rate: Sample rate of the audio
            
        Returns:
            Transcribed text
        """
        # Save audio chunk to temporary file (Groq requires file upload)
        temp_file = "/tmp/audio_chunk.wav"
        try:
            sf.write(temp_file, audio_chunk, sample_rate)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcript = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                temp_file
            )
            return transcript
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _transcribe_sync(self, audio_file: str) -> str:
        """
        Synchronous transcription call to Groq API.
        
        Args:
            audio_file: Path to temporary audio file
            
        Returns:
            Transcribed text
        """
        try:
            with open(audio_file, "rb") as f:
                transcript_response = self.client.audio.transcriptions.create(
                    file=(audio_file, f, "audio/wav"),
                    model="whisper-large-v3-turbo",
                    language="en",
                )
            return transcript_response.text.lower() if transcript_response else ""
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return ""

    def score_transcript_urgency(self, transcript: str) -> float:
        """
        Score the transcribed text for fraud urgency signals.
        
        Returns a normalized urgency score from 0.0 (safe) to 1.0 (extreme threat).
        
        Args:
            transcript: Transcribed text from audio
            
        Returns:
            Urgency score between 0.0 and 1.0
        """
        if not transcript:
            return 0.0
        
        transcript_lower = transcript.lower()
        matched_keywords = {}
        
        # Find all matching keywords and their weights
        for keyword, weight in self.URGENCY_KEYWORDS.items():
            if keyword in transcript_lower:
                # Count occurrences
                count = transcript_lower.count(keyword)
                matched_keywords[keyword] = weight * min(count, 2)  # Cap at 2x weight for repetition
        
        if not matched_keywords:
            urgency_score = 0.0
        else:
            # Average weight of matched keywords, with presence multiplier
            avg_weight = sum(matched_keywords.values()) / len(matched_keywords)
            presence_factor = min(len(matched_keywords) / 5, 1.0)  # Boost if many keywords present
            urgency_score = min(avg_weight * (0.7 + 0.3 * presence_factor), 1.0)
        
        # Track history for trend analysis
        self.urgency_history.append(urgency_score)
        if len(self.urgency_history) > 10:
            self.urgency_history.pop(0)
        
        return urgency_score

    def get_urgency_trend(self) -> float:
        """
        Get the trend of urgency over recent chunks.
        
        Returns:
            Trend score from -1.0 (decreasing) to 1.0 (increasing)
        """
        if len(self.urgency_history) < 2:
            return 0.0
        
        recent = self.urgency_history[-5:]  # Last 5 chunks
        if len(recent) < 2:
            return 0.0
        
        # Simple linear trend
        trend = (recent[-1] - recent[0]) / len(recent) * 10
        return np.clip(trend, -1.0, 1.0)

    def extract_keywords(self, transcript: str) -> List[Dict[str, any]]:
        """
        Extract all matched urgency keywords from transcript.
        
        Args:
            transcript: Transcribed text
            
        Returns:
            List of dicts with 'keyword', 'weight', and 'count'
        """
        transcript_lower = transcript.lower()
        found_keywords = []
        
        for keyword, weight in self.URGENCY_KEYWORDS.items():
            if keyword in transcript_lower:
                count = transcript_lower.count(keyword)
                found_keywords.append({
                    "keyword": keyword,
                    "weight": weight,
                    "count": count
                })
        
        # Sort by weight descending
        found_keywords.sort(key=lambda x: x["weight"], reverse=True)
        return found_keywords

    async def process_chunk(
        self,
        audio_chunk: np.ndarray,
        sample_rate: int,
        chunk_index: int
    ) -> Dict:
        """
        Full processing pipeline for a single audio chunk.
        
        Args:
            audio_chunk: Audio samples
            sample_rate: Sample rate
            chunk_index: Chunk sequence number
            
        Returns:
            Dictionary with transcription, urgency score, and keywords
        """
        transcript = await self.transcribe_audio(audio_chunk, sample_rate)
        urgency_score = self.score_transcript_urgency(transcript)
        keywords = self.extract_keywords(transcript)
        
        return {
            "pillar": "linguistic",
            "chunk_index": chunk_index,
            "transcript": transcript,
            "urgency_score": float(urgency_score),
            "urgency_trend": float(self.get_urgency_trend()),
            "keywords": keywords,
            "keyword_count": len(keywords),
        }
