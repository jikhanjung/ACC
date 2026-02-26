"""
ACC (Adaptive Cluster Circle) GUI Application
PyQt5-based interface for visualizing hierarchical cluster relationships

Four-column layout with step-by-step clustering visualization:
- Data: Raw presence/absence data (multi-sheet, period-based)
- Left: Similarity Matrices (with step slider)
- Center: Dendrograms (with step visualization)
- Right: ACC Concentric Circles
"""

# Import matplotlib components with proper backend setup
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QUndoCommand,
    QUndoStack,
    QVBoxLayout,
    QWidget,
)

os.environ["QT_API"] = "pyqt5"

import matplotlib

matplotlib.use("Qt5Agg")

import logging
from io import StringIO

import matplotlib.patches as mpl_patches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.cluster.hierarchy import dendrogram

from acc_core_acc2 import build_acc2, calculate_merge_points, generate_connection_lines
from acc_utils import (
    build_acc_from_matrices_iterative,
    dict_matrix_from_dataframe,
    validate_similarity_matrix,
)
from clustering_steps import ClusteringStepManager


def compass_to_cart(r, angle_deg):
    """Convert compass angle (0°=north, positive=clockwise) to cartesian coordinates"""
    rad = math.radians(angle_deg)
    return (r * math.sin(rad), r * math.cos(rad))


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent

    return base_path / relative_path


class AreaListEditorDialog(QDialog):
    """Dialog for editing the list of areas (row/column labels)"""

    def __init__(self, current_labels, local_matrix_df, global_matrix_df, parent=None):
        super().__init__(parent)
        self.current_labels = list(current_labels)
        self.local_matrix_df = local_matrix_df.copy()
        self.global_matrix_df = global_matrix_df.copy()
        self.modified = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Area List")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Title
        title = QLabel("<h3>Edit Area List</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Info label
        info = QLabel("Areas must be the same for both Local and Global matrices.")
        info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Main content area
        content_layout = QVBoxLayout()

        # Area name input section
        input_section = QHBoxLayout()
        input_label = QLabel("<b>Area Name:</b>")
        input_section.addWidget(input_label)

        self.area_name_input = QLineEdit()
        self.area_name_input.setPlaceholderText("Enter area name...")
        self.area_name_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        input_section.addWidget(self.area_name_input, stretch=3)

        content_layout.addLayout(input_section)

        # Horizontal layout for list and buttons
        list_and_buttons = QHBoxLayout()

        # List widget
        list_container = QVBoxLayout()
        list_label = QLabel("<b>Current Areas:</b>")
        list_container.addWidget(list_label)

        self.area_list = QListWidget()
        self.area_list.addItems(self.current_labels)
        self.area_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.area_list.itemClicked.connect(self.on_area_selected)
        list_container.addWidget(self.area_list)

        list_and_buttons.addLayout(list_container, stretch=3)

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

        self.update_btn = QPushButton("💾 Update")
        self.update_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.update_btn.clicked.connect(self.update_area)
        self.update_btn.setEnabled(False)
        button_container.addWidget(self.update_btn)

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
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_area)
        self.delete_btn.setEnabled(False)
        button_container.addWidget(self.delete_btn)

        button_container.addStretch()
        list_and_buttons.addLayout(button_container, stretch=1)

        content_layout.addLayout(list_and_buttons)

        layout.addLayout(content_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_area_selected(self, item):
        """Handle area selection from list"""
        # Show selected area name in input field
        self.area_name_input.setText(item.text())
        # Enable Update and Delete buttons
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def add_area(self):
        """Add a new area from LineEdit"""
        text = self.area_name_input.text().strip()

        # Validate
        if not text:
            QMessageBox.warning(self, "Invalid Name", "Area name cannot be empty or whitespace.")
            return

        if text in self.current_labels:
            QMessageBox.warning(self, "Duplicate Name", f"Area '{text}' already exists.")
            return

        # Add to list
        self.current_labels.append(text)
        self.area_list.addItem(text)

        n = len(self.current_labels)

        if n == 1:
            # First area - create new 1x1 matrices
            self.local_matrix_df = pd.DataFrame([[1.0]], index=[text], columns=[text])
            self.global_matrix_df = pd.DataFrame([[1.0]], index=[text], columns=[text])
        else:
            # Add to existing dataframes (new row and column with default value 0.5, diagonal 1.0)
            # Create new row/column data
            new_row_sub = pd.Series([0.5] * n, index=self.current_labels)
            new_row_sub[text] = 1.0  # Diagonal

            new_row_inc = pd.Series([0.5] * n, index=self.current_labels)
            new_row_inc[text] = 1.0  # Diagonal

            # Add to local matrix
            self.local_matrix_df = pd.concat([self.local_matrix_df, pd.DataFrame([new_row_sub], index=[text])])
            self.local_matrix_df[text] = new_row_sub

            # Add to global matrix
            self.global_matrix_df = pd.concat([self.global_matrix_df, pd.DataFrame([new_row_inc], index=[text])])
            self.global_matrix_df[text] = new_row_inc

        self.modified = True
        # Clear input field
        self.area_name_input.clear()

    def update_area(self):
        """Update selected area name from LineEdit"""
        selected_items = self.area_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an area to update.")
            return

        current_item = selected_items[0]
        old_name = current_item.text()
        old_index = self.current_labels.index(old_name)

        text = self.area_name_input.text().strip()

        # Validate
        if not text:
            QMessageBox.warning(self, "Invalid Name", "Area name cannot be empty or whitespace.")
            return

        if text != old_name and text in self.current_labels:
            QMessageBox.warning(self, "Duplicate Name", f"Area '{text}' already exists.")
            return

        # If name unchanged, do nothing
        if text == old_name:
            return

        # Update list
        self.current_labels[old_index] = text
        current_item.setText(text)

        # Update dataframes - rename both index and column
        self.local_matrix_df.rename(index={old_name: text}, columns={old_name: text}, inplace=True)
        self.global_matrix_df.rename(index={old_name: text}, columns={old_name: text}, inplace=True)

        self.modified = True
        # Clear selection and input
        self.area_list.clearSelection()
        self.area_name_input.clear()
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

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
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from list
            index = self.current_labels.index(area_name)
            self.current_labels.pop(index)
            self.area_list.takeItem(index)

            # Remove from both dataframes
            self.local_matrix_df.drop(index=area_name, columns=area_name, inplace=True)
            self.global_matrix_df.drop(index=area_name, columns=area_name, inplace=True)

            self.modified = True
            # Clear selection and input
            self.area_name_input.clear()
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def get_result(self):
        """Get the modified data"""
        return {
            "labels": self.current_labels,
            "local_matrix": self.local_matrix_df,
            "global_matrix": self.global_matrix_df,
            "modified": self.modified,
        }


class LogViewerDialog(QDialog):
    """Dialog for viewing ACC generation logs"""

    def __init__(self, log_text, parent=None):
        super().__init__(parent)
        self.log_text = log_text
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ACC Generation Log")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout()

        # Title
        title = QLabel("<h3>📋 ACC Generation Log</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Info label
        info = QLabel("Detailed log of the ACC generation process")
        info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Log text area (read-only)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlainText(self.log_text)
        self.log_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_display)

        # Button layout
        button_layout = QHBoxLayout()

        # Copy to clipboard button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setStyleSheet("""
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
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)

        # Save to file button
        save_btn = QPushButton("💾 Save to File")
        save_btn.setStyleSheet("""
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
        save_btn.clicked.connect(self.save_to_file)
        button_layout.addWidget(save_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def copy_to_clipboard(self):
        """Copy log text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text)
        QMessageBox.information(self, "Copied", "Log copied to clipboard!")

    def save_to_file(self):
        """Save log to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log File", "acc_generation_log.txt", "Text Files (*.txt);;All Files (*)"
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_text)
                QMessageBox.information(self, "Saved", f"Log saved to:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log:\n{str(e)}")


class StepMatrixWidget(QWidget):
    """Widget for displaying similarity matrix with step control"""

    def __init__(self, title="Matrix", parent=None, show_header=True):
        super().__init__(parent)
        self.title = title
        self.matrix_type = title  # Store as matrix_type for consistency (e.g., "Local", "Global")
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
        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setMinimum(0)
        self.step_slider.setMaximum(0)
        self.step_slider.setValue(0)
        self.step_slider.setTickPosition(QSlider.TicksBelow)
        self.step_slider.setTickInterval(1)
        self.step_slider.valueChanged.connect(self.on_step_changed)
        slider_layout.addWidget(self.step_slider)

        # Navigation buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        self.first_btn = QPushButton("⏮")
        self.first_btn.setMaximumWidth(40)
        self.first_btn.clicked.connect(self.first_step)
        self.first_btn.setEnabled(False)
        btn_layout.addWidget(self.first_btn)

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

        self.last_btn = QPushButton("⏭")
        self.last_btn.setMaximumWidth(40)
        self.last_btn.clicked.connect(self.last_step)
        self.last_btn.setEnabled(False)
        btn_layout.addWidget(self.last_btn)

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
        # Start in data directory where sample files are located
        data_dir = str(get_resource_path("data"))

        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", data_dir, "CSV Files (*.csv);;All Files (*)")

        if file_path:
            try:
                # Read CSV with pandas
                df = pd.read_csv(file_path, index_col=0)

                # Validate it's a square matrix
                if df.shape[0] != df.shape[1]:
                    QMessageBox.warning(
                        self, "Invalid Matrix", "Matrix must be square (same number of rows and columns)"
                    )
                    return

                # Validate similarity matrix properties
                valid, msg = validate_similarity_matrix(df.values)

                if not valid:
                    QMessageBox.warning(
                        self,
                        "Invalid Similarity Matrix",
                        f"The matrix does not meet similarity matrix requirements:\n\n{msg}\n\n"
                        f"Requirements:\n"
                        f"- Diagonal values must be 1.0\n"
                        f"- Matrix must be symmetric (matrix[i,j] = matrix[j,i])\n"
                        f"- All values should be between 0.0 and 1.0",
                    )
                    return

                # Store data
                self.matrix_data = df

                # Create step manager
                self.step_manager = ClusteringStepManager(df.values, df.index.tolist())

                # Set up slider
                num_steps = self.step_manager.get_num_steps()
                self.step_slider.setMaximum(num_steps - 1)
                # Set to last step to show final dendrogram
                self.step_slider.setValue(num_steps - 1)
                self.current_step = num_steps - 1

                # Show step controls
                self.step_controls.setVisible(True)
                self.update_step_display()

                self.info_label.setText(f"✓ Loaded: {df.shape[0]}×{df.shape[1]}, {num_steps} steps")
                self.info_label.setStyleSheet("color: green; font-size: 10px;")

                # Notify parent which matrix was loaded
                if hasattr(self.parent(), "on_matrix_loaded"):
                    self.parent().on_matrix_loaded(self.matrix_type)

            except Exception as e:
                QMessageBox.critical(self, "Error Loading File", f"Failed to load CSV file:\n{str(e)}")
                import traceback

                traceback.print_exc()

    def on_step_changed(self, value):
        """Handle slider value change"""
        self.current_step = value
        self.update_step_display()

        # Notify parent
        if hasattr(self.parent(), "on_step_changed"):
            self.parent().on_step_changed()

    def first_step(self):
        """Go to first step (immediate, no preview)"""
        if self.current_step > 0:
            self.is_preview_mode = False
            self.preview_clusters = None
            self.highlight_merged = False
            self.merged_cluster_idx = None
            self.step_slider.setValue(0)

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

            if next_step_info and next_step_info["merged_pair"]:
                # Get the clusters that will be merged
                cluster_i, cluster_j = next_step_info["merged_pair"]

                # Find their indices in current step
                current_step_info = self.step_manager.get_step(self.current_step)
                current_labels = current_step_info["labels"]

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
            labels = step_info["labels"]
            for idx, label in enumerate(labels):
                if isinstance(label, (tuple, list)):
                    self.merged_cluster_idx = idx
            if self.merged_cluster_idx is not None:
                self.highlight_merged = True
                self.update_step_display()
                QTimer.singleShot(500, self._remove_highlight)

    def last_step(self):
        """Go to last step (immediate, no preview)"""
        if self.step_manager:
            max_step = self.step_manager.get_num_steps() - 1
            if self.current_step < max_step:
                self.is_preview_mode = False
                self.preview_clusters = None
                self.highlight_merged = False
                self.merged_cluster_idx = None
                self.step_slider.setValue(max_step)

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
        max_step = self.step_manager.get_num_steps() - 1
        self.step_label.setText(f"Step: {self.current_step}/{max_step}")

        # If at last step, show original matrix
        if self.current_step == max_step:
            self.step_desc_label.setText("Final step - Original matrix restored")
            # Update table with original matrix
            self.populate_table(self.step_manager.original_similarity, self.step_manager.original_labels)
        else:
            self.step_desc_label.setText(self.step_manager.get_step_description(self.current_step))
            # Update table with current step matrix
            self.populate_table(step_info["matrix"], step_info["labels"])

        # Update buttons
        self.first_btn.setEnabled(self.current_step > 0)
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < max_step)
        self.last_btn.setEnabled(self.current_step < max_step)

    def populate_table(self, matrix, labels):
        """Populate table widget with matrix data"""
        # CRITICAL: Multiple optimizations for massive speedup
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)  # Block itemChanged signals during population
        self.table.setSortingEnabled(False)  # Disable sorting

        self.table.clear()

        # Format labels for display
        display_labels = []
        for label in labels:
            if isinstance(label, (tuple, list)):
                display_labels.append("+".join(str(l) for l in label))
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
        highlight_color = Qt.yellow

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
                    item.setTextAlignment(Qt.AlignCenter)

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
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.table.setItem(i, j, item)
                elif i == j:
                    # Diagonal: empty with gray background
                    item = QTableWidgetItem("")
                    item.setBackground(Qt.lightGray)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setToolTip("Diagonal cells are always 1.0 (not shown)")
                    self.table.setItem(i, j, item)
                else:
                    # Lower triangle: empty with gray background
                    item = QTableWidgetItem("")
                    item.setBackground(Qt.lightGray)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setToolTip("Lower triangle is mirrored from upper triangle (not shown)")
                    self.table.setItem(i, j, item)

        # Re-enable everything before resizing (resizing needs updates enabled)
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)

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

        # Skip if we're programmatically updating
        if hasattr(self, "_updating_programmatically") and self._updating_programmatically:
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
                    self, "Invalid Value", f"Similarity values must be between 0.0 and 1.0\nYou entered: {value}"
                )
                # Restore original value
                if self.matrix_data is not None:
                    self.updating_mirror = True
                    item.setText(f"{self.matrix_data.iloc[row, col]:.3f}")
                    self.updating_mirror = False
                return
        except ValueError:
            QMessageBox.warning(
                self, "Invalid Input", f"Please enter a numeric value between 0.0 and 1.0\nYou entered: '{item.text()}'"
            )
            # Restore original value
            if self.matrix_data is not None:
                self.updating_mirror = True
                item.setText(f"{self.matrix_data.iloc[row, col]:.3f}")
                self.updating_mirror = False
            return

        # Update the underlying data
        if self.matrix_data is not None:
            row_label = self.matrix_data.index[row]
            col_label = self.matrix_data.columns[col]

            self.matrix_data.iloc[row, col] = value
            self.matrix_data.iloc[col, row] = value  # Mirror to lower triangle (data only)

            # Regenerate clustering with updated matrix
            self.step_manager = ClusteringStepManager(self.matrix_data.values, self.matrix_data.index.tolist())

            # Move to last step to show full dendrogram
            max_steps = len(self.step_manager.linkage_matrix) if self.step_manager else 0
            self.current_step = max_steps

            # Update slider
            self.step_slider.setMaximum(max_steps)
            self.step_slider.setValue(max_steps)

            # Update info label
            self.info_label.setText(f"✓ Updated {row_label}-{col_label}: {value:.3f}")
            self.info_label.setStyleSheet("color: green; font-size: 10px;")

            # Notify parent to update dendrogram
            if hasattr(self.parent(), "on_matrix_loaded"):
                self.parent().on_matrix_loaded(self.matrix_type)

    def update_matrix(self, new_matrix_df):
        """Update matrix with new data and labels"""
        self.matrix_data = new_matrix_df

        # Check if matrix is valid (at least 2 areas for clustering)
        if new_matrix_df.shape[0] < 2:
            # Not enough data for clustering
            self.step_controls.setVisible(False)
            self.table.clear()
            if new_matrix_df.shape[0] == 1:
                # Show single area
                label = new_matrix_df.index[0]
                self.table.setRowCount(1)
                self.table.setColumnCount(1)
                self.table.setHorizontalHeaderLabels([label])
                self.table.setVerticalHeaderLabels([label])
                item = QTableWidgetItem("")
                item.setBackground(Qt.lightGray)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setToolTip("Diagonal cell (always 1.0)")
                self.table.setItem(0, 0, item)
                self.info_label.setText("✓ Updated: 1 area (need at least 2 for clustering)")
                self.info_label.setStyleSheet("color: orange; font-size: 10px;")
            else:
                self.info_label.setText("No data")
                self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 9px;")
            return

        # Recreate step manager
        self.step_manager = ClusteringStepManager(new_matrix_df.values, new_matrix_df.index.tolist())

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

        # Enable right-click context menu for saving
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.canvas)

        # Info label
        self.info_label = QLabel("Load matrix to view dendrogram")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def show_context_menu(self, pos):
        """Show context menu for saving image"""
        menu = QMenu(self)

        save_action = QAction("Save Image As...", self)
        save_action.triggered.connect(self.save_image)
        menu.addAction(save_action)

        menu.exec_(self.canvas.mapToGlobal(pos))

    def save_image(self):
        """Save the current figure to an image file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Dendrogram Image",
            f"{self.title.replace(' ', '_')}_dendrogram.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )

        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches="tight")
                QMessageBox.information(self, "Success", f"Image saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")

    def on_checkbox_changed(self):
        """Called when checkbox state changes"""
        self.update_dendrogram()

    def set_step_manager(self, step_manager):
        """Set the step manager"""
        self.step_manager = step_manager
        # Keep current step as set by the matrix widget
        # (matrix widget sets step to 0 before calling this)
        self.update_dendrogram()

    def set_step(self, step_num):
        """Set current step and update display"""
        self.current_step = step_num
        self.update_dendrogram()

    def clear_display(self):
        """Clear dendrogram display (called when matrix is modified)"""
        self.step_manager = None
        self.current_step = 0
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(
            0.5,
            0.5,
            "Matrix Modified\n\nPlease reload or regenerate\nto see updated dendrogram",
            ha="center",
            va="center",
            fontsize=12,
            color="orange",
            weight="bold",
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        self.figure.tight_layout()
        self.canvas.draw()
        self.info_label.setText("Matrix modified - reload needed")
        self.info_label.setStyleSheet("color: orange; font-size: 10px;")

    def update_dendrogram(self):
        """Update dendrogram for current step"""
        if not self.step_manager:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if self.current_step == 0:
            # Step 0: no dendrogram yet
            ax.text(
                0.5, 0.5, "Original Matrix\n(No clustering yet)", ha="center", va="center", fontsize=12, color="gray"
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
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
                        return "blue"  # Completed
                    return "lightgray"  # Not yet completed

                # Plot dendrogram
                ddata = dendrogram(
                    full_linkage,
                    labels=self.step_manager.original_labels,
                    ax=ax,
                    orientation="right",
                    color_threshold=0,
                    above_threshold_color="blue",
                    link_color_func=link_color_func,
                    leaf_font_size=10,
                )

                # Add vertical line to show current step height
                if self.current_step < len(full_linkage):
                    current_height = full_linkage[self.current_step - 1, 2]  # distance of current merge
                    ax.axvline(
                        x=current_height,
                        color="red",
                        linestyle="--",
                        linewidth=2,
                        alpha=0.7,
                        label=f"Step {self.current_step}",
                    )
                    ax.legend(fontsize=8)

                # Convert X-axis labels from distance to similarity
                max_sim = self.step_manager.max_sim

                # Get current x-tick locations (distance values)
                xticks = ax.get_xticks()

                # Convert to similarity and set as labels
                # similarity = max_sim - distance
                similarity_labels = [f"{max_sim - x:.3f}" if 0 <= x <= max_sim else "" for x in xticks]
                ax.set_xticks(xticks)  # Set tick locations first
                ax.set_xticklabels(similarity_labels)  # Then set labels

                # Add similarity values to each merge point if checkbox is checked
                if self.show_values_checkbox.isChecked():
                    # Dendrogram data contains coordinates
                    # dcoord[i] = [x1, x2, x2, x3] where x2 is the merge height (distance)
                    # icoord[i] = [y1, y2, y2, y3] where (x2, (y2+y2)/2) is merge point
                    for i, (xs, ys) in enumerate(zip(ddata["dcoord"], ddata["icoord"])):
                        # xs = [x1, x2, x2, x3], x2 is the merge distance
                        merge_distance = xs[1]  # or xs[2], they're the same
                        merge_y = (ys[1] + ys[2]) / 2.0  # Middle of horizontal line

                        # Convert distance to similarity
                        merge_similarity = max_sim - merge_distance

                        # Add text annotation
                        ax.text(
                            merge_distance,
                            merge_y,
                            f" {merge_similarity:.3f}",
                            fontsize=8,
                            color="darkblue",
                            verticalalignment="center",
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="lightblue", alpha=0.8),
                        )

                # Invert x-axis so high similarity (left) to low similarity (right)
                ax.invert_xaxis()

                # Move y-axis labels to the right side
                ax.yaxis.tick_right()
                ax.yaxis.set_label_position("right")

                ax.set_xlabel("Similarity", fontsize=9)
                ax.tick_params(axis="y", labelsize=9)
                ax.tick_params(axis="x", labelsize=8)

                self.info_label.setText(f"Step {self.current_step}: {self.current_step} merge(s) completed")
                self.info_label.setStyleSheet("color: green; font-size: 10px;")

            except Exception as e:
                ax.text(
                    0.5,
                    0.5,
                    f"Error plotting dendrogram:\n{str(e)}",
                    ha="center",
                    va="center",
                    fontsize=10,
                    color="red",
                )
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis("off")
                print(f"Dendrogram error: {e}")
                import traceback

                traceback.print_exc()

        self.figure.tight_layout()
        self.canvas.draw()


class ACCVisualizationWidget(QWidget):
    """Widget for displaying ACC concentric circles with step-by-step visualization"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.acc_steps = []  # List of all steps
        self.current_step = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Step controls
        self.step_controls = QWidget()
        step_layout = QVBoxLayout()
        step_layout.setContentsMargins(0, 2, 0, 2)
        step_layout.setSpacing(3)

        # Step label and description in one line
        step_info_layout = QHBoxLayout()
        self.step_label = QLabel("Step: 0/0")
        self.step_label.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 10px;")
        step_info_layout.addWidget(self.step_label)

        self.step_desc_label = QLabel("Generate ACC to begin")
        self.step_desc_label.setStyleSheet("font-size: 9px; color: #666;")
        step_info_layout.addWidget(self.step_desc_label)
        step_info_layout.addStretch()
        step_layout.addLayout(step_info_layout)

        # Slider and buttons
        slider_layout = QHBoxLayout()
        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setMinimum(0)
        self.step_slider.setMaximum(0)
        self.step_slider.setValue(0)
        self.step_slider.setTickPosition(QSlider.TicksBelow)
        self.step_slider.setTickInterval(1)
        self.step_slider.valueChanged.connect(self.on_step_changed)
        slider_layout.addWidget(self.step_slider)

        # Navigation buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)

        self.first_btn = QPushButton("⏮")
        self.first_btn.setMaximumWidth(40)
        self.first_btn.clicked.connect(self.first_step)
        self.first_btn.setEnabled(False)
        btn_layout.addWidget(self.first_btn)

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

        self.last_btn = QPushButton("⏭")
        self.last_btn.setMaximumWidth(40)
        self.last_btn.clicked.connect(self.last_step)
        self.last_btn.setEnabled(False)
        btn_layout.addWidget(self.last_btn)

        slider_layout.addLayout(btn_layout)
        step_layout.addLayout(slider_layout)

        self.step_controls.setLayout(step_layout)
        self.step_controls.setVisible(False)
        layout.addWidget(self.step_controls)

        # Matplotlib figure
        self.figure = Figure(figsize=(6, 6))
        self.canvas = FigureCanvas(self.figure)

        # Enable right-click context menu for saving
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.canvas, stretch=1)

        # Info label
        self.info_label = QLabel("Load both matrices and click Generate")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def show_context_menu(self, pos):
        """Show context menu for saving image"""
        menu = QMenu(self)

        save_action = QAction("Save Image As...", self)
        save_action.triggered.connect(self.save_image)
        menu.addAction(save_action)

        menu.exec_(self.canvas.mapToGlobal(pos))

    def save_image(self):
        """Save the current figure to an image file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save ACC Visualization",
            "ACC_visualization.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )

        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches="tight")
                QMessageBox.information(self, "Success", f"Image saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")

    def on_step_changed(self, value):
        """Handle slider value change"""
        self.current_step = value
        self.update_step_display()

    def first_step(self):
        """Go to first step"""
        if self.current_step > 0:
            self.step_slider.setValue(0)

    def prev_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self.step_slider.setValue(self.current_step - 1)

    def next_step(self):
        """Go to next step"""
        if self.current_step < len(self.acc_steps) - 1:
            self.step_slider.setValue(self.current_step + 1)

    def last_step(self):
        """Go to last step"""
        if self.acc_steps and self.current_step < len(self.acc_steps) - 1:
            self.step_slider.setValue(len(self.acc_steps) - 1)

    def update_step_display(self):
        """Update display for current step"""
        if not self.acc_steps or self.current_step >= len(self.acc_steps):
            return

        # Update labels
        total_steps = len(self.acc_steps) - 1
        self.step_label.setText(f"Step: {self.current_step}/{total_steps}")

        step_info = self.acc_steps[self.current_step]
        self.step_desc_label.setText(step_info["description"])

        # Update buttons
        self.first_btn.setEnabled(self.current_step > 0)
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < total_steps)
        self.last_btn.setEnabled(self.current_step < total_steps)

        # Plot current step
        self.plot_acc_step(step_info)

    def set_acc_steps(self, steps):
        """Set ACC steps and display last step"""
        self.acc_steps = steps
        if steps:
            self.step_slider.setMaximum(len(steps) - 1)
            # Set to last step to show final ACC visualization
            last_step = len(steps) - 1
            self.step_slider.setValue(last_step)
            self.current_step = last_step
            self.step_controls.setVisible(True)
            self.update_step_display()
        else:
            self.step_controls.setVisible(False)

    def plot_acc_step(self, step_info):
        """Plot a single ACC step (supports new iterative algorithm)"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # New algorithm uses "clusters" list instead of single "current_cluster"
        clusters = step_info.get("clusters", [])
        highlighted_members = step_info.get("highlighted_members", set())
        action = step_info.get("action", "unknown")

        if not clusters:
            ax.text(0.5, 0.5, "No clusters to display", ha="center", va="center", fontsize=12, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            self.canvas.draw()
            return

        # Find bounds for all clusters
        all_x = []
        all_y = []
        max_radius = 0

        for cluster in clusters:
            points = cluster.get("points", {})
            for x, y in points.values():
                all_x.append(x)
                all_y.append(y)
            radius = cluster.get("radius", 0)
            max_radius = max(max_radius, radius)

        if not all_x:
            ax.text(0.5, 0.5, "No points to display", ha="center", va="center", fontsize=12, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            self.canvas.draw()
            return

        # STEP 1: Collect all unique radii from all clusters
        import math

        all_radii = set()
        all_points = {}

        for cluster in clusters:
            points = cluster.get("points", {})

            for member, (x, y) in points.items():
                # Calculate actual radius from origin (0, 0)
                # All points in ACC lie on concentric circles centered at origin
                actual_radius = math.sqrt(x**2 + y**2)
                all_radii.add(round(actual_radius, 3))
                all_points[member] = (x, y, actual_radius)

        # STEP 2: Draw concentric circles for each unique radius
        sorted_radii = sorted(all_radii)
        circle_colors_concentric = plt.cm.rainbow(np.linspace(0, 1, len(sorted_radii)))

        # Create radius-to-color mapping
        radius_to_color = {}
        for idx, radius in enumerate(sorted_radii):
            radius_to_color[radius] = circle_colors_concentric[idx]
            circle = plt.Circle(
                (0, 0),
                radius,
                fill=False,
                edgecolor=circle_colors_concentric[idx],
                linewidth=2,
                linestyle="-",
                alpha=0.6,
                label=f"Circle r={radius:.3f}",
            )
            ax.add_patch(circle)

        # STEP 3: Plot member points
        total_members = sum(len(c.get("members", set())) for c in clusters)

        for member, (x, y, r) in all_points.items():
            # Find the closest radius in sorted_radii to get the matching color
            rounded_r = round(r, 3)

            # Use different colors for highlighted vs existing members
            if member in highlighted_members:
                color = "red"  # Highlighted (newly added)
                markersize = 12
                label_color = "red"
            else:
                # Use the color of the concentric circle this point is on
                color = radius_to_color.get(rounded_r, circle_colors_concentric[0])
                markersize = 10
                label_color = "black"

            ax.plot(x, y, "o", markersize=markersize, color=color, markeredgecolor="black", markeredgewidth=1.5)
            ax.text(x, y + 0.08, f"{member}", fontsize=10, ha="center", fontweight="bold", color=label_color)

        # Set equal aspect ratio and limits
        margin = max_radius * 0.5 if max_radius > 0 else 1.0
        x_range = max(all_x) - min(all_x) if len(all_x) > 1 else 2.0
        y_range = max(all_y) - min(all_y) if len(all_y) > 1 else 2.0
        plot_range = max(x_range, y_range, max_radius * 2) + margin

        center_x = (max(all_x) + min(all_x)) / 2 if len(all_x) > 1 else 0
        center_y = (max(all_y) + min(all_y)) / 2 if len(all_y) > 1 else 0

        ax.set_xlim(center_x - plot_range / 2, center_x + plot_range / 2)
        ax.set_ylim(center_y - plot_range / 2, center_y + plot_range / 2)
        ax.set_aspect("equal")

        # Add grid and axes
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)
        ax.axvline(x=0, color="k", linestyle="--", alpha=0.3)
        ax.set_xlabel("X", fontsize=10)
        ax.set_ylabel("Y", fontsize=10)

        # Title with step info
        title = f"ACC Step {self.current_step}: {action}"
        ax.set_title(title, fontsize=11, fontweight="bold")

        # Add info text
        info_lines = [f"Active Clusters: {len(clusters)}", f"Total Members: {total_members}", f"Action: {action}"]
        if highlighted_members:
            info_lines.append(f"Added: {', '.join(sorted(highlighted_members))}")

        info_text = "\n".join(info_lines)
        ax.text(
            0.02,
            0.98,
            info_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        self.figure.tight_layout()
        self.canvas.draw()

        # Update info label
        self.info_label.setText(f"✓ Step {self.current_step}: {total_members} members")
        self.info_label.setStyleSheet("color: green; font-size: 10px;")

    def plot_acc_result(self, acc_result):
        """Plot ACC result with multiple concentric circles"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Get clusters from new structure
        clusters = acc_result.get("clusters", [])
        all_members = acc_result.get("all_members", set())

        if len(clusters) == 0:
            ax.text(0.5, 0.5, "No clusters to display", ha="center", va="center", fontsize=12, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            self.canvas.draw()
            return

        # STEP 1: Collect all unique radii from all clusters
        all_radii = set()
        all_points = {}

        for cluster in clusters:
            points = cluster["points"]

            for member, (x, y) in points.items():
                # Calculate actual radius from origin (0, 0)
                # All points in ACC lie on concentric circles centered at origin
                actual_radius = math.sqrt(x**2 + y**2)
                all_radii.add(round(actual_radius, 3))  # Round to avoid floating point issues
                all_points[member] = (x, y, actual_radius)

        # STEP 2: Draw concentric circles for each unique radius
        sorted_radii = sorted(all_radii)
        circle_colors = plt.cm.rainbow(np.linspace(0, 1, len(sorted_radii)))

        for idx, radius in enumerate(sorted_radii):
            circle = plt.Circle(
                (0, 0),
                radius,
                fill=False,
                edgecolor=circle_colors[idx],
                linewidth=2,
                linestyle="-",
                alpha=0.7,
                label=f"Circle r={radius:.3f}",
            )
            ax.add_patch(circle)

        # STEP 3: Plot member points
        for member, (x, y, r) in all_points.items():
            ax.plot(x, y, "o", markersize=10, color="darkblue", markeredgecolor="black", markeredgewidth=1.5)
            ax.text(x, y + 0.08, f"{member}", fontsize=10, ha="center", fontweight="bold")

        # Set equal aspect ratio and limits based on largest circle
        max_radius = max(c["diameter"] / 2.0 for c in clusters)
        margin = max_radius * 0.3
        ax.set_xlim(-max_radius - margin, max_radius + margin)
        ax.set_ylim(-max_radius - margin, max_radius + margin)
        ax.set_aspect("equal")

        # Add grid and axes
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)
        ax.axvline(x=0, color="k", linestyle="--", alpha=0.3)
        ax.set_xlabel("X", fontsize=10)
        ax.set_ylabel("Y", fontsize=10)
        ax.set_title("ACC Concentric Circles", fontsize=11, fontweight="bold")

        # Add legend
        ax.legend(loc="upper right", fontsize=8)

        # Add info text
        info_text = f"Total members: {len(all_members)}\nClusters: {len(clusters)}"
        ax.text(
            0.02,
            0.98,
            info_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        self.figure.tight_layout()
        self.canvas.draw()
        self.info_label.setText(f"✓ Generated: {len(clusters)} clusters, {len(all_members)} members")
        self.info_label.setStyleSheet("color: green; font-size: 10px;")

    def get_all_descendants(self, cluster_id, levels, positions):
        """Get all area descendants of a cluster"""
        # If it's an area (not a cluster), return itself
        if cluster_id in positions:
            return [cluster_id]

        # Find the level that created this cluster
        for level in levels:
            level_cluster_id = f"[{level['cluster1']}, {level['cluster2']}]"
            if level_cluster_id == cluster_id:
                # Recursively get descendants from both children
                child1_descendants = self.get_all_descendants(level["cluster1"], levels, positions)
                child2_descendants = self.get_all_descendants(level["cluster2"], levels, positions)
                return child1_descendants + child2_descendants

        return []

    def apply_acc2_swaps(self, acc2_data, swaps):
        """Apply swaps to ACC2 data and return modified copy

        Strategy: For each swap, exchange the angular positions of two child branches
        by calculating the offset between them and their descendants.
        """
        import copy

        data = copy.deepcopy(acc2_data)
        positions = data["positions"]
        levels = data["levels"]

        # Apply swaps in order from lowest level (earliest merge) to highest level (latest merge)
        sorted_swap_levels = sorted([idx for idx, should_swap in swaps.items() if should_swap])

        for level_idx in sorted_swap_levels:
            if level_idx >= len(levels):
                continue

            level = levels[level_idx]
            cluster1_id = level["cluster1"]
            cluster2_id = level["cluster2"]
            cluster_id = f"[{cluster1_id}, {cluster2_id}]"

            # Calculate current merge point based on current positions
            current_merge_points = calculate_merge_points(levels, positions)
            if cluster_id not in current_merge_points:
                continue

            # Get the angles of the two children (could be areas or clusters)
            def get_child_angle(child_id):
                if child_id in positions:
                    return positions[child_id]["angle"]
                if child_id in current_merge_points:
                    return current_merge_points[child_id]["angle"]
                return None

            child1_angle = get_child_angle(cluster1_id)
            child2_angle = get_child_angle(cluster2_id)

            if child1_angle is None or child2_angle is None:
                continue

            # Get descendants for each child
            child1_descendants = self.get_all_descendants(cluster1_id, levels, positions)
            child2_descendants = self.get_all_descendants(cluster2_id, levels, positions)

            # Calculate the angular offset needed to swap the two children
            # We want to swap them around their midpoint
            midpoint_angle = (child1_angle + child2_angle) / 2.0
            offset1 = child1_angle - midpoint_angle
            offset2 = child2_angle - midpoint_angle

            # Store new angles temporarily to avoid overwriting during swap
            new_angles = {}

            # Move child1's descendants to where child2 was
            for area in child1_descendants:
                if area in positions:
                    current_angle = positions[area]["angle"]
                    # Calculate relative position within child1
                    relative_angle = current_angle - child1_angle
                    # Place it at child2's position with same relative angle
                    new_angles[area] = child2_angle + relative_angle

            # Move child2's descendants to where child1 was
            for area in child2_descendants:
                if area in positions:
                    current_angle = positions[area]["angle"]
                    # Calculate relative position within child2
                    relative_angle = current_angle - child2_angle
                    # Place it at child1's position with same relative angle
                    new_angles[area] = child1_angle + relative_angle

            # Apply all new angles at once
            for area, new_angle in new_angles.items():
                positions[area]["angle"] = new_angle

        # Recalculate merge points and lines with final positions
        data["merge_points"] = calculate_merge_points(levels, positions)
        data["lines"] = generate_connection_lines(levels, positions, data["merge_points"])

        return data

    def plot_acc2(self, acc2_data, reset_swaps=True, acc1_style=False):
        """Plot ACC2 visualization with dendrogram on concentric circles"""
        import copy

        # Apply ACC1 style to the data first (before storing)
        if acc1_style:
            acc2_data = copy.deepcopy(acc2_data)

            # For each area, find its first merge level and place it on that circle
            area_to_first_merge_radius = {}

            for level_idx, level in enumerate(acc2_data["levels"]):
                cluster1 = level["cluster1"]
                cluster2 = level["cluster2"]
                merge_radius = level["radius"]

                # Get all areas in cluster1 and cluster2
                def get_areas(cluster_id):
                    # If it's already an area, return it
                    if cluster_id in acc2_data["positions"]:
                        return [cluster_id]
                    # Otherwise, recursively find areas in this cluster
                    areas = []
                    for lvl in acc2_data["levels"]:
                        if f"[{lvl['cluster1']}, {lvl['cluster2']}]" == cluster_id:
                            areas.extend(get_areas(lvl["cluster1"]))
                            areas.extend(get_areas(lvl["cluster2"]))
                            break
                    return areas

                areas1 = get_areas(cluster1)
                areas2 = get_areas(cluster2)

                # For each area, if not yet assigned, assign to this merge radius
                for area in areas1 + areas2:
                    if area not in area_to_first_merge_radius:
                        area_to_first_merge_radius[area] = merge_radius

            # Update position radii
            for area, merge_radius in area_to_first_merge_radius.items():
                if area in acc2_data["positions"]:
                    acc2_data["positions"][area]["radius"] = merge_radius

        # Store ACC2 data for interactive manipulation (with ACC1 style already applied if requested)
        self.acc2_data = acc2_data

        # Store acc1_style setting
        self.acc1_style = acc1_style

        # Initialize or keep swap state
        if reset_swaps or not hasattr(self, "acc2_swaps"):
            self.acc2_swaps = {}  # {level_idx: True/False}

        # Apply swaps to create modified data
        working_data = self.apply_acc2_swaps(acc2_data, self.acc2_swaps)

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="k", linewidth=0.5, alpha=0.3)
        ax.axvline(x=0, color="k", linewidth=0.5, alpha=0.3)

        circles = working_data["circles"]
        positions = working_data["positions"]
        merge_points = working_data["merge_points"]
        lines = working_data["lines"]
        levels = working_data["levels"]

        # Create radius -> global_sim mapping
        radius_to_sim = {}
        for level in levels:
            radius_to_sim[level["radius"]] = level["global_sim"]

        # Step 1: Draw all concentric circles
        circle_colors = plt.cm.rainbow(np.linspace(0, 1, len(circles)))

        for idx, radius in enumerate(circles):
            # Label with global similarity instead of radius
            if radius == 0.5:
                label = "Areas"
            else:
                global_sim = radius_to_sim.get(radius, 0.0)
                label = f"global_sim={global_sim:.3f}"

            circle = plt.Circle(
                (0, 0),
                radius,
                fill=False,
                edgecolor=circle_colors[idx],
                linewidth=2,
                linestyle="-",
                alpha=0.7,
                label=label,
            )
            ax.add_patch(circle)

        # Step 2: Draw connection lines
        # First draw arcs, then radial lines (so radial lines are on top)

        # Draw arcs
        for line in lines:
            if line["type"] == "arc":
                radius = line["radius"]
                angle_start = line["angle_start"]
                angle_end = line["angle_end"]

                # Convert from compass convention (0° = north, positive = clockwise)
                # to matplotlib convention (0° = east, positive = counter-clockwise)
                # Formula: mpl_angle = 90 - compass_angle
                mpl_angle_start = 90 - angle_start
                mpl_angle_end = 90 - angle_end

                # Ensure proper arc direction (smaller to larger in matplotlib convention)
                if mpl_angle_start > mpl_angle_end:
                    mpl_angle_start, mpl_angle_end = mpl_angle_end, mpl_angle_start

                arc = mpl_patches.Arc(
                    (0, 0),
                    2 * radius,
                    2 * radius,
                    angle=0,
                    theta1=mpl_angle_start,
                    theta2=mpl_angle_end,
                    color="black",
                    linewidth=2,
                    alpha=0.8,
                )
                ax.add_patch(arc)

        # Draw radial lines
        # Get innermost circle radius (minimum radius in circles)
        innermost_radius = min(circles) if circles else 0.5

        for line in lines:
            if line["type"] == "radial":
                r1, angle = line["from"]
                r2, _ = line["to"]

                # Skip radial lines starting from innermost circle if ACC1 style
                if self.acc1_style and abs(r1 - innermost_radius) < 0.001:
                    continue

                # Convert to cartesian using compass convention
                x1, y1 = compass_to_cart(r1, angle)
                x2, y2 = compass_to_cart(r2, angle)

                ax.plot([x1, x2], [y1, y2], "k-", linewidth=2, alpha=0.8)

        # Step 3: Draw areas at r=0.5
        # Calculate label offset based on max radius for proper scaling
        max_radius = max(circles) if circles else 1.0
        label_offset = max_radius * 0.08  # Scale offset proportionally to chart size

        for area, pos in positions.items():
            angle = pos["angle"]
            radius = pos["radius"]

            # Use stored x, y for area position (more accurate than recalculating)
            # Scale to the actual radius in case it was modified
            original_r = math.sqrt(pos["x"] ** 2 + pos["y"] ** 2) if (pos["x"] ** 2 + pos["y"] ** 2) > 0 else 1
            scale = radius / original_r if original_r > 0 else 1
            x, y = pos["x"] * scale, pos["y"] * scale

            # Draw area point
            ax.scatter(x, y, c="darkblue", s=200, zorder=10, edgecolors="black", linewidth=2)

            # Label area with dynamic offset based on max radius
            label_r = radius - label_offset
            label_x, label_y = compass_to_cart(label_r, angle)
            ax.text(label_x, label_y, area, fontsize=14, ha="center", va="center", fontweight="bold", color="darkblue")

        # Step 4: Draw merge points (small red dots) and store their info
        merge_point_data = []  # Store (x, y, merge_angle, subtended_angle, local_sim, cluster_id)

        # Create mapping from cluster_id to local similarity and children
        cluster_to_subsim = {}
        cluster_to_children = {}
        for level in levels:
            cluster_id = f"[{level['cluster1']}, {level['cluster2']}]"
            cluster_to_subsim[cluster_id] = level["local_sim"]
            cluster_to_children[cluster_id] = (level["cluster1"], level["cluster2"])

        for cluster_id, mp in merge_points.items():
            merge_angle = mp["angle"]
            radius = mp["radius"]

            # Convert to cartesian using compass convention
            x, y = compass_to_cart(radius, merge_angle)

            # Draw merge point
            ax.scatter(x, y, c="red", s=50, zorder=9, edgecolors="black", linewidth=1, alpha=0.6)

            # Calculate subtended angle (angle between two children)
            subtended_angle = 0.0
            if cluster_id in cluster_to_children:
                child1_id, child2_id = cluster_to_children[cluster_id]

                # Get child angles
                def get_child_angle(child_id):
                    if child_id in positions:
                        return positions[child_id]["angle"]
                    if child_id in merge_points:
                        return merge_points[child_id]["angle"]
                    return None

                child1_angle = get_child_angle(child1_id)
                child2_angle = get_child_angle(child2_id)

                if child1_angle is not None and child2_angle is not None:
                    # Calculate absolute difference
                    subtended_angle = abs(child2_angle - child1_angle)
                    # Handle wrap-around (e.g., 350° to 10° should be 20°, not 340°)
                    if subtended_angle > 180:
                        subtended_angle = 360 - subtended_angle

            # Store merge point data for hover
            local_sim = cluster_to_subsim.get(cluster_id, 0.0)
            merge_point_data.append((x, y, merge_angle, subtended_angle, local_sim, cluster_id))

        # Set plot limits
        max_radius = max(circles)
        lim = max_radius * 1.2
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)

        # Add title
        ax.set_title("ACC2: Dendrogram on Concentric Circles", fontsize=12, fontweight="bold")

        # Add info text
        info_lines = [
            f"Total areas: {len(positions)}",
            f"Merge levels: {len(levels)}",
            f"Circles: {len(circles)}",
            f"All areas at r={circles[0]:.1f}",
        ]
        info_text = "\n".join(info_lines)
        ax.text(
            0.02,
            0.98,
            info_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )

        # Add legend (limit to first few circles)
        handles, labels = ax.get_legend_handles_labels()
        if len(handles) > 8:
            handles = handles[:4] + handles[-4:]
            labels = labels[:4] + labels[-4:]
        ax.legend(handles, labels, loc="upper right", fontsize=8, ncol=2)

        # Add interactive hover annotation for merge points
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="yellow", alpha=0.9),
            fontsize=9,
            visible=False,
            zorder=100,
        )

        def on_hover(event):
            """Handle mouse hover events"""
            if event.inaxes != ax:
                annot.set_visible(False)
                self.canvas.draw_idle()
                return

            # Check if mouse is near any merge point
            if event.xdata is None or event.ydata is None:
                return

            # Find closest merge point
            min_dist = float("inf")
            closest_point = None

            for x, y, merge_angle, subtended_angle, local_sim, cluster_id in merge_point_data:
                dist = ((event.xdata - x) ** 2 + (event.ydata - y) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_point = (x, y, merge_angle, subtended_angle, local_sim, cluster_id)

            # Show annotation if close enough (threshold based on axes limits)
            threshold = lim * 0.05  # 5% of axis limit
            if min_dist < threshold and closest_point:
                x, y, merge_angle, subtended_angle, local_sim, cluster_id = closest_point
                annot.xy = (x, y)
                text = f"{cluster_id}\nAngle: {subtended_angle:.1f}°\nSub sim: {local_sim:.3f}"
                annot.set_text(text)
                annot.set_visible(True)
            else:
                annot.set_visible(False)

            self.canvas.draw_idle()

        # Connect hover event
        self.canvas.mpl_connect("motion_notify_event", on_hover)

        def on_click(event):
            """Handle mouse click events"""
            if event.inaxes != ax:
                return

            # Check if click is near any merge point
            if event.xdata is None or event.ydata is None:
                return

            # Find closest merge point
            min_dist = float("inf")
            closest_point = None
            closest_level_idx = None

            for x, y, merge_angle, subtended_angle, local_sim, cluster_id in merge_point_data:
                dist = ((event.xdata - x) ** 2 + (event.ydata - y) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_point = (x, y, merge_angle, subtended_angle, local_sim, cluster_id)

                    # Find level index for this cluster_id
                    for idx, level in enumerate(levels):
                        level_cluster_id = f"[{level['cluster1']}, {level['cluster2']}]"
                        if level_cluster_id == cluster_id:
                            closest_level_idx = idx
                            break

            # If click is close enough, toggle swap
            threshold = lim * 0.05  # 5% of axis limit
            if min_dist < threshold and closest_level_idx is not None:
                # Toggle swap for this level
                self.acc2_swaps[closest_level_idx] = not self.acc2_swaps.get(closest_level_idx, False)

                # Redraw with swaps applied
                self.plot_acc2(self.acc2_data, reset_swaps=False)

                # Show feedback
                _, _, _, _, _, cluster_id = closest_point
                swap_state = "swapped" if self.acc2_swaps[closest_level_idx] else "normal"
                self.info_label.setText(f"✓ {cluster_id} - {swap_state}")
                self.info_label.setStyleSheet("color: blue; font-size: 10px;")

        # Connect click event
        self.canvas.mpl_connect("button_press_event", on_click)

        self.figure.tight_layout()
        self.canvas.draw()
        self.info_label.setText(f"✓ ACC2 Generated: {len(positions)} areas, {len(circles)} circles")
        self.info_label.setStyleSheet("color: green; font-size: 10px;")

        # Hide step controls for ACC2
        self.step_controls.setVisible(False)


# ── Undo/Redo Commands ──


class CellChangeCommand(QUndoCommand):
    """Undo/redo a single cell value change (0↔1)"""

    def __init__(self, table, row, col, old_val, new_val, text="Cell Change"):
        super().__init__(text)
        self._table = table
        self._row = row
        self._col = col
        self._old = old_val
        self._new = new_val

    def redo(self):
        self._table._set_cell(self._row, self._col, self._new)

    def undo(self):
        self._table._set_cell(self._row, self._col, self._old)


class BulkCellChangeCommand(QUndoCommand):
    """Undo/redo multiple cell value changes at once (fill selection)"""

    def __init__(self, table, changes, text="Fill Selection"):
        super().__init__(text)
        self._table = table
        # changes: list of (row, col, old_val, new_val)
        self._changes = changes

    def redo(self):
        for row, col, _old, new in self._changes:
            self._table._set_cell(row, col, new)

    def undo(self):
        for row, col, old, _new in self._changes:
            self._table._set_cell(row, col, old)


class AddAreaCommand(QUndoCommand):
    """Undo/redo adding an area to all sheets"""

    def __init__(self, data_panel, at_row, name, text="Add Area"):
        super().__init__(text)
        self._dp = data_panel
        self._at_row = at_row
        self._name = name

    def redo(self):
        for table in self._dp._all_tables():
            at = max(0, min(self._at_row, table.rowCount()))
            table.insertRow(at)
            table.areas.insert(at, self._name)
            table.setVerticalHeaderLabels(table.areas)
            for c in range(table.columnCount()):
                table._set_cell(at, c, 0)
        self._dp._update_global_tab()

    def undo(self):
        for table in self._dp._all_tables():
            if self._at_row < table.rowCount():
                table.removeRow(self._at_row)
                table.areas.pop(self._at_row)
        self._dp._update_global_tab()


class DeleteAreaCommand(QUndoCommand):
    """Undo/redo deleting an area from all sheets"""

    def __init__(self, data_panel, row, area_name, per_sheet_data, text="Delete Area"):
        super().__init__(text)
        self._dp = data_panel
        self._row = row
        self._name = area_name
        # per_sheet_data: list of row-data lists, one per table
        self._per_sheet_data = per_sheet_data

    def redo(self):
        for table in self._dp._all_tables():
            if self._row < table.rowCount():
                table.removeRow(self._row)
                table.areas.pop(self._row)
        self._dp._update_global_tab()

    def undo(self):
        tables = self._dp._all_tables()
        for i, table in enumerate(tables):
            at = min(self._row, table.rowCount())
            table.insertRow(at)
            table.areas.insert(at, self._name)
            table.setVerticalHeaderLabels(table.areas)
            if i < len(self._per_sheet_data):
                row_data = self._per_sheet_data[i]
                for c in range(min(len(row_data), table.columnCount())):
                    table._set_cell(at, c, row_data[c])
            else:
                for c in range(table.columnCount()):
                    table._set_cell(at, c, 0)
        self._dp._update_global_tab()


class RenameAreaCommand(QUndoCommand):
    """Undo/redo renaming an area across all sheets"""

    def __init__(self, data_panel, row, old_name, new_name, text="Rename Area"):
        super().__init__(text)
        self._dp = data_panel
        self._row = row
        self._old = old_name
        self._new = new_name

    def redo(self):
        for table in self._dp._all_tables():
            if self._row < len(table.areas):
                table.areas[self._row] = self._new
                table.setVerticalHeaderLabels(table.areas)
        self._dp._update_global_tab()

    def undo(self):
        for table in self._dp._all_tables():
            if self._row < len(table.areas):
                table.areas[self._row] = self._old
                table.setVerticalHeaderLabels(table.areas)
        self._dp._update_global_tab()


class AddTaxonCommand(QUndoCommand):
    """Undo/redo adding a taxon column to a single table"""

    def __init__(self, table, at_col, name, text="Add Taxon"):
        super().__init__(text)
        self._table = table
        self._at_col = at_col
        self._name = name

    def redo(self):
        at = max(0, min(self._at_col, self._table.columnCount()))
        self._table.insertColumn(at)
        self._table.taxa.insert(at, self._name)
        self._table.setHorizontalHeaderLabels(self._table.taxa)
        for r in range(self._table.rowCount()):
            self._table._set_cell(r, at, 0)

    def undo(self):
        if self._at_col < self._table.columnCount():
            self._table.removeColumn(self._at_col)
            self._table.taxa.pop(self._at_col)


class DeleteTaxonCommand(QUndoCommand):
    """Undo/redo deleting a taxon column from a single table"""

    def __init__(self, table, col, taxon_name, col_data, text="Delete Taxon"):
        super().__init__(text)
        self._table = table
        self._col = col
        self._name = taxon_name
        # col_data: list of values for each row in this column
        self._col_data = col_data

    def redo(self):
        if self._col < self._table.columnCount():
            self._table.removeColumn(self._col)
            self._table.taxa.pop(self._col)

    def undo(self):
        at = min(self._col, self._table.columnCount())
        self._table.insertColumn(at)
        self._table.taxa.insert(at, self._name)
        self._table.setHorizontalHeaderLabels(self._table.taxa)
        for r in range(min(len(self._col_data), self._table.rowCount())):
            self._table._set_cell(r, at, self._col_data[r])


class RenameTaxonCommand(QUndoCommand):
    """Undo/redo renaming a taxon column"""

    def __init__(self, table, col, old_name, new_name, text="Rename Taxon"):
        super().__init__(text)
        self._table = table
        self._col = col
        self._old = old_name
        self._new = new_name

    def redo(self):
        if self._col < len(self._table.taxa):
            self._table.taxa[self._col] = self._new
            self._table.setHorizontalHeaderLabels(self._table.taxa)

    def undo(self):
        if self._col < len(self._table.taxa):
            self._table.taxa[self._col] = self._old
            self._table.setHorizontalHeaderLabels(self._table.taxa)


class ReorderRowCommand(QUndoCommand):
    """Undo/redo reordering rows across all sheets"""

    def __init__(self, data_panel, old_order, new_order, text="Reorder Rows"):
        super().__init__(text)
        self._dp = data_panel
        self._old_order = old_order
        self._new_order = new_order

    def redo(self):
        self._apply_order(self._new_order)

    def undo(self):
        self._apply_order(self._old_order)

    def _apply_order(self, order):
        for table in self._dp._all_tables():
            data = table.get_data()
            areas = [data["areas"][i] for i in order]
            matrix = [data["matrix"][i] for i in order]
            table.set_data(areas, data["taxa"], matrix)
        self._dp._update_global_tab()


class ReorderColumnCommand(QUndoCommand):
    """Undo/redo reordering columns in a single table"""

    def __init__(self, table, old_order, new_order, text="Reorder Columns"):
        super().__init__(text)
        self._table = table
        self._old_order = old_order
        self._new_order = new_order

    def redo(self):
        self._apply_order(self._new_order)

    def undo(self):
        self._apply_order(self._old_order)

    def _apply_order(self, order):
        data = self._table.get_data()
        taxa = [data["taxa"][i] for i in order]
        matrix = [[row[i] for i in order] for row in data["matrix"]]
        self._table.set_data(data["areas"], taxa, matrix)


class PasteTableCommand(QUndoCommand):
    """Undo/redo paste by snapshotting entire table state"""

    def __init__(self, table, before_data, after_data, text="Paste"):
        super().__init__(text)
        self._table = table
        self._before = before_data
        self._after = after_data

    def redo(self):
        self._table.set_data(self._after["areas"], self._after["taxa"], self._after["matrix"])

    def undo(self):
        self._table.set_data(self._before["areas"], self._before["taxa"], self._before["matrix"])


class PresenceAbsenceTable(QTableWidget):
    """Spreadsheet-like table for presence/absence data (0/1 matrix)"""

    PRESENT_COLOR = QColor(200, 235, 200)  # light green
    ABSENT_COLOR = QColor(255, 255, 255)  # white

    def __init__(self, parent=None):
        super().__init__(parent)
        self.areas = []  # row labels
        self.taxa = []  # column labels
        self._cell_values = {}  # track cell values for undo: (row, col) -> value
        self._undo_guard = False  # prevent recursive undo pushes
        self._setup_ui()

    def _setup_ui(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.cellDoubleClicked.connect(self._toggle_cell)
        self.cellChanged.connect(self._on_cell_changed)
        self.setSelectionMode(QTableWidget.ContiguousSelection)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.AnyKeyPressed)
        self.horizontalHeader().setDefaultSectionSize(60)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setShowGrid(True)
        self.setStyleSheet("""
            QTableWidget {
                font-size: 11px;
                gridline-color: #999;
            }
            QTableWidget::item {
                border: 1px solid #bbb;
                padding: 2px;
            }
        """)

        # Header double-click for renaming
        self.horizontalHeader().sectionDoubleClicked.connect(self._rename_taxon)
        self.verticalHeader().sectionDoubleClicked.connect(self._on_area_header_dblclick)

        # Header drag reordering
        self.verticalHeader().setSectionsMovable(True)
        self.verticalHeader().sectionMoved.connect(self._on_row_moved)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().sectionMoved.connect(self._on_column_moved)

    def _on_area_header_dblclick(self, row):
        """Route area rename through DataPanel for sync, or handle locally"""
        dp = self._find_data_panel()
        if dp:
            dp.sync_rename_area(row)
        else:
            self._rename_area(row)

    # ── data access ──

    def get_data(self):
        """Return current table data as dict"""
        matrix = []
        for r in range(self.rowCount()):
            row = []
            for c in range(self.columnCount()):
                item = self.item(r, c)
                row.append(int(item.text()) if item and item.text() == "1" else 0)
            matrix.append(row)
        return {"areas": list(self.areas), "taxa": list(self.taxa), "matrix": matrix}

    def set_data(self, areas, taxa, matrix):
        """Populate table from data"""
        self.areas = list(areas)
        self.taxa = list(taxa)
        self.setRowCount(len(self.areas))
        self.setColumnCount(len(self.taxa))
        self.setHorizontalHeaderLabels(self.taxa)
        self.setVerticalHeaderLabels(self.areas)
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                self._set_cell(r, c, 1 if val else 0)

    # ── cell helpers ──

    def _set_cell(self, row, col, value):
        self.blockSignals(True)
        v = 1 if value else 0
        item = QTableWidgetItem(str(v))
        item.setTextAlignment(Qt.AlignCenter)
        item.setBackground(QBrush(self.PRESENT_COLOR if v else self.ABSENT_COLOR))
        self.setItem(row, col, item)
        self._cell_values[(row, col)] = v
        self.blockSignals(False)

    def _toggle_cell(self, row, col):
        item = self.item(row, col)
        old_val = int(item.text()) if item and item.text() == "1" else 0
        new_val = 0 if old_val else 1
        stack = self._get_undo_stack()
        if stack:
            stack.push(CellChangeCommand(self, row, col, old_val, new_val))
        else:
            self._set_cell(row, col, new_val)

    def _on_cell_changed(self, row, col):
        """Validate edited cell: coerce to 0 or 1 and update color"""
        if self._undo_guard:
            return
        item = self.item(row, col)
        if item is None:
            return
        text = item.text().strip()
        new_val = 1 if text in ("1", "1.0") else 0
        old_val = self._cell_values.get((row, col), 0)
        if old_val == new_val:
            self._set_cell(row, col, new_val)
            return
        stack = self._get_undo_stack()
        if stack:
            self._undo_guard = True
            stack.push(CellChangeCommand(self, row, col, old_val, new_val))
            self._undo_guard = False
        else:
            self._set_cell(row, col, new_val)

    # ── context menu ──

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        idx = self.indexAt(pos)
        row, col = idx.row(), idx.column()

        # Row (Area) operations — delegate to DataPanel if available
        data_panel = self._find_data_panel()
        row_menu = menu.addMenu("Area (Row)")
        if data_panel:
            row_menu.addAction("Add Area Above", lambda: data_panel.sync_add_area(row))
            row_menu.addAction("Add Area Below", lambda: data_panel.sync_add_area(row + 1))
            if self.rowCount() > 0:
                row_menu.addAction("Rename Area", lambda: data_panel.sync_rename_area(row))
                row_menu.addAction("Delete Area", lambda: data_panel.sync_delete_area(row))
        else:
            row_menu.addAction("Add Area Above", lambda: self._add_area(row))
            row_menu.addAction("Add Area Below", lambda: self._add_area(row + 1))
            if self.rowCount() > 0:
                row_menu.addAction("Rename Area", lambda: self._rename_area(row))
                row_menu.addAction("Delete Area", lambda: self._delete_area(row))

        # Column (Taxon) operations
        col_menu = menu.addMenu("Taxon (Column)")
        col_menu.addAction("Add Taxon Left", lambda: self._add_taxon(col))
        col_menu.addAction("Add Taxon Right", lambda: self._add_taxon(col + 1))
        if self.columnCount() > 0:
            col_menu.addAction("Rename Taxon", lambda: self._rename_taxon(col))
            col_menu.addAction("Delete Taxon", lambda: self._delete_taxon(col))

        menu.addSeparator()
        menu.addAction("Fill Selected = 1", lambda: self._fill_selection(1))
        menu.addAction("Fill Selected = 0", lambda: self._fill_selection(0))

        menu.exec_(self.viewport().mapToGlobal(pos))

    def _find_data_panel(self):
        """Walk up the widget tree to find the DataPanel parent"""
        p = self.parent()
        while p is not None:
            if isinstance(p, DataPanel):
                return p
            p = p.parent()
        return None

    def _get_undo_stack(self):
        """Get the undo stack from DataPanel, or None"""
        dp = self._find_data_panel()
        return dp.undo_stack if dp else None

    def _fill_selection(self, value):
        items = self.selectedItems()
        if not items:
            return
        changes = []
        for item in items:
            r, c = item.row(), item.column()
            old_val = self._cell_values.get((r, c), 0)
            new_val = 1 if value else 0
            if old_val != new_val:
                changes.append((r, c, old_val, new_val))
        if not changes:
            return
        stack = self._get_undo_stack()
        if stack:
            stack.push(BulkCellChangeCommand(self, changes))
        else:
            for r, c, _old, new in changes:
                self._set_cell(r, c, new)

    # ── header drag handlers ──

    def _on_row_moved(self, logical, old_visual, new_visual):
        """Handle row header drag: revert visual move, push ReorderRowCommand"""
        header = self.verticalHeader()
        header.blockSignals(True)
        header.moveSection(new_visual, old_visual)
        header.blockSignals(False)

        n = self.rowCount()
        if n == 0:
            return
        old_order = list(range(n))
        new_order = list(range(n))
        item = new_order.pop(old_visual)
        new_order.insert(new_visual, item)

        dp = self._find_data_panel()
        stack = self._get_undo_stack()
        if stack and dp:
            stack.push(ReorderRowCommand(dp, old_order, new_order))

    def _on_column_moved(self, logical, old_visual, new_visual):
        """Handle column header drag: revert visual move, push ReorderColumnCommand"""
        header = self.horizontalHeader()
        header.blockSignals(True)
        header.moveSection(new_visual, old_visual)
        header.blockSignals(False)

        n = self.columnCount()
        if n == 0:
            return
        old_order = list(range(n))
        new_order = list(range(n))
        item = new_order.pop(old_visual)
        new_order.insert(new_visual, item)

        stack = self._get_undo_stack()
        if stack:
            stack.push(ReorderColumnCommand(self, old_order, new_order))

    # ── row (area) management ──

    def _add_area(self, at_row):
        name, ok = QInputDialog.getText(self, "Add Area", "Area name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        at_row = max(0, min(at_row, self.rowCount()))
        self.insertRow(at_row)
        self.areas.insert(at_row, name)
        self.setVerticalHeaderLabels(self.areas)
        for c in range(self.columnCount()):
            self._set_cell(at_row, c, 0)

    def _rename_area(self, row):
        if row < 0 or row >= self.rowCount():
            return
        name, ok = QInputDialog.getText(self, "Rename Area", "New name:", text=self.areas[row])
        if ok and name.strip():
            self.areas[row] = name.strip()
            self.setVerticalHeaderLabels(self.areas)

    def _delete_area(self, row):
        if row < 0 or row >= self.rowCount():
            return
        reply = QMessageBox.question(
            self,
            "Delete Area",
            f"Delete area '{self.areas[row]}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.removeRow(row)
            self.areas.pop(row)

    # ── column (taxon) management ──

    def _add_taxon(self, at_col):
        name, ok = QInputDialog.getText(self, "Add Taxon", "Taxon name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        at_col = max(0, min(at_col, self.columnCount()))
        stack = self._get_undo_stack()
        if stack:
            stack.push(AddTaxonCommand(self, at_col, name))
        else:
            self.insertColumn(at_col)
            self.taxa.insert(at_col, name)
            self.setHorizontalHeaderLabels(self.taxa)
            for r in range(self.rowCount()):
                self._set_cell(r, at_col, 0)

    def _rename_taxon(self, col):
        if col < 0 or col >= self.columnCount():
            return
        old_name = self.taxa[col]
        name, ok = QInputDialog.getText(self, "Rename Taxon", "New name:", text=old_name)
        if ok and name.strip():
            new_name = name.strip()
            stack = self._get_undo_stack()
            if stack:
                stack.push(RenameTaxonCommand(self, col, old_name, new_name))
            else:
                self.taxa[col] = new_name
                self.setHorizontalHeaderLabels(self.taxa)

    def _delete_taxon(self, col):
        if col < 0 or col >= self.columnCount():
            return
        reply = QMessageBox.question(
            self,
            "Delete Taxon",
            f"Delete taxon '{self.taxa[col]}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            taxon_name = self.taxa[col]
            col_data = []
            for r in range(self.rowCount()):
                item = self.item(r, col)
                col_data.append(int(item.text()) if item and item.text() == "1" else 0)
            stack = self._get_undo_stack()
            if stack:
                stack.push(DeleteTaxonCommand(self, col, taxon_name, col_data))
            else:
                self.removeColumn(col)
                self.taxa.pop(col)

    # ── clipboard (copy/paste) ──

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self._copy_selection()
        elif event.matches(QKeySequence.Paste):
            if self.editTriggers() != QTableWidget.NoEditTriggers:
                self._paste_selection()
        elif event.matches(QKeySequence.Undo):
            stack = self._get_undo_stack()
            if stack:
                stack.undo()
        elif event.matches(QKeySequence.Redo):
            stack = self._get_undo_stack()
            if stack:
                stack.redo()
        else:
            super().keyPressEvent(event)

    def _copy_selection(self):
        selection = self.selectedRanges()
        if not selection:
            return
        sel = selection[0]
        top, left = sel.topRow(), sel.leftColumn()
        bottom, right = sel.bottomRow(), sel.rightColumn()

        # If entire table selected (or starting from 0,0), include headers
        include_headers = top == 0 and left == 0

        rows = []
        if include_headers:
            # First row: empty corner + taxa headers
            header_row = [""] + [self.taxa[c] if c < len(self.taxa) else "" for c in range(left, right + 1)]
            rows.append("\t".join(header_row))

        for r in range(top, bottom + 1):
            cols = []
            if include_headers:
                # Prepend area name
                cols.append(self.areas[r] if r < len(self.areas) else "")
            for c in range(left, right + 1):
                item = self.item(r, c)
                cols.append(item.text() if item else "0")
            rows.append("\t".join(cols))
        QApplication.clipboard().setText("\n".join(rows))

    def _paste_selection(self):
        text = QApplication.clipboard().text()
        if not text:
            return

        before_data = self.get_data()

        cur_row = self.currentRow()
        cur_col = self.currentColumn()
        if cur_row < 0:
            cur_row = 0
        if cur_col < 0:
            cur_col = 0

        # Normalize line endings (Windows \r\n → \n)
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        rows = [r for r in text.split("\n") if r.strip()]
        parsed = [row.split("\t") for row in rows]

        # Paste at (0,0): treat as full table with headers
        # Two possible formats from Excel:
        #   With corner:    corner\ttaxa1\ttaxa2\t...   (header has N+1 cols, data has N+1 cols)
        #   Without corner: taxa1\ttaxa2\t...           (header has N cols, data has N+1 cols)
        if cur_row == 0 and cur_col == 0 and len(parsed) >= 2 and len(parsed[0]) >= 1:
            n_header_cols = len(parsed[0])
            n_data_cols = len(parsed[1])

            if n_data_cols > n_header_cols:
                # No corner cell: entire first row is taxa
                new_taxa = [c.strip() for c in parsed[0]]
            else:
                # Has corner cell: skip [0], taxa start at [1]
                new_taxa = [c.strip() for c in parsed[0][1:]]

            # Remaining rows: [area_name, val1, val2, ...]
            new_areas = []
            matrix = []
            for data_row in parsed[1:]:
                cells = [c.strip() for c in data_row]
                if not cells or not cells[0]:
                    continue
                new_areas.append(cells[0])
                vals = [1 if v in ("1", "1.0") else 0 for v in cells[1:]]
                while len(vals) < len(new_taxa):
                    vals.append(0)
                matrix.append(vals[: len(new_taxa)])

            if new_taxa and new_areas:
                self.set_data(new_areas, new_taxa, matrix)
                after_data = self.get_data()
                stack = self._get_undo_stack()
                if stack:
                    stack.push(PasteTableCommand(self, before_data, after_data))
                return

        # Normal paste: fill values starting from current cell, expand if needed
        for dr, data_row in enumerate(parsed):
            for dc, val in enumerate(data_row):
                r, c = cur_row + dr, cur_col + dc
                # Expand rows if needed
                while r >= self.rowCount():
                    new_r = self.rowCount()
                    self.insertRow(new_r)
                    self.areas.append(f"Area_{new_r + 1}")
                    self.setVerticalHeaderLabels(self.areas)
                    for cc in range(self.columnCount()):
                        self._set_cell(new_r, cc, 0)
                # Expand columns if needed
                while c >= self.columnCount():
                    new_c = self.columnCount()
                    self.insertColumn(new_c)
                    self.taxa.append(f"Taxon_{new_c + 1}")
                    self.setHorizontalHeaderLabels(self.taxa)
                    for rr in range(self.rowCount()):
                        self._set_cell(rr, new_c, 0)
                self._set_cell(r, c, 1 if val.strip() in ("1", "1.0") else 0)

        after_data = self.get_data()
        stack = self._get_undo_stack()
        if stack:
            stack.push(PasteTableCommand(self, before_data, after_data))


class DataPanel(QWidget):
    """Leftmost panel: Raw presence/absence data with multi-sheet (period) tabs"""

    GLOBAL_TAB_NAME = "Global"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = None
        self._global_container = None  # container widget for the Global tab
        self.undo_stack = QUndoStack(self)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # ── Header ──
        header = QHBoxLayout()
        header_label = QLabel("<b>Raw Data</b>")
        header.addWidget(header_label)
        header.addStretch()

        btn_style = """
            QPushButton {
                background-color: %s; color: white;
                padding: 5px 10px; border-radius: 3px; font-size: 10px;
            }
            QPushButton:hover { background-color: %s; }
        """

        self.new_btn = QPushButton("New")
        self.new_btn.setStyleSheet(btn_style % ("#607D8B", "#455A64"))
        self.new_btn.clicked.connect(self.new_project)
        header.addWidget(self.new_btn)

        self.load_btn = QPushButton("Open")
        self.load_btn.setStyleSheet(btn_style % ("#2196F3", "#1976D2"))
        self.load_btn.clicked.connect(self.load_file)
        header.addWidget(self.load_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setStyleSheet(btn_style % ("#4CAF50", "#388E3C"))
        self.save_btn.clicked.connect(self.save_file)
        header.addWidget(self.save_btn)

        layout.addLayout(header)

        # ── Tab widget for sheets ──
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.South)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab {
                padding: 4px 12px; font-size: 10px;
                border: 1px solid #ccc; border-bottom: none;
                margin-right: 2px; border-radius: 3px 3px 0 0;
            }
            QTabBar::tab:selected {
                background: #e3f2fd; font-weight: bold;
            }
        """)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget, stretch=1)

        # ── Sheet management buttons ──
        sheet_btns = QHBoxLayout()
        sheet_btns.setSpacing(4)

        self.add_sheet_btn = QPushButton("+ Add Sheet")
        self.add_sheet_btn.setStyleSheet(btn_style % ("#FF9800", "#F57C00"))
        self.add_sheet_btn.clicked.connect(self.add_sheet)
        sheet_btns.addWidget(self.add_sheet_btn)

        self.rename_sheet_btn = QPushButton("Rename")
        self.rename_sheet_btn.setStyleSheet(btn_style % ("#9C27B0", "#7B1FA2"))
        self.rename_sheet_btn.clicked.connect(self.rename_current_sheet)
        sheet_btns.addWidget(self.rename_sheet_btn)

        self.delete_sheet_btn = QPushButton("Delete")
        self.delete_sheet_btn.setStyleSheet(btn_style % ("#f44336", "#d32f2f"))
        self.delete_sheet_btn.clicked.connect(self.delete_current_sheet)
        sheet_btns.addWidget(self.delete_sheet_btn)

        sheet_btns.addStretch()
        layout.addLayout(sheet_btns)

        # ── Import CSV button ──
        import_layout = QHBoxLayout()
        self.import_csv_btn = QPushButton("Import CSV")
        self.import_csv_btn.setStyleSheet(btn_style % ("#795548", "#5D4037"))
        self.import_csv_btn.clicked.connect(self.import_csv)
        import_layout.addWidget(self.import_csv_btn)
        import_layout.addStretch()
        layout.addLayout(import_layout)

        # ── Similarity method selector ──
        sim_method_layout = QHBoxLayout()
        sim_method_label = QLabel("Similarity:")
        sim_method_layout.addWidget(sim_method_label)
        self.similarity_combo = QComboBox()
        from acc_utils import SIMILARITY_METHODS

        for key, label in SIMILARITY_METHODS.items():
            self.similarity_combo.addItem(label, key)
        self.similarity_combo.currentIndexChanged.connect(self._on_similarity_method_changed)
        sim_method_layout.addWidget(self.similarity_combo)

        # Raup-Crick iterations input
        self.rc_iterations_label = QLabel("Iterations:")
        self.rc_iterations_input = QLineEdit("10000")
        self.rc_iterations_input.setFixedWidth(80)
        self.rc_iterations_input.setToolTip("Number of Monte Carlo iterations for Raup-Crick (default: 10000)")
        sim_method_layout.addWidget(self.rc_iterations_label)
        sim_method_layout.addWidget(self.rc_iterations_input)

        sim_method_layout.addStretch()
        layout.addLayout(sim_method_layout)

        # Initially hide Raup-Crick iterations input
        self._on_similarity_method_changed()

        # ── Calculate Similarity button ──
        self.calc_btn = QPushButton("Calculate Similarity →")
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #E65100; color: white;
                padding: 8px 16px; border-radius: 4px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #BF360C; }
        """)
        self.calc_btn.clicked.connect(self.calculate_similarity)
        layout.addWidget(self.calc_btn)

        self.setLayout(layout)

    # ── Sheet management ──

    def _current_table(self):
        """Get current PresenceAbsenceTable or None"""
        w = self.tab_widget.currentWidget()
        if w is None:
            return None
        if isinstance(w, PresenceAbsenceTable):
            return w
        # Container wrapping a table
        return getattr(w, "_table", None)

    def _get_existing_areas(self):
        """Get area list from the first existing tab, or empty list"""
        for i in range(self.tab_widget.count()):
            t = self._get_table_at(i)
            if t is not None and t.areas:
                return list(t.areas)
        return []

    def add_sheet(self, name=None):
        """Add a new empty sheet"""
        if name is None or isinstance(name, bool):
            # Generate default name (count only data tabs, not Global)
            n_data = len(self._all_tables())
            idx = n_data + 1
            existing = {self.tab_widget.tabText(i) for i in range(self.tab_widget.count())}
            while f"new_{idx}" in existing:
                idx += 1
            name = f"new_{idx}"
        # Wrap table in a container with toolbar
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        # Toolbar for row/column operations
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        tb_style = """QPushButton {
            background-color: %s; color: white;
            padding: 3px 8px; border-radius: 2px; font-size: 10px;
        } QPushButton:hover { background-color: %s; }"""

        add_area_btn = QPushButton("+ Area")
        add_area_btn.setStyleSheet(tb_style % ("#43A047", "#2E7D32"))
        toolbar.addWidget(add_area_btn)

        add_taxon_btn = QPushButton("+ Taxon")
        add_taxon_btn.setStyleSheet(tb_style % ("#1E88E5", "#1565C0"))
        toolbar.addWidget(add_taxon_btn)

        toolbar.addStretch()

        info_label = QLabel("")
        info_label.setStyleSheet("font-size: 9px; color: #888;")
        toolbar.addWidget(info_label)

        container_layout.addLayout(toolbar)

        table = PresenceAbsenceTable(self)
        container_layout.addWidget(table, stretch=1)
        container.setLayout(container_layout)

        # Connect toolbar buttons
        add_area_btn.clicked.connect(lambda: self.sync_add_area(table.rowCount()))
        add_taxon_btn.clicked.connect(lambda: table._add_taxon(table.columnCount()))

        # Store table reference on the container
        container._table = table
        container._info_label = info_label

        # Update info on changes
        def update_info():
            info_label.setText(f"{table.rowCount()} areas x {table.columnCount()} taxa")

        table.model().rowsInserted.connect(update_info)
        table.model().rowsRemoved.connect(update_info)
        table.model().columnsInserted.connect(update_info)
        table.model().columnsRemoved.connect(update_info)

        self.tab_widget.addTab(container, name)
        self.tab_widget.setCurrentWidget(container)

        # Initialize: inherit areas from existing tabs, or use defaults
        if table.rowCount() == 0 and table.columnCount() == 0:
            existing = self._get_existing_areas()
            if existing:
                # Inherit area list from other tabs, start with empty taxa
                default_taxa = ["Taxon_1", "Taxon_2", "Taxon_3"]
                default_matrix = [[0] * len(default_taxa) for _ in range(len(existing))]
                table.set_data(existing, default_taxa, default_matrix)
            else:
                default_areas = ["Area_1", "Area_2", "Area_3"]
                default_taxa = ["Taxon_1", "Taxon_2", "Taxon_3"]
                default_matrix = [[0] * 3 for _ in range(3)]
                table.set_data(default_areas, default_taxa, default_matrix)
            update_info()

        self._update_global_tab()
        return table

    def rename_current_sheet(self):
        idx = self.tab_widget.currentIndex()
        if idx < 0:
            return
        if self._is_global_tab(idx):
            QMessageBox.information(self, "Info", "The Global tab cannot be renamed.")
            return
        old_name = self.tab_widget.tabText(idx)
        name, ok = QInputDialog.getText(self, "Rename Sheet", "New name:", text=old_name)
        if ok and name.strip():
            self.tab_widget.setTabText(idx, name.strip())

    def delete_current_sheet(self):
        idx = self.tab_widget.currentIndex()
        if idx < 0:
            return
        if self._is_global_tab(idx):
            QMessageBox.information(self, "Info", "The Global tab cannot be deleted.")
            return
        name = self.tab_widget.tabText(idx)
        reply = QMessageBox.question(
            self,
            "Delete Sheet",
            f"Delete sheet '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.tab_widget.removeTab(idx)
            self.undo_stack.clear()
            self._update_global_tab()

    # ── Area synchronization across all tabs ──

    def _is_global_tab(self, index):
        """Check if the tab at index is the Global (union) tab"""
        w = self.tab_widget.widget(index)
        return w is self._global_container

    def _on_tab_changed(self, index):
        """When Global tab is clicked, refresh its data"""
        if index >= 0 and self._is_global_tab(index):
            self._update_global_tab()

    def _all_tables(self, include_global=False):
        """Return list of all PresenceAbsenceTable widgets (excluding Global tab by default)"""
        tables = []
        for i in range(self.tab_widget.count()):
            if not include_global and self._is_global_tab(i):
                continue
            t = self._get_table_at(i)
            if t is not None:
                tables.append(t)
        return tables

    def _update_global_tab(self):
        """Create or update the Global (union) read-only tab"""
        from acc_utils import union_presence_matrix

        data_tables = self._all_tables(include_global=False)
        if not data_tables:
            # Remove global tab if no data sheets
            if self._global_container is not None:
                idx = self.tab_widget.indexOf(self._global_container)
                if idx >= 0:
                    self.tab_widget.removeTab(idx)
                self._global_container = None
            return

        # Collect sheet data
        all_sheets = [t.get_data() for t in data_tables]
        areas, union_taxa, union_matrix = union_presence_matrix(all_sheets)

        if not areas or not union_taxa:
            return

        # Create or reuse global container
        if self._global_container is None:
            container = QWidget()
            container_layout = QVBoxLayout()
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            info_label = QLabel("")
            info_label.setStyleSheet("font-size: 9px; color: #666; font-style: italic;")
            container_layout.addWidget(info_label)

            table = PresenceAbsenceTable(self)
            # Make read-only: disable editing and context menu
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setContextMenuPolicy(Qt.NoContextMenu)
            # Disable header drag for Global tab
            table.verticalHeader().setSectionsMovable(False)
            table.horizontalHeader().setSectionsMovable(False)
            # Disconnect toggle on double-click
            try:
                table.cellDoubleClicked.disconnect(table._toggle_cell)
            except TypeError:
                pass
            table.setStyleSheet("""
                QTableWidget {
                    font-size: 11px;
                    gridline-color: #999;
                    background-color: #f5f5f5;
                }
                QTableWidget::item {
                    border: 1px solid #bbb;
                    padding: 2px;
                }
            """)
            container_layout.addWidget(table, stretch=1)
            container.setLayout(container_layout)
            container._table = table
            container._info_label = info_label
            self._global_container = container

        # Update table data
        global_table = self._global_container._table
        global_table.set_data(areas, union_taxa, union_matrix)
        self._global_container._info_label.setText(
            f"Read-only union of {len(data_tables)} sheet(s): {len(areas)} areas x {len(union_taxa)} taxa"
        )

        # Add Global tab if not yet present; keep it at the end
        idx = self.tab_widget.indexOf(self._global_container)
        last = self.tab_widget.count() - 1
        if idx < 0:
            # Not in tab widget yet — add at end
            self.tab_widget.blockSignals(True)
            self.tab_widget.addTab(self._global_container, self.GLOBAL_TAB_NAME)
            self.tab_widget.blockSignals(False)
        elif idx != last:
            # Exists but not last — move to end
            self.tab_widget.blockSignals(True)
            self.tab_widget.removeTab(idx)
            self.tab_widget.addTab(self._global_container, self.GLOBAL_TAB_NAME)
            self.tab_widget.blockSignals(False)

        # Style the Global tab differently
        global_idx = self.tab_widget.indexOf(self._global_container)
        self.tab_widget.tabBar().setTabTextColor(global_idx, QColor("#1565C0"))

    def sync_add_area(self, at_row):
        """Add an area to ALL tabs at the same row position"""
        name, ok = QInputDialog.getText(self, "Add Area", "Area name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.undo_stack.push(AddAreaCommand(self, at_row, name))

    def sync_rename_area(self, row):
        """Rename an area across ALL tabs"""
        tables = self._all_tables()
        if not tables or row < 0 or row >= tables[0].rowCount():
            return
        old_name = tables[0].areas[row]
        name, ok = QInputDialog.getText(self, "Rename Area", "New name:", text=old_name)
        if ok and name.strip():
            new_name = name.strip()
            self.undo_stack.push(RenameAreaCommand(self, row, old_name, new_name))

    def sync_delete_area(self, row):
        """Delete an area from ALL tabs"""
        tables = self._all_tables()
        if not tables or row < 0 or row >= tables[0].rowCount():
            return
        area_name = tables[0].areas[row]
        reply = QMessageBox.question(
            self,
            "Delete Area",
            f"Delete area '{area_name}' from all sheets?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Snapshot per-sheet row data for undo
            per_sheet_data = []
            for table in tables:
                row_data = []
                if row < table.rowCount():
                    for c in range(table.columnCount()):
                        item = table.item(row, c)
                        row_data.append(int(item.text()) if item and item.text() == "1" else 0)
                per_sheet_data.append(row_data)
            self.undo_stack.push(DeleteAreaCommand(self, row, area_name, per_sheet_data))

    # ── Similarity calculation ──

    def _on_similarity_method_changed(self):
        """Show/hide Raup-Crick iterations input based on selected method"""
        method = self.similarity_combo.currentData()
        is_raup_crick = (method == "raup_crick")
        self.rc_iterations_label.setVisible(is_raup_crick)
        self.rc_iterations_input.setVisible(is_raup_crick)

    def calculate_similarity(self):
        """Calculate local and global similarity and send to LeftPanel"""
        from acc_utils import similarity_from_presence, union_presence_matrix, validate_similarity_matrix

        tables = self._all_tables()
        if not tables:
            QMessageBox.warning(self, "No Data", "No sheets available.")
            return

        # Check if Global tab is selected — use first data tab instead
        cur_idx = self.tab_widget.currentIndex()
        if cur_idx >= 0 and self._is_global_tab(cur_idx):
            QMessageBox.warning(
                self, "Select a Sheet", "Please select a data sheet (not Global) for local similarity calculation."
            )
            return

        # Get current tab data for local similarity
        current_table = self._current_table()
        if current_table is None:
            QMessageBox.warning(self, "No Data", "No active sheet selected.")
            return

        current_data = current_table.get_data()
        if len(current_data["areas"]) < 2:
            QMessageBox.warning(self, "Insufficient Data", "Need at least 2 areas.")
            return

        # Warning: empty areas (all taxa = 0)
        empty_areas = []
        for i, row in enumerate(current_data["matrix"]):
            if all(v == 0 for v in row):
                empty_areas.append(current_data["areas"][i])
        if empty_areas:
            reply = QMessageBox.warning(
                self,
                "Empty Areas",
                f"The following areas have no taxa present:\n"
                f"{', '.join(empty_areas)}\n\n"
                f"This may result in 0.0 similarity values.\n"
                f"Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Warning: empty sheets (no data)
        empty_sheets = []
        for i in range(self.tab_widget.count()):
            if self._is_global_tab(i):
                continue
            t = self._get_table_at(i)
            if t is not None and (t.rowCount() == 0 or t.columnCount() == 0):
                empty_sheets.append(self.tab_widget.tabText(i))
        if empty_sheets:
            QMessageBox.information(
                self,
                "Empty Sheets",
                f"The following sheets have no data and will be skipped:\n{', '.join(empty_sheets)}",
            )

        # Update Global tab first
        self._update_global_tab()

        # Selected similarity method
        method = self.similarity_combo.currentData()

        # Get Raup-Crick iterations if applicable
        raup_crick_iterations = 10000  # default
        if method == "raup_crick":
            try:
                raup_crick_iterations = int(self.rc_iterations_input.text())
                if raup_crick_iterations < 1:
                    raise ValueError("Iterations must be positive")
            except ValueError:
                QMessageBox.warning(
                    self, "Invalid Input", "Raup-Crick iterations must be a positive integer. Using default (10000)."
                )
                raup_crick_iterations = 10000

        # Local similarity: current tab
        local_df = similarity_from_presence(
            current_data["areas"],
            current_data["taxa"],
            current_data["matrix"],
            method=method,
            raup_crick_iterations=raup_crick_iterations,
        )

        # Global similarity: union of all tabs
        all_sheets = [t.get_data() for t in tables]
        areas, union_taxa, union_matrix = union_presence_matrix(all_sheets)
        global_df = similarity_from_presence(
            areas, union_taxa, union_matrix, method=method, raup_crick_iterations=raup_crick_iterations
        )

        # Validate results
        valid_local, msg_local = validate_similarity_matrix(local_df.values)
        if not valid_local:
            QMessageBox.warning(self, "Local Matrix Warning", f"Local similarity matrix issue:\n{msg_local}")

        valid_global, msg_global = validate_similarity_matrix(global_df.values)
        if not valid_global:
            QMessageBox.warning(self, "Global Matrix Warning", f"Global similarity matrix issue:\n{msg_global}")

        # Send to LeftPanel via MainWindow
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.left_panel.local_matrix_widget.update_matrix(local_df)
            main_window.left_panel.global_matrix_widget.update_matrix(global_df)
            main_window.update_dendrogram("both")

    # ── Project data serialization ──

    def _get_table_at(self, index):
        """Get PresenceAbsenceTable from tab index (handles container wrapping)"""
        w = self.tab_widget.widget(index)
        if isinstance(w, PresenceAbsenceTable):
            return w
        return getattr(w, "_table", None)

    def get_all_data(self):
        """Collect all sheets into a serializable dict (excludes Global tab)"""
        sheets = []
        for i in range(self.tab_widget.count()):
            if self._is_global_tab(i):
                continue
            table = self._get_table_at(i)
            if table is not None:
                d = table.get_data()
                d["name"] = self.tab_widget.tabText(i)
                sheets.append(d)
        return {"version": "1.0", "sheets": sheets}

    def set_all_data(self, data):
        """Load project data from dict"""
        # Clear existing tabs (including Global)
        self._global_container = None
        self.undo_stack.clear()
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        for sheet in data.get("sheets", []):
            table = self.add_sheet(name=sheet.get("name", "Untitled"))
            table.set_data(
                sheet.get("areas", []),
                sheet.get("taxa", []),
                sheet.get("matrix", []),
            )
        self._update_global_tab()

    # ── File operations ──

    def new_project(self):
        """Create a new empty project"""
        if self.tab_widget.count() > 0:
            reply = QMessageBox.question(
                self,
                "New Project",
                "Discard current data and start new?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        self._current_file = None
        self.undo_stack.clear()
        self.add_sheet(name="Sheet1")

    def save_file(self):
        """Save project to .accdata JSON file"""
        if self.tab_widget.count() == 0:
            QMessageBox.warning(self, "No Data", "No sheets to save.")
            return
        path = self._current_file
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Raw Data", "", "ACC Data Files (*.accdata);;All Files (*)"
            )
        if not path:
            return
        try:
            data = self.get_all_data()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._current_file = path
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def save_file_as(self):
        """Save project to a new file"""
        old = self._current_file
        self._current_file = None
        self.save_file()
        if not self._current_file:
            self._current_file = old

    def load_file(self):
        """Load project from .accdata JSON file"""
        path, _ = QFileDialog.getOpenFileName(self, "Open Raw Data", "", "ACC Data Files (*.accdata);;All Files (*)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.set_all_data(data)
            self._current_file = path
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def import_csv(self):
        """Import a CSV file as a single sheet"""
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            df = pd.read_csv(path, index_col=0)
            areas = [str(a) for a in df.index.tolist()]
            taxa = [str(t) for t in df.columns.tolist()]
            matrix = []
            for _, row in df.iterrows():
                matrix.append([1 if v else 0 for v in row.values])
            name = Path(path).stem
            table = self.add_sheet(name=name)
            table.set_data(areas, taxa, matrix)
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))


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
        # Local matrix section
        sub_header_layout = QHBoxLayout()
        sub_label = QLabel("<b>Local</b>")
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
        # Always enabled - can create area list from scratch
        sub_header_layout.addWidget(self.edit_areas_btn)

        self.local_matrix_widget = StepMatrixWidget("Local", show_header=False)
        sub_header_layout.addWidget(self.local_matrix_widget.load_btn)
        self.content_layout.addLayout(sub_header_layout)

        self.content_layout.addWidget(self.local_matrix_widget, stretch=1)

        # Separator line
        separator = QLabel()
        separator.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setMaximumHeight(2)
        self.content_layout.addWidget(separator)

        # Global matrix section
        inc_header_layout = QHBoxLayout()
        inc_label = QLabel("<b>Global</b>")
        inc_header_layout.addWidget(inc_label)
        inc_header_layout.addStretch()

        self.global_matrix_widget = StepMatrixWidget("Global", show_header=False)
        inc_header_layout.addWidget(self.global_matrix_widget.load_btn)
        self.content_layout.addLayout(inc_header_layout)

        self.content_layout.addWidget(self.global_matrix_widget, stretch=1)

    def on_matrix_loaded(self, matrix_type):
        """
        Called when a matrix is loaded

        Args:
            matrix_type: 'Local' or 'Global'
        """
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            # Update only the dendrogram for the loaded matrix
            if matrix_type == "Local":
                main_window.update_dendrogram("local")
            elif matrix_type == "Global":
                main_window.update_dendrogram("global")

    def on_matrix_modified(self, matrix_type):
        """
        Called when a matrix value is modified

        Args:
            matrix_type: 'Local' or 'Global'
        """
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            # Clear the dendrogram
            if matrix_type == "Local":
                main_window.clear_dendrogram("local")
            elif matrix_type == "Global":
                main_window.clear_dendrogram("global")

    def on_step_changed(self):
        """Called when step changes"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.update_dendrogram_steps()

    def edit_area_list(self):
        """Open dialog to edit area list"""
        try:
            # Check if matrices are loaded
            sub_loaded = self.local_matrix_widget.is_loaded()
            inc_loaded = self.global_matrix_widget.is_loaded()

            if sub_loaded and inc_loaded:
                # Both loaded - edit existing

                # Get current labels (should be same for both)
                local_labels = self.local_matrix_widget.get_labels()
                global_labels = self.global_matrix_widget.get_labels()

                # Verify they match
                if local_labels != global_labels:
                    QMessageBox.warning(
                        self,
                        "Label Mismatch",
                        "Local and Global matrices have different labels.\n"
                        "Please reload the matrices to ensure consistency.",
                    )
                    return

                # Get current matrices
                local_df = self.local_matrix_widget.get_dataframe()
                global_df = self.global_matrix_widget.get_dataframe()

            elif sub_loaded or inc_loaded:
                # Only one loaded - warn user
                QMessageBox.warning(
                    self,
                    "Incomplete Data",
                    "Only one matrix is loaded. Please load both matrices or start from scratch.\n\n"
                    "To start from scratch, close both matrices and use Edit Area List.",
                )
                return

            else:
                # Neither loaded - start from scratch
                local_labels = []
                local_df = pd.DataFrame()
                global_df = pd.DataFrame()

            # Open dialog
            dialog = AreaListEditorDialog(local_labels, local_df, global_df, self)

            result_code = dialog.exec_()

            if result_code == QDialog.Accepted:
                result = dialog.get_result()

                if result["modified"] or len(result["labels"]) > 0:
                    # Update both matrices
                    self.local_matrix_widget.update_matrix(result["local_matrix"])
                    self.global_matrix_widget.update_matrix(result["global_matrix"])

                    # Notify main window to update dendrograms
                    main_window = self.window()
                    if isinstance(main_window, MainWindow):
                        main_window.update_dendrograms()

                    QMessageBox.information(
                        self,
                        "Success",
                        f"Area list {'created' if not sub_loaded and not inc_loaded else 'updated'} successfully!\n\n"
                        f"Total areas: {len(result['labels'])}\n"
                        f"Matrix size: {result['local_matrix'].shape[0]}×{result['local_matrix'].shape[1]}",
                    )
        except Exception as e:
            print(f"Error in edit_area_list: {e}")  # Debug
            import traceback

            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred while opening the Area List Editor:\n{str(e)}")


class CenterPanel(ColumnPanel):
    """Center panel: Dendrograms with step visualization"""

    def __init__(self, parent=None):
        super().__init__("Cluster Dendrograms", parent)
        self.setup_content()

    def setup_content(self):
        # Local dendrogram
        self.local_dendro_widget = StepDendrogramWidget("Local")
        self.content_layout.addWidget(self.local_dendro_widget, stretch=1)

        # Separator line
        separator = QLabel()
        separator.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setMaximumHeight(2)
        self.content_layout.addWidget(separator)

        # Global dendrogram
        self.global_dendro_widget = StepDendrogramWidget("Global")
        self.content_layout.addWidget(self.global_dendro_widget, stretch=1)


class NMDSVisualizationWidget(QWidget):
    """Widget for displaying NMDS 2D scatter plot"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure
        self.figure = Figure(figsize=(6, 6))
        self.canvas = FigureCanvas(self.figure)

        # Enable right-click context menu for saving
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.canvas, stretch=1)

        # Info label
        self.info_label = QLabel("Select matrix type and click Run NMDS")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def show_context_menu(self, pos):
        """Show context menu for saving image"""
        menu = QMenu(self)
        save_action = QAction("Save Image As...", self)
        save_action.triggered.connect(self.save_image)
        menu.addAction(save_action)
        menu.exec_(self.canvas.mapToGlobal(pos))

    def save_image(self):
        """Save the current figure to an image file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save NMDS Visualization",
            "NMDS_visualization.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg);;All Files (*)",
        )
        if file_path:
            try:
                self.figure.savefig(file_path, dpi=300, bbox_inches="tight")
                QMessageBox.information(self, "Success", f"Image saved successfully to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{str(e)}")

    def run_nmds(self, similarity_dict, n_components=2):
        """Run NMDS on similarity dict and plot results (2D or 3D)"""
        from sklearn.manifold import MDS

        from acc_utils import similarity_to_distance

        # Convert similarity to distance
        distance_matrix, labels = similarity_to_distance(similarity_dict)

        # Run NMDS (non-metric MDS)
        mds = MDS(n_components=n_components, metric_mds=False, metric="precomputed",
                   init="random", random_state=42, n_init=4, max_iter=300,
                   normalized_stress="auto")
        coords = mds.fit_transform(distance_matrix)
        stress = mds.stress_

        # Plot
        self.figure.clear()

        if n_components == 3:
            ax = self.figure.add_subplot(111, projection="3d")

            ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2],
                       s=80, c="#1976D2", edgecolors="white", linewidths=0.5)

            for i, label in enumerate(labels):
                ax.text(coords[i, 0], coords[i, 1], coords[i, 2],
                        f"  {label}", fontsize=9, color="#333333")

            ax.set_title(f"NMDS 3D (Stress = {stress:.4f})", fontsize=12, fontweight="bold")
            ax.set_xlabel("NMDS 1", fontsize=9)
            ax.set_ylabel("NMDS 2", fontsize=9)
            ax.set_zlabel("NMDS 3", fontsize=9)
        else:
            ax = self.figure.add_subplot(111)

            ax.scatter(coords[:, 0], coords[:, 1], s=80, c="#1976D2", edgecolors="white",
                       linewidths=0.5, zorder=5)

            for i, label in enumerate(labels):
                ax.annotate(label, (coords[i, 0], coords[i, 1]),
                            textcoords="offset points", xytext=(6, 6),
                            fontsize=9, color="#333333")

            ax.set_title(f"NMDS (Stress = {stress:.4f})", fontsize=12, fontweight="bold")
            ax.set_xlabel("NMDS 1", fontsize=10)
            ax.set_ylabel("NMDS 2", fontsize=10)
            ax.axhline(y=0, color="#cccccc", linewidth=0.5, zorder=0)
            ax.axvline(x=0, color="#cccccc", linewidth=0.5, zorder=0)
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

        dim_label = "3D" if n_components == 3 else "2D"
        self.info_label.setText(f"{dim_label} | Stress: {stress:.4f} | {len(labels)} areas")

        return stress

    def clear_display(self):
        """Clear the display"""
        self.figure.clear()
        self.canvas.draw()
        self.info_label.setText("Select matrix type and click Run NMDS")


class NMDSPanel(ColumnPanel):
    """NMDS panel: Non-metric Multidimensional Scaling visualization"""

    def __init__(self, parent=None):
        super().__init__("NMDS", parent)
        self.setup_content()

    def setup_content(self):
        # Controls layout
        controls_layout = QHBoxLayout()

        # Matrix type selector
        controls_layout.addWidget(QLabel("Matrix:"))
        self.matrix_combo = QComboBox()
        self.matrix_combo.addItems(["Local", "Global"])
        self.matrix_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        controls_layout.addWidget(self.matrix_combo)

        # Dimension selector
        controls_layout.addWidget(QLabel("Dim:"))
        self.dim_combo = QComboBox()
        self.dim_combo.addItems(["2D", "3D"])
        self.dim_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        controls_layout.addWidget(self.dim_combo)

        # Run button
        self.run_btn = QPushButton("Run NMDS")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.run_btn.clicked.connect(self.on_run_clicked)
        controls_layout.addWidget(self.run_btn)

        controls_layout.addStretch()

        # Stress value label
        self.stress_label = QLabel("")
        self.stress_label.setAlignment(Qt.AlignCenter)
        self.stress_label.setStyleSheet("font-size: 11px; color: gray;")
        controls_layout.addWidget(self.stress_label)

        self.content_layout.addLayout(controls_layout)

        # NMDS visualization widget
        self.nmds_widget = NMDSVisualizationWidget()
        self.content_layout.addWidget(self.nmds_widget, stretch=1)

    def on_run_clicked(self):
        """Handle Run NMDS button click"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.run_nmds()


class RightPanel(ColumnPanel):
    """Right panel: ACC visualization with tabs for ACC1 and ACC2"""

    def __init__(self, parent=None):
        super().__init__("ACC Visualization", parent)
        self.setup_content()

    def setup_content(self):
        # Button layout (horizontal)
        button_layout = QHBoxLayout()

        # Single Generate button
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
        button_layout.addWidget(self.generate_btn, stretch=2)

        # Show Log button
        self.show_log_btn = QPushButton("📋 Show Log")
        self.show_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.show_log_btn.clicked.connect(self.on_show_log_clicked)
        self.show_log_btn.setEnabled(False)  # Disabled until ACC is generated
        button_layout.addWidget(self.show_log_btn, stretch=1)

        self.content_layout.addLayout(button_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)

        # Tab 1: ACC (original)
        self.acc_widget = ACCVisualizationWidget()
        self.tab_widget.addTab(self.acc_widget, "ACC")

        # Tab 2: ACC2 with options
        self.acc2_tab = QWidget()
        acc2_layout = QVBoxLayout(self.acc2_tab)
        acc2_layout.setContentsMargins(0, 0, 0, 0)
        acc2_layout.setSpacing(5)

        # ACC2 options panel
        options_panel = QWidget()
        options_layout = QHBoxLayout(options_panel)
        options_layout.setContentsMargins(5, 5, 5, 5)

        options_label = QLabel("<b>ACC2 Options:</b>")
        options_layout.addWidget(options_label)

        # Min diameter
        options_layout.addWidget(QLabel("Min Diameter:"))
        self.acc2_min_diameter = QLineEdit("1.0")
        self.acc2_min_diameter.setFixedWidth(60)
        self.acc2_min_diameter.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        options_layout.addWidget(self.acc2_min_diameter)

        # Max diameter
        options_layout.addWidget(QLabel("Max Diameter:"))
        self.acc2_max_diameter = QLineEdit("2.0")
        self.acc2_max_diameter.setFixedWidth(60)
        self.acc2_max_diameter.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        options_layout.addWidget(self.acc2_max_diameter)

        # ACC1 Style checkbox
        self.acc2_acc1_style = QCheckBox("ACC1 Style")
        self.acc2_acc1_style.setToolTip("Place areas on their first merge circle instead of innermost circle")
        options_layout.addWidget(self.acc2_acc1_style)

        # Limit Angle checkbox
        self.acc2_limit_angle = QCheckBox("Limit Angle:")
        self.acc2_limit_angle.setToolTip("Scale angles to fit within max angle limit")
        options_layout.addWidget(self.acc2_limit_angle)

        # Max angle input
        self.acc2_max_angle = QLineEdit("180")
        self.acc2_max_angle.setFixedWidth(50)
        self.acc2_max_angle.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        self.acc2_max_angle.setToolTip("Maximum total angular span (default: 180)")
        self.acc2_max_angle.setEnabled(False)  # Disabled until checkbox is checked
        options_layout.addWidget(self.acc2_max_angle)

        # Connect checkbox to enable/disable input
        self.acc2_limit_angle.stateChanged.connect(
            lambda state: self.acc2_max_angle.setEnabled(state == 2)  # 2 = Qt.CheckState.Checked
        )

        # Connect signals for real-time updates
        self.acc2_min_diameter.editingFinished.connect(self.on_acc2_options_changed)
        self.acc2_max_diameter.editingFinished.connect(self.on_acc2_options_changed)
        self.acc2_acc1_style.stateChanged.connect(self.on_acc2_options_changed)
        self.acc2_limit_angle.stateChanged.connect(self.on_acc2_options_changed)
        self.acc2_max_angle.editingFinished.connect(self.on_acc2_options_changed)

        options_layout.addStretch()

        acc2_layout.addWidget(options_panel)

        # ACC2 visualization widget
        self.acc2_widget = ACCVisualizationWidget()
        acc2_layout.addWidget(self.acc2_widget)

        self.tab_widget.addTab(self.acc2_tab, "ACC2")

        # Connect tab change to update button text
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.content_layout.addWidget(self.tab_widget)

    def on_tab_changed(self, index):
        """Update button text when tab changes"""
        if index == 0:
            self.generate_btn.setText("🎯 Generate ACC")
        elif index == 1:
            self.generate_btn.setText("🎯 Generate ACC2")

    def on_generate_clicked(self):
        """Handle generate button click - generates based on current tab"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            # Check which tab is currently active
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:
                # ACC tab
                main_window.generate_acc()
            elif current_tab == 1:
                # ACC2 tab
                main_window.generate_acc2()

    def on_show_log_clicked(self):
        """Handle show log button click"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            main_window.show_acc_log()

    def on_acc2_options_changed(self):
        """Handle ACC2 options change - update visualization in real-time"""
        main_window = self.window()
        if isinstance(main_window, MainWindow):
            # Only update if matrices are loaded
            if not main_window.left_panel.local_matrix_widget.is_loaded():
                return
            if not main_window.left_panel.global_matrix_widget.is_loaded():
                return

            # Validate inputs
            try:
                min_diameter = float(self.acc2_min_diameter.text())
                max_diameter = float(self.acc2_max_diameter.text())
                acc1_style = self.acc2_acc1_style.isChecked()
                limit_angle = self.acc2_limit_angle.isChecked()
                max_angle = float(self.acc2_max_angle.text()) if limit_angle else None

                if min_diameter <= 0 or max_diameter <= 0:
                    return  # Silently ignore invalid values during real-time updates

                if min_diameter >= max_diameter:
                    return  # Silently ignore invalid values during real-time updates

                if limit_angle and max_angle is not None and max_angle <= 0:
                    return  # Silently ignore invalid values during real-time updates

                # Regenerate ACC2 with new parameters
                main_window.generate_acc2_with_options(min_diameter, max_diameter, acc1_style, max_angle)

            except ValueError:
                pass  # Silently ignore invalid values during real-time updates


class MainWindow(QMainWindow):
    """Main application window with 5-column layout and step-by-step visualization"""

    def __init__(self):
        super().__init__()
        self.acc_log = ""  # Store ACC generation log
        self.log_handler = None  # Log handler for capturing logs
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ACC Visualizer - Step-by-Step Clustering")
        self.setGeometry(50, 50, 2400, 900)

        # Create five panels
        self.data_panel = DataPanel()
        self.left_panel = LeftPanel()
        self.center_panel = CenterPanel()
        self.right_panel = RightPanel()
        self.nmds_panel = NMDSPanel()

        # Add to scroll areas (instance variables for toggle access)
        self.data_scroll = QScrollArea()
        self.data_scroll.setWidgetResizable(True)
        self.data_scroll.setWidget(self.data_panel)

        self.left_scroll = QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setWidget(self.left_panel)

        self.center_scroll = QScrollArea()
        self.center_scroll.setWidgetResizable(True)
        self.center_scroll.setWidget(self.center_panel)

        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setWidget(self.right_panel)

        self.nmds_scroll = QScrollArea()
        self.nmds_scroll.setWidgetResizable(True)
        self.nmds_scroll.setWidget(self.nmds_panel)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.data_scroll)
        self.splitter.addWidget(self.left_scroll)
        self.splitter.addWidget(self.center_scroll)
        self.splitter.addWidget(self.right_scroll)
        self.splitter.addWidget(self.nmds_scroll)

        # Set initial sizes
        self.splitter.setSizes([400, 450, 450, 500, 500])

        # Set central widget
        self.setCentralWidget(self.splitter)

        # --- View menu & toolbar for panel show/hide ---
        panel_names = ["Data", "Similarity", "Dendrogram", "ACC", "NMDS"]
        self.panel_actions = []

        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")

        toolbar = self.addToolBar("Panels")

        for i, name in enumerate(panel_names):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(True)
            action.toggled.connect(lambda visible, idx=i: self.toggle_panel(idx, visible))
            view_menu.addAction(action)
            toolbar.addAction(action)
            self.panel_actions.append(action)

    def toggle_panel(self, index, visible):
        """Show or hide a panel in the splitter by index."""
        self.splitter.widget(index).setVisible(visible)

    def update_dendrogram(self, which="both"):
        """
        Update specific dendrogram(s)

        Args:
            which: 'local', 'global', or 'both'
        """
        if which in ("local", "both"):
            # Update local dendrogram
            sub_step_mgr = self.left_panel.local_matrix_widget.get_step_manager()
            if sub_step_mgr:
                self.center_panel.local_dendro_widget.set_step_manager(sub_step_mgr)
                self.center_panel.local_dendro_widget.set_step(self.left_panel.local_matrix_widget.get_current_step())

        if which in ("global", "both"):
            # Update global dendrogram
            inc_step_mgr = self.left_panel.global_matrix_widget.get_step_manager()
            if inc_step_mgr:
                self.center_panel.global_dendro_widget.set_step_manager(inc_step_mgr)
                self.center_panel.global_dendro_widget.set_step(self.left_panel.global_matrix_widget.get_current_step())

    def update_dendrograms(self):
        """Update both dendrograms (for backward compatibility)"""
        self.update_dendrogram("both")

    def clear_dendrogram(self, which):
        """
        Clear dendrogram when matrix is modified

        Args:
            which: 'local' or 'global'
        """
        if which == "local":
            self.center_panel.local_dendro_widget.clear_display()
        elif which == "global":
            self.center_panel.global_dendro_widget.clear_display()

    def update_dendrogram_steps(self):
        """Update dendrogram display when step changes"""
        # Update local
        sub_step = self.left_panel.local_matrix_widget.get_current_step()
        self.center_panel.local_dendro_widget.set_step(sub_step)

        # Update global
        inc_step = self.left_panel.global_matrix_widget.get_current_step()
        self.center_panel.global_dendro_widget.set_step(inc_step)

    def generate_acc(self):
        """Generate ACC visualization"""
        try:
            # Check if both matrices are loaded
            if not self.left_panel.local_matrix_widget.is_loaded():
                QMessageBox.warning(self, "Missing Data", "Please load the Local Similarity Matrix first")
                return

            if not self.left_panel.global_matrix_widget.is_loaded():
                QMessageBox.warning(self, "Missing Data", "Please load the Global Similarity Matrix first")
                return

            # Get original matrices (not step matrices)
            local_df = self.left_panel.local_matrix_widget.get_dataframe()
            global_df = self.left_panel.global_matrix_widget.get_dataframe()

            local_matrix = dict_matrix_from_dataframe(local_df)
            global_matrix = dict_matrix_from_dataframe(global_df)

            # Validate matrices
            valid, msg = validate_similarity_matrix(local_matrix)
            if not valid:
                QMessageBox.warning(self, "Invalid Local Matrix", f"Local matrix validation failed:\n{msg}")
                return

            valid, msg = validate_similarity_matrix(global_matrix)
            if not valid:
                QMessageBox.warning(self, "Invalid Global Matrix", f"Global matrix validation failed:\n{msg}")
                return

            # Setup log capture
            log_stream = StringIO()
            log_handler = logging.StreamHandler(log_stream)
            log_handler.setLevel(logging.INFO)
            log_formatter = logging.Formatter("%(levelname)s: %(message)s")
            log_handler.setFormatter(log_formatter)

            # Get logger from acc_core_new (logger name is 'ACC_Iterative')
            logger = logging.getLogger("ACC_Iterative")
            original_level = logger.level
            logger.setLevel(logging.INFO)
            logger.addHandler(log_handler)

            try:
                # Run ACC algorithm step by step (NEW ITERATIVE ALGORITHM)
                acc_steps = build_acc_from_matrices_iterative(local_matrix, global_matrix, unit=1.0, method="average")
            finally:
                # Remove handler and restore logger
                logger.removeHandler(log_handler)
                logger.setLevel(original_level)

                # Save log
                self.acc_log = log_stream.getvalue()
                log_stream.close()

                # Enable Show Log button
                self.right_panel.show_log_btn.setEnabled(True)

            # Visualize with step controls
            self.right_panel.acc_widget.set_acc_steps(acc_steps)

            # No message box - just silently complete
            # Log info for debugging if needed
            if acc_steps:
                final_step = acc_steps[-1]
                clusters = final_step["clusters"]
                if clusters:
                    cluster = clusters[0]
                    print(f"[ACC] Generated: {len(acc_steps)} steps, {len(cluster['members'])} members")
                else:
                    print("[ACC] Warning: No clusters found")
            else:
                print("[ACC] Warning: No steps generated")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate visualization:\n{str(e)}")
            import traceback

            traceback.print_exc()

    def generate_acc2(self):
        """Generate ACC2 visualization with default parameters"""
        # Get default min/max diameter from UI
        try:
            min_diameter = float(self.right_panel.acc2_min_diameter.text())
            max_diameter = float(self.right_panel.acc2_max_diameter.text())
            acc1_style = self.right_panel.acc2_acc1_style.isChecked()
            limit_angle = self.right_panel.acc2_limit_angle.isChecked()
            max_angle = float(self.right_panel.acc2_max_angle.text()) if limit_angle else None
        except:
            min_diameter = 1.0
            max_diameter = 2.0
            acc1_style = False
            max_angle = None

        self.generate_acc2_with_options(min_diameter, max_diameter, acc1_style, max_angle)

    def generate_acc2_with_options(self, min_diameter, max_diameter, acc1_style=False, max_angle=None):
        """Generate ACC2 visualization with custom diameter range and optional angle limit"""
        try:
            # Check if both matrices are loaded
            if not self.left_panel.local_matrix_widget.is_loaded():
                QMessageBox.warning(self, "Missing Data", "Please load the Local Similarity Matrix first")
                return

            if not self.left_panel.global_matrix_widget.is_loaded():
                QMessageBox.warning(self, "Missing Data", "Please load the Global Similarity Matrix first")
                return

            # Get original matrices (not step matrices)
            local_df = self.left_panel.local_matrix_widget.get_dataframe()
            global_df = self.left_panel.global_matrix_widget.get_dataframe()

            local_matrix = dict_matrix_from_dataframe(local_df)
            global_matrix = dict_matrix_from_dataframe(global_df)

            # Validate matrices
            valid, msg = validate_similarity_matrix(local_matrix)
            if not valid:
                QMessageBox.warning(self, "Invalid Local Matrix", f"Local matrix validation failed:\n{msg}")
                return

            valid, msg = validate_similarity_matrix(global_matrix)
            if not valid:
                QMessageBox.warning(self, "Invalid Global Matrix", f"Global matrix validation failed:\n{msg}")
                return

            # Build ACC2 with parameters (including optional angle limit)
            acc2_data = build_acc2(local_matrix, global_matrix, unit=1.0, max_angle=max_angle)

            # Store ACC2 data for future option updates
            self.acc2_data = acc2_data

            # Convert diameter inputs to radius (circles are stored as radii)
            min_radius = min_diameter / 2.0
            max_radius = max_diameter / 2.0

            # Scale circles to fit min/max radius range
            # Original circles are in radius units
            original_min = min(acc2_data["circles"])
            original_max = max(acc2_data["circles"])
            original_range = original_max - original_min

            if original_range > 0:
                # Scale circles (radii)
                new_range = max_radius - min_radius
                scaled_circles = []
                for r in acc2_data["circles"]:
                    scaled_r = min_radius + (r - original_min) / original_range * new_range
                    scaled_circles.append(scaled_r)
                acc2_data["circles"] = scaled_circles

                # Scale merge point radii
                for cluster_id, mp in acc2_data["merge_points"].items():
                    old_r = mp["radius"]
                    new_r = min_radius + (old_r - original_min) / original_range * new_range
                    acc2_data["merge_points"][cluster_id]["radius"] = new_r

                # Scale level radii
                for level in acc2_data["levels"]:
                    old_r = level["radius"]
                    new_r = min_radius + (old_r - original_min) / original_range * new_range
                    level["radius"] = new_r

                # Scale area positions (all areas at innermost circle)
                for area, pos in acc2_data["positions"].items():
                    old_r = pos["radius"]
                    new_r = min_radius + (old_r - original_min) / original_range * new_range
                    # Update radius
                    acc2_data["positions"][area]["radius"] = new_r
                    # Recalculate x, y from new radius and existing angle (using compass convention)
                    new_x, new_y = compass_to_cart(new_r, pos["angle"])
                    acc2_data["positions"][area]["x"] = new_x
                    acc2_data["positions"][area]["y"] = new_y

            # Visualize ACC2 in the ACC2 tab
            # ACC1 style will be applied inside plot_acc2
            self.right_panel.acc2_widget.plot_acc2(acc2_data, acc1_style=acc1_style)

            # No message box - just silently complete
            angle_info = f", max angle: {max_angle}°" if max_angle else ""
            print(
                f"[ACC2] Generated: {len(acc2_data['positions'])} areas, diameter range: {min_diameter:.1f}-{max_diameter:.1f}{angle_info}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate ACC2 visualization:\n{str(e)}")
            import traceback

            traceback.print_exc()

    def run_nmds(self):
        """Run NMDS based on selected matrix type"""
        try:
            matrix_type = self.nmds_panel.matrix_combo.currentText()

            if matrix_type == "Local":
                if not self.left_panel.local_matrix_widget.is_loaded():
                    QMessageBox.warning(self, "Missing Data", "Please load the Local Similarity Matrix first")
                    return
                df = self.left_panel.local_matrix_widget.get_dataframe()
            else:
                if not self.left_panel.global_matrix_widget.is_loaded():
                    QMessageBox.warning(self, "Missing Data", "Please load the Global Similarity Matrix first")
                    return
                df = self.left_panel.global_matrix_widget.get_dataframe()

            similarity_dict = dict_matrix_from_dataframe(df)
            n_components = 3 if self.nmds_panel.dim_combo.currentText() == "3D" else 2
            stress = self.nmds_panel.nmds_widget.run_nmds(similarity_dict, n_components=n_components)

            # Update stress label with quality interpretation
            if stress is not None:
                if stress < 0.05:
                    quality, color = "Excellent", "#4CAF50"
                elif stress < 0.1:
                    quality, color = "Good", "#8BC34A"
                elif stress < 0.2:
                    quality, color = "Fair", "#FF9800"
                else:
                    quality, color = "Poor", "#F44336"
                self.nmds_panel.stress_label.setText(f"Stress: {stress:.4f} ({quality})")
                self.nmds_panel.stress_label.setStyleSheet(
                    f"font-size: 11px; font-weight: bold; color: {color};"
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run NMDS:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def show_acc_log(self):
        """Show ACC generation log in a dialog"""
        if not self.acc_log:
            QMessageBox.information(
                self, "No Log Available", "No ACC generation log is available.\nPlease generate ACC first."
            )
            return

        # Show log in dialog
        log_dialog = LogViewerDialog(self.acc_log, self)
        log_dialog.exec_()


def main():
    """Main entry point"""
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"ERROR in main(): {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Build command:
# pyinstaller --name "AACCViz_v0.0.2_20251113.exe" --onefile --noconsole acc_gui.py
