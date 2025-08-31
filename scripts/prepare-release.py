#!/usr/bin/env python3
"""
RadioBridge Release Preparation Script.

This script helps prepare releases by validating version consistency,
running tests, and providing guidance for release workflow.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple


def run_command(cmd: list[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_current_version() -> Optional[str]:
    """Extract current version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    try:
        with open(pyproject_path, "r") as f:
            content = f.read()

        match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")

    return None


def get_init_version() -> Optional[str]:
    """Extract version from __init__.py."""
    init_path = Path(__file__).parent.parent / "src" / "radiobridge" / "__init__.py"

    try:
        with open(init_path, "r") as f:
            content = f.read()

        match = re.search(r'^__version__ = "([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"❌ Error reading __init__.py: {e}")

    return None


def check_git_status() -> bool:
    """Check if git working directory is clean."""
    exit_code, stdout, stderr = run_command(["git", "status", "--porcelain"])

    if exit_code != 0:
        print(f"❌ Git status check failed: {stderr}")
        return False

    if stdout.strip():
        print("❌ Git working directory is not clean:")
        print(stdout)
        return False

    return True


def check_git_branch() -> Tuple[bool, str]:
    """Check current git branch."""
    exit_code, stdout, stderr = run_command(["git", "branch", "--show-current"])

    if exit_code != 0:
        print(f"❌ Git branch check failed: {stderr}")
        return False, ""

    branch = stdout.strip()
    return True, branch


def run_tests() -> bool:
    """Run the test suite."""
    print("🧪 Running test suite...")

    # Check if pytest is available
    exit_code, _, _ = run_command(["python", "-m", "pytest", "--version"])
    if exit_code != 0:
        print("❌ pytest not available, installing...")
        exit_code, _, stderr = run_command(["pip", "install", "pytest", "pytest-cov"])
        if exit_code != 0:
            print(f"❌ Failed to install pytest: {stderr}")
            return False

    # Run tests
    exit_code, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "pytest",
            "--cov=radiobridge",
            "--cov-report=term-missing",
            "-v",
        ]
    )

    if exit_code != 0:
        print("❌ Tests failed:")
        print(stderr)
        return False

    print("✅ All tests passed!")
    return True


def check_code_quality() -> bool:
    """Check code formatting and linting."""
    print("🎨 Checking code quality...")

    # Check Black formatting
    exit_code, _, stderr = run_command(["black", "--check", "src/", "tests/"])
    if exit_code != 0:
        print("❌ Code formatting check failed:")
        print("Run: black src/ tests/")
        return False

    # Check flake8 linting
    exit_code, _, stderr = run_command(
        [
            "flake8",
            "src/",
            "tests/",
            "--count",
            "--select=E9,F63,F7,F82",
            "--show-source",
            "--statistics",
        ]
    )
    if exit_code != 0:
        print("❌ Linting check failed:")
        print(stderr)
        return False

    print("✅ Code quality checks passed!")
    return True


def build_package() -> bool:
    """Build the package and validate it."""
    print("📦 Building package...")

    # Clean previous builds
    for path in ["dist", "build"]:
        if Path(path).exists():
            run_command(["rm", "-rf", path])

    # Build package
    exit_code, stdout, stderr = run_command(["python", "-m", "build"])
    if exit_code != 0:
        print(f"❌ Package build failed: {stderr}")
        return False

    # Validate with twine
    exit_code, _, stderr = run_command(["python", "-m", "twine", "check", "dist/*"])
    if exit_code != 0:
        print(f"❌ Package validation failed: {stderr}")
        return False

    print("✅ Package built and validated successfully!")
    return True


def main():
    """Run the main release preparation workflow."""
    print("🚀 RadioBridge Release Preparation")
    print("=" * 40)

    # Change to project root
    os.chdir(Path(__file__).parent.parent)

    # Check version consistency
    print("🔍 Checking version consistency...")
    pyproject_version = get_current_version()
    init_version = get_init_version()

    if not pyproject_version:
        print("❌ Could not read version from pyproject.toml")
        sys.exit(1)

    if not init_version:
        print("❌ Could not read version from __init__.py")
        sys.exit(1)

    if pyproject_version != init_version:
        print("❌ Version mismatch:")
        print(f"   pyproject.toml: {pyproject_version}")
        print(f"   __init__.py: {init_version}")
        sys.exit(1)

    print(f"✅ Version consistency check passed: {pyproject_version}")

    # Check git status
    print("🔍 Checking git status...")
    if not check_git_status():
        print("❌ Please commit or stash your changes before preparing a release")
        sys.exit(1)

    # Check git branch
    success, branch = check_git_branch()
    if not success:
        sys.exit(1)

    if branch != "main":
        print(f"⚠️  You are on branch '{branch}', not 'main'")
        response = input("Do you want to continue? (y/N): ").lower()
        if response != "y":
            print("❌ Aborted - switch to main branch for releases")
            sys.exit(1)

    print(f"✅ Git status check passed (branch: {branch})")

    # Run tests
    if not run_tests():
        sys.exit(1)

    # Check code quality
    if not check_code_quality():
        sys.exit(1)

    # Build and validate package
    if not build_package():
        sys.exit(1)

    # Success summary
    print("\n🎉 Release preparation completed successfully!")
    print("=" * 50)
    print("📋 Release Summary:")
    print(f"   Version: {pyproject_version}")
    print(f"   Branch: {branch}")
    print("   Tests: ✅ Passed")
    print("   Code Quality: ✅ Passed")
    print("   Package Build: ✅ Passed")
    print()
    print("🚀 Next Steps:")
    print(
        "   1. Use GitHub Actions 'Version Bump & Changelog' workflow to create release"
    )
    print("   2. Or manually create and push a version tag:")
    print(f"      git tag -a v{pyproject_version} -m 'Release {pyproject_version}'")
    print(f"      git push origin v{pyproject_version}")
    print()
    print("   The release workflow will automatically:")
    print("   - Create GitHub release")
    print("   - Publish to PyPI")
    print("   - Validate the release")


if __name__ == "__main__":
    main()
