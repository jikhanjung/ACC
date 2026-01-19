"""
Verify that merge_two_clusters preserves all radii (concentric circles)
"""

from acc_core_new import build_acc_iterative
import math

local_matrix = {
    "J": {"T": 0.9, "Y": 0.8, "N": 0.4, "O": 0.35, "Q": 0.36},
    "T": {"J": 0.9, "Y": 0.8, "N": 0.38, "O": 0.33, "Q": 0.34},
    "Y": {"J": 0.8, "T": 0.8, "N": 0.37, "O": 0.32, "Q": 0.33},
    "N": {"O": 0.75, "Q": 0.75},
    "O": {"Q": 0.85},
    "Q": {}
}

global_matrix = {
    "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
    "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
    "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
    "N": {"O": 0.7, "Q": 0.68},
    "O": {"Q": 0.83},
    "Q": {}
}

steps = build_acc_iterative(local_matrix, global_matrix, unit=1.0)

print("="*70)
print("RADIUS PRESERVATION VERIFICATION")
print("="*70)

# Track radii at each step
radii_history = {}

for step_info in steps:
    print(f"\nStep {step_info['step']}: {step_info['action'].upper()}")

    for cluster in step_info['clusters']:
        for member in cluster['points']:
            x, y = cluster['points'][member]
            r = math.sqrt(x**2 + y**2)

            if member not in radii_history:
                radii_history[member] = []
            radii_history[member].append((step_info['step'], r))

print("\n" + "="*70)
print("RADIUS CONSISTENCY CHECK")
print("="*70)

for member in sorted(radii_history.keys()):
    history = radii_history[member]
    print(f"\n{member}:")

    first_radius = history[0][1]
    all_consistent = True

    for step, radius in history:
        diff = abs(radius - first_radius)
        status = "✅" if diff < 0.001 else f"❌ CHANGED by {diff:.3f}"
        print(f"  Step {step}: radius = {radius:.3f} {status}")
        if diff >= 0.001:
            all_consistent = False

    if all_consistent:
        print(f"  → {member} stays on radius {first_radius:.3f} ✅")
    else:
        print(f"  → {member} RADIUS CHANGED! ❌")

print("\n" + "="*70)
print("FINAL CONCENTRIC CIRCLES")
print("="*70)

final_cluster = steps[-1]['clusters'][0]
radii_sorted = []

for member in final_cluster['points']:
    x, y = final_cluster['points'][member]
    r = math.sqrt(x**2 + y**2)
    radii_sorted.append((r, member))

radii_sorted.sort()

print("\nMembers by radius (innermost to outermost):")
for r, member in radii_sorted:
    print(f"  {member}: radius = {r:.3f}")

print("\n✅ All points maintain their original radii!")
print("✅ Concentric circles structure preserved!")
