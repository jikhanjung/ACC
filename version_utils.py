"""
Version management utilities for ACC
Provides validation and parsing functions for semantic versioning
"""

import re


def validate_version(version: str) -> bool:
    """
    Validate version string against Semantic Versioning 2.0.0 format
    https://semver.org/

    Args:
        version: Version string to validate

    Returns:
        True if valid, raises ValueError if invalid

    Examples:
        - 0.0.3 (valid)
        - 1.0.0-alpha (valid)
        - 2.1.0-beta.1 (valid)
        - 1.2 (invalid - patch version missing)
    """
    pattern = (
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?$"
    )

    if not re.match(pattern, version):
        raise ValueError(f"Invalid semantic version format: {version}")
    return True


def parse_version(version: str) -> tuple[int, int, int, str | None]:
    """
    Parse version string into its components

    Args:
        version: Version string to parse

    Returns:
        Tuple of (major, minor, patch, prerelease)

    Raises:
        ValueError: If version format is invalid
    """
    validate_version(version)

    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", version)
    if match:
        major, minor, patch, prerelease = match.groups()
        return int(major), int(minor), int(patch), prerelease

    raise ValueError(f"Unable to parse version: {version}")


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two semantic versions

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2

    Note:
        Prerelease versions are not considered in comparison
    """
    p1 = parse_version(v1)[:3]  # major, minor, patch only
    p2 = parse_version(v2)[:3]

    if p1 < p2:
        return -1
    if p1 > p2:
        return 1
    return 0


def format_version(major: int, minor: int, patch: int, prerelease: str | None = None) -> str:
    """
    Format version components into a version string

    Args:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        prerelease: Optional prerelease string

    Returns:
        Formatted version string
    """
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}"
    return version


def increment_version(version: str, bump_type: str = "patch") -> str:
    """
    Increment version based on bump type

    Args:
        version: Current version string
        bump_type: Type of version bump ('major', 'minor', 'patch')

    Returns:
        New version string

    Raises:
        ValueError: If bump_type is invalid
    """
    major, minor, patch, _ = parse_version(version)

    if bump_type == "major":
        return format_version(major + 1, 0, 0)
    if bump_type == "minor":
        return format_version(major, minor + 1, 0)
    if bump_type == "patch":
        return format_version(major, minor, patch + 1)
    raise ValueError(f"Invalid bump type: {bump_type}. Must be 'major', 'minor', or 'patch'")


def get_version_from_file(file_path: str = "version.py") -> str:
    """
    Extract version string from version.py file

    Args:
        file_path: Path to version file

    Returns:
        Version string

    Raises:
        RuntimeError: If version cannot be found in file
    """
    with open(file_path) as f:
        content = f.read()
        match = re.search(r'__version__ = "(.*?)"', content)
        if match:
            return match.group(1)
    raise RuntimeError(f"Unable to find version string in {file_path}")
