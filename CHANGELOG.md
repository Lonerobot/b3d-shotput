# Changelog

All notable changes to Shotput will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0-rc] - 2025-11-25

### Changed
- Release candidate for Blender 4.x final stable version
- Prepared codebase for Blender 5.0 migration branch split
- Fixed UI panel visibility bug in shader editor (now compositor-only)
- Renamed `pass_name` property to `pass_type` for semantic clarity
- UI now shows pass type as read-only in header format "Type: Core | Version: 1.x.x"
- Changed override field labels from "Core Override" to "Name Override"

### Added
- Build Render Layers operator optimization (reuses existing default nodes)
- Comprehensive documentation clarifying `{passname}` token vs `pass_type` property

### Fixed
- Critical bug where override names were incorrectly set as `pass_type`
- Build Render Layers now properly detects and reuses Blender's auto-created default node
- Pass type now always correctly set to category ("core", "aov", "data", "composite") independent of override names

### Notes
- This is the final release candidate for Blender 4.x support
- Future development will split into:
  - `blender4x` branch: Maintenance and bug fixes for Blender 4.0-4.x
  - `blender5x` branch: New development for Blender 5.0+ (v2.0.0)

## [1.2.8] - Previous

### Summary
- Beta version with token-based render output system
- AYON integration support
- Core, AOV, Data pass creation
- Version management system
- Preset save/load functionality
