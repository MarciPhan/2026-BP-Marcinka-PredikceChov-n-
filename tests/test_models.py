import unittest
import numpy as np
from shared.models import CommunityModels

class TestCommunityModels(unittest.TestCase):
    def test_calculate_markov_matrix(self):
        # 0: New, 1: Active, 2: Passive
        transitions = [
            (0, 1), (0, 1), (0, 2),  # 0 -> 1 (2x), 0 -> 2 (1x)
            (1, 1), (1, 2),          # 1 -> 1 (1x), 1 -> 2 (1x)
            (2, 2)                   # 2 -> 2 (1x)
        ]
        matrix = CommunityModels.calculate_markov_matrix(transitions, num_states=3)
        
        # State 0 goes to 1 (2/3) and 2 (1/3)
        self.assertAlmostEqual(matrix[0][0], 0.0)
        self.assertAlmostEqual(matrix[0][1], 2.0 / 3.0)
        self.assertAlmostEqual(matrix[0][2], 1.0 / 3.0)
        
        # State 1 goes to 1 (1/2) and 2 (1/2)
        self.assertAlmostEqual(matrix[1][0], 0.0)
        self.assertAlmostEqual(matrix[1][1], 0.5)
        self.assertAlmostEqual(matrix[1][2], 0.5)
        
        # State 2 goes to 2 (1/1)
        self.assertAlmostEqual(matrix[2][0], 0.0)
        self.assertAlmostEqual(matrix[2][1], 0.0)
        self.assertAlmostEqual(matrix[2][2], 1.0)

    def test_predict_future_states(self):
        matrix = np.array([
            [0.5, 0.5],
            [0.0, 1.0]
        ])
        current_state = np.array([1.0, 0.0])
        
        # After 1 step: [0.5, 0.5]
        res1 = CommunityModels.predict_future_states(current_state, matrix, steps=1)
        self.assertAlmostEqual(res1[0], 0.5)
        self.assertAlmostEqual(res1[1], 0.5)
        
        # After 2 steps: [0.25, 0.75]
        res2 = CommunityModels.predict_future_states(current_state, matrix, steps=2)
        self.assertAlmostEqual(res2[0], 0.25)
        self.assertAlmostEqual(res2[1], 0.75)

    def test_survival_rate_and_expectancy(self):
        # 4 users:
        # User 1 left at day 5 (event=True)
        # User 2 left at day 10 (event=True)
        # User 3 censored at day 10 (event=False)
        # User 4 left at day 15 (event=True)
        
        durations = [5, 10, 10, 15]
        observed = [True, True, False, True]
        
        curve = CommunityModels.calculate_survival_rate(durations, observed)
        
        # At day 5: 1 death out of 4 -> S(5) = 1 - 1/4 = 0.75
        self.assertAlmostEqual(curve[5], 0.75)
        
        # At day 10: 1 death, 1 censored out of 3 -> S(10) = 0.75 * (1 - 1/3) = 0.50
        # Censored is removed from risk set AFTER day 10 calculation
        self.assertAlmostEqual(curve[10], 0.50)
        
        # At day 15: 1 death out of 1 -> S(15) = 0.50 * (1 - 1/1) = 0.00
        self.assertAlmostEqual(curve[15], 0.0)
        
        # Expectancy:
        # 0-5: S=1.0 -> 5 * 1.0 = 5.0
        # 5-10: S=0.75 -> 5 * 0.75 = 3.75
        # 10-15: S=0.50 -> 5 * 0.50 = 2.50
        # Total = 5.0 + 3.75 + 2.50 = 11.25
        expectancy = CommunityModels.estimate_life_expectancy(curve)
        self.assertAlmostEqual(expectancy, 11.25)

if __name__ == '__main__':
    unittest.main()
