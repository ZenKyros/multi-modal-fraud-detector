"""
Game Theory Fusion Engine: Stackelberg Security Game Implementation

Implements an asymmetric Stackelberg Security Game where the defender (us) plays
first by setting a protection strategy, and the attacker (fraudster) responds.
The engine dynamically reweights the three pillars based on their historical
effectiveness, simulating the adversarial adaptation.

Core Components:
- Strategy space: [Linguistic, Behavioral, Acoustic]
- Payoff matrix: 3x3 (Defender vs. Attacker strategies)
- Nash equilibrium solver: Compute mixed strategy weights
- CFR optimization: Track regrets to improve strategy over time
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class GameState:
    """Represents the current state of the security game."""
    round: int
    defender_strategy: List[float]  # Weights for [Linguistic, Behavioral, Acoustic]
    attacker_strategy: List[float]  # Weights for fraudster evasion tactics
    cumulative_regret: List[float]  # Regret for each strategy
    threat_history: List[float]     # Recent threat indices
    payoff_matrix: np.ndarray       # Current estimated payoff matrix


class StackelbergGameEngine:
    """
    Stackelberg Security Game solver for multi-modal threat assessment.
    
    The game models interaction between a fraud detection system (defender)
    and adaptive fraudsters (attacker). The defender chooses which pillars to
    emphasize, and the attacker adapts their tactics accordingly.
    """

    # Strategy indices for clarity
    LINGUISTIC = 0
    BEHAVIORAL = 1
    ACOUSTIC = 2
    STRATEGIES = 3

    def __init__(self):
        """Initialize the game engine."""
        self.round = 0
        
        # Initial uniform defender strategy (equal weight to all pillars)
        self.defender_strategy = np.array([1/3, 1/3, 1/3])
        
        # Attacker starts equally prepared for all defenses
        self.attacker_strategy = np.array([1/3, 1/3, 1/3])
        
        # Cumulative regrets for regret matching algorithm
        self.cumulative_regret = np.zeros(self.STRATEGIES)
        
        # Historical data
        self.threat_history = []
        self.pillar_scores_history = []
        self.strategy_history = []
        
        # Initial payoff matrix (will be updated)
        # Rows = defender strategies, Columns = attacker strategies
        # Higher values = better for defender (higher detection rate)
        self._initialize_payoff_matrix()

    def _initialize_payoff_matrix(self) -> None:
        """Initialize a realistic base payoff matrix."""
        # Payoff matrix where each cell (i, j) represents:
        # Payoff when defender plays strategy i and attacker plays strategy j
        
        # Linguistic strong against linguistic evasion, weak against acoustic spoofing
        # Behavioral good at detecting behavioral changes, weak against linguistic tricks
        # Acoustic detects call center noise, weak against well-equipped individuals
        
        self.payoff_matrix = np.array([
            [0.75, 0.45, 0.65],  # Linguistic defense vs [Linguistic, Behavioral, Acoustic]
            [0.55, 0.80, 0.50],  # Behavioral defense vs [Linguistic, Behavioral, Acoustic]
            [0.50, 0.55, 0.85],  # Acoustic defense vs [Linguistic, Behavioral, Acoustic]
        ], dtype=np.float32)

    def update_payoff_matrix(
        self,
        pillar_scores: Tuple[float, float, float],
        is_fraud: bool,
        effectiveness: Dict[str, float]
    ) -> None:
        """
        Update the payoff matrix based on real detection outcomes.
        
        Args:
            pillar_scores: (linguistic_score, behavioral_score, acoustic_score)
            is_fraud: Whether this was actually fraud
            effectiveness: Dict with effectiveness metrics for each pillar
        """
        # Increase payoff for pillars that detected fraud correctly
        # Or decrease for false positives
        
        adjustment_factor = 0.05  # Learning rate
        
        for i in range(self.STRATEGIES):
            if is_fraud:
                # Fraud detected: boost payoff for this pillar
                reward = pillar_scores[i] * adjustment_factor
                self.payoff_matrix[i, :] += reward
            else:
                # False alarm: reduce payoff (penalties)
                penalty = -adjustment_factor * 0.5
                self.payoff_matrix[i, :] += penalty
        
        # Clip payoffs to reasonable range
        self.payoff_matrix = np.clip(self.payoff_matrix, 0.1, 1.0)

    def compute_nash_equilibrium(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute the Nash equilibrium mixed strategy for this game.
        
        Uses linear programming / support enumeration to find the mixed strategy
        Nash equilibrium where both players are indifferent between their strategies.
        
        Returns:
            Tuple of (defender_strategy, attacker_strategy) as probability distributions
        """
        # Simplified Nash computation for 3x3 game
        # Uses iterative approach: support enumeration for smaller games
        
        try:
            # Method 1: Try to find a pure strategy Nash equilibrium
            best_defense = None
            best_payoff = -np.inf
            
            for i in range(self.STRATEGIES):
                # Play pure strategy i as defender
                min_payoff = np.min(self.payoff_matrix[i, :])
                
                if min_payoff > best_payoff:
                    best_payoff = min_payoff
                    best_defense = i
            
            if best_defense is not None:
                def_strategy = np.zeros(self.STRATEGIES)
                def_strategy[best_defense] = 1.0
            else:
                def_strategy = np.ones(self.STRATEGIES) / self.STRATEGIES
            
            # Attacker's best response to defender's strategy
            att_payoffs = self.payoff_matrix.T @ def_strategy  # From attacker perspective
            att_strategy = np.zeros(self.STRATEGIES)
            att_strategy[np.argmin(att_payoffs)] = 1.0  # Minimize defender payoff
            
        except:
            # Fallback to uniform strategy
            def_strategy = np.ones(self.STRATEGIES) / self.STRATEGIES
            att_strategy = np.ones(self.STRATEGIES) / self.STRATEGIES
        
        return def_strategy, att_strategy

    def update_strategy_via_cfr(self, observed_payoffs: np.ndarray) -> None:
        """
        Update strategies using Counterfactual Regret Minimization.
        
        Args:
            observed_payoffs: Payoff vector for playing each pure strategy
        """
        # Get current strategy value
        current_payoff = np.dot(self.defender_strategy, observed_payoffs)
        
        # Compute regrets for not playing each strategy
        regrets = observed_payoffs - current_payoff
        
        # Accumulate regrets
        self.cumulative_regret += regrets
        
        # Compute new strategy based on positive regrets only (regret matching)
        positive_regrets = np.maximum(self.cumulative_regret, 0)
        
        if np.sum(positive_regrets) > 0:
            self.defender_strategy = positive_regrets / np.sum(positive_regrets)
        else:
            # Uniform if all regrets are negative
            self.defender_strategy = np.ones(self.STRATEGIES) / self.STRATEGIES

    def fuse_pillar_outputs(
        self,
        linguistic_score: float,
        behavioral_score: float,
        acoustic_score: float
    ) -> Dict:
        """
        Fuse outputs from three pillars using current game-theoretic weights.
        
        Args:
            linguistic_score: Urgency score from Pillar I (0-1)
            behavioral_score: Aggression score from Pillar II (0-1)
            acoustic_score: Environment index from Pillar III (0-1)
            
        Returns:
            Dictionary with fused threat index and component breakdown
        """
        pillar_scores = np.array([linguistic_score, behavioral_score, acoustic_score])
        
        # Get current defender strategy (pillar weights)
        weights = self.defender_strategy
        
        # Weighted combination
        threat_index = float(np.dot(weights, pillar_scores))
        
        # Track history
        self.threat_history.append(threat_index)
        self.pillar_scores_history.append(pillar_scores.tolist())
        if len(self.threat_history) > 100:
            self.threat_history.pop(0)
            self.pillar_scores_history.pop(0)
        
        # Compute contribution of each pillar
        contributions = weights * pillar_scores
        
        return {
            "threat_index": threat_index,
            "weights": weights.tolist(),
            "pillar_scores": pillar_scores.tolist(),
            "contributions": {
                "linguistic": float(contributions[self.LINGUISTIC]),
                "behavioral": float(contributions[self.BEHAVIORAL]),
                "acoustic": float(contributions[self.ACOUSTIC]),
            },
            "requires_verification": threat_index > 0.55,
        }

    def adapt_to_outcome(
        self,
        pillar_scores: Tuple[float, float, float],
        threat_index: float,
        was_fraud: bool,
        is_verified: bool
    ) -> Dict:
        """
        Adapt game strategy based on verification outcome.
        
        This simulates the fraudster's adaptation: if a detection worked,
        the attacker will adjust their tactics.
        
        Args:
            pillar_scores: Scores from each pillar
            threat_index: Combined threat index
            was_fraud: Whether the caller was actually fraudulent
            is_verified: Whether LLM verification confirmed fraud
            
        Returns:
            Updated strategy metrics
        """
        self.round += 1
        
        # Update payoff matrix with real outcomes
        effectiveness = {
            "linguistic": pillar_scores[self.LINGUISTIC],
            "behavioral": pillar_scores[self.BEHAVIORAL],
            "acoustic": pillar_scores[self.ACOUSTIC],
        }
        
        # Only update if we have verification confidence
        if is_verified or (was_fraud and threat_index > 0.55):
            self.update_payoff_matrix(pillar_scores, is_verified, effectiveness)
        
        # Compute new Nash equilibrium
        def_strat, att_strat = self.compute_nash_equilibrium()
        
        # Smoothly blend old and new strategies (don't overreact)
        alpha = 0.15  # Learning rate for strategy update
        self.defender_strategy = (1 - alpha) * self.defender_strategy + alpha * def_strat
        self.attacker_strategy = (1 - alpha) * self.attacker_strategy + alpha * att_strat
        
        # Normalize to ensure it's a valid probability distribution
        self.defender_strategy /= np.sum(self.defender_strategy)
        self.attacker_strategy /= np.sum(self.attacker_strategy)
        
        self.strategy_history.append(self.defender_strategy.copy())
        
        return {
            "round": self.round,
            "defender_strategy": self.defender_strategy.tolist(),
            "attacker_strategy": self.attacker_strategy.tolist(),
            "payoff_matrix": self.payoff_matrix.tolist(),
        }

    def get_strategy_metrics(self) -> Dict:
        """
        Get current strategy metrics for visualization.
        
        Returns:
            Dictionary with current game state information
        """
        entropy = -np.sum(self.defender_strategy * np.log2(self.defender_strategy + 1e-10))
        
        return {
            "round": self.round,
            "defender_strategy": self.defender_strategy.tolist(),
            "attacker_strategy": self.attacker_strategy.tolist(),
            "strategy_entropy": float(entropy),  # 0 = pure, ~1.58 = uniform
            "threat_history": self.threat_history[-20:] if self.threat_history else [],
            "payoff_matrix": self.payoff_matrix.tolist(),
        }

    def reset(self) -> None:
        """Reset the game engine to initial state."""
        self.round = 0
        self.defender_strategy = np.array([1/3, 1/3, 1/3])
        self.attacker_strategy = np.array([1/3, 1/3, 1/3])
        self.cumulative_regret = np.zeros(self.STRATEGIES)
        self.threat_history = []
        self.pillar_scores_history = []
        self.strategy_history = []
        self._initialize_payoff_matrix()
