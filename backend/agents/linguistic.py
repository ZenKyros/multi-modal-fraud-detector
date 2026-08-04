# agents/linguistic.py
import re
from typing import Dict, Any, List

class LinguisticAgent:
    """Extracts linguistic features: urgency, threats, financial requests."""

    def __init__(self):
        # Keywords grouped by category
        self.keywords = {
            "urgency": [
                "urgent", "immediately", "right now", "asap",
                "emergency", "hurry", "quick", "don't delay",
                "act now", "limited time", "deadline"
            ],
            "threat": [
                "arrest", "police", "custody", "court", "legal action",
                "sue", "prosecute", "jail", "prison", "criminal",
                "enforcement", "officer", "law", "summons",
                "warrant", "bailiff"
            ],
            "financial": [
                "bank", "account", "sort code", "card number",
                "password", "pin", "otp", "one time password",
                "transfer", "payment", "pay", "money",
                "balance", "funds", "withdraw", "deposit",
                "credit", "debit", "transaction"
            ],
            "impersonation": [
                "hmrc", "irs", "social security", "microsoft",
                "apple", "amazon", "google", "your bank",
                "calling from", "official", "government",
                "representative", "department"
            ],
            "information_request": [
                "tell me your", "confirm your", "verify your",
                "what is your", "give me your", "provide your",
                "read out", "spell your"
            ]
        }

        # Compile regex patterns for phrase matching
        self.compiled = {cat: [re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
                               for phrase in phrases]
                        for cat, phrases in self.keywords.items()}

    def analyze(self, transcript: str) -> Dict[str, Any]:
        """
        Returns counts, scores, and matched keywords per category.
        """
        if not transcript:
            return self._empty_result()

        results = {}
        total_matches = 0
        for category, patterns in self.compiled.items():
            matches = []
            for pat in patterns:
                found = pat.findall(transcript)
                if found:
                    matches.append(found[0])  # keep one example
            count = len(matches)
            total_matches += count
            results[category] = {
                "count": count,
                "examples": matches[:5],  # max 5 examples
                "score": min(1.0, count * 0.2)  # simple scaling
            }

        # Composite urgency score (weighted)
        urgency_score = min(1.0,
            0.4 * results.get("urgency", {}).get("score", 0) +
            0.3 * results.get("threat", {}).get("score", 0) +
            0.3 * results.get("financial", {}).get("score", 0)
        )

        return {
            "categories": results,
            "total_keyword_hits": total_matches,
            "urgency_score": round(urgency_score, 3)
        }

    def _empty_result(self):
        return {
            "categories": {},
            "total_keyword_hits": 0,
            "urgency_score": 0.0
        }