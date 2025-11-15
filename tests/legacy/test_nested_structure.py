"""
Test hierarchical nested structure display
"""

from acc_core_new import build_acc_iterative

# Example with clear nesting
sub_matrix = {
    "A": {"B": 0.9, "C": 0.8, "D": 0.3},
    "B": {"A": 0.9, "C": 0.75, "D": 0.25},
    "C": {"A": 0.8, "B": 0.75, "D": 0.2},
    "D": {}
}

inc_matrix = {
    "A": {"B": 0.85, "C": 0.7, "D": 0.35},
    "B": {"A": 0.85, "C": 0.65, "D": 0.3},
    "C": {"A": 0.7, "B": 0.65, "D": 0.25},
    "D": {}
}

print("="*70)
print("HIERARCHICAL CLUSTER STRUCTURE DISPLAY")
print("="*70)
print("\nExpected clustering order:")
print("  1. A-B pair (highest similarity: 0.9)")
print("  2. Add C to {A, B} → [[A, B], C]")
print("  3. Add D to {A, B, C} → [[[A, B], C], D]")
print("\n")

steps = build_acc_iterative(sub_matrix, inc_matrix, unit=1.0)

print("="*70)
print("ACTUAL CLUSTERING STEPS")
print("="*70)

for step_info in steps:
    print(f"\n{step_info['description']}")
