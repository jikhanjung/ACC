"""
Utility functions for ACC GUI application
Handles conversion between similarity matrices and dendrogram structures
"""

import numpy as np
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform
from acc_core import DendroNode


def similarity_to_distance(similarity_matrix):
    """
    Convert similarity matrix to distance matrix

    For similarity matrix: higher value = more similar
    For distance matrix: higher value = more dissimilar
    Therefore: distance = max(similarity) - similarity

    Args:
        similarity_matrix: dict of dict or 2D array, values in [0, 1]

    Returns:
        distance_matrix: 2D numpy array
        labels: list of labels
    """
    # Convert dict to numpy array if necessary
    if isinstance(similarity_matrix, dict):
        labels = sorted(similarity_matrix.keys())
        n = len(labels)
        sim_array = np.zeros((n, n))

        for i, label1 in enumerate(labels):
            for j, label2 in enumerate(labels):
                if label1 in similarity_matrix and label2 in similarity_matrix[label1]:
                    sim_array[i, j] = similarity_matrix[label1][label2]
                elif label2 in similarity_matrix and label1 in similarity_matrix[label2]:
                    sim_array[i, j] = similarity_matrix[label2][label1]
                elif i == j:
                    sim_array[i, j] = 1.0  # diagonal should be 1
    else:
        sim_array = np.array(similarity_matrix)
        labels = [f"Item_{i}" for i in range(len(sim_array))]

    # Convert similarity to distance
    # Use max - similarity to preserve relative distances properly
    max_sim = np.max(sim_array)
    distance_matrix = max_sim - sim_array

    return distance_matrix, labels


def linkage_to_dendronode(linkage_matrix, labels, max_sim=1.0):
    """
    Convert scipy linkage matrix to DendroNode structure

    Args:
        linkage_matrix: scipy linkage result (n-1 x 4 array)
        labels: list of original labels
        max_sim: maximum similarity value (used for distance conversion)

    Returns:
        root: DendroNode representing the dendrogram
    """
    n = len(labels)
    nodes = {}

    # Create leaf nodes
    for i, label in enumerate(labels):
        nodes[i] = DendroNode([label], sim=1.0)

    # Build internal nodes from linkage matrix
    for idx, (i, j, dist, count) in enumerate(linkage_matrix):
        cluster_id = n + idx
        i, j = int(i), int(j)

        left = nodes[i]
        right = nodes[j]

        # Combine members from both children
        members = list(left.members | right.members)

        # Convert distance back to similarity
        # Since we used distance = max_sim - similarity
        # Therefore: similarity = max_sim - distance
        sim = max_sim - dist

        nodes[cluster_id] = DendroNode(members, sim=sim, left=left, right=right)

    # Return the root (last node created)
    root_id = n + len(linkage_matrix) - 1
    return nodes[root_id]


def extract_clusters_from_dendro_filtered(root):
    """
    Extract clusters from dendrogram, excluding single-member leaf nodes
    This matches the behavior expected by acc_core.build_acc()

    Args:
        root: DendroNode structure

    Returns:
        clusters: list of cluster dicts with 2 or more members
    """
    clusters = []

    def dfs(node):
        if node is None:
            return
        # Only include clusters with 2 or more members
        if len(node.members) >= 2:
            clusters.append({
                "members": set(node.members),
                "sim_sub": node.sim,
                "sim_inc": None,
                "diameter": None,
                "theta": None,
                "center": None,
                "points": {},
                "midline_angle": 0.0
            })
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    return clusters


def matrix_to_dendrogram(similarity_matrix, method='average'):
    """
    Convert similarity matrix to dendrogram structure

    Args:
        similarity_matrix: dict of dict or 2D array
        method: linkage method ('average', 'single', 'complete', 'ward')

    Returns:
        dendro_node: DendroNode structure
        labels: list of labels
    """
    # Convert to distance matrix
    distance_matrix, labels = similarity_to_distance(similarity_matrix)

    # Get max similarity for conversion back
    if isinstance(similarity_matrix, dict):
        values = [v for row in similarity_matrix.values() for v in row.values()]
        max_sim = max(values) if values else 1.0
    else:
        max_sim = np.max(np.array(similarity_matrix))

    # Convert to condensed distance matrix for scipy
    condensed_dist = squareform(distance_matrix, checks=False)

    # Perform hierarchical clustering
    linkage_matrix = linkage(condensed_dist, method=method)

    # Convert to DendroNode structure
    dendro_node = linkage_to_dendronode(linkage_matrix, labels, max_sim=max_sim)

    return dendro_node, labels


def validate_similarity_matrix(matrix):
    """
    Validate that the matrix is a proper similarity matrix

    Args:
        matrix: dict of dict or 2D array

    Returns:
        valid: bool
        message: str describing any issues
    """
    try:
        if isinstance(matrix, dict):
            labels = list(matrix.keys())
            n = len(labels)

            # Check if square
            for label in labels:
                if label not in matrix:
                    return False, f"Missing row for {label}"
                if len(matrix[label]) == 0:
                    return False, f"Empty row for {label}"

            # Check symmetry and diagonal
            for i, label1 in enumerate(labels):
                for j, label2 in enumerate(labels):
                    if i == j:
                        # Diagonal should be 1 or close to 1
                        if label1 in matrix and label1 in matrix[label1]:
                            val = matrix[label1][label1]
                            if abs(val - 1.0) > 0.01:
                                return False, f"Diagonal element {label1} is {val}, should be 1.0"
                    else:
                        # Check symmetry
                        val1 = matrix.get(label1, {}).get(label2, None)
                        val2 = matrix.get(label2, {}).get(label1, None)

                        if val1 is not None and val2 is not None:
                            if abs(val1 - val2) > 0.01:
                                return False, f"Matrix not symmetric at ({label1}, {label2})"
        else:
            # numpy array
            arr = np.array(matrix)
            if len(arr.shape) != 2:
                return False, "Matrix must be 2D"

            if arr.shape[0] != arr.shape[1]:
                return False, "Matrix must be square"

            # Check symmetry
            if not np.allclose(arr, arr.T):
                return False, "Matrix is not symmetric"

            # Check diagonal
            diag = np.diag(arr)
            if not np.allclose(diag, 1.0):
                return False, "Diagonal elements should be 1.0"

        return True, "Matrix is valid"

    except Exception as e:
        return False, f"Error validating matrix: {str(e)}"


def dict_matrix_from_dataframe(df):
    """
    Convert pandas DataFrame to dict-of-dict matrix format

    Args:
        df: pandas DataFrame with row and column labels

    Returns:
        matrix: dict of dict
    """
    matrix = {}
    for idx in df.index:
        matrix[idx] = {}
        for col in df.columns:
            matrix[idx][col] = float(df.loc[idx, col])

    return matrix


def build_acc_from_matrices(sub_matrix, inc_matrix, unit=1.0, method='average'):
    """
    Build ACC result directly from similarity matrices
    This is a convenience function that handles the complete pipeline

    Args:
        sub_matrix: subordinate similarity matrix (dict of dict)
        inc_matrix: inclusive similarity matrix (dict of dict)
        unit: unit parameter for diameter calculation
        method: linkage method for hierarchical clustering

    Returns:
        acc_result: dict with 'members', 'diameter', 'theta', 'center', 'points'
    """
    from acc_core import build_acc, DendroNode

    # Convert matrices to dendrograms
    sub_dendro, sub_labels = matrix_to_dendrogram(sub_matrix, method=method)
    inc_dendro, inc_labels = matrix_to_dendrogram(inc_matrix, method=method)

    # Extract clusters (filtered to exclude single-member leaves)
    clusters = extract_clusters_from_dendro_filtered(sub_dendro)

    # Decorate clusters with sim_inc, diameter, theta
    from acc_core import decorate_clusters, place_first_cluster, add_area_to_cluster, merge_two_clusters

    decorate_clusters(clusters, inc_dendro, inc_matrix, unit=unit)

    # Sort by sim_sub descending
    clusters.sort(key=lambda c: c["sim_sub"], reverse=True)

    if len(clusters) == 0:
        raise ValueError("No clusters found with 2 or more members")

    # Place first cluster
    base = place_first_cluster(clusters[0])

    # Merge remaining clusters
    for c in clusters[1:]:
        if len(c["members"]) == len(base["members"]) + 1 and base["members"].issubset(c["members"]):
            base = add_area_to_cluster(base, c, inc_matrix)
        else:
            base = merge_two_clusters(base, c, inc_matrix)

    return base
