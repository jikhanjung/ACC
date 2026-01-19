"""
Test ACC algorithm with simple A, B, C example
"""

from acc_core_new import build_acc_iterative

# Simple 3-area example from user's log
local_matrix = {
    "A": {"B": 0.5, "C": 0.2},
    "B": {"A": 0.5, "C": 0.2},
    "C": {"A": 0.2, "B": 0.2}
}

global_matrix = {
    "A": {"B": 0.3, "C": 0.15},
    "B": {"A": 0.3, "C": 0.15},
    "C": {"A": 0.15, "B": 0.15}
}

print("="*70)
print("Testing ACC with A, B, C example")
print("="*70)
print("\nLocal matrix (specific time period):")
print("  A-B: 0.5, A-C: 0.2, B-C: 0.2")
print("\nGlobal matrix (overall period):")
print("  A-B: 0.3, A-C: 0.15, B-C: 0.15")
print("\n")

steps = build_acc_iterative(local_matrix, global_matrix, unit=1.0, method='average')

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

for step_info in steps:
    print(f"\nStep {step_info['step']}: {step_info['action'].upper()}")
    print(f"  {step_info['description']}")

    for idx, cluster in enumerate(step_info['clusters']):
        print(f"\n  Cluster {idx + 1}: {sorted(cluster['members'])}")
        print(f"    Local sim: {cluster['local_sim']:.3f}")
        print(f"    Global sim: {cluster['global_sim']:.3f}")
        print(f"    Diameter: {cluster['diameter']:.3f}")
        print(f"    Angle: {cluster['angle']:.2f}°")
