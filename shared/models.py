
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

class CommunityModels:
    """
    Mathematical implementations of Markov Chains and Survival Analysis
    for community behavior prediction.
    """

    @staticmethod
    def calculate_markov_matrix(transitions: List[Tuple[int, int]], num_states: int = 5) -> np.ndarray:
        """
        Calculates the transition probability matrix.
        States: 0: New, 1: Active, 2: Passive, 3: Inactive, 4: Churned
        """
        matrix = np.zeros((num_states, num_states))
        
        # Count transitions
        for start, end in transitions:
            matrix[start][end] += 1
            
        # Normalize to probabilities
        for i in range(num_states):
            row_sum = np.sum(matrix[i])
            if row_sum > 0:
                matrix[i] = matrix[i] / row_sum
            else:
                # If no data for a state, assume it stays in that state (equilibrium)
                matrix[i][i] = 1.0
                
        return matrix

    @staticmethod
    def predict_future_states(current_vector: np.ndarray, matrix: np.ndarray, steps: int = 7) -> np.ndarray:
        """
        Predicts state distribution after N steps.
        """
        result = current_vector
        for _ in range(steps):
            result = np.dot(result, matrix)
        return result

    @staticmethod
    def calculate_survival_rate(durations: List[int], event_observed: List[bool]) -> Dict[int, float]:
        """
        Kaplan-Meier estimator for survival (retention) rate.
        durations: list of days since join until last activity or leave.
        event_observed: True if the user actually left (churned), False if censored (still active).
        """
        if not durations:
            return {}

        sorted_indices = np.argsort(durations)
        d = np.array(durations)[sorted_indices]
        e = np.array(event_observed)[sorted_indices]

        unique_times = np.unique(d)
        survival_curve = {}
        s_t = 1.0
        n_at_risk = len(d)

        for t in unique_times:
            # Number of events at time t
            n_events = np.sum((d == t) & e)
            # Number of censored at time t (handled at the end of the interval)
            n_censored = np.sum((d == t) & ~e)
            
            if n_at_risk > 0:
                s_t *= (1 - n_events / n_at_risk)
                
            survival_curve[int(t)] = float(s_t)
            n_at_risk -= (n_events + n_censored)

        return survival_curve

    @staticmethod
    def estimate_life_expectancy(survival_curve: Dict[int, float]) -> float:
        """
        Calculates the Mean Residual Life / Expectancy from the survival curve area.
        """
        if not survival_curve:
            return 0.0
            
        times = sorted(survival_curve.keys())
        area = 0.0
        prev_t = 0
        prev_s = 1.0
        
        for t in times:
            area += prev_s * (t - prev_t)
            prev_t = t
            prev_s = survival_curve[t]
            
        return round(area, 2)
