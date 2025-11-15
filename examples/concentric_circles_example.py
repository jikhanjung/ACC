"""
Test concentric circles structure
"""

from acc_core_new import build_acc_iterative
import math

# User's example:
# A-B: subordinate 0.8, inclusive 0.5
# (A+B)-C: subordinate 0.15, inclusive 0.35

sub_matrix = {
    "A": {"B": 0.8, "C": 0.15},
    "B": {"A": 0.8, "C": 0.15},
    "C": {"A": 0.15, "B": 0.15}
}

inc_matrix = {
    "A": {"B": 0.5, "C": 0.35},
    "B": {"A": 0.5, "C": 0.35},
    "C": {"A": 0.35, "B": 0.35}
}

print("="*70)
print("Testing Concentric Circles Structure")
print("="*70)
print("\nExpected:")
print("  Step 0: {A, B}")
print("    - diameter = 1.0 / 0.5 = 2.0, radius = 1.0")
print("    - A, B on radius 1.0 circle")
print("  ")
print("  Step 1: {A, B} + C")
print("    - linkage similarity = 0.35")
print("    - diameter = 1.0 / 0.35 = 2.857, radius = 1.4285")
print("    - A, B STAY on radius 1.0 circle (inner)")
print("    - C placed on radius 1.4285 circle (outer)")
print("    - Concentric circles structure!")
print("\n")

steps = build_acc_iterative(sub_matrix, inc_matrix, unit=1.0)

print("="*70)
print("ACTUAL RESULTS")
print("="*70)

for step_info in steps:
    print(f"\nStep {step_info['step']}: {step_info['action'].upper()}")

    for idx, cluster in enumerate(step_info['clusters']):
        print(f"\n  Cluster {sorted(cluster['members'])}:")
        print(f"    Diameter: {cluster['diameter']:.3f}, Radius: {cluster['radius']:.3f}")
        print(f"    Positions:")

        for member in sorted(cluster['points'].keys()):
            x, y = cluster['points'][member]
            r = math.sqrt(x**2 + y**2)
            print(f"      {member}: ({x:7.3f}, {y:7.3f}) → radius = {r:.3f}")

print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

if len(steps) >= 2:
    final_cluster = steps[1]['clusters'][0]
    print(f"\nFinal cluster: {sorted(final_cluster['members'])}")

    # Check A, B radii
    xa, ya = final_cluster['points']['A']
    xb, yb = final_cluster['points']['B']
    r_a = math.sqrt(xa**2 + ya**2)
    r_b = math.sqrt(xb**2 + yb**2)

    print(f"\n  A radius: {r_a:.3f}")
    print(f"  Expected: 1.000 (should stay on inner circle)")
    print(f"  Match: {'✅' if abs(r_a - 1.0) < 0.01 else '❌ WRONG - got scaled!'}")

    print(f"\n  B radius: {r_b:.3f}")
    print(f"  Expected: 1.000 (should stay on inner circle)")
    print(f"  Match: {'✅' if abs(r_b - 1.0) < 0.01 else '❌ WRONG - got scaled!'}")

    # Check C radius
    xc, yc = final_cluster['points']['C']
    r_c = math.sqrt(xc**2 + yc**2)

    print(f"\n  C radius: {r_c:.3f}")
    print(f"  Expected: 1.429 (should be on outer circle)")
    print(f"  Match: {'✅' if abs(r_c - 1.4285) < 0.01 else '❌'}")
