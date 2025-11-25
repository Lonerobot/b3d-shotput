# Repository Structure Guide

## Overview

This repository maintains Shotput addon for both Blender 4.x and Blender 5.0+ through a multi-branch development strategy.

## Branch Layout

```
master (Release coordination)
├── v1.3.0-rc tag
│
├─── blender4x (Maintenance)
│    └── Version: 1.3.x
│    └── Blender: 4.0 - 4.x
│    └── Status: Bug fixes only
│
└─── blender5x (Active Development)
     └── Version: 2.0.x
     └── Blender: 5.0+
     └── Status: Feature development
```

## Branches

### `master` - Release Coordination
- **Purpose:** Documentation hub and release tag management
- **Contains:** Main README, CHANGELOG, branch navigation
- **Deployments:** Release tags point here
- **Do NOT:** Commit code changes directly to master

### `blender4x` - Blender 4.x Support
- **Version:** 1.3.x (Maintenance)
- **Blender:** 4.0, 4.1, 4.2, 4.3, 4.4+
- **Status:** 🟢 Stable - Production Ready
- **Policy:** Bug fixes and critical patches only
- **No:** New features, breaking changes

**When to use:**
- Fixing bugs in production environments
- Security patches
- Critical compatibility fixes
- Blender 4.x API adjustments

### `blender5x` - Blender 5.0+ Support
- **Version:** 2.0.x (Alpha → Beta → Release)
- **Blender:** 5.0+
- **Status:** 🟡 Active Development
- **Policy:** New features, major refactoring
- **Breaking Changes:** Allowed (major version bump)

**When to use:**
- Blender 5.0 API migration
- New features leveraging 5.0 capabilities
- Major architectural improvements
- Experimental features

## Version Strategy

### Blender 4.x (1.3.x)
- **Current:** 1.3.0-rc
- **Next:** 1.3.1 (patch), 1.3.2 (patch), etc.
- **Never:** 1.4.0 (no more minor versions)

### Blender 5.x (2.0.x)
- **Current:** 2.0.0-alpha
- **Next:** 2.0.0-beta, 2.0.0-rc, 2.0.0
- **Future:** 2.1.0 (new features), 2.0.1 (patches)

## Development Workflow

### Bug Fix for Blender 4.x

```bash
git checkout blender4x
git pull origin blender4x

# Make your fix
git commit -m "Fix: description of bug fix"
git push origin blender4x

# Create PR targeting blender4x
```

### Feature for Blender 5.x

```bash
git checkout blender5x
git pull origin blender5x

# Develop feature
git commit -m "Feature: description"
git push origin blender5x

# Create PR targeting blender5x
```

### Creating a Release

**For Blender 4.x patch:**
```bash
git checkout blender4x
# Update version in __init__.py (e.g., 1.3.1)
# Update CHANGELOG.md
git commit -m "Release: v1.3.1"
git tag -a v1.3.1 -m "Release v1.3.1 for Blender 4.x"
git push origin blender4x --tags
```

**For Blender 5.x release:**
```bash
git checkout blender5x
# Update version in __init__.py (e.g., 2.0.0)
# Update __release_stage__ to "release"
# Update CHANGELOG.md
git commit -m "Release: v2.0.0"
git tag -a v2.0.0 -m "Release v2.0.0 for Blender 5.0+"
git push origin blender5x --tags
```

## File Organization

```
repo/
├── README.md                          # Branch navigation (master)
├── CHANGELOG.md                       # Version history (all branches)
├── BRANCH_STRATEGY.md                 # This file (master)
├── BLENDER5_MIGRATION_REPORT.md       # Technical migration guide
│
├── [blender4x branch]
│   ├── addons/shotput/
│   │   ├── __init__.py               # v1.3.x, Blender 4.4+
│   │   └── ...                        # Stable 4.x codebase
│   └── README_BLENDER4X.md           # 4.x specific docs
│
└── [blender5x branch]
    ├── addons/shotput/
    │   ├── __init__.py               # v2.0.x, Blender 5.0+
    │   └── ...                        # New 5.x codebase
    ├── README_BLENDER5X.md           # 5.x specific docs
    └── test_*.py                      # 5.0 API test suite
```

## Merging Strategy

### ❌ DO NOT merge between blender4x and blender5x

These branches have **divergent codebases** due to Blender 5.0's breaking API changes.

### ✅ DO cherry-pick specific fixes

If a bug fix in `blender4x` applies to `blender5x`:

```bash
# On blender4x, find commit hash
git log --oneline

# Switch to blender5x
git checkout blender5x

# Cherry-pick the fix
git cherry-pick <commit-hash>

# Resolve conflicts if API differences exist
# Test thoroughly!
```

### ⚠️ Most changes will be branch-specific

Due to API differences, most fixes will need separate implementations for each branch.

## Release Tags

All release tags are created from their respective branches but reference back to master for documentation:

- `v1.3.0-rc` - Blender 4.x release candidate
- `v1.3.1` - Future Blender 4.x patch
- `v2.0.0-alpha` - Blender 5.x alpha
- `v2.0.0` - Future Blender 5.x stable

## Support Timeline

### Blender 4.x (blender4x branch)
- **Active Support:** Until Blender 5.x becomes production-stable (v2.0.0+)
- **Maintenance:** Bug fixes for critical issues
- **End of Life:** When Blender 5.x adoption is widespread

### Blender 5.x (blender5x branch)
- **Current:** Alpha development
- **Target:** Production-ready v2.0.0
- **Timeline:** 4-8 weeks for complete migration

## Questions?

- **Which branch?** Use Blender version to decide
- **Bug in both?** Fix in both branches separately
- **New feature?** Only add to blender5x
- **Production work?** Stick with blender4x

---

**Last Updated:** 2025-11-25  
**Maintained by:** Pete.Addington / The Line Studio
