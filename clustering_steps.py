"""
Clustering step-by-step manager
Manages hierarchical clustering progression step-by-step
"""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform


class ClusteringStepManager:
    """
    Manages step-by-step hierarchical clustering process
    """

    def __init__(self, similarity_matrix, labels):
        """
        Initialize with similarity matrix

        Args:
            similarity_matrix: 2D numpy array (similarity values)
            labels: list of original labels
        """
        self.original_similarity = similarity_matrix.copy()
        self.original_labels = labels.copy()
        self.n_items = len(labels)

        # Convert similarity to distance
        max_sim = np.max(similarity_matrix)
        distance_matrix = max_sim - similarity_matrix
        condensed_dist = squareform(distance_matrix, checks=False)

        # Perform hierarchical clustering
        self.linkage_matrix = linkage(condensed_dist, method='average')
        self.max_sim = max_sim

        # Generate all steps
        self.steps = self._generate_steps()

    def _generate_steps(self):
        """
        Generate all clustering steps

        Returns:
            list of step dicts with keys: step_num, matrix, labels, merged_pair, distance
        """
        steps = []

        # Step 0: original state
        steps.append({
            'step_num': 0,
            'matrix': self.original_similarity.copy(),
            'labels': self.original_labels.copy(),
            'merged_pair': None,
            'distance': None,
            'cluster_map': {i: [label] for i, label in enumerate(self.original_labels)}
        })

        # Track current clusters
        cluster_map = {i: [label] for i, label in enumerate(self.original_labels)}
        current_matrix = self.original_similarity.copy()
        current_labels = self.original_labels.copy()

        # Process each merge step
        for step_idx, (i, j, dist, count) in enumerate(self.linkage_matrix):
            i, j = int(i), int(j)
            step_num = step_idx + 1

            # Determine which labels are being merged
            if i < self.n_items:
                cluster_i = [self.original_labels[i]]
            else:
                cluster_i = cluster_map[i]

            if j < self.n_items:
                cluster_j = [self.original_labels[j]]
            else:
                cluster_j = cluster_map[j]

            # New cluster ID
            new_cluster_id = self.n_items + step_idx
            merged_cluster = cluster_i + cluster_j

            # Create new cluster map
            new_cluster_map = {}
            for key, val in cluster_map.items():
                if key != i and key != j:
                    new_cluster_map[key] = val
            new_cluster_map[new_cluster_id] = merged_cluster

            # Create merged matrix
            new_matrix, new_labels = self._merge_matrix(
                current_matrix,
                current_labels,
                cluster_i,
                cluster_j,
                merged_cluster
            )

            # Convert distance back to similarity
            similarity_dist = self.max_sim - dist

            steps.append({
                'step_num': step_num,
                'matrix': new_matrix,
                'labels': new_labels,
                'merged_pair': (cluster_i, cluster_j),
                'distance': dist,
                'similarity': similarity_dist,
                'cluster_map': new_cluster_map
            })

            # Update current state
            current_matrix = new_matrix
            current_labels = new_labels
            cluster_map = new_cluster_map

        return steps

    def _merge_matrix(self, matrix, labels, cluster_i, cluster_j, new_cluster):
        """
        Merge two clusters in the matrix
        The merged cluster takes the position of the earlier cluster (smaller index)

        Args:
            matrix: current similarity matrix
            labels: current labels
            cluster_i: members of first cluster
            cluster_j: members of second cluster
            new_cluster: merged cluster name

        Returns:
            new_matrix: reduced matrix
            new_labels: reduced labels
        """
        # Find indices of clusters to merge
        idx_i = [i for i, label in enumerate(labels) if label in cluster_i or str(label) == str(cluster_i)]
        idx_j = [j for j, label in enumerate(labels) if label in cluster_j or str(label) == str(cluster_j)]

        # Handle cases where cluster_i or cluster_j are already merged (represented as tuples/lists)
        if not idx_i:
            # cluster_i might be represented as a tuple in labels
            for i, label in enumerate(labels):
                if isinstance(label, (list, tuple)):
                    if set(label) == set(cluster_i):
                        idx_i = [i]
                        break

        if not idx_j:
            for j, label in enumerate(labels):
                if isinstance(label, (list, tuple)):
                    if set(label) == set(cluster_j):
                        idx_j = [j]
                        break

        if not idx_i or not idx_j:
            # Fallback: just return current matrix
            return matrix, labels

        idx_i = idx_i[0]
        idx_j = idx_j[0]

        # Ensure idx_i < idx_j (idx_i will be the position of merged cluster)
        if idx_i > idx_j:
            idx_i, idx_j = idx_j, idx_i

        n = len(labels)

        # Create new matrix (one dimension smaller)
        new_size = n - 1
        new_matrix = np.zeros((new_size, new_size))

        # Create new labels with merged cluster at idx_i position
        new_labels = []
        old_to_new_idx = {}
        new_idx = 0

        for old_idx in range(n):
            if old_idx == idx_i:
                # Merged cluster takes the position of idx_i
                merged_label = tuple(sorted(new_cluster))
                new_labels.append(merged_label)
                old_to_new_idx[old_idx] = new_idx
                new_idx += 1
            elif old_idx == idx_j:
                # Skip idx_j (it's merged into idx_i)
                continue
            else:
                # Keep other labels in their relative positions
                new_labels.append(labels[old_idx])
                old_to_new_idx[old_idx] = new_idx
                new_idx += 1

        # Fill new matrix
        merged_idx = old_to_new_idx[idx_i]  # Position of merged cluster

        for old_i in range(n):
            if old_i == idx_j:
                continue  # Skip removed row

            new_i = old_to_new_idx.get(old_i, merged_idx) if old_i == idx_i else old_to_new_idx[old_i]

            for old_j in range(n):
                if old_j == idx_j:
                    continue  # Skip removed column

                if old_i == idx_i and old_j == idx_i:
                    # Diagonal for merged cluster
                    new_matrix[merged_idx, merged_idx] = 1.0
                elif old_i == idx_i:
                    # Row for merged cluster: average with idx_j
                    new_j = old_to_new_idx.get(old_j, merged_idx) if old_j == idx_i else old_to_new_idx[old_j]
                    avg_sim = (matrix[idx_i, old_j] + matrix[idx_j, old_j]) / 2.0
                    new_matrix[merged_idx, new_j] = avg_sim
                elif old_j == idx_i:
                    # Column for merged cluster: average with idx_j
                    new_i_actual = old_to_new_idx[old_i]
                    avg_sim = (matrix[old_i, idx_i] + matrix[old_i, idx_j]) / 2.0
                    new_matrix[new_i_actual, merged_idx] = avg_sim
                else:
                    # Other cells: copy directly
                    new_i_actual = old_to_new_idx[old_i]
                    new_j = old_to_new_idx[old_j]
                    new_matrix[new_i_actual, new_j] = matrix[old_i, old_j]

        return new_matrix, new_labels

    def get_step(self, step_num):
        """
        Get information for a specific step

        Args:
            step_num: step number (0 to n-1)

        Returns:
            step dict
        """
        if step_num < 0 or step_num >= len(self.steps):
            return None
        return self.steps[step_num]

    def get_num_steps(self):
        """Get total number of steps"""
        return len(self.steps)

    def get_step_description(self, step_num):
        """
        Get human-readable description of a step

        Args:
            step_num: step number

        Returns:
            str description
        """
        step = self.get_step(step_num)
        if step is None:
            return "Invalid step"

        if step_num == 0:
            return f"Step 0: Original matrix ({self.n_items} items)"

        merged_pair = step['merged_pair']
        cluster_i_str = '+'.join(merged_pair[0])
        cluster_j_str = '+'.join(merged_pair[1])
        sim = step.get('similarity', 0)

        return f"Step {step_num}: Merge ({cluster_i_str}) + ({cluster_j_str}), similarity={sim:.3f}"

    def get_partial_linkage(self, step_num):
        """
        Get partial linkage matrix up to step_num

        Args:
            step_num: step number

        Returns:
            partial_linkage: linkage matrix up to this step
        """
        if step_num <= 0:
            return None

        # Return first step_num rows of linkage matrix
        return self.linkage_matrix[:step_num, :]
