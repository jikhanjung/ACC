"""
ACC Build Script
Builds executable using PyInstaller and creates installers for Windows, macOS, and Linux
"""

import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Import version from centralized version file
try:
    from version import __version__ as version

    VERSION = version
except ImportError:
    # Fallback: extract from version.py file
    def get_version_from_file():
        with open("version.py") as f:
            content = f.read()
            match = re.search(r'__version__ = "(.*?)"', content)
            if match:
                return match.group(1)
        raise RuntimeError("Unable to find version string")

    VERSION = get_version_from_file()


def run_pyinstaller(args):
    """Runs PyInstaller with the specified arguments."""
    pyinstaller_cmd = ["pyinstaller"] + args
    try:
        subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("PyInstaller completed successfully")

        # Check if the executable was created
        actual_name = "ACC"  # default
        for arg in args:
            if arg.startswith("--name="):
                actual_name = arg.split("=", 1)[1]
                break

        # For onedir, check if executable exists
        if "--onedir" in args:
            exe_extension = get_platform_executable_extension()
            exe_path = Path(f"dist/{actual_name}/ACC{exe_extension}")
        else:
            exe_path = Path(f"dist/{actual_name}")

        if not exe_path.exists():
            dist_path = Path("dist")
            if dist_path.exists():
                print("Contents of dist directory:")
                for item in dist_path.iterdir():
                    print(f"  {item}")
                if (dist_path / "ACC").exists():
                    print("Contents of dist/ACC directory:")
                    for item in (dist_path / "ACC").iterdir():
                        print(f"  {item}")
            raise FileNotFoundError(f"Expected executable not found: {exe_path}")
        print(f"Executable created: {exe_path}")

    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        raise


def prepare_inno_setup_template(template_path, version):
    """Prepare InnoSetup script from template, return path to temp file."""
    temp_dir = Path(tempfile.mkdtemp())
    temp_iss = temp_dir / "ACC.iss"

    # Read template file
    template_file = Path(template_path)
    if template_file.with_suffix(".iss.template").exists():
        template_file = template_file.with_suffix(".iss.template")

    content = template_file.read_text()

    # Replace version placeholder
    content = re.sub(r'#define AppVersion ".*?"', f'#define AppVersion "{version}"', content)
    content = content.replace("{{VERSION}}", version)

    # Get absolute paths
    dist_abs_path = Path("dist").resolve()
    project_root = Path.cwd()

    content = content.replace("{{DIST_PATH}}", str(dist_abs_path))
    content = content.replace("{{PROJECT_ROOT}}", str(project_root))

    # Write temporary ISS file
    temp_iss.write_text(content)
    return temp_iss


def run_inno_setup(iss_file, version, build_number):
    """Runs Inno Setup Compiler with the specified ISS file."""
    if platform.system() != "Windows":
        print("Inno Setup is Windows-only, skipping...")
        return

    # Prepare ISS file from template
    temp_iss = prepare_inno_setup_template(iss_file, version)

    inno_setup_cmd = [
        "ISCC.exe",
        f"/DBuildNumber={build_number}",
        str(temp_iss),
    ]

    try:
        subprocess.run(inno_setup_cmd, check=True, capture_output=True, text=True)
        print(f"Installer created with version {version}")
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        print("Skipping installer creation...")
    except FileNotFoundError:
        print("Inno Setup not found, skipping installer creation...")
    finally:
        # Cleanup temp directory
        if temp_iss.parent.exists():
            shutil.rmtree(temp_iss.parent)


def get_platform_executable_extension():
    """Get the appropriate executable extension for the current platform."""
    if platform.system() == "Windows":
        return ".exe"
    return ""


def get_platform_separator():
    """Get the appropriate path separator for PyInstaller add-data."""
    if platform.system() == "Windows":
        return ";"
    return ":"


# --- Configuration ---
NAME = "ACC"
BUILD_NUMBER = os.environ.get("BUILD_NUMBER", "local")
today = datetime.now(UTC).date()
DATE = today.strftime("%Y%m%d")

print(f"Building {NAME} version {VERSION}")
print(f"Build number: {BUILD_NUMBER}")
print(f"Build date: {DATE}")

# Create build_info.json
build_info = {
    "version": VERSION,
    "build_number": BUILD_NUMBER,
    "build_date": DATE,
    "build_year": datetime.now(UTC).year,
    "platform": platform.system().lower(),
}
with open("build_info.json", "w") as f:
    json.dump(build_info, f, indent=2)
print("Created build_info.json")

OUTPUT_DIR = "dist"
# No icon for now - can be added later
# ICON = "images/acc_icon.png"
# --- End Configuration ---

# PyInstaller arguments
exe_extension = get_platform_executable_extension()
sep = get_platform_separator()

pyinstaller_args = [
    "--clean",
    "--noconfirm",
    "--onedir",  # Create one-directory bundle
    "--windowed",  # Hide console window
    "--name=ACC",
    f"--add-data=data{sep}data",  # Include data directory
    f"--add-data=build_info.json{sep}.",  # Include build info
    "acc_gui.py",  # Main script
]

# Add icon if it exists
# if os.path.exists(ICON):
#     pyinstaller_args.append(f"--icon={ICON}")

print("\n=== Running PyInstaller ===")
print(f"Command: pyinstaller {' '.join(pyinstaller_args)}")
run_pyinstaller(pyinstaller_args)

# Platform-specific packaging
if platform.system() == "Windows":
    print("\n=== Creating Windows Installer ===")
    iss_file = "InnoSetup/ACC.iss.template"
    if os.path.exists(iss_file):
        run_inno_setup(iss_file, VERSION, BUILD_NUMBER)
    else:
        print(f"InnoSetup template not found: {iss_file}")
        print("Skipping installer creation.")
        print("Creating portable ZIP instead...")
        # Create portable ZIP
        zip_name = f"ACC-Windows-Portable-v{VERSION}-build{BUILD_NUMBER}"
        shutil.make_archive(zip_name, "zip", "dist/ACC")
        print(f"Created {zip_name}.zip")

elif platform.system() == "Darwin":
    print("\n=== macOS build completed ===")
    print("Use create-dmg or other tools to package as DMG")

elif platform.system() == "Linux":
    print("\n=== Linux build completed ===")
    print("Use packaging/linux/create_appimage.sh to create AppImage")

print("\n=== Build Complete ===")
print("Executable location: dist/ACC/")
