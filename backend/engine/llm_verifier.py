import os
import json
import aiohttp
import asyncio
from typing import Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMVerifier:
    """
    LLM-based verification gate using Groq Chat API.
    Uses Groq's LLM models (Llama, Mixtral) to evaluate fraud indicators.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")  # Reuse same key
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # or "mixtral-8x7b-32768"
        self.timeout = 15

        if self.api_key:
            logger.info("✅ Using Groq LLM for verification")
        else:
            logger.error("❌ GROQ_API_KEY is MISSING, verification disabled")

    async def verify(self, pillar_results: Dict[str, Any], threat_index: float, transcript: str = "") -> Dict[str, Any]:
        """
        Verify fraud detection using Groq LLM.

        Returns:
            dict with is_fraud, confidence, reasons, recommended_action, verified
        """
        if not self.api_key:
            logger.warning("No API key, using fallback")
            return self._fallback_verification(threat_index)

        try:
            # Build prompt
            prompt = self._build_prompt(pillar_results, threat_index, transcript)

            # Call Groq API
            response = await self._call_groq_api(prompt)

            # Parse response
            parsed = self._parse_response(response)
            parsed["verified"] = True
            return parsed

        except asyncio.TimeoutError:
            logger.error("Groq LLM timeout")
            return self._fallback_verification(threat_index)
        except Exception as e:
            logger.error(f"Groq verification error: {str(e)}")
            return self._fallback_verification(threat_index)

    def _build_prompt(self, pillar_results: Dict[str, Any], threat_index: float, transcript: str) -> str:
        """Build a structured prompt for the LLM."""
        linguistic = pillar_results.get("linguistic", {})
        behavioral = pillar_results.get("behavioral", {})
        acoustic = pillar_results.get("acoustic", {})

        transcript_short = transcript[:500] + "..." if len(transcript) > 500 else transcript

        prompt = f"""You are a fraud detection expert analyzing a phone call.

Context:
- Threat Index (0-1): {threat_index:.2f} (threshold for fraud is 0.55)
- Transcript (partial): {transcript_short}

Pillar Analysis:
1. Linguistic:
   - Urgency Score: {linguistic.get('urgency_score', 0):.2f}
   - Urgency Keywords: {linguistic.get('keyword_matches', [])}
   - Pillar Score: {linguistic.get('pillar_score', 0):.2f}

2. Behavioral:
   - Speaker Dominance: {behavioral.get('speaker_dominance', 0):.2f}
   - Volume Pressure: {behavioral.get('volume_pressure', 0):.2f}
   - Speech/Pause Ratio: {behavioral.get('speech_pause_ratio', 0):.2f}
   - Speaking Rate: {behavioral.get('speaking_rate', 0):.2f}
   - Pillar Score: {behavioral.get('pillar_score', 0):.2f}

3. Acoustic:
   - Noise Floor: {acoustic.get('noise_floor', 0):.2f}
   - Background Classification: {acoustic.get('background_classification', 0):.2f}
   - Environment Type: {acoustic.get('environment_type', 'unknown')}
   - Pillar Score: {acoustic.get('pillar_score', 0):.2f}

Question:
Based on this data, is this call likely a fraud/scam attempt?
Provide a structured answer in valid JSON only (no extra text) with the following fields:
{{
  "is_fraud": boolean,
  "confidence": float (0-1),
  "reasons": [string, string, ...] (at least 2 reasons),
  "recommended_action": string (one of: "Block", "Warn", "Monitor", "Ignore")
}}

Be objective and cite the evidence."""
        return prompt

    async def _call_groq_api(self, prompt: str) -> Dict[str, Any]:
        """Send request to Groq Chat API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a fraud detection expert. Respond only with JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 300,
            "response_format": {"type": "json_object"}  # Groq supports this
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload, headers=headers, timeout=self.timeout) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Groq API error {resp.status}: {error_text}")
                    raise Exception(f"API error {resp.status}: {error_text}")
                return await resp.json()

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the JSON answer from Groq response."""
        try:
            # Groq returns OpenAI-like structure
            choices = response.get("choices", [])
            if not choices:
                raise ValueError("No choices in response")
            message = choices[0].get("message", {})
            content = message.get("content", "")
            if not content:
                raise ValueError("No content in message")

            # Parse JSON
            data = json.loads(content)

            # Ensure required fields
            data["is_fraud"] = bool(data.get("is_fraud", False))
            data["confidence"] = float(data.get("confidence", 0.5))
            data["confidence"] = max(0.0, min(1.0, data["confidence"]))
            if not isinstance(data.get("reasons"), list):
                data["reasons"] = [str(data["reasons"])] if data.get("reasons") else ["No specific reasons given."]
            data["recommended_action"] = str(data.get("recommended_action", "Monitor"))

            return data

        except Exception as e:
            logger.error(f"Failed to parse Groq response: {e}")
            return {
                "is_fraud": False,
                "confidence": 0.5,
                "reasons": ["LLM response parsing failed, using fallback."],
                "recommended_action": "Monitor"
            }

    def _fallback_verification(self, threat_index: float) -> Dict[str, Any]:
        """Rule-based fallback when LLM is unavailable."""
        return {
            "is_fraud": threat_index > 0.65,
            "confidence": min(threat_index * 0.8, 0.9),
            "reasons": ["LLM verification unavailable – using rule-based fallback."],
            "recommended_action": "Investigate" if threat_index > 0.65 else "Monitor",
            "verified": False
        }