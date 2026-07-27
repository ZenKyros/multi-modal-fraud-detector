"""
LLM Verifier: Google Gemini API Validation Gate

When the game-theoretic fusion engine produces a threat index > 0.55, the output
gates through this verification layer. Uses Google Gemini to perform semantic
validation and confirm the fraud classification before sending alerts.

Enforces strict JSON schema to ensure parseable, structured responses.
"""

import os
import json
import asyncio
from typing import Dict, Optional, List
import google.generativeai as genai


class LLMVerifierGate:
    """LLM-powered verification gate using Google Gemini API."""

    # JSON schema that Gemini must conform to
    VERIFICATION_SCHEMA = {
        "type": "object",
        "properties": {
            "is_fraud": {
                "type": "boolean",
                "description": "Final determination: is this call fraudulent?"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence level (0-1) of the determination"
            },
            "fraud_type": {
                "type": "string",
                "enum": ["scam", "phishing", "social_engineering", "financial_fraud", "impersonation", "unknown"],
                "description": "Classification of fraud type if detected"
            },
            "key_indicators": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key fraud indicators found"
            },
            "reasoning": {
                "type": "string",
                "description": "Concise explanation of the determination"
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Recommended actions (e.g., 'hang up', 'report to FTC')"
            }
        },
        "required": ["is_fraud", "confidence", "fraud_type", "key_indicators", "reasoning", "recommendations"]
    }

    def __init__(self):
        """Initialize Gemini client with API key from environment."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.verification_cache: Dict[str, Dict] = {}

    async def verify_fraud_alert(
        self,
        transcript: str,
        linguistic_data: Dict,
        behavioral_data: Dict,
        acoustic_data: Dict,
        threat_index: float
    ) -> Dict:
        """
        Verify fraud classification using Gemini LLM.
        
        Args:
            transcript: Transcribed text from audio
            linguistic_data: Output from linguistic pillar
            behavioral_data: Output from behavioral pillar
            acoustic_data: Output from acoustic pillar
            threat_index: Combined threat index from game theory engine
            
        Returns:
            Structured verification result matching VERIFICATION_SCHEMA
        """
        # Create detailed context prompt
        prompt = self._build_verification_prompt(
            transcript, linguistic_data, behavioral_data, acoustic_data, threat_index
        )
        
        # Run Gemini call in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._call_gemini_sync, prompt)
        
        return result

    def _build_verification_prompt(
        self,
        transcript: str,
        linguistic_data: Dict,
        behavioral_data: Dict,
        acoustic_data: Dict,
        threat_index: float
    ) -> str:
        """Build detailed prompt for Gemini to analyze."""
        
        prompt = f"""
You are an expert fraud detection analyst. Analyze the following call data and determine if this is likely a fraudulent call.

CALL TRANSCRIPT:
{transcript}

AUDIO ANALYSIS DATA:
- Linguistic Analysis: Urgency Score: {linguistic_data.get('urgency_score', 0):.2f}, Keywords: {linguistic_data.get('keyword_count', 0)} urgent phrases detected
  Keywords: {', '.join([k['keyword'] for k in linguistic_data.get('keywords', [])[:5]])}
  
- Behavioral Analysis: Aggression Score: {behavioral_data.get('aggression_score', 0):.2f}
  Dominance: {behavioral_data.get('voice_features', {}).get('dominance_score', 0):.2f}
  Pause Duration: {behavioral_data.get('voice_features', {}).get('avg_pause_duration', 0):.2f}s
  
- Acoustic Analysis: Environment Index: {acoustic_data.get('environment_index', 0):.2f}
  Noise Floor: {acoustic_data.get('noise_floor_features', {}).get('noise_elevation', 0):.2f}
  Background: Call center indicators present
  
COMBINED THREAT INDEX: {threat_index:.2f} / 1.0

Based on this data, determine:
1. Is this likely a fraudulent call? (true/false)
2. What type of fraud if detected?
3. Key indicators that support your determination
4. Confidence level in your assessment
5. Recommended actions

Provide your response ONLY as valid JSON conforming to this schema:
{{
    "is_fraud": boolean,
    "confidence": number (0-1),
    "fraud_type": string (one of: "scam", "phishing", "social_engineering", "financial_fraud", "impersonation", "unknown"),
    "key_indicators": [array of strings],
    "reasoning": string,
    "recommendations": [array of strings]
}}
"""
        return prompt

    def _call_gemini_sync(self, prompt: str) -> Dict:
        """
        Synchronous call to Gemini API.
        
        Args:
            prompt: Detailed verification prompt
            
        Returns:
            Parsed JSON response matching schema
        """
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                return self._default_verification_response()
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            if response_text.startswith("{"):
                json_str = response_text
            else:
                # Look for JSON block
                import re
                match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    return self._default_verification_response()
            
            # Parse JSON
            result = json.loads(json_str)
            
            # Validate against schema
            result = self._validate_response(result)
            
            return result
            
        except json.JSONDecodeError:
            return self._default_verification_response()
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return self._default_verification_response()

    def _validate_response(self, response: Dict) -> Dict:
        """
        Validate response matches schema and fill in defaults if needed.
        
        Args:
            response: Response from Gemini
            
        Returns:
            Validated response
        """
        validated = {
            "is_fraud": bool(response.get("is_fraud", False)),
            "confidence": float(response.get("confidence", 0.5)),
            "fraud_type": str(response.get("fraud_type", "unknown")),
            "key_indicators": list(response.get("key_indicators", [])),
            "reasoning": str(response.get("reasoning", "Analysis inconclusive")),
            "recommendations": list(response.get("recommendations", [])),
        }
        
        # Validate confidence range
        validated["confidence"] = float(max(0.0, min(1.0, validated["confidence"])))
        
        # Validate fraud_type
        valid_types = ["scam", "phishing", "social_engineering", "financial_fraud", "impersonation", "unknown"]
        if validated["fraud_type"] not in valid_types:
            validated["fraud_type"] = "unknown"
        
        return validated

    def _default_verification_response(self) -> Dict:
        """Return a safe default response when verification fails."""
        return {
            "is_fraud": False,
            "confidence": 0.3,
            "fraud_type": "unknown",
            "key_indicators": [],
            "reasoning": "Could not verify due to API limitations. Treat with caution.",
            "recommendations": ["Review manually", "Contact call recipient for confirmation"],
        }

    async def batch_verify(
        self,
        verification_requests: List[Dict]
    ) -> List[Dict]:
        """
        Verify multiple calls (useful for batch processing).
        
        Args:
            verification_requests: List of call data dicts
            
        Returns:
            List of verification results
        """
        results = []
        for request in verification_requests:
            result = await self.verify_fraud_alert(
                request["transcript"],
                request["linguistic_data"],
                request["behavioral_data"],
                request["acoustic_data"],
                request["threat_index"]
            )
            results.append(result)
        
        return results

    def is_response_valid(self, response: Dict) -> bool:
        """
        Check if response is valid and has sufficient confidence.
        
        Args:
            response: Verification response
            
        Returns:
            Whether the response should be trusted
        """
        required_fields = {"is_fraud", "confidence", "fraud_type", "key_indicators", "reasoning", "recommendations"}
        
        if not all(field in response for field in required_fields):
            return False
        
        # High confidence is good, but also accept unanimous decisions with moderate confidence
        if response.get("is_fraud", False) and response.get("confidence", 0) >= 0.6:
            return True
        
        return False
