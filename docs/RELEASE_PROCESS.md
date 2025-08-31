# Release Process Documentation 🚀

This document describes the automated release system for RadioBridge, including workflows, processes, and troubleshooting.

## Overview

RadioBridge uses a comprehensive automated release system that includes:

- **Version Management**: Automated version bumping with changelog generation
- **Release Validation**: Multi-platform testing and validation
- **Package Distribution**: Automatic publishing to PyPI and GitHub Releases
- **Quality Assurance**: Comprehensive testing across platforms and Python versions

## 🛠️ Release Workflows

### 1. Version Bump & Changelog (`version-bump.yml`)

**Trigger**: Manual workflow dispatch
**Purpose**: Updates version numbers, generates changelog, creates release tag

#### Inputs:
- **version_type**: `major` | `minor` | `patch` | `prerelease`
- **prerelease_type**: `alpha` | `beta` | `rc` (only for prerelease)
- **custom_version**: Override with specific version (optional)

#### Process:
1. Validates current version consistency
2. Calculates new version based on input
3. Updates `pyproject.toml` and `src/radiobridge/__init__.py`
4. Generates changelog entry from git commits
5. Commits changes and creates version tag
6. Automatically triggers release workflow

#### Usage:
```bash
# Via GitHub UI: Actions -> Version Bump & Changelog -> Run workflow
# Select version type and optional parameters
```

### 2. Release (`release.yml`)

**Trigger**: Git tag push (format: `v*`)
**Purpose**: Creates GitHub release and publishes to PyPI

#### Process:
1. **Version Validation**: Ensures consistency between tag and code versions
2. **Build & Test**: Comprehensive testing and package building
3. **GitHub Release**: Creates release with changelog and assets
4. **PyPI Publishing**: Publishes to Test PyPI then production PyPI
5. **Success Notification**: Reports completion status

#### Requirements:
- GitHub secrets: `GITHUB_TOKEN` (automatic)
- PyPI secrets: `PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN`
- Environment: `pypi` (for publishing step)

### 3. Release Validation (`release-validation.yml`)

**Trigger**: Release published OR manual dispatch
**Purpose**: Validates release works correctly across platforms

#### Process:
1. **PyPI Installation Test**: Tests installation across 9 platform/Python combinations
2. **GitHub Release Validation**: Validates release assets and metadata
3. **Functionality Testing**: Tests CLI and core functionality
4. **Report Generation**: Comprehensive validation report

#### Test Matrix:
- **Platforms**: Ubuntu, Windows, macOS
- **Python Versions**: 3.9, 3.11, 3.13
- **Total Combinations**: 9

## 📋 Release Process Steps

### Option A: Automated Release (Recommended)

1. **Ensure Clean State**:
   ```bash
   git checkout main
   git pull origin main
   git status  # Should be clean
   ```

2. **Run Release Preparation** (Optional):
   ```bash
   python scripts/prepare-release.py
   ```

3. **Trigger Version Bump**:
   - Go to GitHub Actions → "Version Bump & Changelog"
   - Click "Run workflow"
   - Select version type (patch/minor/major/prerelease)
   - Click "Run workflow"

4. **Monitor Workflows**:
   - Version bump workflow creates tag
   - Release workflow automatically triggered
   - Validation workflow runs after release

5. **Verify Release**:
   - Check GitHub release page
   - Verify PyPI package: `pip install radiobridge==<version>`
   - Review validation results

### Option B: Manual Release

1. **Prepare Release**:
   ```bash
   python scripts/prepare-release.py
   ```

2. **Update Version** (if needed):
   ```bash
   # Edit pyproject.toml and src/radiobridge/__init__.py
   # Ensure versions match
   ```

3. **Create and Push Tag**:
   ```bash
   git tag -a v0.4.0 -m "Release version 0.4.0"
   git push origin v0.4.0
   ```

4. **Monitor Release Workflow**:
   - Release workflow triggers automatically
   - Check GitHub Actions for progress

## 🔧 Configuration

### GitHub Secrets

Required secrets for full automation:

```
GITHUB_TOKEN        # Automatic, for creating releases
PYPI_API_TOKEN      # PyPI publishing (production)
TEST_PYPI_API_TOKEN # Test PyPI publishing
```

### Environment Setup

The `pypi` environment should be configured with:
- Protection rules (optional)
- Required reviewers (optional)
- Deployment branches: `main` only

### Version Format

Supported version formats:
- **Production**: `1.0.0`, `2.1.3`
- **Prerelease**: `1.0.0alpha1`, `2.1.0beta2`, `1.5.0rc1`

## 🧪 Testing & Validation

### Pre-Release Validation

The `scripts/prepare-release.py` script performs:
- ✅ Version consistency checks
- ✅ Git status validation
- ✅ Test suite execution
- ✅ Code quality checks (Black, Flake8)
- ✅ Package building and validation

### Post-Release Validation

Automatic validation includes:
- ✅ PyPI package installation across platforms
- ✅ CLI functionality testing
- ✅ Core API functionality testing
- ✅ GitHub release asset validation
- ✅ Source distribution validation

### Quality Gates

All releases must pass:
1. **All tests**: 100% test suite success
2. **Code quality**: Black formatting + Flake8 linting
3. **Build validation**: Package builds and validates
4. **Cross-platform**: Works on Ubuntu, Windows, macOS
5. **Multi-Python**: Compatible with Python 3.9, 3.11, 3.13

## 🐛 Troubleshooting

### Common Issues

#### Version Mismatch Errors
**Problem**: Version in `pyproject.toml` doesn't match `__init__.py`
**Solution**:
```bash
# Check versions
grep 'version =' pyproject.toml
grep '__version__' src/radiobridge/__init__.py

# Update manually if needed, then commit
```

#### PyPI Publishing Failures
**Problem**: Package upload to PyPI fails
**Solutions**:
- Check `PYPI_API_TOKEN` secret is valid
- Ensure version doesn't already exist on PyPI
- Verify package builds successfully in earlier step
- Check for PyPI service issues

#### Validation Failures
**Problem**: Release validation fails on some platforms
**Solutions**:
- Check specific platform logs in GitHub Actions
- Test locally with same Python version
- Verify dependencies are compatible
- Check for platform-specific issues

#### Workflow Permissions
**Problem**: GitHub Actions lack required permissions
**Solutions**:
- Ensure repository settings allow GitHub Actions
- Check workflow permissions in `.github/workflows/`
- Verify `GITHUB_TOKEN` has required scopes

### Manual Recovery

If automation fails, you can:

1. **Delete and Recreate Tag**:
   ```bash
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   # Fix issues, then recreate tag
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

2. **Manual PyPI Upload**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

3. **Manual GitHub Release**:
   - Use GitHub web interface
   - Upload dist/ artifacts manually

## 📊 Monitoring & Metrics

### Release Health

Monitor these metrics:
- **Release Success Rate**: Should be >95%
- **Validation Pass Rate**: Should be 100%
- **Time to Release**: Target <15 minutes
- **PyPI Availability**: Usually <5 minutes after release

### Key Workflows

Track these workflows:
- `Version Bump & Changelog`: Should complete in <2 minutes
- `Release`: Should complete in <10 minutes
- `Release Validation`: Should complete in <15 minutes

## 🔄 Changelog Management

### Automatic Generation

The version bump workflow automatically:
- Extracts commits since last tag
- Formats as bullet points
- Inserts into `CHANGELOG.md`
- Uses semantic commit format when available

### Manual Curation

For better changelogs:
1. Use descriptive commit messages
2. Manually edit generated changelog if needed
3. Follow [Keep a Changelog](https://keepachangelog.com/) format
4. Group changes by type: Added, Changed, Fixed, etc.

## 🎯 Best Practices

### For Contributors

1. **Commit Messages**: Use clear, descriptive messages
2. **Testing**: Ensure all tests pass before proposing releases
3. **Documentation**: Update relevant docs with changes
4. **Version Bumps**: Use semantic versioning principles

### For Maintainers

1. **Regular Releases**: Consider regular release cadence
2. **Security Updates**: Prioritize security fixes
3. **Breaking Changes**: Use major version bumps appropriately
4. **Communication**: Announce significant releases

### For Automation

1. **Secret Rotation**: Rotate PyPI tokens periodically
2. **Workflow Updates**: Keep GitHub Actions up to date
3. **Validation Enhancement**: Add new validation checks as needed
4. **Monitoring**: Watch for workflow failures and address promptly

---

## 📞 Support

For release process issues:
- **GitHub Issues**: [Create an issue](https://github.com/ko6gxm/radiobridge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ko6gxm/radiobridge/discussions)
- **Contact**: craig@ko6gxm.com

*This release system ensures RadioBridge releases are consistent, tested, and reliable across all supported platforms and Python versions.*
