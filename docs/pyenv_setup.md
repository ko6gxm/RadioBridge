# Python Environment Management with pyenv

A comprehensive guide for setting up and using pyenv to manage Python versions for the RadioBridge project.

## Table of Contents

1. [Introduction to pyenv](#introduction-to-pyenv)
2. [Installing pyenv on macOS](#installing-pyenv-on-macos)
3. [Basic pyenv Usage](#basic-pyenv-usage)
4. [Understanding pipenv](#understanding-pipenv)
5. [Setting up RadioBridge with pyenv + pipenv](#setting-up-radiobridge-with-pyenv--pipenv)
6. [Complete Workflow](#complete-workflow)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Introduction to pyenv

### What is pyenv?

**pyenv** is a simple Python version management tool that lets you easily switch between multiple versions of Python on your system. Think of it as a smart way to organize different Python installations without conflicts.

### Why do you need pyenv?

#### The Problem
- macOS comes with Python pre-installed, but it's often outdated
- Different projects require different Python versions
- Installing packages globally can cause conflicts
- System Python should not be modified (it may break macOS)

#### The Solution
```
┌─────────────────────────────────────────────────┐
│                    pyenv                        │
├─────────────────────────────────────────────────┤
│ Python 3.9.18    │ Python 3.11.9  │ Python 3.13.7 │
│                  │                 │               │
│ ├─ project-a/    │ ├─ project-b/   │ ├─ RadioBridge/ │
│                  │                 │               │
└─────────────────────────────────────────────────┘
            ↓              ↓                ↓
     Uses Python 3.9   Uses 3.11      Uses 3.13.7
```

### How pyenv works with pipenv

- **pyenv** manages Python versions (the interpreters)
- **pipenv** manages project dependencies and virtual environments
- Together, they provide complete project isolation

## Installing pyenv on macOS

### Prerequisites

First, ensure you have Homebrew installed. If not, install it:

```bash path=null start=null
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 1: Install pyenv

```bash path=null start=null
# Update Homebrew
brew update

# Install pyenv and pyenv-virtualenv
brew install pyenv pyenv-virtualenv
```

### Step 2: Configure your shell

Add pyenv to your shell configuration. For **zsh** (default on macOS):

```bash path=null start=null
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
```

For **bash** users:
```bash path=null start=null
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
```

### Step 3: Restart your shell

```bash path=null start=null
# Restart your terminal or reload your shell configuration
exec "$SHELL"
```

### Step 4: Verify installation

```bash path=null start=null
pyenv --version
# Should output something like: pyenv 2.x.x
```

## Basic pyenv Usage

### Essential Commands

#### List available Python versions
```bash path=null start=null
pyenv install --list
# Shows all available Python versions you can install
```

#### Install a specific Python version
```bash path=null start=null
pyenv install 3.13.7
# Downloads, compiles, and installs Python 3.13.7
```

#### See installed Python versions
```bash path=null start=null
pyenv versions
# * system (set by /Users/craig/.pyenv/version)
#   3.13.7
```

#### Set global Python version (system-wide default)
```bash path=null start=null
pyenv global 3.13.7
# Sets Python 3.13.7 as your default Python
```

#### Set local Python version (project-specific)
```bash path=null start=null
cd /path/to/your/project
pyenv local 3.13.7
# Creates .python-version file in current directory
```

#### Check current Python version
```bash path=null start=null
python --version
# Shows the active Python version
```

### Understanding pyenv "shims"

When you run `python`, pyenv intercepts the command and routes it to the correct Python version based on:

1. **PYENV_VERSION** environment variable (if set)
2. **Local** `.python-version` file (current directory)
3. **Global** version (set with `pyenv global`)
4. **System** Python (fallback)

## Understanding pipenv

### What is pipenv?

**pipenv** is a modern dependency management tool that combines the functionality of pip (package installer) and virtualenv (virtual environment creator) into one easy-to-use command. Think of it as the missing piece that makes Python project management simple and reliable.

### Why pipenv over pip + virtualenv?

#### Traditional Approach Problems
```bash path=null start=null
# Old way - many manual steps, error-prone
virtualenv venv
source venv/bin/activate
pip install requests pandas
pip freeze > requirements.txt
# Later: pip install -r requirements.txt
# Always need to remember to activate venv
```

#### The pipenv Solution
```bash path=null start=null
# Modern way - simple, automatic
pipenv install requests pandas
pipenv run python my_script.py
# That's it! Virtual environment handled automatically
```

### Key pipenv Advantages

1. **Automatic virtual environment management** - Creates and manages virtual environments automatically
2. **Deterministic builds** - Uses lock files to ensure identical environments
3. **Security scanning** - Built-in vulnerability checking
4. **Development vs production dependencies** - Separate dev and production packages
5. **Simplified workflow** - One tool instead of pip + virtualenv + requirements.txt

### How pipenv Works with pyenv

```
┌─────────────────────────────────────────────────┐
│ pyenv: Manages Python interpreters             │
├─────────────────────────────────────────────────┤
│ Python 3.13.7 ← Selected by pyenv              │
│     ↓                                           │
│ ┌─────────────────────────────────────────────┐ │
│ │ pipenv: Manages dependencies + virtualenv   │ │
│ │                                             │ │
│ │ Virtual Environment                         │ │
│ │ ├─ requests==2.31.0                        │ │
│ │ ├─ pandas==2.1.0                           │ │
│ │ ├─ RadioBridge (editable install)        │ │
│ │ └─ dev dependencies (pytest, black, etc.)  │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Installing pipenv

#### Method 1: Using pip (recommended after pyenv setup)
```bash path=null start=null
# After setting up pyenv and activating the right Python version
pip install --upgrade pipenv
```

#### Method 2: Using Homebrew (system-wide)
```bash path=null start=null
brew install pipenv
```

#### Method 3: Using curl (if pip isn't available)
```bash path=null start=null
curl https://raw.githubusercontent.com/pypa/pipenv/master/get-pipenv.py | python
```

#### Verify Installation
```bash path=null start=null
pipenv --version
# Should output: pipenv, version 2023.x.x
```

### Essential pipenv Commands

#### Project Initialization
```bash path=null start=null
# Initialize a new pipenv project (creates Pipfile)
pipenv --python 3.13.7

# Or let pipenv detect Python version automatically
pipenv install
```

#### Installing Packages
```bash path=null start=null
# Install production dependencies
pipenv install requests pandas click

# Install development dependencies
pipenv install pytest black flake8 --dev

# Install from requirements.txt (migration)
pipenv install -r requirements.txt

# Install all dependencies from existing Pipfile
pipenv install

# Install including development dependencies
pipenv install --dev
```

#### Running Commands
```bash path=null start=null
# Run a command in the virtual environment
pipenv run python script.py
pipenv run pytest
pipenv run black .

# Activate the virtual environment shell
pipenv shell
# Now you're inside the virtual environment
python script.py  # No need for 'pipenv run'
exit  # Leave the shell
```

#### Environment Management
```bash path=null start=null
# Show virtual environment information
pipenv --venv
# Output: /Users/craig/.local/share/virtualenvs/RadioBridge-xyz123

# Show project location
pipenv --where
# Output: /Users/craig/source_code/RadioBridge

# Show Python interpreter location
pipenv --py
# Output: /Users/craig/.local/share/virtualenvs/RadioBridge-xyz123/bin/python
```

#### Dependency Management
```bash path=null start=null
# Show dependency graph
pipenv graph

# Show installed packages
pipenv run pip list

# Update all packages
pipenv update

# Update specific package
pipenv update requests

# Check for security vulnerabilities
pipenv check
```

#### Lock File Management
```bash path=null start=null
# Generate/update Pipfile.lock
pipenv lock

# Install from lock file (production deployment)
pipenv sync

# Install from lock file including dev dependencies
pipenv sync --dev
```

#### Cleanup Commands
```bash path=null start=null
# Remove unused packages
pipenv clean

# Remove virtual environment (keeps Pipfile/Pipfile.lock)
pipenv --rm

# Uninstall packages
pipenv uninstall requests

# Uninstall dev packages
pipenv uninstall pytest --dev
```

### Understanding Pipfile and Pipfile.lock

#### Pipfile (Human-readable, editable)

The `Pipfile` is your project's dependency specification:

```toml path=/Users/craig/source_code/RadioBridge/Pipfile start=1
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
click = "*"
requests = "*"
pandas = "*"
python-dateutil = "*"
beautifulsoup4 = "*"
lxml = "*"

[dev-packages]
black = "*"
flake8 = "*"
pytest = "*"
pre-commit = "*"
ipython = "*"
responses = "*"

[requires]
python_version = "3.13"
python_full_version = "3.13.7"
```

**Key sections:**
- `[packages]`: Production dependencies
- `[dev-packages]`: Development dependencies (testing, linting, etc.)
- `[requires]`: Python version requirements
- `[[source]]`: Package repositories (usually PyPI)

#### Pipfile.lock (Machine-generated, exact versions)

The `Pipfile.lock` contains exact versions and hashes for reproducible builds:

```json path=null start=null
{
    "_meta": {
        "hash": {...},
        "pipfile-spec": 6,
        "requires": {
            "python_full_version": "3.13.7",
            "python_version": "3.13"
        }
    },
    "default": {
        "requests": {
            "hashes": ["sha256:abc123..."],
            "index": "pypi",
            "version": "==2.31.0"
        }
    },
    "develop": {
        "pytest": {
            "hashes": ["sha256:def456..."],
            "index": "pypi",
            "version": "==7.4.2"
        }
    }
}
```

**Key differences:**
- **Pipfile**: Flexible version specifiers (`"*"`, `">= 2.0"`, `"~=1.4.0"`)
- **Pipfile.lock**: Exact versions (`"==2.31.0"`) with security hashes
- **Pipfile**: Edited by developers
- **Pipfile.lock**: Generated by `pipenv lock`, committed to version control

### Pipenv Workflow for RadioBridge

#### Initial Setup (First Time)
```bash path=null start=null
# 1. Clone the repository
git clone <repository-url>
cd RadioBridge

# 2. Ensure correct Python version is active
pyenv local 3.13.7
python --version  # Verify: Python 3.13.7

# 3. Install pipenv if not already installed
pip install --upgrade pipenv

# 4. Install all dependencies (production + development)
pipenv install --dev
# This creates a virtual environment and installs:
# - click, requests, pandas, python-dateutil, beautifulsoup4, lxml
# - black, flake8, pytest, pre-commit, ipython, responses

# 5. Install RadioBridge in development mode
pipenv run pip install -e .
# This makes the 'radiobridge' command available
```

#### Verify Installation
```bash path=null start=null
# Test the CLI tool
pipenv run radiobridge --help
# Should display help message

# Test Python environment
pipenv run python -c "import radiobridge; print('Success!')"

# Check installed packages
pipenv graph
# Shows dependency tree
```

#### Daily Development Workflow
```bash path=null start=null
# Navigate to project
cd RadioBridge

# Option 1: Use 'pipenv run' for individual commands
pipenv run radiobridge list-radios
pipenv run radiobridge download --state CA --output ca_repeaters.csv
pipenv run pytest
pipenv run black src/ tests/

# Option 2: Enter the virtual environment shell
pipenv shell
# Now you're inside the virtual environment
radiobridge list-radios
python -c "import requests; print(requests.__version__)"
pytest -v
exit  # Leave the virtual environment shell
```

#### Adding New Dependencies
```bash path=null start=null
# Add production dependency
pipenv install new-package

# Add development dependency
pipenv install new-dev-package --dev

# Update lock file after adding packages
pipenv lock

# Commit both Pipfile and Pipfile.lock
git add Pipfile Pipfile.lock
git commit -m "Add new-package dependency"
```

#### Production Deployment
```bash path=null start=null
# Install only production dependencies (no dev packages)
pipenv sync

# Or explicitly install from lock file
pipenv install --ignore-pipfile
```

## Setting up RadioBridge with pyenv + pipenv

### Step 1: Install the required Python version

The RadioBridge project requires Python 3.13.7 (as specified in the Pipfile):

```bash path=null start=null
# Install Python 3.13.7 (this may take several minutes)
pyenv install 3.13.7
```

**Note**: If you encounter build errors, see the [Troubleshooting](#troubleshooting) section.

### Step 2: Navigate to the project and set local Python version

```bash path=null start=null
cd /path/to/RadioBridge
pyenv local 3.13.7
```

This creates a `.python-version` file containing `3.13.7`. Now whenever you're in this directory, pyenv will automatically use Python 3.13.7.

### Step 3: Verify Python version

```bash path=null start=null
python --version
# Should output: Python 3.13.7

which python
# Should output: /Users/craig/.pyenv/shims/python
```

### Step 4: Install pipenv

Install pipenv for the current Python version:

```bash path=null start=null
pip install --upgrade pipenv
```

Alternatively, you can install pipenv globally with Homebrew:
```bash path=null start=null
brew install pipenv
```

### Step 5: Install project dependencies

```bash path=null start=null
# Install all dependencies (including dev dependencies)
pipenv install --dev
```

This will:
- Use the Python version specified by pyenv (3.13.7)
- Create a virtual environment
- Install all dependencies from Pipfile

### Step 6: Install RadioBridge in development mode

```bash path=null start=null
pipenv run pip install -e .
```

This installs the `radiobridge` command-line tool in "editable" mode, meaning changes to the source code are immediately reflected.

### Step 7: Test the installation

```bash path=null start=null
pipenv run radiobridge --help
# Should display the help message for radiobridge
```

## Complete Workflow

Here's the complete process for setting up RadioBridge on a fresh macOS system:

### First-time setup (do once)

```bash path=null start=null
# 1. Install pyenv (if not already installed)
brew install pyenv pyenv-virtualenv

# 2. Configure shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc

# 3. Restart shell
exec "$SHELL"

# 4. Install required Python version
pyenv install 3.13.7
```

### Project setup (do for each new clone)

```bash path=null start=null
# 1. Clone the repository
git clone <repository-url>
cd RadioBridge

# 2. Set local Python version (reads .python-version if it exists)
pyenv local 3.13.7

# 3. Install pipenv if needed
pip install --upgrade pipenv

# 4. Install dependencies
pipenv install --dev

# 5. Install the CLI tool
pipenv run pip install -e .

# 6. Test it works
pipenv run radiobridge --help
```

### Daily usage

```bash path=null start=null
# Navigate to your project
cd RadioBridge

# Python version is automatically set by pyenv
python --version  # Should show 3.13.7

# Use the tool
pipenv run radiobridge list-radios
pipenv run radiobridge download --state CA --output ca_repeaters.csv

# Run tests
pipenv run pytest

# Format code
pipenv run black src/ tests/
```

## Troubleshooting

### Common Error: "pyenv: command not found"

**Problem**: Shell can't find pyenv command.

**Solution**:
1. Verify pyenv is installed: `brew list | grep pyenv`
2. Make sure shell configuration is correct (see [Installation](#step-2-configure-your-shell))
3. Restart your terminal: `exec "$SHELL"`

### Common Error: Python build fails

**Problem**: `pyenv install 3.13.7` fails with compilation errors.

**Solution**:
```bash path=null start=null
# Install build dependencies
brew install openssl readline sqlite3 xz zlib

# Set environment variables and retry
export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix readline)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix readline)/include"

pyenv install 3.13.7
```

### Common Error: pipenv uses wrong Python version

**Problem**: `pipenv install` creates environment with system Python instead of pyenv Python.

**Solution**:
1. Verify pyenv is active: `python --version`
2. Remove existing environment: `pipenv --rm`
3. Recreate environment: `pipenv install --dev`
4. Or explicitly specify Python: `pipenv --python $(pyenv which python) install --dev`

### Common Error: "No module named radiobridge"

**Problem**: CLI command not found after installation.

**Solution**:
1. Make sure you installed in development mode: `pipenv run pip install -e .`
2. Use pipenv run: `pipenv run radiobridge --help`
3. Verify installation: `pipenv run pip list | grep radiobridge`

### Python version compatibility

If Python 3.13.7 won't compile, you can use any version 3.9 or higher:

```bash path=null start=null
# Install an alternative version
pyenv install 3.11.9
pyenv local 3.11.9

# Update Pipfile to match if needed
# Then continue with pipenv install --dev
```

### Pipenv-Specific Troubleshooting

#### Common Error: "pipenv: command not found"

**Problem**: pipenv command not available after installation.

**Solution**:
1. Verify installation: `which pipenv`
2. If using pyenv Python: `pip install --upgrade pipenv`
3. If using Homebrew: `brew install pipenv`
4. Restart shell: `exec "$SHELL"`

#### Common Error: Virtual environment in wrong location

**Problem**: Can't find where pipenv created the virtual environment.

**Solution**:
```bash path=null start=null
# Show virtual environment path
pipenv --venv

# Show Python interpreter path
pipenv --py

# Show project root
pipenv --where
```

#### Common Error: Pipfile.lock conflicts

**Problem**: `pipenv install` fails due to lock file conflicts.

**Solution**:
```bash path=null start=null
# Option 1: Regenerate lock file
pipenv lock

# Option 2: Ignore lock file and install from Pipfile
pipenv install --skip-lock

# Option 3: Force recreation
pipenv --rm
pipenv install --dev
```

#### Common Error: "No matching distribution found"

**Problem**: Package can't be installed for the current Python version.

**Solution**:
1. Check Python version: `python --version`
2. Verify package supports your Python version
3. Try alternative version: `pipenv install "package>=1.0,<2.0"`

#### Common Error: Virtual environment activation issues

**Problem**: `pipenv shell` doesn't work or shows wrong Python.

**Solution**:
```bash path=null start=null
# Remove and recreate environment
pipenv --rm
pipenv install --dev

# Explicitly specify Python
pipenv --python $(pyenv which python) install --dev

# Use pipenv run instead of shell
pipenv run python --version
```

#### Common Error: "Warning: Python X was not found on your system"

**Problem**: pipenv can't find the specified Python version.

**Solution**:
1. Ensure Python is installed: `pyenv versions`
2. Set local version: `pyenv local 3.13.7`
3. Verify Python is active: `python --version`
4. Recreate environment: `pipenv --rm && pipenv install --dev`

#### Performance: Slow package installation

**Problem**: `pipenv install` is very slow.

**Solution**:
```bash path=null start=null
# Skip lock file generation during development
pipenv install --skip-lock

# Use pip index directly
pipenv install --index https://pypi.org/simple/

# Generate lock file only when needed
pipenv lock
```

## Best Practices

### 1. Use .python-version files

**Note**: This project has `.python-version` in `.gitignore`, which is common practice since Python version preferences can be developer-specific. However, the project's `Pipfile` specifies `python_version = "3.13"` and `python_full_version = "3.13.7"` for consistency.

The `.python-version` file is still useful locally:
```bash path=null start=null
# This file exists locally but isn't tracked in git
cat .python-version
# 3.13.7
```

### 2. Keep pyenv updated

```bash path=null start=null
# Update pyenv regularly
brew upgrade pyenv
```

### 3. Use specific Python versions

Don't use `3.13` or `3`, always specify the full version like `3.13.7` for reproducibility.

### 4. Cache Python builds

If you work on multiple projects, avoid recompiling:
```bash path=null start=null
# Check if already installed before installing
pyenv install --skip-existing 3.13.7
```

### 5. Document Python requirements

Always specify Python requirements in your project:
- `pyproject.toml`: `requires-python = ">=3.9"`
- `Pipfile`: `python_version = "3.13"`
- `.python-version`: `3.13.7`

### 6. Use pyenv global sparingly

Only set global Python versions for general development. Use `pyenv local` for projects:
```bash path=null start=null
# Good: project-specific
cd myproject && pyenv local 3.13.7

# Use cautiously: affects entire system
pyenv global 3.11.9
```

### 7. Clean up old versions

Periodically remove unused Python versions to save disk space:
```bash path=null start=null
# List installed versions
pyenv versions

# Remove old version
pyenv uninstall 3.10.12
```

### 8. Backup your configuration

Your pyenv configuration lives in `~/.pyenv/`. Consider backing up:
- `~/.pyenv/version` (global version)
- Your shell configuration (`~/.zshrc`)

### 9. pipenv Best Practices

#### Always use pipenv run for consistency
```bash path=null start=null
# Good: Always works, regardless of shell state
pipenv run python script.py
pipenv run pytest

# Okay: But requires remembering to activate/deactivate
pipenv shell
python script.py
exit
```

#### Commit both Pipfile and Pipfile.lock
```bash path=null start=null
# Always commit both files together
git add Pipfile Pipfile.lock
git commit -m "Update dependencies"
```

#### Separate development and production dependencies
```bash path=null start=null
# Production dependencies
pipenv install requests pandas click

# Development dependencies (testing, linting, debugging)
pipenv install pytest black flake8 ipython --dev
```

#### Regular security checks
```bash path=null start=null
# Check for known vulnerabilities
pipenv check

# Update packages regularly
pipenv update
```

#### Use lock files for deployment
```bash path=null start=null
# Development: Install from Pipfile (flexible versions)
pipenv install --dev

# Production: Install from lock file (exact versions)
pipenv sync
```

#### Keep virtual environments clean
```bash path=null start=null
# Remove unused packages
pipenv clean

# Start fresh if needed
pipenv --rm
pipenv install --dev
```

---

## Summary

With pyenv properly set up:

1. **You can manage multiple Python versions** without conflicts
2. **Each project gets its own Python version** automatically
3. **Dependencies are isolated** using pipenv virtual environments
4. **RadioBridge runs consistently** across different machines
5. **Development is reproducible** for all team members

The combination of pyenv + pipenv provides professional-grade Python project management that scales from personal projects to enterprise development.
