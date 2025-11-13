"""
ACC2 Visualization

Visualize ACC2 with dendrogram mapped onto concentric circles
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from acc_core_acc2 import build_acc2, dict_matrix_from_dataframe, pol2cart


def visualize_acc2(acc2_data, title="ACC2: Dendrogram on Concentric Circles"):
    """
    Visualize ACC2 data

    Args:
        acc2_data: dict from build_acc2()
        title: str, plot title
    """
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
    ax.axvline(x=0, color='k', linewidth=0.5, alpha=0.3)

    circles = acc2_data['circles']
    positions = acc2_data['positions']
    merge_points = acc2_data['merge_points']
    lines = acc2_data['lines']
    levels = acc2_data['levels']

    # Create radius -> inc_sim mapping
    radius_to_sim = {}
    for level in levels:
        radius_to_sim[level['radius']] = level['inc_sim']

    # Step 1: Draw all concentric circles
    circle_colors = plt.cm.rainbow(np.linspace(0, 1, len(circles)))

    for idx, radius in enumerate(circles):
        # Label with inclusive similarity instead of radius
        if radius == 0.5:
            label = "Areas"
        else:
            inc_sim = radius_to_sim.get(radius, 0.0)
            label = f"inc_sim={inc_sim:.3f}"

        circle = plt.Circle((0, 0), radius, fill=False,
                           edgecolor=circle_colors[idx],
                           linewidth=2,
                           linestyle='-',
                           alpha=0.7,
                           label=label)
        ax.add_patch(circle)

    # Step 2: Draw connection lines
    # First draw arcs, then radial lines (so radial lines are on top)

    # Draw arcs
    for line in lines:
        if line['type'] == 'arc':
            radius = line['radius']
            angle_start = line['angle_start']
            angle_end = line['angle_end']

            # Convert to matplotlib's convention (degrees, counter-clockwise from x-axis)
            # Our convention: 0° is up (y-axis), positive is counter-clockwise
            # Matplotlib: 0° is right (x-axis), positive is counter-clockwise
            # Conversion: mpl_angle = our_angle + 90

            mpl_angle_start = angle_start + 90
            mpl_angle_end = angle_end + 90

            # Ensure start < end for arc drawing
            if mpl_angle_start > mpl_angle_end:
                mpl_angle_start, mpl_angle_end = mpl_angle_end, mpl_angle_start

            arc = patches.Arc((0, 0), 2*radius, 2*radius,
                            angle=0,
                            theta1=mpl_angle_start,
                            theta2=mpl_angle_end,
                            color='black',
                            linewidth=2,
                            alpha=0.8)
            ax.add_patch(arc)

    # Draw radial lines
    for line in lines:
        if line['type'] == 'radial':
            r1, angle = line['from']
            r2, _ = line['to']

            # Convert to cartesian
            x1, y1 = pol2cart(r1, angle)
            x2, y2 = pol2cart(r2, angle)

            ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2, alpha=0.8)

    # Step 3: Draw areas at r=0.5
    for area, pos in positions.items():
        angle = pos['angle']
        radius = pos['radius']  # Should be 0.5

        # Convert to cartesian
        x, y = pol2cart(radius, angle)

        # Draw area point
        ax.scatter(x, y, c='darkblue', s=200, zorder=10,
                  edgecolors='black', linewidth=2)

        # Label area
        # Position label slightly outside the circle
        label_r = radius - 0.1
        label_x, label_y = pol2cart(label_r, angle)
        ax.text(label_x, label_y, area, fontsize=14, ha='center', va='center',
               fontweight='bold', color='darkblue')

    # Step 4: Draw merge points and store their info
    merge_point_data = []  # Store (x, y, angle, sub_sim, cluster_id)

    # Create mapping from cluster_id to subordinate similarity
    cluster_to_subsim = {}
    for level in levels:
        cluster_id = f"[{level['cluster1']}, {level['cluster2']}]"
        cluster_to_subsim[cluster_id] = level['sub_sim']

    for cluster_id, mp in merge_points.items():
        angle = mp['angle']
        radius = mp['radius']

        # Convert to cartesian
        x, y = pol2cart(radius, angle)

        # Draw merge point (small dot)
        ax.scatter(x, y, c='red', s=50, zorder=9,
                  edgecolors='black', linewidth=1, alpha=0.6)

        # Store merge point data for hover
        sub_sim = cluster_to_subsim.get(cluster_id, 0.0)
        merge_point_data.append((x, y, angle, sub_sim, cluster_id))

    # Set plot limits
    max_radius = max(circles)
    lim = max_radius * 1.2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    # Add title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Add info text
    info_lines = [
        f"Total areas: {len(positions)}",
        f"Merge levels: {len(levels)}",
        f"Concentric circles: {len(circles)}",
        f"All areas at r={circles[0]:.1f}"
    ]
    info_text = '\n'.join(info_lines)
    ax.text(0.02, 0.98, info_text,
           transform=ax.transAxes,
           fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # Add legend (only for circles, limit to first few)
    handles, labels = ax.get_legend_handles_labels()
    if len(handles) > 8:
        # Show only first 4 and last 4 circles
        handles = handles[:4] + handles[-4:]
        labels = labels[:4] + labels[-4:]
    ax.legend(handles, labels, loc='upper right', fontsize=8, ncol=2)

    # Add interactive hover annotation for merge points
    annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                       textcoords="offset points",
                       bbox=dict(boxstyle="round", fc="yellow", alpha=0.9),
                       fontsize=9,
                       visible=False,
                       zorder=100)

    def on_hover(event):
        """Handle mouse hover events"""
        if event.inaxes != ax:
            annot.set_visible(False)
            fig.canvas.draw_idle()
            return

        # Check if mouse is near any merge point
        if event.xdata is None or event.ydata is None:
            return

        # Find closest merge point
        min_dist = float('inf')
        closest_point = None

        for x, y, angle, sub_sim, cluster_id in merge_point_data:
            dist = ((event.xdata - x)**2 + (event.ydata - y)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_point = (x, y, angle, sub_sim, cluster_id)

        # Show annotation if close enough (threshold based on axes limits)
        threshold = lim * 0.05  # 5% of axis limit
        if min_dist < threshold and closest_point:
            x, y, angle, sub_sim, cluster_id = closest_point
            annot.xy = (x, y)
            text = f"{cluster_id}\nAngle: {angle:.1f}°\nSub sim: {sub_sim:.3f}"
            annot.set_text(text)
            annot.set_visible(True)
        else:
            annot.set_visible(False)

        fig.canvas.draw_idle()

    # Connect hover event
    fig.canvas.mpl_connect('motion_notify_event', on_hover)

    plt.tight_layout()
    return fig, ax


if __name__ == "__main__":
    # Load sample data
    sub_df = pd.read_csv('data/sample_subordinate.csv', index_col=0)
    inc_df = pd.read_csv('data/sample_inclusive.csv', index_col=0)

    sub_matrix = dict_matrix_from_dataframe(sub_df)
    inc_matrix = dict_matrix_from_dataframe(inc_df)

    # Build ACC2
    print("Building ACC2...")
    acc2_data = build_acc2(sub_matrix, inc_matrix)

    # Visualize
    print("Visualizing ACC2...")
    fig, ax = visualize_acc2(acc2_data)

    # Save
    output_path = '/mnt/d/projects/ACC/acc2_visualization.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ ACC2 visualization saved to: {output_path}")

    plt.show()
