# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ACC (Adaptive Cluster Circle) is a Python-based algorithm for visualizing hierarchical cluster relationships using circular diagrams. The algorithm combines similarity information from two types of dendrograms (local and global) to create 2D geometric representations of cluster relationships.

## Core Concepts

The ACC algorithm processes two dendrograms with different structural information:

- **Local dendrogram**: Provides the primary cluster hierarchy and similarity scores (sim_local)
- **Global dendrogram**: Provides alternative similarity scores (sim_global) for the same clusters
- **Global similarity matrix**: Fallback pairwise similarity data when clusters don't exist in the global dendrogram

Each cluster gets transformed into geometric parameters:
- **Diameter (d)**: Calculated as `unit / sim_global` (inverse relationship)
- **Angle (θ)**: Calculated as `180° * (1 - sim_local)` (higher similarity = smaller angle)

## Running the Code

### Execute the main algorithm

```bash
python acc_core.py
```

The script runs a built-in example with sample dendrograms and outputs:
- Merged cluster members
- Final diameter and theta values
- Coordinate positions for each member

### Testing with custom data

Modify the `if __name__ == "__main__":` block in `acc_core.py` to provide your own:
1. Local dendrogram (DendroNode structure)
2. Global dendrogram (DendroNode structure)
3. Global similarity matrix (nested dictionary)

## Code Architecture

### Data Structures

**DendroNode** (lines 9-20): Tree structure representing dendrogram nodes
- `members`: Set of region/object identifiers
- `sim`: Similarity score (0-1 range)
- `left/right`: Child nodes

**Cluster dictionary** (created in extract_clusters_from_dendro): Working representation of clusters
- `members`: Set of members in this cluster
- `sim_local`: Local dendrogram similarity
- `sim_global`: Global similarity (calculated)
- `diameter`, `theta`: Geometric parameters
- `center`: (x, y) coordinates
- `points`: Dictionary mapping members to (x, y) positions
- `midline_angle`: Reference angle for cluster orientation

### Core Algorithm Pipeline (build_acc function, lines 342-366)

1. **extract_clusters_from_dendro** (lines 26-51): Traverse local dendrogram and collect all clusters
2. **decorate_clusters** (lines 114-138): Calculate sim_global, diameter, and theta for each cluster
3. **Sort clusters** by sim_local descending (highest similarity first)
4. **place_first_cluster** (lines 163-200): Initialize the base cluster at origin
5. **Iteratively merge** remaining clusters using two strategies:
   - **add_area_to_cluster** (lines 206-262): When adding a single new member to existing cluster
   - **merge_two_clusters** (lines 268-336): When combining two multi-member clusters

### Key Implementation Details

**Similarity lookup strategy** (find_cluster_in_dendro_by_members, lines 57-75):
- First attempts to find matching member set in global dendrogram
- Falls back to average_pairwise_similarity (lines 81-108) using the global matrix

**Geometric placement**:
- Clusters are built incrementally from highest to lowest similarity
- New members are positioned based on maximum similarity to existing members
- Merging uses rotation to align most-similar member pairs
- Diameter scales to accommodate the larger of two merged clusters
- Angle contracts to the smaller (tighter) value

**Coordinate system**:
- Polar coordinates (radius, angle) converted to Cartesian (x, y)
- All coordinates are centered at origin (0, 0)
- Rotation and scaling operations maintain spatial relationships

## Algorithm Characteristics

- **Deterministic**: Same input always produces same output
- **Greedy approach**: Processes clusters in similarity order without backtracking
- **Spatial constraints**: Enforces circular geometry with angle and diameter constraints
- **Similarity-driven**: Both local and global similarities influence final layout

## Potential Extensions

The algorithm can be extended for:
- Visualization using matplotlib or svgwrite
- Export to CSV/JSON for external visualization tools
- Performance optimization with NumPy for large datasets
- Interactive visualizations for exploring cluster relationships
- Application to phylogenetic, geographic, or ecological data

## Documentation

For more detailed information, refer to:
- **Algorithm Details**: [doc/ACC_Algorithm_Overview.md](doc/ACC_Algorithm_Overview.md)
- **User Manual**: [doc/USER_MANUAL.md](doc/USER_MANUAL.md)
- **Development Guide**: [doc/development.md](doc/development.md)
- **Build Instructions**: [doc/build/BUILDING.md](doc/build/BUILDING.md)
- **QA Setup**: [doc/QA_SETUP_SUMMARY.md](doc/QA_SETUP_SUMMARY.md)
- **Sphinx Documentation**: [docs/](docs/) - HTML documentation (use `make html` in docs/)
