#!/usr/bin/env python3
"""
Generate PDF from Markdown using pandoc

This script converts USER_MANUAL.md to PDF with proper formatting,
including images and table of contents.

Requirements:
    pip install pypandoc

System requirements:
    - pandoc (https://pandoc.org/installing.html)
    - pdflatex or wkhtmltopdf (for PDF generation)

Usage:
    python scripts/generate_pdf.py
    python scripts/generate_pdf.py --input doc/USER_MANUAL.md --output doc/ACC_USER_MANUAL.pdf
"""

import argparse
import sys
from pathlib import Path

try:
    import pypandoc
except ImportError:
    print("Error: pypandoc is not installed.")
    print("Install it with: pip install pypandoc")
    sys.exit(1)


def ensure_pandoc_installed():
    """Check if pandoc is installed, download if not."""
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        print("Pandoc not found. Attempting to download...")
        try:
            pypandoc.download_pandoc()
            print("Pandoc downloaded successfully.")
        except Exception as e:
            print(f"Failed to download pandoc: {e}")
            print("Please install pandoc manually: https://pandoc.org/installing.html")
            sys.exit(1)


def generate_pdf(input_file: str, output_file: str, engine: str = "xelatex"):
    """
    Generate PDF from Markdown file.

    Args:
        input_file: Path to input Markdown file
        output_file: Path to output PDF file
        engine: PDF engine to use ('pdflatex', 'xelatex', or 'wkhtmltopdf')
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Change working directory to doc/ to resolve relative image paths
    original_cwd = Path.cwd()
    doc_dir = input_path.parent

    print(f"Converting {input_file} to PDF...")
    print(f"Engine: {engine}")
    print(f"Working directory: {doc_dir}")

    # Extra arguments for better PDF formatting
    extra_args = [
        "--toc",  # Table of contents
        "--toc-depth=3",  # TOC depth
        "--number-sections",  # Number sections
        "-V",
        "geometry:margin=1in",  # Margins
        "-V",
        "linkcolor:blue",  # Link color
        "-V",
        "fontsize=11pt",  # Font size
        "--highlight-style=tango",  # Code syntax highlighting
        "-V",
        "caption-position:bottom",  # Place captions below images
    ]

    if engine == "pdflatex" or engine == "xelatex":
        extra_args.append(f"--pdf-engine={engine}")

        # Add LaTeX packages for better image caption handling
        extra_args.extend([
            "-V",
            "header-includes=\\usepackage{caption}",
            "-V",
            "header-includes=\\captionsetup[figure]{position=bottom,skip=10pt}",
        ])

        # XeLaTeX is required for Korean/Unicode support
        if engine == "xelatex":
            import platform

            system = platform.system()
            if system == "Windows":
                # Windows: Use Malgun Gothic (맑은 고딕)
                korean_font = "Malgun Gothic"
            elif system == "Darwin":
                # macOS: Use AppleGothic or other system font
                korean_font = "AppleGothic"
            else:
                # Linux: Use Noto Sans CJK KR
                korean_font = "Noto Sans CJK KR"

            extra_args.extend([
                "-V",
                f"mainfont={korean_font}",
                "-V",
                f"monofont={korean_font}",
            ])
        else:
            extra_args.extend([
                "-V",
                "mainfont=DejaVu Sans",  # Main font
                "-V",
                "monofont=DejaVu Sans Mono",  # Code font
            ])

    try:
        # Change to doc directory to resolve relative image paths
        import os

        os.chdir(doc_dir)

        # Convert to PDF using relative paths
        pypandoc.convert_file(str(input_path.name), "pdf", outputfile=str(output_path.resolve()), extra_args=extra_args)

        # Restore original working directory
        os.chdir(original_cwd)

        print(f"✓ PDF generated successfully: {output_file}")

        # Show file size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")

    except RuntimeError as e:
        # Restore original working directory
        import os

        os.chdir(original_cwd)
        print(f"Error generating PDF: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure pandoc is installed: pandoc --version")
        print("2. Make sure pdflatex is installed (part of LaTeX distribution)")
        print("   - Windows: Install MiKTeX or TeX Live")
        print("   - macOS: Install MacTeX")
        print("   - Linux: sudo apt-get install texlive-latex-base texlive-fonts-recommended")
        print("\nAlternatively, use --engine wkhtmltopdf:")
        print("  pip install pdfkit")
        print("  Download wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate PDF from Markdown")
    parser.add_argument(
        "--input", default="doc/USER_MANUAL.md", help="Input Markdown file (default: doc/USER_MANUAL.md)"
    )
    parser.add_argument(
        "--output", default="doc/ACC_USER_MANUAL.pdf", help="Output PDF file (default: doc/ACC_USER_MANUAL.pdf)"
    )
    parser.add_argument(
        "--engine",
        choices=["pdflatex", "xelatex", "wkhtmltopdf"],
        default="xelatex",
        help="PDF engine to use (default: xelatex for Korean support)",
    )

    args = parser.parse_args()

    ensure_pandoc_installed()
    generate_pdf(args.input, args.output, args.engine)


if __name__ == "__main__":
    main()
