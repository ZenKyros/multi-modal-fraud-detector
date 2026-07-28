import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BayesianFusionEngine:
    def __init__(self):
        self.type_names = ["Normal", "BankScam", "TechSupport", "Government"]
        self.num_types = len(self.type_names)
        self.prior = np.array([0.6, 0.2, 0.1, 0.1])

        # Beta parameters for each pillar (alpha, beta) per type
        self.linguistic_alpha = np.array([[2,4],[8,2],[5,3],[6,3]])
        self.linguistic_beta = np.array([[4,2],[2,8],[3,5],[3,6]])
        self.behavioral_alpha = np.array([[3,4],[7,3],[5,4],[4,4]])
        self.behavioral_beta = np.array([[4,3],[3,7],[4,5],[4,4]])
        self.acoustic_alpha = np.array([[2,5],[4,5],[7,3],[5,4]])
        self.acoustic_beta = np.array([[5,2],[5,4],[3,7],[4,5]])

        self.posterior = self.prior.copy()
        self.pillar_scores = [0.0, 0.0, 0.0]
        self.iteration = 0
        logger.info("🧠 Bayesian Fusion Engine initialized (Matrix‑Driven).")

    def calculate_threat_index(self, pillar_results: Dict[str, Any]) -> float:
        ling = pillar_results.get("linguistic", {}).get("pillar_score", 0.0)
        beh = pillar_results.get("behavioral", {}).get("pillar_score", 0.0)
        aco = pillar_results.get("acoustic", {}).get("pillar_score", 0.0)
        self.pillar_scores = [ling, beh, aco]

        likelihoods = np.zeros(self.num_types)
        for t in range(self.num_types):
            ll_ling = self._triangular_pdf(ling, self.linguistic_alpha[t,0], self.linguistic_beta[t,0])
            ll_beh = self._triangular_pdf(beh, self.behavioral_alpha[t,0], self.behavioral_beta[t,0])
            ll_aco = self._triangular_pdf(aco, self.acoustic_alpha[t,0], self.acoustic_beta[t,0])
            likelihoods[t] = ll_ling * ll_beh * ll_aco

        unnormalized = self.prior * likelihoods
        evidence = np.sum(unnormalized)
        if evidence > 0:
            self.posterior = unnormalized / evidence

        threat_index = 1.0 - self.posterior[0]
        self.iteration += 1
        if self.iteration % 5 == 0:
            logger.info(f"📊 Posterior: {self.posterior.round(3).tolist()}")
            logger.info(f"📈 Threat: {threat_index:.3f}")

        return float(np.clip(threat_index, 0.0, 1.0))

    def _triangular_pdf(self, x, alpha, beta):
        mean = alpha / (alpha + beta) if (alpha+beta)>0 else 0.5
        if x < 0 or x > 1:
            return 1e-10
        if x <= mean:
            return 2 * x / mean if mean > 0 else 1e-10
        else:
            return 2 * (1 - x) / (1 - mean) if mean < 1 else 1e-10

    def _compute_payoff_matrix(self) -> np.ndarray:
        scores = self.pillar_scores
        matrix = np.zeros((3,3))
        for i in range(3):
            for j in range(3):
                if i == j:
                    base = scores[i] * 1.2
                else:
                    base = (scores[i] + scores[j]) / 2 * 0.8
                matrix[i,j] = min(1.0, max(0.0, base))
        return matrix

    def _nash_equilibrium(self, matrix: np.ndarray) -> np.ndarray:
        strat = np.array([1/3, 1/3, 1/3])
        for _ in range(100):
            defender_payoff = np.dot(strat, matrix)
            attacker_best = np.argmin(defender_payoff)
            defender_best = np.argmax(matrix[:, attacker_best])
            new_strat = np.zeros(3)
            new_strat[defender_best] = 0.6
            strat = 0.4 * strat + 0.6 * new_strat
            strat = strat / np.sum(strat)
        return strat

    def get_equilibrium(self) -> Dict[str, Any]:
        payoff = self._compute_payoff_matrix()
        def_strat = self._nash_equilibrium(payoff)
        att_strat = self._nash_equilibrium(payoff.T)
        return {
            "defender": def_strat.tolist(),
            "attacker": att_strat.tolist(),
            "payoff_matrix": payoff.tolist()
        }

    def get_strategy_weights(self) -> Dict[str, Any]:
        eq = self.get_equilibrium()
        return {
            "weights": {
                "linguistic": eq["defender"][0],
                "behavioral": eq["defender"][1],
                "acoustic": eq["defender"][2]
            },
            "posterior": {
                "normal": float(self.posterior[0]),
                "bank_scam": float(self.posterior[1]),
                "tech_support": float(self.posterior[2]),
                "government": float(self.posterior[3])
            },
            "threat_index": 1.0 - float(self.posterior[0]),
            "payoff_matrix": eq["payoff_matrix"],
            "defender_equilibrium": eq["defender"],
            "attacker_equilibrium": eq["attacker"]
        }