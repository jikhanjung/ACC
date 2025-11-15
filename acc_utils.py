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

            # Check value range
            if np.any(arr < 0.0) or np.any(arr > 1.0):
                min_val = np.min(arr)
                max_val = np.max(arr)
                return False, f"All values must be between 0.0 and 1.0 (found min={min_val:.3f}, max={max_val:.3f})"

            # Check symmetry
            if not np.allclose(arr, arr.T, rtol=1e-5, atol=1e-8):
                # Find the asymmetric elements
                diff = np.abs(arr - arr.T)
                max_diff_idx = np.unravel_index(np.argmax(diff), diff.shape)
                i, j = max_diff_idx
                return False, f"Matrix is not symmetric: matrix[{i},{j}]={arr[i,j]:.6f} but matrix[{j},{i}]={arr[j,i]:.6f}"

            # Check diagonal
            diag = np.diag(arr)
            if not np.allclose(diag, 1.0, rtol=1e-5, atol=1e-8):
                bad_diag_idx = np.where(np.abs(diag - 1.0) > 0.01)[0]
                if len(bad_diag_idx) > 0:
                    idx = bad_diag_idx[0]
                    return False, f"Diagonal element [{idx},{idx}] is {diag[idx]:.6f}, should be 1.0"

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
    Build ACC result directly from similarity matrices with multiple concentric circles
    This is a convenience function that handles the complete pipeline

    Args:
        sub_matrix: subordinate similarity matrix (dict of dict)
        inc_matrix: inclusive similarity matrix (dict of dict)
        unit: unit parameter for diameter calculation
        method: linkage method for hierarchical clustering

    Returns:
        acc_result: dict with:
            - 'clusters': list of positioned clusters
            - 'all_members': set of all members across all clusters
    """
    from acc_core import build_acc, DendroNode

    # Convert matrices to dendrograms
    sub_dendro, sub_labels = matrix_to_dendrogram(sub_matrix, method=method)
    inc_dendro, inc_labels = matrix_to_dendrogram(inc_matrix, method=method)

    # Call build_acc which now returns multiple clusters
    acc_result = build_acc(sub_dendro, inc_dendro, inc_matrix, unit=unit)

    return acc_result


def build_acc_from_matrices_steps(sub_matrix, inc_matrix, unit=1.0, method='average'):
    """
    Build ACC step by step directly from similarity matrices
    This returns all intermediate states for visualization

    Args:
        sub_matrix: subordinate similarity matrix (dict of dict)
        inc_matrix: inclusive similarity matrix (dict of dict)
        unit: unit parameter for diameter calculation
        method: linkage method for hierarchical clustering

    Returns:
        steps: list of dicts, each containing step information
    """
    from acc_core import build_acc_steps, DendroNode

    # Convert matrices to dendrograms
    sub_dendro, sub_labels = matrix_to_dendrogram(sub_matrix, method=method)
    inc_dendro, inc_labels = matrix_to_dendrogram(inc_matrix, method=method)

    # Call build_acc_steps which returns all steps
    steps = build_acc_steps(sub_dendro, inc_dendro, inc_matrix, unit=unit)

    return steps


def build_acc_from_matrices_iterative(sub_matrix, inc_matrix, unit=1.0, method='average'):
    """
    Build ACC iteratively using the new algorithm (Option 1 approach)
    Always selects globally highest similarity at each step

    This is the NEW algorithm that doesn't require dendrograms.

    Args:
        sub_matrix: subordinate similarity matrix (dict of dict)
        inc_matrix: inclusive similarity matrix (dict of dict)
        unit: unit parameter for diameter calculation
        method: linkage method for cluster similarity calculation

    Returns:
        steps: list of dicts, each containing step information
    """
    from acc_core_new import build_acc_iterative

    # Call the new iterative algorithm directly on matrices
    steps = build_acc_iterative(sub_matrix, inc_matrix, unit=unit, method=method)

    return steps
