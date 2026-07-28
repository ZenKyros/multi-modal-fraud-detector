import os
import json
import aiohttp
import asyncio
import tempfile
import subprocess
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LinguisticPillar:
    """
    Linguistic analysis pillar using Groq Whisper API.
    Supports MP3, M4A, WebM, WAV, etc. via automatic conversion.
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        self.sample_rate = sample_rate
        self.urgency_keywords = [
            "urgent", "immediately", "now", "quick", "emergency",
            "bank", "account", "money", "payment", "transfer",
            "social security", "credit card", "verify", "confirm",
            "fraud", "suspicious", "alert", "warning",
            "action required", "deadline", "limited time"
        ]
        if self.api_key:
            logger.info("✅ GROQ_API_KEY is set (starts with %s)", self.api_key[:10])
        else:
            logger.error("❌ GROQ_API_KEY is MISSING")

    async def analyze(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio for linguistic patterns."""
        try:
            # 1. Load audio and convert to temporary WAV (if needed)
            wav_path = self._convert_to_wav(audio_path)
            if wav_path is None:
                return self._fallback_result("audio conversion failed")

            # 2. Transcribe with Groq
            transcript = await self.transcribe_audio(wav_path)

            # 3. Clean up temporary WAV if it was created
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)

            # 4. Compute urgency and keywords
            urgency_score = self.calculate_urgency_score(transcript)
            keyword_matches = self.detect_keywords(transcript)

            return {
                "transcript": transcript,
                "urgency_score": urgency_score,
                "keyword_matches": keyword_matches,
                "keyword_count": len(keyword_matches),
                "pillar_score": min(1.0, urgency_score + (len(keyword_matches) * 0.05))
            }

        except Exception as e:
            logger.error(f"Linguistic analysis error: {str(e)}")
            return self._fallback_result(str(e))

    def _convert_to_wav(self, audio_path: str) -> Optional[str]:
        """
        Convert any audio file to WAV (16kHz, mono, PCM) using ffmpeg.
        Returns path to WAV file (or original path if already WAV).
        """
        if not os.path.exists(audio_path):
            logger.error(f"File not found: {audio_path}")
            return None

        # If it's already a WAV, return as-is
        if audio_path.lower().endswith('.wav'):
            return audio_path

        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                wav_path = tmp.name
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', '1',
                wav_path,
                '-y'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return None
            logger.info(f"Converted to WAV: {wav_path}")
            return wav_path
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return None

    async def transcribe_audio(self, wav_path: str) -> str:
        """Transcribe the WAV file using Groq Whisper API."""
        if not self.api_key:
            return self._fallback_transcription("Missing API key")

        try:
            async with aiohttp.ClientSession() as session:
                with open(wav_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='audio.wav')
                    data.add_field('model', 'whisper-large-v3')
                    data.add_field('response_format', 'json')
                    headers = {'Authorization': f'Bearer {self.api_key}'}

                    logger.info(f"📡 Calling Groq API for {wav_path}")
                    async with session.post(self.api_url, headers=headers, data=data, timeout=30) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            transcript = result.get('text', '')
                            logger.info(f"✅ Transcription successful: {transcript[:50]}...")
                            return transcript
                        else:
                            error_text = await resp.text()
                            logger.error(f"❌ Groq API error {resp.status}: {error_text}")
                            return self._fallback_transcription(f"API error {resp.status}")
        except asyncio.TimeoutError:
            logger.error("❌ Groq API timeout")
            return self._fallback_transcription("Timeout")
        except Exception as e:
            logger.error(f"❌ Transcription error: {str(e)}")
            return self._fallback_transcription(str(e))

    def calculate_urgency_score(self, transcript: str) -> float:
        if not transcript:
            return 0.0
        words = transcript.lower().split()
        urgent = ["urgent","immediately","asap","now","quick","emergency","critical","important"]
        urgent_count = sum(1 for w in words if w in urgent)
        financial = ["bank","account","money","payment","transfer","credit","debit","card","funds","transaction"]
        financial_count = sum(1 for w in words if w in financial)
        return min(1.0, urgent_count * 0.2 + financial_count * 0.05)

    def detect_keywords(self, transcript: str) -> list:
        if not transcript:
            return []
        t_lower = transcript.lower()
        return [kw for kw in self.urgency_keywords if kw.lower() in t_lower]

    def _fallback_transcription(self, reason: str = "") -> str:
        return f"[Fallback: {reason}]"

    def _fallback_result(self, error_msg: str = "unknown error") -> Dict[str, Any]:
        return {
            "transcript": self._fallback_transcription(error_msg),
            "urgency_score": 0.0,
            "keyword_matches": [],
            "keyword_count": 0,
            "pillar_score": 0.0,
            "error": error_msg
        }