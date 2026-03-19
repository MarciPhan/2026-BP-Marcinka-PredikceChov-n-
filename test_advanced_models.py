
import sys
import os
from pathlib import Path
import numpy as np

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared.models import CommunityModels

def test_markov():
    print("--- Testing Markov Model ---")
    # Transitions: (from_state, to_state)
    # States: 0:New, 1:Active, 2:Passive, 3:Inactive, 4:Churned
    transitions = [
        (0, 1), (0, 1), (0, 2), # 2 Active, 1 Passive
        (1, 1), (1, 1), (1, 3), # 2 Stay Active, 1 Inactive
        (2, 1), (2, 2), (2, 3), # 1 Active, 1 Passive, 1 Inactive
        (3, 3), (3, 4),         # 1 Stay Inactive, 1 Churn
        (4, 4)                  # Absorbing state
    ]
    
    matrix = CommunityModels.calculate_markov_matrix(transitions)
    print("Transition Matrix:\n", matrix)
    
    # Check if rows sum to 1
    for i, row in enumerate(matrix):
        s = np.sum(row)
        print(f"Row {i} sum: {s}")
        assert np.isclose(s, 1.0) or s == 0
        
    # Future prediction
    current = np.array([1, 0, 0, 0, 0]) # 100% New users
    future = CommunityModels.predict_future_states(current, matrix, steps=5)
    print("Distribution after 5 steps:", future)
    print("Sum:", np.sum(future))

def test_survival():
    print("\n--- Testing Survival Analysis ---")
    # Days survived: [10, 20, 30, 30, 40]
    # Event observed (churned): [True, True, True, False, False]
    durations = [10, 20, 30, 30, 40]
    observed = [True, True, True, False, False]
    
    curve = CommunityModels.calculate_survival_rate(durations, observed)
    print("Survival Curve (KM):", curve)
    
    expectancy = CommunityModels.estimate_life_expectancy(curve)
    print("Life Expectancy:", expectancy, "days")
    
    # Simple check
    assert expectancy > 10 and expectancy < 40

if __name__ == "__main__":
    try:
        test_markov()
        test_survival()
        print("\n✅ All mathematical tests PASSED!")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
