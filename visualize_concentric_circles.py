"""
Visualize ACC with concentric circles at each step
"""

from acc_core_new import build_acc_iterative
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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

# Create visualization for each step
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for step_idx, step_info in enumerate(steps):
    ax = axes[step_idx]
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)

    # Collect all radii from all clusters
    all_radii = set()
    all_points = {}

    for cluster in step_info['clusters']:
        for member, (x, y) in cluster['points'].items():
            r = math.sqrt(x**2 + y**2)
            all_radii.add(round(r, 3))  # Round to avoid floating point issues
            all_points[member] = (x, y, r)

    # Draw concentric circles for each unique radius
    for radius in sorted(all_radii):
        circle = plt.Circle((0, 0), radius, fill=False,
                           edgecolor='blue', linewidth=1.5,
                           linestyle='--', alpha=0.5)
        ax.add_patch(circle)

        # Label the circle with its radius
        ax.text(radius * 0.7, radius * 0.7, f'r={radius:.3f}',
               fontsize=8, color='blue', alpha=0.7)

    # Draw points
    for member, (x, y, r) in all_points.items():
        is_new = member in step_info.get('highlighted_members', set())
        color = 'red' if is_new else 'darkblue'
        size = 150 if is_new else 100

        ax.scatter(x, y, c=color, s=size, zorder=10, edgecolors='black', linewidth=1.5)
        ax.text(x, y + 0.08, member, fontsize=12, ha='center', fontweight='bold')

    # Set title with structure
    from acc_core_new import format_cluster_structure

    title = f"Step {step_info['step']}: {step_info['action'].upper()}\n"

    if step_info['action'] == 'initial':
        title += f"{step_info['description']}"
    elif step_info['action'] == 'add_area':
        for cluster in step_info['clusters']:
            structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
            if len(cluster['members']) == len(step_info['placed_areas']):
                title += f"Structure: {structure}"
                break
    elif step_info['action'] == 'merge_clusters':
        for cluster in step_info['clusters']:
            structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
            title += f"Structure: {structure}"
            break

    ax.set_title(title, fontsize=10, fontweight='bold')

    # Set axis limits
    max_r = max(all_radii) if all_radii else 1.0
    lim = max_r * 1.3
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # Add legend
    ax.plot([], [], 'o', color='red', markersize=8, label='New members')
    ax.plot([], [], 'o', color='darkblue', markersize=8, label='Existing members')
    ax.plot([], [], '--', color='blue', linewidth=1.5, label='Concentric circles')
    ax.legend(loc='upper right', fontsize=8)

# Hide unused subplot
if len(steps) < len(axes):
    for i in range(len(steps), len(axes)):
        axes[i].axis('off')

plt.suptitle('ACC Algorithm: Concentric Circles Visualization\n' +
             'Each point stays on its original circle throughout the algorithm',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('/mnt/d/projects/ACC/concentric_circles_visualization.png', dpi=150, bbox_inches='tight')
print("✅ Visualization saved to: concentric_circles_visualization.png")

# Also create a detailed view of the final step
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)

final_step = steps[-1]
all_radii = set()
all_points = {}

for cluster in final_step['clusters']:
    for member, (x, y) in cluster['points'].items():
        r = math.sqrt(x**2 + y**2)
        all_radii.add(round(r, 3))
        all_points[member] = (x, y, r)

# Draw concentric circles with different colors
colors = plt.cm.rainbow(range(0, 256, 256 // len(all_radii)))
for idx, radius in enumerate(sorted(all_radii)):
    circle = plt.Circle((0, 0), radius, fill=False,
                       edgecolor=colors[idx], linewidth=2.5,
                       linestyle='-', alpha=0.7, label=f'Circle r={radius:.3f}')
    ax.add_patch(circle)

# Draw points
for member, (x, y, r) in all_points.items():
    ax.scatter(x, y, c='darkblue', s=200, zorder=10, edgecolors='black', linewidth=2)
    ax.text(x, y + 0.1, member, fontsize=14, ha='center', fontweight='bold')

from acc_core_new import format_cluster_structure
structure = format_cluster_structure(final_step['clusters'][0].get('structure',
                                      sorted(final_step['clusters'][0]['members'])))

ax.set_title(f'Final ACC Structure: {structure}\n' +
             f'Total members: {len(all_points)}, Concentric circles: {len(all_radii)}',
             fontsize=14, fontweight='bold')

max_r = max(all_radii)
lim = max_r * 1.2
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.legend(loc='upper left', fontsize=10)

plt.tight_layout()
plt.savefig('/mnt/d/projects/ACC/final_concentric_circles.png', dpi=150, bbox_inches='tight')
print("✅ Final step visualization saved to: final_concentric_circles.png")

plt.show()
