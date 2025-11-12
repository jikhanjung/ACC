"""
ACC (Adaptive Cluster Circle) GUI Application
PyQt6-based interface for visualizing hierarchical cluster relationships

Three-column layout with step-by-step clustering visualization:
- Left: Similarity Matrices (with step slider)
- Center: Dendrograms (with step visualization)
- Right: ACC Concentric Circles
"""

import sys
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QLabel, QSlider, QMessageBox, QScrollArea, QCheckBox, QSplitter,
    QDialog, QListWidget, QInputDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

from acc_utils import validate_similarity_matrix, dict_matrix_from_dataframe, build_acc_from_matrices
from clustering_steps import ClusteringStepManager


class AreaListEditorDialog(QDialog):
    """Dialog for editing the list of areas (row/column labels)"""

    def __init__(self, current_labels, sub_matrix_df, inc_matrix_df, parent=None):
        super().__init__(parent)
        self.current_labels = list(current_labels)
        self.sub_matrix_df = sub_matrix_df.copy()
        self.inc_matrix_df = inc_matrix_df.copy()
        self.modified = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Area List")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Title
        title = QLabel("<h3>Edit Area List</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Info label
        info = QLabel("Areas must be the same for both Subordinate and Inclusive matrices.")
        info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Main content area
        content_layout = QHBoxLayout()

        # List widget
        list_container = QVBoxLayout()
        list_label = QLabel("<b>Current Areas:</b>")
        list_container.addWidget(list_label)

        self.area_list = QListWidget()
        self.area_list.addItems(self.current_labels)
        self.area_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        list_container.addWidget(self.area_list)

        content_layout.addLayout(list_container, stretch=3)

        # Buttons
        button_container = QVBoxLayout()
        button_container.addStretch()

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_btn.clicked.connect(self.add_area)
        button_container.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_area)
        button_container.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_area)
        button_container.addWidget(self.delete_btn)

        button_container.addStretch()
        content_layout.addLayout(button_container, stretch=1)

        layout.addLayout(content_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def add_area(self):
        """Add a new area"""
        text, ok = QInputDialog.getText(
            self,
            "Add Area",
            "Enter new area name:",
        )

        if ok and text:
            # Validate
            text = text.strip()
            if not text:
                QMessageBox.warning(self, "Invalid Name", "Area name cannot be empty or whitespace.")
                return

            if text in self.current_labels:
                QMessageBox.warning(self, "Duplicate Name", f"Area '{text}' already exists.")
                return

            # Add to list
            self.current_labels.append(text)
            self.area_list.addItem(text)

            # Add to both dataframes (new row and column with default value 0.5, diagonal 1.0)
            n = len(self.current_labels)

            # Create new row/column data
            new_row_sub = pd.Series([0.5] * n, index=self.current_labels)
            new_row_sub[text] = 1.0  # Diagonal

            new_row_inc = pd.Series([0.5] * n, index=self.current_labels)
            new_row_inc[text] = 1.0  # Diagonal

            # Add to subordinate matrix
            self.sub_matrix_df = pd.concat([self.sub_matrix_df, pd.DataFrame([new_row_sub], index=[text])])
            self.sub_matrix_df[text] = new_row_sub

            # Add to inclusive matrix
            self.inc_matrix_df = pd.concat([self.inc_matrix_df, pd.DataFrame([new_row_inc], index=[text])])
            self.inc_matrix_df[text] = new_row_inc

            self.modified = True

    def edit_area(self):
        """Edit selected area name"""
        selected_items = self.area_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an area to edit.")
            return

        current_item = selected_items[0]
        old_name = current_item.text()
        old_index = self.current_labels.index(old_name)

        text, ok = QInputDialog.getText(
            self,
            "Edit Area",
            "Enter new area name:",
            text=old_name
        )

        if ok and text:
            # Validate
            text = text.strip()
            if not text:
                QMessageBox.warning(self, "Invalid Name", "Area name cannot be empty or whitespace.")
                return

            if text != old_name and text in self.current_labels:
                QMessageBox.warning(self, "Duplicate Name", f"Area '{text}' already exists.")
                return

            # Update list
            self.current_labels[old_index] = text
            current_item.setText(text)

            # Update dataframes - rename both index and column
            self.sub_matrix_df.rename(index={old_name: text}, columns={old_name: text}, inplace=True)
            self.inc_matrix_df.rename(index={old_name: text}, columns={old_name: text}, inplace=True)

            self.modified = True

    def delete_area(self):
        """Delete selected area"""
        selected_items = self.area_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an area to delete.")
            return

        area_name = selected_items[0].text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete area '{area_name}'?\n\n"
            f"This will remove it from both matrices and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            index = self.current_labels.index(area_name)
            self.current_labels.pop(index)
            self.area_list.takeItem(index)

            # Remove from both dataframes
            self.sub_matrix_df.drop(index=area_name, columns=area_name, inplace=True)
            self.inc_matrix_df.drop(index=area_name, columns=area_name, inplace=True)

            self.modified = True

    def get_result(self):
        """Get the modified data"""
        return {
            "labels": self.current_labels,
            "sub_matrix": self.sub_matrix_df,
            "inc_matrix": self.inc_matrix_df,
            "modified": self.modified
        }


class StepMatrixWidget(QWidget):
    """Widget for displaying similarity matrix with step control"""

    def __init__(self, title="Matrix", parent=None, show_header=True):
        super().__init__(parent)
        self.title = title
        self.show_header = show_header
        self.matrix_data = None
        self.step_manager = None
        self.current_step = 0
        self.is_preview_mode = False  # Preview mode: highlight clusters to be merged
        self.preview_clusters = None  # (idx_i, idx_j) to highlight
        self.highlight_merged = False  # Whether to highlight just-merged cluster in yellow
        self.merged_cluster_idx = None  # Index of just-merged cluster
        self.updating_mirror = False  # Flag to prevent recursive updates
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header (optional)
        if self.show_header:
            header_layout = QHBoxLayout()
            header_layout.addStretch()

            self.load_btn = QPushButton("Load CSV")
            self.load_btn.clicked.connect(self.load_csv)
            self.load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            header_layout.addWidget(self.load_btn)
            layout.addLayout(header_layout)
        else:
            # Create load_btn even if header is hidden (will be accessed externally)
            self.load_btn = QPushButton("Load CSV")
            self.load_btn.clicked.connect(self.load_csv)
            self.load_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)

        # Step controls
        self.step_controls = QWidget()
        step_layout = QVBoxLayout()
        step_layout.setContentsMargins(0, 2, 0, 2)
        step_layout.setSpacing(3)

        # Step label and description in one line
        step_info_layout = QHBoxLayout()
        self.step_label = QLabel("Step: 0")
        self.step_label.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 10px;")
        step_info_layout.addWidget(self.step_label)

        self.step_desc_label = QLabel("Load matrix to begin")
        self.step_desc_label.setStyleSheet("font-size: 9px; color: #666;")
        step_info_layout.addWidget(self.step_desc_label)
        step_info_layout.addStretch()
        step_layout.addLayout(step_info_layout)

        # Slider and buttons
        slider_layout = QHBoxLayout()
        self.step_slider = QSlider(Qt.Orientation.Horizontal)
        self.step_slider.setMinimum(0)
        self.step_slider.setMaximum(0)
        self.step_slider.setValue(0)
        self.step_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.step_slider.setTickInterval(1)
        self.step_slider.valueChanged.connect(self.on_step_changed)
        slider_layout.addWidget(self.step_slider)

        # Navigation buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setMaximumWidth(40)
        self.prev_btn.clicked.connect(self.prev_step)
        self.prev_btn.setEnabled(False)
        btn_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▶")
        self.next_btn.setMaximumWidth(40)
        self.next_btn.clicked.connect(self.next_step)
        self.next_btn.setEnabled(False)
        btn_layout.addWidget(self.next_btn)

        slider_layout.addLayout(btn_layout)
        step_layout.addLayout(slider_layout)

        self.step_controls.setLayout(step_layout)
        self.step_controls.setVisible(False)
        layout.addWidget(self.step_controls)

        # Table widget (no max height to allow it to expand)
        self.table = QTableWidget()
        self.table.setMinimumHeight(200)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table, stretch=1)  # Allow table to expand

        # Info label (compact)
        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 9px;")
        self.info_label.setMaximumHeight(15)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def load_csv(self):
        """Load similarity matrix from CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                # Read CSV with pandas
                df = pd.read_csv(file_path, index_col=0)

                # Validate it's a square matrix
                if df.shape[0] != df.shape[1]:
                    QMessageBox.warning(
                        self,
                        "Invalid Matrix",
                        "Matrix must be square (same number of rows and columns)"
                    )
                    return

                # Store data
                self.matrix_data = df

                # Create step manager
                self.step_manager = ClusteringStepManager(
                    df.values,
                    df.index.tolist()
                )

                # Set up slider
                num_steps = self.step_manager.get_num_steps()
                self.step_slider.setMaximum(num_steps - 1)
                self.step_slider.setValue(0)
                self.current_step = 0

                # Show step controls
                self.step_controls.setVisible(True)
                self.update_step_display()

                self.info_label.setText(f"✓ Loaded: {df.shape[0]}×{df.shape[1]}, {num_steps} steps")
                self.info_label.setStyleSheet("color: green; font-size: 10px;")

                # Notify parent
                if hasattr(self.parent(), 'on_matrix_loaded'):
                    self.parent().on_matrix_loaded()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Loading File",
                    f"Failed to load CSV file:\n{str(e)}"
                )
                import traceback
                traceback.print_exc()

    def on_step_changed(self, value):
        """Handle slider value change"""
        self.current_step = value
        self.update_step_display()

        # Notify parent
        if hasattr(self.parent(), 'on_step_changed'):
            self.parent().on_step_changed()

    def prev_step(self):
        """Go to previous step (immediate, no preview)"""
        if self.current_step > 0:
            self.is_preview_mode = False
            self.preview_clusters = None
            self.highlight_merged = False
            self.merged_cluster_idx = None
            self.step_slider.setValue(self.current_step - 1)

    def next_step(self):
        """Go to next step (with preview animation)"""
        if self.step_manager and self.current_step < self.step_manager.get_num_steps() - 1:
            # Show preview first: highlight clusters that will be merged
            next_step_num = self.current_step + 1
            next_step_info = self.step_manager.get_step(next_step_num)

            if next_step_info and next_step_info['merged_pair']:
                # Get the clusters that will be merged
                cluster_i, cluster_j = next_step_info['merged_pair']

                # Find their indices in current step
                current_step_info = self.step_manager.get_step(self.current_step)
                current_labels = current_step_info['labels']

                idx_i = self._find_cluster_index(current_labels, cluster_i)
                idx_j = self._find_cluster_index(current_labels, cluster_j)

                if idx_i is not None and idx_j is not None:
                    # Enter preview mode
                    self.is_preview_mode = True
                    self.preview_clusters = (idx_i, idx_j)
                    self.update_step_display()

                    # After 500ms, actually move to next step
                    QTimer.singleShot(500, self._complete_next_step)
                else:
                    # Fallback: just move immediately
                    self._complete_next_step()
            else:
                # No merge info, just move
                self._complete_next_step()

    def _find_cluster_index(self, labels, cluster):
        """Find the index of a cluster in labels list"""
        cluster_set = set(cluster)
        for idx, label in enumerate(labels):
            if isinstance(label, (tuple, list)):
                if set(label) == cluster_set:
                    return idx
            else:
                if {label} == cluster_set:
                    return idx
        return None

    def _complete_next_step(self):
        """Complete the transition to next step"""
        # Remember the preview clusters before clearing
        preview_idx_i, preview_idx_j = None, None
        if self.preview_clusters:
            preview_idx_i, preview_idx_j = self.preview_clusters
            # The merged cluster will be at the position of the smaller index
            if preview_idx_i is not None and preview_idx_j is not None:
                # Ensure idx_i < idx_j
                if preview_idx_i > preview_idx_j:
                    preview_idx_i, preview_idx_j = preview_idx_j, preview_idx_i

        # Move to next step
        self.is_preview_mode = False
        self.preview_clusters = None
        self.step_slider.setValue(self.current_step + 1)

        # Highlight merged cluster in yellow
        # The merged cluster is at the position of the smaller preview index
        if preview_idx_i is not None:
            self.merged_cluster_idx = preview_idx_i
            self.highlight_merged = True
            self.update_step_display()

            # After 500ms, remove highlight (turn white)
            QTimer.singleShot(500, self._remove_highlight)
        elif self.step_manager and self.current_step > 0:
            # Fallback: find the last merged cluster (should not happen normally)
            step_info = self.step_manager.get_step(self.current_step)
            labels = step_info['labels']
            for idx, label in enumerate(labels):
                if isinstance(label, (tuple, list)):
                    self.merged_cluster_idx = idx
            if self.merged_cluster_idx is not None:
                self.highlight_merged = True
                self.update_step_display()
                QTimer.singleShot(500, self._remove_highlight)

    def _remove_highlight(self):
        """Remove yellow highlight from merged cluster"""
        self.highlight_merged = False
        self.merged_cluster_idx = None
        self.update_step_display()

    def update_step_display(self):
        """Update display for current step"""
        if not self.step_manager:
            return

        step_info = self.step_manager.get_step(self.current_step)
        if not step_info:
            return

        # Update labels
        self.step_label.setText(f"Step: {self.current_step}/{self.step_manager.get_num_steps()-1}")
        self.step_desc_label.setText(self.step_manager.get_step_description(self.current_step))

        # Update buttons
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < self.step_manager.get_num_steps() - 1)

        # Update table
        self.populate_table(step_info['matrix'], step_info['labels'])

    def populate_table(self, matrix, labels):
        """Populate table widget with matrix data"""
        self.table.clear()

        # Format labels for display
        display_labels = []
        for label in labels:
            if isinstance(label, (tuple, list)):
                display_labels.append('+'.join(str(l) for l in label))
            else:
                display_labels.append(str(label))

        n = len(labels)
        self.table.setRowCount(n)
        self.table.setColumnCount(n)

        # Set headers
        self.table.setHorizontalHeaderLabels(display_labels)
        self.table.setVerticalHeaderLabels(display_labels)

        # Determine which row/col to highlight
        highlight_indices = ()
        highlight_color = Qt.GlobalColor.yellow

        if self.is_preview_mode and self.preview_clusters:
            # Preview mode: highlight clusters to be merged (yellow)
            highlight_indices = self.preview_clusters
        elif self.highlight_merged and self.merged_cluster_idx is not None:
            # Just-merged mode: highlight merged cluster (yellow)
            highlight_indices = (self.merged_cluster_idx,)

        # Fill data - only upper triangle
        for i in range(n):
            for j in range(n):
                if i < j:
                    # Upper triangle: show values (editable)
                    value = matrix[i, j]
                    item = QTableWidgetItem(f"{value:.3f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Highlight appropriate rows/cols
                    # In upper triangle: i is row index, j is column index
                    # Small index clusters appear as rows, large index clusters as columns
                    should_highlight = False
                    if self.is_preview_mode and self.preview_clusters:
                        # Preview: highlight both clusters (as rows and/or columns)
                        idx_i, idx_j = self.preview_clusters
                        if i == idx_i or i == idx_j or j == idx_i or j == idx_j:
                            should_highlight = True
                    elif self.highlight_merged and self.merged_cluster_idx is not None:
                        # Just-merged: highlight merged cluster (as row and/or column)
                        if i == self.merged_cluster_idx or j == self.merged_cluster_idx:
                            should_highlight = True

                    if should_highlight:
                        item.setBackground(highlight_color)

                    # Upper triangle is editable
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(i, j, item)
                elif i == j:
                    # Diagonal: read-only with gray background (always 1.0)
                    item = QTableWidgetItem("1.000")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip("Diagonal cells are always 1.0 and cannot be edited")
                    self.table.setItem(i, j, item)
                else:
                    # Lower triangle: read-only mirror of upper triangle
                    value = matrix[i, j]
                    item = QTableWidgetItem(f"{value:.3f}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip("Lower triangle is read-only (mirrored from upper triangle)")
                    self.table.setItem(i, j, item)

        # Adjust column widths
        self.table.resizeColumnsToContents()

    def get_dataframe(self):
        """Get the loaded dataframe"""
        return self.matrix_data

    def get_step_manager(self):
        """Get the step manager"""
        return self.step_manager

    def get_current_step(self):
        """Get current step number"""
        return self.current_step

    def is_loaded(self):
        """Check if matrix is loaded"""
        return self.matrix_data is not None

    def on_item_changed(self, item):
        """Handle item change - validate and mirror to lower triangle"""
        if self.updating_mirror:
            return

        # Only process if we're at step 0 (original matrix)
        if self.current_step != 0:
            return

        row = item.row()
        col = item.column()

        # Only process upper triangle edits
        if row >= col:
            return

        # Validate input
        try:
            value = float(item.text())
            if value < 0.0 or value > 1.0:
                QMessageBox.warning(
                    self,
                    "Invalid Value",
                    f"Similarity values must be between 0.0 and 1.0\nYou entered: {value}"
                )
                # Restore original value
                if self.matrix_data is not None:
                    self.updating_mirror = True
                    item.setText(f"{self.matrix_data.iloc[row, col]:.3f}")
                    self.updating_mirror = False
                return
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                f"Please enter a numeric value between 0.0 and 1.0\nYou entered: '{item.text()}'"
            )
            # Restore original value
            if self.matrix_data is not None:
                self.updating_mirror = True
                item.setText(f"{self.matrix_data.iloc[row, col]:.3f}")
                self.updating_mirror = False
            return

        # Update the underlying data
        if self.matrix_data is not None:
            self.matrix_data.iloc[row, col] = value
            self.matrix_data.iloc[col, row] = value  # Mirror to lower triangle

            # Update the step manager with new matrix
            self.step_manager = ClusteringStepManager(
                self.matrix_data.values,
                self.matrix_data.index.tolist()
            )

            # Update the mirror cell in the table
            self.updating_mirror = True
            mirror_item = self.table.item(col, row)
            if mirror_item:
                mirror_item.setText(f"{value:.3f}")
            self.updating_mirror = False

            # Notify parent to update dendrograms
            if hasattr(self.parent(), 'on_matrix_loaded'):
                self.parent().on_matrix_loaded()

    def update_matrix(self, new_matrix_df):
        """Update matrix with new data and labels"""
        self.matrix_data = new_matrix_df

        # Recreate step manager
        self.step_manager = ClusteringStepManager(
            new_matrix_df.values,
            new_matrix_df.index.tolist()
        )

        # Reset to step 0
        num_steps = self.step_manager.get_num_steps()
        self.step_slider.setMaximum(num_steps - 1)
        self.step_slider.setValue(0)
        self.current_step = 0

        # Show step controls
        self.step_controls.setVisible(True)
        self.update_step_display()

        # Update info label
        self.info_label.setText(f"✓ Updated: {new_matrix_df.shape[0]}×{new_matrix_df.shape[1]}, {num_steps} steps")
        self.info_label.setStyleSheet("color: green; font-size: 10px;")

    def get_labels(self):
        """Get current labels"""
        if self.matrix_data is not None:
            return self.matrix_data.index.tolist()
        return []


class StepDendrogramWidget(QWidget):
    """Widget for displaying dendrogram with step visualization"""

    def __init__(self, title="Dendrogram", parent=None):
        super().__init__(parent)
        self.title = title
        self.step_manager = None
        self.current_step = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header: title (left) and checkbox (right) in one line
        header_layout = QHBoxLayout()
        title_label = QLabel(f"<b>{self.title}</b>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.show_values_checkbox = QCheckBox("Show similarity values")
        self.show_values_checkbox.setStyleSheet("font-size: 10px;")
        self.show_values_checkbox.stateChanged.connect(self.on_checkbox_changed)
        header_layout.addWidget(self.show_values_checkbox)
        layout.addLayout(header_layout)

        # Matplotlib figure
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Info label
        self.info_label = QLabel("Load matrix to view dendrogram")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def on_checkbox_changed(self):
        """Called when checkbox state changes"""
        self.update_dendrogram()

    def set_step_manager(self, step_manager):
        """Set the step manager"""
        self.step_manager = step_manager
        self.current_step = 0
        self.update_dendrogram()

    def set_step(self, step_num):
        """Set current step and update display"""
        self.current_step = step_num
        self.update_dendrogram()

    def update_dendrogram(self):
        """Update dendrogram for current step"""
        if not self.step_manager:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.current_step == 0:
            # Step 0: no dendrogram yet
            ax.text(0.5, 0.5, 'Original Matrix\n(No clustering yet)',
                   ha='center', va='center', fontsize=12, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.info_label.setText("Step 0: Original matrix")
        else:
            # Draw full dendrogram with partial highlighting
            try:
                full_linkage = self.step_manager.linkage_matrix

                # Create custom color function to highlight completed steps
                def link_color_func(k):
                    # k is the cluster id
                    # Clusters formed in steps 1 to current_step should be colored
                    # Clusters formed after current_step should be gray
                    n = len(self.step_manager.original_labels)
                    cluster_step = k - n + 1  # Which step formed this cluster

                    if cluster_step <= self.current_step:
                        return 'blue'  # Completed
                    else:
                        return 'lightgray'  # Not yet completed

                # Plot dendrogram
                ddata = dendrogram(
                    full_linkage,
                    labels=self.step_manager.original_labels,
                    ax=ax,
                    orientation='right',
                    color_threshold=0,
                    above_threshold_color='blue',
                    link_color_func=link_color_func,
                    leaf_font_size=10
                )

                # Add vertical line to show current step height
                if self.current_step < len(full_linkage):
                    current_height = full_linkage[self.current_step - 1, 2]  # distance of current merge
                    ax.axvline(x=current_height, color='red', linestyle='--',
                              linewidth=2, alpha=0.7, label=f'Step {self.current_step}')
                    ax.legend(fontsize=8)

                # Convert X-axis labels from distance to similarity
                max_sim = self.step_manager.max_sim

                # Get current x-tick locations (distance values)
                xticks = ax.get_xticks()

                # Convert to similarity and set as labels
                # similarity = max_sim - distance
                similarity_labels = [f'{max_sim - x:.3f}' if 0 <= x <= max_sim else '' for x in xticks]
                ax.set_xticklabels(similarity_labels)

                # Add similarity values to each merge point if checkbox is checked
                if self.show_values_checkbox.isChecked():
                    # Dendrogram data contains coordinates
                    # dcoord[i] = [x1, x2, x2, x3] where x2 is the merge height (distance)
                    # icoord[i] = [y1, y2, y2, y3] where (x2, (y2+y2)/2) is merge point
                    for i, (xs, ys) in enumerate(zip(ddata['dcoord'], ddata['icoord'])):
                        # xs = [x1, x2, x2, x3], x2 is the merge distance
                        merge_distance = xs[1]  # or xs[2], they're the same
                        merge_y = (ys[1] + ys[2]) / 2.0  # Middle of horizontal line

                        # Convert distance to similarity
                        merge_similarity = max_sim - merge_distance

                        # Add text annotation
                        ax.text(merge_distance, merge_y, f' {merge_similarity:.3f}',
                               fontsize=8, color='darkblue',
                               verticalalignment='center',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                       edgecolor='lightblue', alpha=0.8))

                # Invert x-axis so high similarity (left) to low similarity (right)
                ax.invert_xaxis()

                ax.set_xlabel('Similarity', fontsize=9)
                ax.tick_params(axis='y', labelsize=9)
                ax.tick_params(axis='x', labelsize=8)

                self.info_label.setText(f"Step {self.current_step}: {self.current_step} merge(s) completed")
                self.info_label.setStyleSheet("color: green; font-size: 10px;")

            except Exception as e:
                ax.text(0.5, 0.5, f'Error plotting dendrogram:\n{str(e)}',
                       ha='center', va='center', fontsize=10, color='red')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                print(f"Dendrogram error: {e}")
                import traceback
                traceback.print_exc()

        self.figure.tight_layout()
        self.canvas.draw()


class ACCVisualizationWidget(QWidget):
    """Widget for displaying ACC concentric circles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Matplotlib figure
        self.figure = Figure(figsize=(6, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Info label
        self.info_label = QLabel("Load both matrices and click Generate")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def plot_acc_result(self, acc_result):
        """Plot ACC result with multiple concentric circles"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Get clusters from new structure
        clusters = acc_result.get("clusters", [])
        all_members = acc_result.get("all_members", set())

        if len(clusters) == 0:
            ax.text(0.5, 0.5, 'No clusters to display',
                   ha='center', va='center', fontsize=12, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
            return

        # Generate colors for clusters
        cluster_colors = plt.cm.Set3(np.linspace(0, 1, len(clusters)))

        # Track which members we've plotted (to avoid duplicates)
        plotted_members = set()

        # Draw each cluster as a separate circle
        for cluster_idx, cluster in enumerate(clusters):
            center = cluster.get("center", (0, 0))
            diameter = cluster["diameter"]
            radius = diameter / 2.0
            points = cluster["points"]
            members = cluster["members"]

            # Draw cluster circle
            circle = plt.Circle(center, radius, fill=False,
                              edgecolor=cluster_colors[cluster_idx],
                              linewidth=2,
                              label=f"Cluster {cluster_idx+1} ({len(members)} members)")
            ax.add_patch(circle)

            # Plot member points on this circle
            for member, (x, y) in points.items():
                # Only plot each member once (on the first/smallest cluster it appears in)
                if member not in plotted_members:
                    ax.plot(x, y, 'o', markersize=10,
                           color=cluster_colors[cluster_idx],
                           markeredgecolor='black', markeredgewidth=1.5)
                    ax.text(x, y, f'  {member}', fontsize=10,
                           va='center', fontweight='bold')
                    plotted_members.add(member)

        # Set equal aspect ratio and limits based on largest circle
        max_radius = max(c["diameter"]/2.0 for c in clusters)
        margin = max_radius * 0.3
        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect('equal')

        # Add grid and axes
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)
        ax.set_xlabel('X', fontsize=10)
        ax.set_ylabel('Y', fontsize=10)
        ax.set_title('ACC Concentric Circles', fontsize=11, fontweight='bold')

        # Add legend
        ax.legend(loc='upper right', fontsize=8)

        # Add info text
        info_text = f"Total members: {len(all_members)}\nClusters: {len(clusters)}"
        ax.text(0.02, 0.98, info_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        self.figure.tight_layout()
        self.canvas.draw()
        self.info_label.setText(f"✓ Generated: {len(clusters)} clusters, {len(all_members)} members")
        self.info_label.setStyleSheet("color: green; font-size: 10px;")


class ColumnPanel(QWidget):
    """Base class for column panels"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Content area
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout, stretch=1)

        self.setLayout(layout)


class LeftPanel(ColumnPanel):
    """Left panel: Similarity matrices with step control"""

    def __init__(self, parent=None):
        super().__init__("Similarity Matrices", parent)
        self.setup_content()

    def setup_content(self):
        # Subordinate matrix section
        sub_header_layout = QHBoxLayout()
        sub_label = QLabel("<b>Subordinate</b>")
        sub_header_layout.addWidget(sub_label)
        sub_header_layout.addStretch()

        # Edit Area List button (shared for both matrices)
        self.edit_areas_btn = QPushButton("Edit Area List")
        self.edit_areas_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        self.edit_areas_btn.clicked.connect(self.edit_area_list)
        self.edit_areas_btn.setEnabled(False)  # Disabled until both matrices loaded
        sub_header_layout.addWidget(self.edit_areas_btn)

        self.sub_matrix_widget = StepMatrixWidget("Subordinate", show_header=False)
        sub_header_layout.addWidget(self.sub_matrix_widget.load_btn)
        self.content_layout.addLayout(sub_header_layout)

        self.content_layout.addWidget(self.sub_matrix_widget, stretch=1)

        # Separator line
        separator = QLabel()
        separator.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setMaximumHeight(2)
        self.content_layout.addWidget(separator)

        # Inclusive matrix section
        inc_header_layout = QHBoxLayout()
        inc_label = QLabel("<b>Inclusive</b>")
        inc_header_layout.addWidget(inc_label)
        inc_header_layout.addStretch()

        self.inc_matrix_widget = StepMatrixWidget("Inclusive", show_header=False)
        inc_header_layout.addWidget(self.inc_matrix_widget.load_btn)
        self.content_layout.addLayout(inc_header_layout)

        self.content_layout.addWidget(self.inc_matrix_widget, stretch=1)

    def on_matrix_loaded(self):
        """Called when a matrix is loaded"""
        # Enable Edit Area List button if both matrices are loaded
        if self.sub_matrix_widget.is_loaded() and self.inc_matrix_widget.is_loaded():
            self.edit_areas_btn.setEnabled(True)

        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.update_dendrograms()

    def on_step_changed(self):
        """Called when step changes"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.update_dendrogram_steps()

    def edit_area_list(self):
        """Open dialog to edit area list"""
        # Check if both matrices are loaded
        if not self.sub_matrix_widget.is_loaded() or not self.inc_matrix_widget.is_loaded():
            QMessageBox.warning(
                self,
                "Missing Data",
                "Please load both Subordinate and Inclusive matrices first."
            )
            return

        # Get current labels (should be same for both)
        sub_labels = self.sub_matrix_widget.get_labels()
        inc_labels = self.inc_matrix_widget.get_labels()

        # Verify they match
        if sub_labels != inc_labels:
            QMessageBox.warning(
                self,
                "Label Mismatch",
                "Subordinate and Inclusive matrices have different labels.\n"
                "Please reload the matrices to ensure consistency."
            )
            return

        # Get current matrices
        sub_df = self.sub_matrix_widget.get_dataframe()
        inc_df = self.inc_matrix_widget.get_dataframe()

        # Open dialog
        dialog = AreaListEditorDialog(sub_labels, sub_df, inc_df, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_result()

            if result["modified"]:
                # Update both matrices
                self.sub_matrix_widget.update_matrix(result["sub_matrix"])
                self.inc_matrix_widget.update_matrix(result["inc_matrix"])

                # Notify main window to update dendrograms
                main_window = self.window()
                if isinstance(main_window, MainWindow):
                    main_window.update_dendrograms()

                QMessageBox.information(
                    self,
                    "Success",
                    f"Area list updated successfully!\n\n"
                    f"Total areas: {len(result['labels'])}\n"
                    f"Matrix size: {result['sub_matrix'].shape[0]}×{result['sub_matrix'].shape[1]}"
                )


class CenterPanel(ColumnPanel):
    """Center panel: Dendrograms with step visualization"""

    def __init__(self, parent=None):
        super().__init__("Cluster Dendrograms", parent)
        self.setup_content()

    def setup_content(self):
        # Subordinate dendrogram
        self.sub_dendro_widget = StepDendrogramWidget("Subordinate")
        self.content_layout.addWidget(self.sub_dendro_widget, stretch=1)

        # Separator line
        separator = QLabel()
        separator.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setMaximumHeight(2)
        self.content_layout.addWidget(separator)

        # Inclusive dendrogram
        self.inc_dendro_widget = StepDendrogramWidget("Inclusive")
        self.content_layout.addWidget(self.inc_dendro_widget, stretch=1)


class RightPanel(ColumnPanel):
    """Right panel: ACC visualization"""

    def __init__(self, parent=None):
        super().__init__("ACC Visualization", parent)
        self.setup_content()

    def setup_content(self):
        # Generate button
        self.generate_btn = QPushButton("🎯 Generate ACC")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #357a38;
            }
        """)
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        self.content_layout.addWidget(self.generate_btn)

        # ACC visualization
        self.acc_widget = ACCVisualizationWidget()
        self.content_layout.addWidget(self.acc_widget)

    def on_generate_clicked(self):
        """Handle generate button click"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.generate_acc()


class MainWindow(QMainWindow):
    """Main application window with 3-column layout and step-by-step visualization"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ACC Visualizer - Step-by-Step Clustering")
        self.setGeometry(50, 50, 1800, 900)

        # Create three panels
        self.left_panel = LeftPanel()
        self.center_panel = CenterPanel()
        self.right_panel = RightPanel()

        # Add to scroll areas
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(self.left_panel)

        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setWidget(self.center_panel)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setWidget(self.right_panel)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_scroll)
        splitter.addWidget(center_scroll)
        splitter.addWidget(right_scroll)

        # Set initial sizes (equal width)
        splitter.setSizes([600, 600, 600])

        # Set central widget
        self.setCentralWidget(splitter)

    def update_dendrograms(self):
        """Update dendrograms when matrices are loaded"""
        # Update subordinate dendrogram
        sub_step_mgr = self.left_panel.sub_matrix_widget.get_step_manager()
        if sub_step_mgr:
            self.center_panel.sub_dendro_widget.set_step_manager(sub_step_mgr)
            self.center_panel.sub_dendro_widget.set_step(
                self.left_panel.sub_matrix_widget.get_current_step()
            )

        # Update inclusive dendrogram
        inc_step_mgr = self.left_panel.inc_matrix_widget.get_step_manager()
        if inc_step_mgr:
            self.center_panel.inc_dendro_widget.set_step_manager(inc_step_mgr)
            self.center_panel.inc_dendro_widget.set_step(
                self.left_panel.inc_matrix_widget.get_current_step()
            )

    def update_dendrogram_steps(self):
        """Update dendrogram display when step changes"""
        # Update subordinate
        sub_step = self.left_panel.sub_matrix_widget.get_current_step()
        self.center_panel.sub_dendro_widget.set_step(sub_step)

        # Update inclusive
        inc_step = self.left_panel.inc_matrix_widget.get_current_step()
        self.center_panel.inc_dendro_widget.set_step(inc_step)

    def generate_acc(self):
        """Generate ACC visualization"""
        try:
            # Check if both matrices are loaded
            if not self.left_panel.sub_matrix_widget.is_loaded():
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "Please load the Subordinate Similarity Matrix first"
                )
                return

            if not self.left_panel.inc_matrix_widget.is_loaded():
                QMessageBox.warning(
                    self,
                    "Missing Data",
                    "Please load the Inclusive Similarity Matrix first"
                )
                return

            # Get original matrices (not step matrices)
            sub_df = self.left_panel.sub_matrix_widget.get_dataframe()
            inc_df = self.left_panel.inc_matrix_widget.get_dataframe()

            sub_matrix = dict_matrix_from_dataframe(sub_df)
            inc_matrix = dict_matrix_from_dataframe(inc_df)

            # Validate matrices
            valid, msg = validate_similarity_matrix(sub_matrix)
            if not valid:
                QMessageBox.warning(
                    self,
                    "Invalid Subordinate Matrix",
                    f"Subordinate matrix validation failed:\n{msg}"
                )
                return

            valid, msg = validate_similarity_matrix(inc_matrix)
            if not valid:
                QMessageBox.warning(
                    self,
                    "Invalid Inclusive Matrix",
                    f"Inclusive matrix validation failed:\n{msg}"
                )
                return

            # Run ACC algorithm
            acc_result = build_acc_from_matrices(sub_matrix, inc_matrix, unit=1.0, method='average')

            # Visualize
            self.right_panel.acc_widget.plot_acc_result(acc_result)

            # Build info message for new structure
            clusters = acc_result.get('clusters', [])
            all_members = acc_result.get('all_members', set())

            # Get diameter range
            if clusters:
                diameters = [c['diameter'] for c in clusters]
                min_d = min(diameters)
                max_d = max(diameters)
                diameter_info = f"Diameter range: {min_d:.3f} - {max_d:.3f}"
            else:
                diameter_info = "No clusters"

            QMessageBox.information(
                self,
                "Success",
                f"ACC Visualization generated!\n\n"
                f"Total members: {len(all_members)}\n"
                f"Clusters: {len(clusters)}\n"
                f"{diameter_info}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate visualization:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
