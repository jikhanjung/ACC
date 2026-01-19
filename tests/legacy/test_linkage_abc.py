"""
Test ACC algorithm with ABC example to verify linkage similarity calculation
"""

from acc_core_new import build_acc_iterative

# Example from user's log
# A-B cluster should have sim=0.9
# When C is added, linkage similarity should be (A-C + B-C) / 2 = (0.5 + 0.5) / 2 = 0.5

local_matrix = {
    "A": {"B": 0.9, "C": 0.5},
    "B": {"A": 0.9, "C": 0.5},
    "C": {"A": 0.5, "B": 0.5}
}

global_matrix = {
    "A": {"B": 0.8, "C": 0.4},
    "B": {"A": 0.8, "C": 0.4},
    "C": {"A": 0.4, "B": 0.4}
}

print("="*70)
print("Testing ACC Linkage Similarity Calculation")
print("="*70)
print("\nLocal matrix:")
print("  A-B: 0.9, A-C: 0.5, B-C: 0.5")
print("\nGlobal matrix:")
print("  A-B: 0.8, A-C: 0.4, B-C: 0.4")
print("\n")

print("Expected behavior:")
print("  Step 0: {A, B} cluster formed with sim_local=0.9, sim_global=0.8")
print("  Step 1: Add C to {A, B}")
print("    Linkage similarity (local) = (A-C + B-C) / 2 = (0.5 + 0.5) / 2 = 0.5")
print("    Linkage similarity (global) = (A-C + B-C) / 2 = (0.4 + 0.4) / 2 = 0.4")
print("    New diameter = 1.0 / 0.4 = 2.5")
print("    New angle = 180° × (1 - 0.5) = 90.0°")
print("\n")

steps = build_acc_iterative(local_matrix, global_matrix, unit=1.0, method='average')

print("\n" + "="*70)
print("ACTUAL RESULTS")
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

print("\n" + "="*70)
print("VERIFICATION")
print("="*70)
if len(steps) >= 2:
    final_cluster = steps[1]['clusters'][0]
    print(f"\nFinal cluster: {sorted(final_cluster['members'])}")
    print(f"  Expected local linkage: 0.500")
    print(f"  Actual local linkage: {final_cluster['local_sim']:.3f}")
    print(f"  Match: {'✅' if abs(final_cluster['local_sim'] - 0.5) < 0.001 else '❌'}")
    print(f"\n  Expected global linkage: 0.400")
    print(f"  Actual global linkage: {final_cluster['global_sim']:.3f}")
    print(f"  Match: {'✅' if abs(final_cluster['global_sim'] - 0.4) < 0.001 else '❌'}")
    print(f"\n  Expected diameter: 2.500")
    print(f"  Actual diameter: {final_cluster['diameter']:.3f}")
    print(f"  Match: {'✅' if abs(final_cluster['diameter'] - 2.5) < 0.001 else '❌'}")
    print(f"\n  Expected angle: 90.00°")
    print(f"  Actual angle: {final_cluster['angle']:.2f}°")
    print(f"  Match: {'✅' if abs(final_cluster['angle'] - 90.0) < 0.1 else '❌'}")
