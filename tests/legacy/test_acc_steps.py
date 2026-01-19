"""
Test ACC step-by-step algorithm
"""

from acc_core import DendroNode, build_acc_steps

# Create sample dendrograms (same as in acc_core.py example)
# Local dendrogram: (((J,T),Y),(N,(O,Q)))
jt = DendroNode(["J", "T"], sim=0.9)
jty = DendroNode(["J", "T", "Y"], sim=0.8, left=jt, right=DendroNode(["Y"], sim=1.0))
oq = DendroNode(["O", "Q"], sim=0.85)
noq = DendroNode(["N", "O", "Q"], sim=0.75, left=DendroNode(["N"], sim=1.0), right=oq)
sub_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.6, left=jty, right=noq)

# Global dendrogram
jt_inc = DendroNode(["J", "T"], sim=0.88)
jy_inc = DendroNode(["J", "Y"], sim=0.82)
jty_inc = DendroNode(["J", "T", "Y"], sim=0.78, left=jt_inc, right=jy_inc)
oq_inc = DendroNode(["O", "Q"], sim=0.83)
n_inc = DendroNode(["N"], sim=1.0)
noq_inc = DendroNode(["N", "O", "Q"], sim=0.7, left=n_inc, right=oq_inc)
inc_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.55, left=jty_inc, right=noq_inc)

# Global similarity matrix
global_matrix = {
    "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
    "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
    "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
    "N": {"O": 0.7, "Q": 0.68, "J": 0.4},
    "O": {"Q": 0.83, "N": 0.7},
    "Q": {"O": 0.83, "N": 0.68},
}

print("Testing ACC Step-by-Step Algorithm")
print("="*60)

# Run the step-by-step algorithm
steps = build_acc_steps(sub_root, inc_root, global_matrix, unit=1.0)

print(f"\nTotal steps generated: {len(steps)}\n")

# Display each step
for step_info in steps:
    print(f"\n{'='*60}")
    print(f"Step {step_info['step']}: {step_info['action'].upper()}")
    print(f"{'='*60}")
    print(f"Description: {step_info['description']}")

    cluster = step_info['current_cluster']
    print(f"\nCurrent cluster:")
    print(f"  Members: {sorted(cluster['members'])}")
    print(f"  Diameter: {cluster['diameter']:.3f}")
    print(f"  Theta: {cluster['theta']:.2f}°")
    print(f"  sim_local: {cluster['sim_local']:.3f}")
    print(f"  sim_global: {cluster['sim_global']:.3f}")

    if step_info['highlighted_members']:
        print(f"\nHighlighted (new) members: {sorted(step_info['highlighted_members'])}")

    print(f"\nMember positions:")
    for member in sorted(cluster['points'].keys()):
        x, y = cluster['points'][member]
        marker = " <-- NEW" if member in step_info['highlighted_members'] else ""
        print(f"  {member}: ({x:7.3f}, {y:7.3f}){marker}")

print(f"\n{'='*60}")
print("Test completed successfully!")
print(f"{'='*60}")

# Summary
final_step = steps[-1]
final_cluster = final_step['current_cluster']
print(f"\nFinal state:")
print(f"  Total members: {len(final_cluster['members'])}")
print(f"  Final diameter: {final_cluster['diameter']:.3f}")
print(f"  Final theta: {final_cluster['theta']:.2f}°")
