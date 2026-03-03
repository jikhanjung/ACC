# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.6] - 2026-03-03

### Added
- Tree-based ACC algorithm (`acc_core_tree.py`): ACCNode dataclass with explicit binary tree structure
  - Build/Render separation: diameter changes recompute coordinates without rebuilding tree
  - Diversity index for area ordering (left/right) based on present taxa count
  - `build_acc_tree()`, `render_tree()`, `generate_steps()`, `build_acc_from_tree()` API
- Min/Max Diameter controls in ACC panel for interactive diameter scaling
- Tree algorithm wrappers in `acc_utils.py`: `build_acc_from_matrices_tree()`, `rerender_acc_tree()`
- Unit tests for tree module: `test_acc_core_tree.py` (35 tests)
- GUI test suite: `tests/gui/test_acc_gui.py` (13 tests covering utilities, widget smoke tests, code quality checks)
- `QApplication` session fixture in `tests/conftest.py` for GUI tests
- Module-level `logger` in acc_gui.py with `logging.basicConfig()` in `main()`

### Changed
- ACC panel now uses tree-based algorithm (`acc_core_tree.py`) instead of `acc_core_new.py`
- Magic numbers replaced with named constants: `THETA_MAX_DEGREES` (acc_core.py, acc_core_new.py), `DEFAULT_SIMILARITY` (acc_core_new.py)
- All `print()` statements in acc_gui.py converted to `logging` module calls
- Bare `except:` clause replaced with `except (ValueError, AttributeError):` in acc_gui.py
- `E722` rule removed from ruff ignore list (no longer needed)

### Removed
- ACC2 tab and all related code (~420 lines removed from acc_gui.py)
  - `plot_acc2()` and 10 related private methods in ACCVisualizationWidget
  - `generate_acc2()`, `generate_acc2_with_options()`, `on_tab_changed()`, `on_acc2_options_changed()`
  - `compass_to_cart()` utility function
  - `from acc_core_acc2 import ...` imports

## [0.0.5] - 2026-02-26

### Added
- NMDS (Non-metric Multidimensional Scaling) 패널 추가 (5번째 패널)
  - Local/Global 유사도 행렬 선택 콤보박스
  - scikit-learn MDS(metric_mds=False)를 이용한 비계량 다차원척도법
  - 2D 산점도 시각화 (area 이름 라벨, Stress 값 표시)
  - 우클릭 이미지 저장 (PNG/PDF/SVG)
- `scikit-learn>=1.6.0` 의존성 추가
- Raup-Crick similarity index with Monte Carlo simulation (10,000 iterations default)
- GUI input field for Raup-Crick iteration count (dynamic visibility)
- Four standardized similarity indices: Jaccard, Ochiai, Raup-Crick, Simpson
- NMDS 2D/3D 차원 선택 기능
- 패널 Show/Hide 토글 (View 메뉴 + Panels 툴바)
- ACC 포인트 스케일링 제거 및 NMDS Stress 품질 표시

### Changed
- Similarity index selection reduced from 5 to 4 methods
- Raup-Crick upgraded from deterministic to probabilistic implementation
- Default Raup-Crick iterations increased to 10,000 for better accuracy

### Removed
- Dice (Sørensen) similarity index
- Braun-Blanquet similarity index

## [0.0.4] - 2026-02-10

### Added
- Manual release workflow (GitHub Actions)
- InnoSetup installer EXE included in release artifacts
- Resource path helper for PyInstaller data directory access
- ACC1 style option
- `semver` added to requirements

### Changed
- Bumped version to 0.0.4 (tagged as `v0.0.4-build.1`)
- Improved InnoSetup installer configuration
- Performance optimizations and UI improvements
- Sphinx docs now include figure captions
- PDF regenerated with Unicode fixes
- Terminology unification and data structure refactor
- Enforced Python 3.11+ requirement with `datetime.UTC`

### Fixed
- ACC2 swap bug
- ACC2 options update live; area position scaling adjusted
- Matrix edits now reflect in real time
- Import issues
- Build script no longer references missing images directory
- PDF generation path and Unicode issues

## [0.0.3] - 2025-11-16

### Added
- Comprehensive QA infrastructure (code coverage, pre-commit hooks, Ruff linting)
- Version management system with `manage_version.py` script
- Semantic versioning support with `semver` library
- Makefile for common development tasks
- PDF generation automation from Markdown
- GitHub Actions workflow for automatic documentation generation
- Project structure documentation (STRUCTURE.md)
- Complete documentation reorganization (`doc/` for Markdown, `docs/` for Sphinx)
- Development guide with testing and CI/CD instructions
- QA setup summary documentation
- PDF generation guide
- Version utilities module

### Changed
- Reorganized documentation structure (separated Markdown and Sphinx docs)
- Moved all build-related documentation to `doc/build/`
- Moved images to `doc/images/` and examples to `doc/examples/`
- Updated README.md with comprehensive project information
- Enhanced pytest configuration with test markers
- Improved GitHub Actions test workflow with coverage reporting
- Updated all cross-references to new documentation paths

### Fixed
- PyQt version inconsistency (now using PyQt5 consistently)
- Documentation path references
- Pre-commit hook Python version compatibility

## [0.1.0] - 2024-11-15

### Added
- Initial GUI implementation with PyQt5
- Core ACC algorithm for cluster visualization
- CSV file import for similarity matrices
- Automatic dendrogram generation
- Interactive matplotlib visualizations
- Sample data files
- Basic documentation

### Changed
- Switched from PyQt6 to PyQt5 for better compatibility

### Fixed
- Build issues on various platforms
- matplotlib backend compatibility

## [0.0.1] - 2024-11-11

### Added
- Initial project setup
- Core algorithm implementation
- Basic CLI interface
- Sample dendrogram data structures
