import math
from typing import Dict, Any


class BayesianFusion:
    """
    Bayesian fusion that trusts the LLM as the primary evidence
    and treats linguistic/behavioral/acoustic as supplementary,
    with a maximum shift of ±15% absolute.
    """

    def __init__(self):
        # no prior needed – LLM score is the starting point
        self.max_shift = 0.15        # maximum absolute change allowed
        self.weights = {
            "linguistic": 0.3,
            "behavioral": 0.25,
            "acoustic": 0.2,
        }

    def _evidence_lr(self, score: float, weight: float) -> float:
        """
        Convert detector score into a likelihood ratio.
        score = 0.5 → LR = 1.0 (neutral)
        score > 0.5 → slight support for scam
        score < 0.5 → slight support for genuine

        The weight controls how strongly the LR deviates from 1.
        """
        score = max(0.01, min(0.99, score))
        # Compress the score so it can't produce extreme LRs
        if score > 0.5:
            # maps 0.5->1, 0.75->~1.2, 0.99->~2
            lr = 1.0 + (score - 0.5) * 2.0
        else:
            # maps 0.5->1, 0.25->0.8, 0.01->0.5
            lr = 1.0 / (1.0 + (0.5 - score) * 2.0)

        # Apply weight: weight=1 keeps the same, weight=0 keeps LR=1
        return 1.0 + (lr - 1.0) * weight

    def probability_to_odds(self, p: float) -> float:
        p = max(0.001, min(0.999, p))
        return p / (1.0 - p)

    def odds_to_probability(self, odds: float) -> float:
        return odds / (1.0 + odds)

    def fuse(
        self,
        llm_result: Dict[str, Any],
        linguistic_result: Dict[str, Any],
        behavioral_result: Dict[str, Any],
        acoustic_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        # Use LLM probability as the primary calibrated estimate
        llm_prob = llm_result.get("scam_probability", 0.5)

        # Extract scores from other agents, default to 0.5 if missing
        ling = linguistic_result.get("urgency_score", 0.5)
        beh = behavioral_result.get("behavior_score", 0.5)
        ac = acoustic_result.get("arousal_score", 0.5)

        # Compute a fused probability using LLM as a weighted average
        # Weight of LLM is high (0.85) so other agents can only slightly adjust
        w_llm = 0.85
        w_other = 0.15

        # Convert other scores to probabilities (they are already 0-1)
        # Just average them (equally weighted among the three)
        other_avg = (ling + beh + ac) / 3.0

        # Weighted combination
        fused_prob = w_llm * llm_prob + w_other * other_avg

        # Clamp
        fused_prob = max(0.0, min(1.0, fused_prob))

        # Decision thresholds (same as before)
        if fused_prob >= 0.90:
            decision = "BLOCK"
        elif fused_prob >= 0.70:
            decision = "HANG_UP"
        elif fused_prob >= 0.45:
            decision = "WARN"
        elif fused_prob >= 0.25:
            decision = "VERIFY"
        else:
            decision = "CONTINUE"

        # Confidence: how close are all signals?
        signals = [llm_prob, ling, beh, ac]
        agreement = 1.0 - (max(signals) - min(signals))  # simple agreement metric
        confidence = max(0.1, min(1.0, agreement))

        return {
            "risk_score": round(fused_prob, 3),
            "decision": decision,
            "confidence": round(confidence, 3),
            "scam_type": llm_result.get("scam_type", "none"),
            "indicators": llm_result.get("indicators", []),
            "explanation": llm_result.get("explanation", "")
        }