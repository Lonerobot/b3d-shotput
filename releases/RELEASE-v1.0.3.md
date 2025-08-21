# 🎬 Shotput v1.0.3

> **Additional bug fix release for file output node path generation**

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## 🐛 **Bug Fixes**

### 🔧 **Fixed: File Output Node Slot Paths for PNG/JPG**
- **Issue**: File output nodes generated incomplete paths with trailing underscores (e.g., `MyRenderLayer_AO_MAIN_`)
- **Fixed**: Enhanced `_update_file_slots` method to include proper sequence padding and file extensions
- **Result**: File output nodes now generate complete paths like `MyRenderLayer_AO_MAIN.####.png`

### ✨ **What's Improved**
- Removed trailing underscores from file output slot paths
- Added proper sequence numbering (`.####.`) to all file output slots
- Added intelligent file extension detection for PNG, JPEG, and EXR formats
- Unified path generation logic between composite nodes and file output nodes

## 📦 **Installation**

Download `shotput-v1.0.3.zip` and install via Blender → Edit → Preferences → Add-ons → Install

## 🔄 **Upgrade from v1.0.1 or v1.0.2**

Simply install v1.0.3 over the existing installation. Your scenes will automatically benefit from the improved path generation for both composite and file output nodes.

---

## 📚 **Support**

- **Author**: Pete Addington @ THE LINE STUDIO
- **License**: Open Source
- **Support**: Community-driven

---

*Built with ❤️ for the Blender community*
