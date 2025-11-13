"""
Verify concentric circles structure in full J-T-Y-N-O-Q example
"""

from acc_core_new import build_acc_iterative
import math

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

steps = build_acc_iterative(sub_matrix, inc_matrix, unit=1.0)

print("="*70)
print("CONCENTRIC CIRCLES VERIFICATION")
print("="*70)

for step_info in steps:
    print(f"\n{'='*70}")
    print(f"Step {step_info['step']}: {step_info['action'].upper()}")
    print(f"{'='*70}")

    for idx, cluster in enumerate(step_info['clusters']):
        print(f"\nCluster {idx + 1}: {sorted(cluster['members'])}")
        print(f"  Cluster radius: {cluster['radius']:.3f} (outermost circle)")
        print(f"  Member positions and radii:")

        for member in sorted(cluster['points'].keys()):
            x, y = cluster['points'][member]
            r = math.sqrt(x**2 + y**2)
            is_new = member in step_info.get('highlighted_members', set())
            marker = " <-- NEW" if is_new else ""
            print(f"    {member}: ({x:7.3f}, {y:7.3f}) → radius = {r:.3f}{marker}")

print("\n" + "="*70)
print("FINAL VERIFICATION")
print("="*70)

final_cluster = steps[-1]['clusters'][0]
print(f"\nFinal cluster: {sorted(final_cluster['members'])}")
print(f"Cluster radius: {final_cluster['radius']:.3f}")

print("\nMember radii (should show concentric circles):")
for member in sorted(final_cluster['points'].keys()):
    x, y = final_cluster['points'][member]
    r = math.sqrt(x**2 + y**2)
    print(f"  {member}: {r:.3f}")

print("\nExpected behavior:")
print("  - Earlier members should be on smaller (inner) circles")
print("  - Later members should be on larger (outer) circles")
print("  - Each step adds members to progressively larger circles")
