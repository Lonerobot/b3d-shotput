# Shotput v1.0.3 Release Notes

**Release Date:** August 21, 2025  
**Compatibility:** Blender 4.4+  

## 🎯 Overview

Critical path generation consistency fixes. File paths are now identical whether nodes are created fresh or updated via versioning.

## ✨ What's Fixed

### Path Generation Consistency
- **Fixed:** File extensions now included during node creation (PNG/JPEG/EXR single)
- **Before:** `MyRenderLayer_AO_MAIN.####` (creation) vs `MyRenderLayer_AO_MAIN.####.png` (update)
- **After:** `MyRenderLayer_AO_MAIN.####.png` (both creation and update)

### EXR Multilayer Data Passes  
- **Fixed:** Versioning now properly handles multichannel EXR format
- **Result:** Version updates preserve full file paths correctly

## 🐛 Bug Fixes

- ✅ Path inconsistency between creation and versioning operators
- ✅ Missing file extensions during node creation  
- ✅ EXR multilayer versioning breaking multichannel structure
- ✅ Redundant channel names in paths (from v1.0.2 - still fixed)

## 🚀 Installation

1. Download `shotput-v1.0.3.zip`
2. Blender → Preferences → Add-ons → Install  
3. Enable "Shotput" in add-ons list

## 🆘 Support

- **Docs:** [lonerobot.github.io/b3d-shotput-docs](https://lonerobot.github.io/b3d-shotput-docs/)
- **Issues:** [GitHub Issues](https://github.com/Lonerobot/b3d-shotput/issues)
