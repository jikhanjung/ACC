# Makefile for ACC project
# Common development tasks

.PHONY: help install install-dev test coverage clean docs pdf sphinx

help:
	@echo "ACC Project - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make pre-commit   - Run pre-commit hooks on all files"
	@echo ""
	@echo "Documentation:"
	@echo "  make pdf          - Generate USER_MANUAL.pdf from Markdown"
	@echo "  make sphinx       - Build Sphinx HTML documentation"
	@echo "  make docs         - Build all documentation (PDF + Sphinx)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo ""

install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest -v

coverage:
	pytest --cov=. --cov-report=html --cov-report=term-missing

lint:
	ruff check .

format:
	ruff check --fix .
	ruff format .

pre-commit:
	pre-commit run --all-files

pdf:
	@echo "Generating PDF from USER_MANUAL.md..."
	python scripts/generate_pdf.py --engine xelatex

sphinx:
	@echo "Building Sphinx documentation..."
	cd docs && make html
	@echo "HTML documentation: docs/_build/html/index.html"

docs: pdf sphinx
	@echo "All documentation built successfully!"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/ htmlcov/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	@echo "Clean complete!"
