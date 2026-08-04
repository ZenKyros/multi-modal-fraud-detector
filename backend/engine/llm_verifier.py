import os
import json
import logging
import aiohttp
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# ─────────────────────────── SCORING TABLE ───────────────────────────
# Each scam technique adds a base score. Combinations increase it.
# You can tune these values to match your desired sensitivity.
TECHNIQUE_SCORES = {
    "threat_of_arrest": 0.95,          # almost certainly scam
    "financial_data_request": 0.85,    # asking for sort code, CVV, OTP, etc.
    "authority_impersonation": 0.30,   # impersonating bank, police, HMRC, DHL, etc.
    "payment_request": 0.30,           # any demand for money
    "urgency": 0.15,                   # time pressure
    "sensitive_info_request": 0.20,    # asking for personal details (name, address)
    "spoofing_attempt": 0.20,          # fake verification, number spoofing
}

# When multiple techniques are present, we don't simply sum; we use rules.
# For example:
#   arrest threat alone -> 0.95
#   authority + financial data -> 0.90
#   authority + payment only -> 0.50
#   payment + urgency -> 0.45
#   sensitive info alone -> 0.20
#   no technique -> 0.05

def compute_probability(techniques: List[str]) -> float:
    """
    Deterministic mapping from detected techniques to a scam probability.
    Never returns extreme values unless appropriate.
    """
    techniques = [t.lower().strip() for t in techniques]
    if not techniques:
        return 0.05

    # Critical combinations first
    if "threat_of_arrest" in techniques:
        return 0.95
    if "financial_data_request" in techniques:
        if "authority_impersonation" in techniques:
            return 0.92
        else:
            return 0.85
    # Authority impersonation with payment request
    if "authority_impersonation" in techniques and "payment_request" in techniques:
        base = 0.55
        if "urgency" in techniques:
            base += 0.10
        if "spoofing_attempt" in techniques:
            base += 0.10
        return min(0.75, base)

    # Payment request alone
    if "payment_request" in techniques:
        base = 0.30
        if "urgency" in techniques:
            base += 0.15
        if "authority_impersonation" in techniques:
            base += 0.10
        return min(0.50, base)

    # Authority alone
    if "authority_impersonation" in techniques:
        base = 0.30
        if "sensitive_info_request" in techniques:
            base += 0.15
        if "urgency" in techniques:
            base += 0.10
        return min(0.45, base)

    # Sensitive info alone
    if "sensitive_info_request" in techniques:
        return 0.20

    # Spoofing alone
    if "spoofing_attempt" in techniques:
        return 0.25

    # Urgency alone (very generic)
    if "urgency" in techniques:
        return 0.15

    # Fallback
    return 0.10


class LLMVerifier:
    """
    Groq-powered scam verifier that outputs calibrated threat probability.
    No API keys except Groq needed.
    """

    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"   # free tier, good balance

    async def analyze(self, transcript: str) -> Dict[str, Any]:
        if not transcript or not transcript.strip():
            return self._empty_result()

        if self.groq_key:
            try:
                result = await self._call_groq(transcript)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Groq call failed: {e}")

        # If LLM unavailable, use built‑in heuristic
        return self._heuristic_analysis(transcript)

    async def _call_groq(self, transcript: str) -> Dict[str, Any] | None:
        prompt = f"""
You are a scam call analyst. For the phone conversation transcript below, identify which scam techniques are present. Choose from this list:
- "threat_of_arrest" – police, jail, custody, legal action
- "financial_data_request" – asking for sort code, CVV, OTP, password, card number, bank account
- "authority_impersonation" – pretending to be HMRC, IRS, police, bank, DHL, Microsoft, etc.
- "payment_request" – any demand to pay money (fee, fine, delivery charge)
- "urgency" – limited time, immediately, right now, act fast
- "sensitive_info_request" – asking for personal details (full name, address, DOB) not yet financial
- "spoofing_attempt" – caller tries to prove identity via fake callback, Google, etc.

Return ONLY a JSON object (no markdown) with a single key "techniques" containing an array of the techniques that apply. If none, return empty array.

Transcript:
---
{transcript.strip()}
---
"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            async with session.post(self.groq_url, headers=headers, json=payload, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    techniques = self._parse_techniques(content)
                    if techniques is not None:
                        prob = compute_probability(techniques)
                        return {
                            "scam_probability": prob,
                            "scam_type": self._guess_scam_type(techniques),
                            "indicators": techniques,
                            "explanation": f"Detected techniques: {', '.join(techniques)}"
                        }
                else:
                    err = await resp.text()
                    logger.error(f"Groq API error {resp.status}: {err}")
                    return None

    def _parse_techniques(self, text: str) -> List[str] | None:
        text = text.strip()
        # Remove markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            data = json.loads(text)
            techniques = data.get("techniques", [])
            if isinstance(techniques, list):
                return [t for t in techniques if isinstance(t, str)]
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    return data.get("techniques", [])
                except:
                    pass
        logger.warning(f"Could not parse techniques from: {text[:150]}")
        return None

    def _guess_scam_type(self, techniques: List[str]) -> str:
        if "threat_of_arrest" in techniques:
            return "government_impersonation"
        if "financial_data_request" in techniques:
            return "banking"
        if "authority_impersonation" in techniques:
            if any(t in " ".join(techniques) for t in ["hmrc", "irs", "police"]):
                return "government_impersonation"
            if "payment_request" in techniques:
                return "delivery_scam"
            return "other"
        if "payment_request" in techniques:
            return "other"
        return "none"

    def _heuristic_analysis(self, transcript: str) -> Dict[str, Any]:
        """Rule‑based fallback if LLM fails."""
        t = transcript.lower()
        techniques = []
        if any(w in t for w in ["arrest", "custody", "police will come"]):
            techniques.append("threat_of_arrest")
        if any(w in t for w in ["sort code", "cvv", "otp", "one time password", "card number"]):
            techniques.append("financial_data_request")
        if any(w in t for w in ["hmrc", "irs", "social security", "crown court", "microsoft", "dhl"]):
            techniques.append("authority_impersonation")
        if any(w in t for w in ["pay", "fee", "fine", "transfer", "payment"]):
            techniques.append("payment_request")
        if any(w in t for w in ["urgent", "immediately", "right now", "24 hours"]):
            techniques.append("urgency")
        if any(w in t for w in ["open google", "call back", "official number"]):
            techniques.append("spoofing_attempt")

        prob = compute_probability(techniques)
        return {
            "scam_probability": prob,
            "scam_type": self._guess_scam_type(techniques),
            "indicators": techniques,
            "explanation": f"Heuristic analysis: {', '.join(techniques) if techniques else 'no techniques'}"
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "scam_probability": 0.0,
            "scam_type": "none",
            "indicators": [],
            "explanation": "Empty transcript"
        }