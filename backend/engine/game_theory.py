import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class GameTheoryEngine:
    def __init__(self, learning_rate: float = 0.3, equilibrium_blend: float = 0.2):
        self.strategies = ["linguistic", "behavioral", "acoustic"]
        self.num_strategies = len(self.strategies)
        self.payoff_matrix = np.array([
            [0.7, 0.3, 0.5],
            [0.4, 0.8, 0.3],
            [0.5, 0.2, 0.6]
        ])
        self.weights = np.array([1/3, 1/3, 1/3])
        self.pillar_performance = {s: 0.5 for s in self.strategies}
        self.learning_rate = learning_rate
        self.equilibrium_blend = equilibrium_blend
        self.iteration_count = 0
        logger.info(f"GameTheoryEngine initialized with lr={learning_rate}, blend={equilibrium_blend}")

    def calculate_threat_index(self, pillar_results: Dict[str, Any]) -> float:
        scores = []
        for s in self.strategies:
            score = pillar_results.get(s, {}).get("pillar_score", 0.0)
            scores.append(score)

        # Update performance tracking
        self._update_performance(scores)

        # Update payoff matrix
        self._update_payoff_matrix(scores)

        # Compute Nash equilibrium
        nash_eq = self._compute_nash_equilibrium()

        # Blend weights
        self.weights = (1 - self.equilibrium_blend) * self.weights + self.equilibrium_blend * np.array(nash_eq)
        self.weights = np.clip(self.weights, 0.05, 0.95)  # prevent extreme values
        self.weights = self.weights / np.sum(self.weights)

        # Log every 10 iterations
        self.iteration_count += 1
        if self.iteration_count % 10 == 0:
            logger.info(f"Weights: {self.weights.tolist()}")

        # Compute weighted sum
        weighted_sum = np.dot(self.weights, scores)

        # Apply game adjustment
        adjustment = self._compute_game_adjustment(nash_eq)
        threat_index = weighted_sum * (1 + adjustment)
        return float(np.clip(threat_index, 0.0, 1.0))

    def _update_performance(self, scores: List[float]):
        for i, s in enumerate(self.strategies):
            old = self.pillar_performance[s]
            new = old * (1 - self.learning_rate) + scores[i] * self.learning_rate
            self.pillar_performance[s] = new

    def _update_payoff_matrix(self, scores: List[float]):
        for i in range(self.num_strategies):
            self.payoff_matrix[i, i] = 0.5 + 0.5 * scores[i]
            for j in range(self.num_strategies):
                if i != j:
                    avg = (scores[i] + scores[j]) / 2
                    self.payoff_matrix[i, j] = 0.3 + 0.4 * avg

    def _compute_nash_equilibrium(self) -> List[float]:
        strategies = np.array([1/3, 1/3, 1/3])
        for _ in range(50):  # fewer iterations for speed
            attacker_best = np.argmin(np.dot(self.payoff_matrix.T, strategies))
            defender_best = np.argmax(self.payoff_matrix[:, attacker_best])
            new_strategies = np.zeros(3)
            new_strategies[defender_best] = 0.6
            strategies = 0.4 * strategies + 0.6 * new_strategies
            strategies = strategies / np.sum(strategies)
        return strategies.tolist()

    def _compute_game_adjustment(self, nash_eq: List[float]) -> float:
        nash = np.array(nash_eq)
        divergence = np.sum(np.abs(self.weights - nash)) / 2
        return 0.1 * (1 - 2 * divergence)

    def get_strategy_weights(self) -> Dict[str, Any]:
        return {
            "weights": {
                "linguistic": float(self.weights[0]),
                "behavioral": float(self.weights[1]),
                "acoustic": float(self.weights[2])
            },
            "performance": self.pillar_performance,
            "payoff_matrix": self.payoff_matrix.tolist()
        }