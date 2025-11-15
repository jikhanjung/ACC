"""
Test ACC iterative algorithm with logging
"""

from acc_core_new import build_acc_iterative

# Example matrices
sub_matrix = {
    "J": {"T": 0.9, "Y": 0.8, "N": 0.4, "O": 0.35, "Q": 0.36},
    "T": {"J": 0.9, "Y": 0.8, "N": 0.38, "O": 0.33, "Q": 0.34},
    "Y": {"J": 0.8, "T": 0.8, "N": 0.37, "O": 0.32, "Q": 0.33},
    "N": {"O": 0.75, "Q": 0.75},
    "O": {"Q": 0.85},
    "Q": {}
}

inc_matrix = {
    "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
    "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
    "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
    "N": {"O": 0.7, "Q": 0.68},
    "O": {"Q": 0.83},
    "Q": {}
}

print("Running ACC Iterative Algorithm with detailed logging...\n")

steps = build_acc_iterative(sub_matrix, inc_matrix, unit=1.0, method='average')

print(f"\n\nFinal Summary:")
print(f"Total steps: {len(steps)}")
if steps:
    final_step = steps[-1]
    clusters = final_step["clusters"]
    if clusters:
        print(f"Final cluster members: {sorted(clusters[0]['members'])}")
