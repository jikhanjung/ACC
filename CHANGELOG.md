# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
