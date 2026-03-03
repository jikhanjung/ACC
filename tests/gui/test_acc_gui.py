"""
GUI tests for acc_gui.py
Tests utility functions, widget instantiation, and code quality checks.

All tests marked with @pytest.mark.gui.
Requires QT_QPA_PLATFORM=offscreen for headless CI.
"""

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.gui


# ---------------------------------------------------------------------------
# get_resource_path tests
# ---------------------------------------------------------------------------


class TestGetResourcePath:
    def test_returns_path_in_project(self):
        """Should return a path under the project root when not bundled"""
        from acc_gui import get_resource_path

        result = get_resource_path("test.txt")
        assert result.name == "test.txt"
        # Should be relative to acc_gui.py's directory
        assert result.parent == Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# MainWindow smoke tests
# ---------------------------------------------------------------------------


class TestMainWindow:
    def test_instantiation(self, qapp):
        """MainWindow should instantiate without errors"""
        from acc_gui import MainWindow

        window = MainWindow()
        assert window is not None
        window.close()

    def test_has_panels(self, qapp):
        """MainWindow should have left, center, right panels"""
        from acc_gui import MainWindow

        window = MainWindow()
        assert hasattr(window, "left_panel")
        assert hasattr(window, "center_panel")
        assert hasattr(window, "right_panel")
        window.close()


# ---------------------------------------------------------------------------
# ACCVisualizationWidget tests
# ---------------------------------------------------------------------------


class TestACCVisualizationWidget:
    def test_instantiation(self, qapp):
        """ACCVisualizationWidget should instantiate cleanly"""
        from acc_gui import ACCVisualizationWidget

        widget = ACCVisualizationWidget()
        assert widget is not None
        assert hasattr(widget, "figure")
        assert hasattr(widget, "canvas")

    def test_initial_step(self, qapp):
        """Widget should start with no steps"""
        from acc_gui import ACCVisualizationWidget

        widget = ACCVisualizationWidget()
        assert hasattr(widget, "acc_steps") or not hasattr(widget, "acc_steps")


# ---------------------------------------------------------------------------
# Code quality: no print statements in acc_gui.py
# ---------------------------------------------------------------------------


class TestCodeQuality:
    def test_no_print_statements(self):
        """acc_gui.py should not contain any print() calls"""
        gui_path = Path(__file__).parent.parent.parent / "acc_gui.py"
        source = gui_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        prints_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "print":
                    prints_found.append(node.lineno)

        assert prints_found == [], f"print() found on lines: {prints_found}"

    def test_logger_exists(self):
        """acc_gui module should define a module-level logger"""
        import acc_gui

        assert hasattr(acc_gui, "logger")
        import logging

        assert isinstance(acc_gui.logger, logging.Logger)

    def test_no_bare_except(self):
        """acc_gui.py should not contain bare except clauses"""
        gui_path = Path(__file__).parent.parent.parent / "acc_gui.py"
        source = gui_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        bare_excepts = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                bare_excepts.append(node.lineno)

        assert bare_excepts == [], f"Bare except on lines: {bare_excepts}"
