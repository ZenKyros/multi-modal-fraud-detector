import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BayesianFusionEngine:
    """
    Improved Bayesian Fusion Engine with:
    - Adaptive prior updates based on recent history
    - Smoother posterior updates with exponential forgetting
    - Better likelihood modeling with Beta distributions
    - Confidence score for each prediction
    """
    
    def __init__(self, alpha: float = 0.3):
        """
        Args:
            alpha: Forgetting factor for prior adaptation (0-1)
                  Higher = faster adaptation to new data
        """
        self.type_names = ["Normal", "BankScam", "TechSupport", "Government"]
        self.num_types = len(self.type_names)
        
        # Initial priors (can be updated adaptively)
        self.prior = np.array([0.6, 0.2, 0.1, 0.1])
        self.adaptive_prior = self.prior.copy()
        self.alpha = alpha
        
        # Beta parameters for each pillar and type
        # Each type has (alpha, beta) parameters for Beta distribution
        self.pillar_params = {
            "linguistic": {
                "Normal": (2.0, 4.0),
                "BankScam": (8.0, 2.0),
                "TechSupport": (5.0, 3.0),
                "Government": (6.0, 3.0)
            },
            "behavioral": {
                "Normal": (3.0, 4.0),
                "BankScam": (7.0, 3.0),
                "TechSupport": (5.0, 4.0),
                "Government": (4.0, 4.0)
            },
            "acoustic": {
                "Normal": (2.0, 5.0),
                "BankScam": (4.0, 5.0),
                "TechSupport": (7.0, 3.0),
                "Government": (5.0, 4.0)
            }
        }
        
        # History for adaptive prior updates
        self.posterior_history = []
        self.history_length = 20
        self.iteration = 0
        
        logger.info("🧠 Improved Bayesian Fusion Engine initialized.")

    def calculate_threat_index(self, pillar_results: Dict[str, Any]) -> float:
        """Calculate threat index with improved Bayesian fusion."""
        # Extract scores
        scores = {
            "linguistic": pillar_results.get("linguistic", {}).get("pillar_score", 0.0),
            "behavioral": pillar_results.get("behavioral", {}).get("pillar_score", 0.0),
            "acoustic": pillar_results.get("acoustic", {}).get("pillar_score", 0.0)
        }
        
        # Update adaptive prior based on history
        self._update_adaptive_prior(scores)
        
        # Compute likelihood for each type
        likelihoods = np.zeros(self.num_types)
        for t, type_name in enumerate(self.type_names):
            ll = 1.0
            for pillar, score in scores.items():
                a, b = self.pillar_params[pillar][type_name]
                ll *= self._beta_pdf(score, a, b)
            likelihoods[t] = ll
        
        # Bayes' rule with adaptive prior
        unnormalized = self.adaptive_prior * likelihoods
        evidence = np.sum(unnormalized)
        if evidence > 0:
            posterior = unnormalized / evidence
        else:
            posterior = self.prior.copy()
        
        # Store posterior history
        self.posterior_history.append(posterior.copy())
        if len(self.posterior_history) > self.history_length:
            self.posterior_history.pop(0)
        
        # Compute threat index with confidence
        threat_index = 1.0 - posterior[0]
        
        # Compute confidence (based on posterior entropy)
        confidence = self._compute_confidence(posterior)
        
        self.iteration += 1
        if self.iteration % 5 == 0:
            logger.info(f"📊 Posterior: {posterior.round(3).tolist()}")
            logger.info(f"📈 Threat: {threat_index:.3f}, Confidence: {confidence:.3f}")
        
        return float(np.clip(threat_index, 0.0, 1.0))

    def _update_adaptive_prior(self, scores: Dict[str, float]):
        """Update adaptive prior based on recent history."""
        if len(self.posterior_history) < 5:
            return
        
        # Compute average posterior over recent history
        recent_avg = np.mean(self.posterior_history[-5:], axis=0)
        
        # Smooth update with forgetting factor
        self.adaptive_prior = (1 - self.alpha) * self.adaptive_prior + self.alpha * recent_avg
        self.adaptive_prior = self.adaptive_prior / np.sum(self.adaptive_prior)

    def _beta_pdf(self, x: float, a: float, b: float) -> float:
        """Beta distribution probability density function."""
        if x <= 0 or x >= 1:
            return 1e-10
        # Log-beta for numerical stability
        from scipy.special import betaln
        log_pdf = (a - 1) * np.log(x) + (b - 1) * np.log(1 - x) - betaln(a, b)
        return np.exp(log_pdf)

    def _compute_confidence(self, posterior: np.ndarray) -> float:
        """Compute confidence based on posterior entropy."""
        # High confidence = low entropy
        entropy = -np.sum(posterior * np.log(posterior + 1e-10))
        max_entropy = np.log(self.num_types)
        confidence = 1.0 - (entropy / max_entropy)
        return float(np.clip(confidence, 0.0, 1.0))

    def get_strategy_weights(self) -> Dict[str, Any]:
        """Return current fusion state."""
        # For Bayesian fusion, we return posterior-based weights
        # This mimics the "strategy" concept but is posterior-driven
        weights = self.adaptive_prior.copy()
        weights[0] = 0  # Normal type weight set to 0 for strategy
        weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.array([1/3, 1/3, 1/3])
        
        return {
            "weights": {
                "linguistic": float(weights[1] if len(weights) > 1 else 0.33),
                "behavioral": float(weights[2] if len(weights) > 2 else 0.33),
                "acoustic": float(weights[3] if len(weights) > 3 else 0.33)
            },
            "posterior": {
                "normal": float(self.adaptive_prior[0]),
                "bank_scam": float(self.adaptive_prior[1]),
                "tech_support": float(self.adaptive_prior[2]),
                "government": float(self.adaptive_prior[3])
            },
            "threat_index": 1.0 - float(self.adaptive_prior[0]),
            "confidence": 1.0 - float(self.adaptive_prior[0])  # Placeholder, can be improved
        }