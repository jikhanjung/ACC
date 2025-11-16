#!/usr/bin/env python
"""
Version management utility for ACC

Usage:
  python manage_version.py <command> [token]

Commands:
  major, minor, patch: Increment major, minor, or patch version.
    (e.g., 0.0.3 -> 1.0.0 with 'major')
    (e.g., 0.0.3 -> 0.1.0 with 'minor')
    (e.g., 0.0.3 -> 0.0.4 with 'patch')

  premajor, preminor, prepatch [token]: Start a new pre-release cycle.
    Token defaults to 'alpha'.
    (e.g., 0.0.3 -> 0.1.0-alpha.1 with 'preminor')
    (e.g., 0.0.3 -> 0.1.0-beta.1 with 'preminor beta')

  prerelease: Increment the pre-release number.
    (e.g., 0.1.0-alpha.1 -> 0.1.0-alpha.2)

  stage <alpha|beta|rc>: Transition to a new pre-release stage.
    (e.g., 0.1.0-alpha.2 -> 0.1.0-beta.1 with 'stage beta')

  release: Finalize a pre-release version to a stable version.
    (e.g., 0.1.0-alpha.2 -> 0.1.0)

Examples:
  python manage_version.py patch           # 0.0.3 -> 0.0.4
  python manage_version.py minor           # 0.0.3 -> 0.1.0
  python manage_version.py preminor beta   # 0.0.3 -> 0.1.0-beta.1
  python manage_version.py prerelease      # 0.1.0-beta.1 -> 0.1.0-beta.2
  python manage_version.py release         # 0.1.0-beta.2 -> 0.1.0
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import semver
except ImportError:
    print("Error: 'semver' library not found. Please install it with 'pip install semver'")
    sys.exit(1)


def get_current_version() -> str:
    """Read current version from version.py"""
    version_file = Path("version.py")
    if not version_file.exists():
        raise FileNotFoundError("version.py not found")

    content = version_file.read_text()
    match = re.search(r'__version__ = "(.*?)"', content)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string in version.py")


def update_version_file(new_version: str) -> None:
    """Update version.py with new version"""
    version_file = Path("version.py")
    content = version_file.read_text()

    new_content = re.sub(r'__version__ = ".*?"', f'__version__ = "{new_version}"', content)

    backup_file = version_file.with_suffix(".py.bak")
    version_file.rename(backup_file)

    try:
        version_file.write_text(new_content)
        print(f"✅ Version updated to {new_version}")
        backup_file.unlink()
    except Exception as e:
        backup_file.rename(version_file)
        raise e


def get_new_version(command: str, current_ver_info: semver.VersionInfo, token: str | None = None) -> str:
    """Get the new version based on the command."""
    if command in ["major", "minor", "patch"]:
        if current_ver_info.prerelease:
            return str(current_ver_info.finalize_version())
        return str(getattr(current_ver_info, f"bump_{command}")())

    if command.startswith("pre") and command != "prerelease":
        base_command = command.replace("pre", "")
        if base_command not in ["major", "minor", "patch"]:
            raise ValueError(f"Invalid command: {command}")
        next_version = getattr(current_ver_info.finalize_version(), f"bump_{base_command}")()
        return str(next_version.bump_prerelease(token or "alpha"))

    if command == "prerelease":
        if not current_ver_info.prerelease:
            raise ValueError(
                "Cannot bump prerelease on a stable version. Start a pre-release cycle first (e.g., 'prepatch')."
            )
        return str(current_ver_info.bump_prerelease())

    if command == "stage":
        if not current_ver_info.prerelease:
            raise ValueError("Cannot transition stage on a stable version. Start a pre-release cycle first.")
        if not token or token not in ["alpha", "beta", "rc"]:
            raise ValueError("A valid stage token (alpha, beta, rc) is required.")
        if token == current_ver_info.prerelease.split(".")[0]:
            raise ValueError(f"Already in '{token}' stage.")
        return str(current_ver_info.replace(prerelease=f"{token}.1"))

    if command == "release":
        if not current_ver_info.prerelease:
            print("Version is already stable.")
            return str(current_ver_info)
        return str(current_ver_info.finalize_version())

    raise ValueError(f"Invalid command: {command}")


def create_git_tag(version: str, message: str | None = None) -> None:
    """Create git tag (without automatic push)"""
    tag_name = f"v{version}"
    if message is None:
        message = f"Release version {version}"

    try:
        result = subprocess.run(["git", "tag", "-l", tag_name], capture_output=True, text=True)
        if result.stdout.strip():
            print(f"⚠️  Tag {tag_name} already exists")
            return

        subprocess.run(["git", "tag", "-a", tag_name, "-m", message], check=True)
        print(f"✅ Git tag created: {tag_name}")
        print(f"   To push: git push origin {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create git tag: {e}")


def update_changelog(version: str) -> None:
    """Update or create CHANGELOG.md"""
    changelog_file = Path("CHANGELOG.md")
    date_str = datetime.now(datetime.UTC).strftime("%Y-%m-%d")

    header = f"## [{version}] - {date_str}"
    if changelog_file.exists() and header in changelog_file.read_text():
        print(f"⚠️  Version {version} already in CHANGELOG.md")
        return

    new_section = f"""
{header}

### Added
-

### Changed
-

### Fixed
-

"""

    if not changelog_file.exists():
        content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
{new_section}"""
        changelog_file.write_text(content)
        print("✅ CHANGELOG.md created")
    else:
        content = changelog_file.read_text()
        insert_index = -1
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("## ["):
                insert_index = i
                break
        if insert_index == -1:
            lines.append(new_section)
        else:
            lines.insert(insert_index, new_section)

        changelog_file.write_text("\n".join(lines))
        print("✅ CHANGELOG.md updated")
    print("⚠️  Please update the changelog entries before committing")


def check_git_status() -> bool:
    """Check if git working directory is clean"""
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("⚠️  Warning: You have uncommitted changes")
            response = input("Continue anyway? (y/N): ")
            return response.lower() == "y"
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Not a git repository or git not available. Skipping check.")
        return True


def main():
    """Main execution function"""
    args = sys.argv[1:]
    if not args or args[0] in ["-h", "--help"]:
        print(__doc__)
        sys.exit(0)

    command = args[0]
    token = args[1] if len(args) > 1 else None

    valid_commands = ["major", "minor", "patch", "premajor", "preminor", "prepatch", "prerelease", "release", "stage"]
    if command not in valid_commands:
        print(f"Error: Invalid command '{command}'")
        print("See 'python manage_version.py --help' for usage.")
        sys.exit(1)

    try:
        if not check_git_status():
            print("Aborted")
            sys.exit(1)

        current_version_str = get_current_version()
        print(f"Current version: {current_version_str}")

        try:
            current_ver_info = semver.VersionInfo.parse(current_version_str)
        except ValueError:
            print(f"Error: Invalid semantic version in version.py: '{current_version_str}'")
            sys.exit(1)

        new_version = get_new_version(command, current_ver_info, token)
        print(f"New version will be: {new_version}")

        response = input(f"Update version to {new_version}? (y/N): ")
        if response.lower() != "y":
            print("Aborted")
            sys.exit(0)

        update_version_file(new_version)

        response = input("Update CHANGELOG.md? (y/N): ")
        if response.lower() == "y":
            update_changelog(new_version)

        response = input("Create git commit? (y/N): ")
        if response.lower() == "y":
            subprocess.run(["git", "add", "version.py", "CHANGELOG.md"], check=True)
            commit_message = f"chore: bump version to {new_version}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(f"✅ Git commit created: {commit_message}")

            response = input("Create git tag? (y/N): ")
            if response.lower() == "y":
                create_git_tag(new_version)

        print(f"\n🎉 Version {new_version} is ready!")
        print("\nNext steps:")
        print("1. Manually edit CHANGELOG.md to add details for this version.")
        print("2. Push your changes: git push")
        print("3. Push the tag: git push origin v{new_version}")

    except (KeyboardInterrupt, EOFError):
        print("\nAborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
