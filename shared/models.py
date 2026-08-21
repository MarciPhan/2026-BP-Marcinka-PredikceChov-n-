import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from enum import IntEnum

class UserState(IntEnum):
    NEW = 0
    ACTIVE = 1
    PASSIVE = 2
    INACTIVE = 3

class CommunityModels:
    """
    Mathematical implementations of Markov Chains and Survival Analysis
    for prototypical analytical models.
    """

    @staticmethod
    def calculate_markov_matrix(transitions: List[Tuple[int, int]], num_states: int = len(UserState)) -> np.ndarray:
        """
        Calculates the transition probability matrix based strictly on historical data.
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
                # BP requirement: Do not use artificial probabilities (e.g., matrix[i][i] = 1.0)
                # for missing data. The row remains all zeros. This means if a system enters
                # an unobserved state, the prediction will explicitly yield zeros (undefined)
                # rather than fabricating a false continuation.
                pass
                
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
        Kaplan-Meier estimator for activity survival (not necessarily membership).
        durations: list of days since observation started until last activity or event.
        event_observed: True if the user actually dropped activity (event occurred), False if censored (still active).
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
    def estimate_median_survival(survival_curve: Dict[int, float]) -> Optional[int]:
        """
        Calculates the exact median survival time (first t where S(t) <= 0.5).
        If the curve never drops to 0.5, the median is undefined (returns None).
        """
        for t in sorted(survival_curve.keys()):
            if survival_curve[t] <= 0.5:
                return t
        return None

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
