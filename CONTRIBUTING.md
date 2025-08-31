# Contributing to RadioBridge 🤝

**Thank you for your interest in contributing to RadioBridge!** This project thrives on community contributions and we welcome all forms of participation - from bug reports to code contributions to documentation improvements.

*RadioBridge is built by the amateur radio community, for the amateur radio community.*

## 🚀 Quick Start for Contributors

1. **⭐ Star the repository** to show your support
2. **🐛 Check existing issues** to see what needs help
3. **💬 Join discussions** to share ideas and get guidance
4. **🔧 Set up development environment** following our guide below
5. **🎯 Pick an issue** labeled "good first issue" for beginners

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Types of Contributions](#-types-of-contributions)
- [Development Setup](#-development-setup)
- [Making Changes](#-making-changes)
- [Testing](#-testing)
- [Submitting Changes](#-submitting-changes)
- [Adding Radio Support](#-adding-radio-support)
- [Community](#-community)

## 🤝 Code of Conduct

RadioBridge follows the amateur radio community's tradition of respect, helpfulness, and technical excellence. We expect all contributors to:

- **Be Respectful**: Treat all community members with courtesy and respect
- **Be Helpful**: Share knowledge and assist others when possible
- **Be Technical**: Focus on technical merit and constructive feedback
- **Be Patient**: Remember that volunteers contribute in their spare time
- **Follow License Terms**: Respect open source licensing and attribution

*If you experience or witness unacceptable behavior, please contact craig@ko6gxm.com.*

## 🎯 Getting Started

### Prerequisites

- **Python 3.9+** installed on your system
- **Git** for version control
- **GitHub account** for submitting contributions
- Basic familiarity with **amateur radio concepts** (helpful but not required)

### First-Time Contributors

**New to open source?** We're here to help! Look for issues labeled:
- `good first issue` - Perfect for beginners
- `documentation` - Help improve our docs
- `help wanted` - Community input needed

**Questions?** Don't hesitate to:
- Comment on issues asking for clarification
- Start a [Discussion](https://github.com/ko6gxm/radiobridge/discussions)
- Email craig@ko6gxm.com directly

## 🛠️ Types of Contributions

### 🐛 Bug Reports
Found a bug? Help us fix it!

**Before submitting:**
- Search existing issues to avoid duplicates
- Test with the latest version
- Gather debugging information

**When reporting:**
- Use the bug report template
- Include error messages and logs
- Describe your environment (OS, Python version, etc.)
- Provide steps to reproduce

### ✨ Feature Requests
Have an idea for improvement?

**Consider:**
- Is this useful for multiple users?
- Does it align with the project's goals?
- Can it be implemented maintainably?

**When requesting:**
- Use the feature request template
- Describe the problem you're solving
- Provide examples and use cases
- Consider implementation complexity

### 📖 Documentation
Documentation is crucial for user adoption!

**Areas that need help:**
- Real-world usage examples
- Troubleshooting guides
- API documentation
- Tutorial content

### 🔧 Code Contributions
Ready to write code? Awesome!

**Focus areas:**
- New radio formatter support
- Performance improvements
- Bug fixes
- Testing improvements

## 🏗️ Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/radiobridge.git
cd radiobridge
```

### 2. Set Up Environment

```bash
# Install pipenv if not already installed
pip install pipenv

# Create virtual environment and install dependencies
pipenv install --dev

# Install in development mode
pipenv run pip install -e .

# Install pre-commit hooks
pipenv run pre-commit install
```

### 3. Verify Setup

```bash
# Run tests to ensure everything works
pipenv run pytest

# Try the CLI
pipenv run rb --help

# Verify code formatting
pipenv run black --check .
```

## 🔄 Making Changes

### Development Workflow

1. **Create a branch** for your changes
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes** thoroughly
   ```bash
   pipenv run pytest
   pipenv run black .
   pipenv run flake8
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "Add support for Yaesu FT-991A"
   ```

### Coding Standards

#### Python Code Style
- **Black formatting**: Run `black .` before committing
- **Import ordering**: Use `isort` for consistent imports
- **Line length**: 88 characters maximum
- **Type hints**: Use type hints for new functions

#### Documentation
- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain "why" not "what"
- **README updates**: Update documentation for new features

#### Commit Messages
Use conventional commit format:
```
type(scope): short description

longer explanation if needed

Fixes #123
```

**Types:**
- `feat`: new features
- `fix`: bug fixes
- `docs`: documentation changes
- `test`: adding/updating tests
- `refactor`: code refactoring

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage (default behavior)
pipenv run pytest

# Run tests with detailed coverage report
pipenv run pytest --cov-report=html
open htmlcov/index.html  # View detailed coverage in browser

# Run specific test categories
pipenv run pytest -m unit          # Unit tests only
pipenv run pytest -m integration   # Integration tests only
pipenv run pytest -m "not slow"    # Skip slow tests

# Run tests for specific functionality
pipenv run pytest tests/test_radios.py              # Radio formatters
pipenv run pytest tests/test_downloader.py          # Data downloading
pipenv run pytest tests/test_cli.py                 # CLI interface

# Performance testing with larger datasets
pipenv run pytest --benchmark-only  # If benchmark tests exist
```

**Coverage Goals:**
- **Critical modules**: Aim for 90%+ coverage
- **User-facing functionality**: 100% coverage preferred
- **Error handling**: Test both success and failure paths
- **Integration points**: Mock external dependencies

**Current Coverage Status:**
- **Overall**: 69% (focused on critical code paths)
- **CLI Module**: 81% (high user impact)
- **Radio Formatters**: 80%+ average (core functionality)
- **Download Logic**: 75%+ (network operations tested with mocks)

### Writing Tests

**Test Structure:**
- `tests/test_*.py` - Unit tests
- `tests/fixtures/` - Test data files
- `tests/integration/` - Integration tests

**Guidelines:**
- Test both success and error cases
- Use descriptive test names
- Mock external dependencies (HTTP calls)
- Include edge cases and boundary conditions

**Example Test:**
```python
def test_frequency_validation():
    """Test that invalid frequencies are rejected."""
    formatter = get_radio_formatter("anytone-878")

    invalid_data = pd.DataFrame({
        "frequency": ["invalid", "", "999.999"]
    })

    with pytest.raises(ValueError, match="Invalid frequency"):
        formatter.format(invalid_data)
```

## 📤 Submitting Changes

### Pull Request Process

1. **Ensure your branch is up to date**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**
   - Use the PR template
   - Link related issues
   - Describe what you changed and why
   - Include testing information

### Pull Request Requirements

**Before submitting:**
- ✅ All tests pass
- ✅ Code is formatted with Black
- ✅ No linting errors
- ✅ Documentation updated if needed
- ✅ Commit messages follow conventions

**PR Description should include:**
- Summary of changes
- Testing performed
- Related issues (use "Fixes #123")
- Screenshots if UI changes
- Breaking changes if any

## 📡 Adding Radio Support

One of the most valuable contributions is adding support for new radio models!

### Step-by-Step Guide

#### 1. Create Formatter Class

```python
# src/radiobridge/radios/my_radio.py
from typing import List
import pandas as pd
from .base import BaseRadioFormatter
from ..logging_config import get_logger

class MyRadioFormatter(BaseRadioFormatter):
    """Formatter for My Radio Model XYZ."""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.logger.info("Initialized My Radio formatter")

    @property
    def radio_name(self) -> str:
        return "My Radio XYZ"

    @property
    def description(self) -> str:
        return "Dual-band handheld with digital modes"

    @property
    def required_columns(self) -> List[str]:
        return ["frequency"]  # Minimum required fields

    @property
    def output_columns(self) -> List[str]:
        return ["Channel", "Frequency", "Name", "Tone"]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format data for My Radio."""
        self.validate_input(data)

        formatted_rows = []
        for idx, row in data.iterrows():
            # Your formatting logic here
            formatted_row = {
                "Channel": idx + 1,
                "Frequency": f"{float(row['frequency']):.4f}",
                "Name": row.get('callsign', f'RPT{idx+1}'),
                "Tone": row.get('tone', '88.5')
            }
            formatted_rows.append(formatted_row)

        return pd.DataFrame(formatted_rows)
```

#### 2. Register the Formatter

```python
# src/radiobridge/radios/__init__.py
from .my_radio import MyRadioFormatter

# Add to the registry
RADIO_FORMATTERS = {
    # ... existing formatters ...
    "my-radio": MyRadioFormatter,
}
```

#### 3. Add Tests

```python
# tests/test_my_radio.py
import pytest
import pandas as pd
from radiobridge.radios.my_radio import MyRadioFormatter

class TestMyRadioFormatter:
    def setup_method(self):
        self.formatter = MyRadioFormatter()
        self.sample_data = pd.DataFrame({
            "frequency": ["146.520", "147.000"],
            "callsign": ["W6ABC", "K6XYZ"],
            "tone": ["88.5", "100.0"]
        })

    def test_format_basic_data(self):
        result = self.formatter.format(self.sample_data)

        assert len(result) == 2
        assert "Channel" in result.columns
        assert result.iloc[0]["Frequency"] == "146.5200"
```

#### 4. Update Documentation

Add your radio to:
- README.md supported radios table
- Any relevant documentation
- CLI help text updates

### Radio-Specific Considerations

**CSV Format Requirements:**
- What column names does the radio software expect?
- Are there required fields or default values?
- Any special formatting (frequency decimals, tone formats)?

**Data Validation:**
- Frequency ranges supported by the radio
- Valid tone/DCS codes
- Power level restrictions

**Testing:**
- Test with real RepeaterBook data
- Verify imports work in radio software
- Test edge cases (missing data, unusual values)

## 🌟 Recognition

Contributors are recognized in several ways:

### Hall of Fame
- **Major Contributors**: Listed in README.md
- **First-time Contributors**: Mentioned in release notes
- **Radio Supporters**: Credited for each radio formatter

### Community Recognition
- Shoutouts on [ko6gxm.com](https://ko6gxm.com)
- Feature announcements highlighting contributors
- Amateur radio community forums and social media

*Your contributions make RadioBridge better for thousands of amateur radio operators worldwide!*

## 💬 Community

### Getting Help

- **📖 Documentation**: Start with README.md and inline help
- **💬 Discussions**: [GitHub Discussions](https://github.com/ko6gxm/radiobridge/discussions)
- **🐛 Issues**: [GitHub Issues](https://github.com/ko6gxm/radiobridge/issues) for bugs
- **📧 Direct Contact**: craig@ko6gxm.com for urgent matters

### Stay Connected

- **🌐 Website**: [ko6gxm.com](https://ko6gxm.com) for tutorials and updates
- **📻 Amateur Radio**: Find KO6GXM on the airwaves
- **📱 Social**: Follow amateur radio and open source communities

### Project Communication

**Response Times:**
- Issues and PRs: Usually within 24-48 hours
- Discussions: Check regularly, community-driven
- Email: Within 24 hours for urgent matters

**Priority:**
1. Security issues (immediate)
2. Critical bugs affecting all users
3. Feature requests and enhancements
4. Documentation improvements

---

<div align="center">

**Thank you for contributing to RadioBridge! 🎉**

*Every contribution, no matter how small, makes a difference in the amateur radio community.*

[![Contributors](https://img.shields.io/github/contributors/ko6gxm/radiobridge)](https://github.com/ko6gxm/radiobridge/graphs/contributors)
[![Amateur Radio](https://img.shields.io/badge/amateur%20radio-community-red.svg)](https://ko6gxm.com)

*73 and happy coding!*
*Craig - KO6GXM*

</div>
