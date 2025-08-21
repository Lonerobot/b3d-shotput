# 🎬 Shotput v1.0.2

> **Bug fix release for composite node path generation**

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## 🐛 **Bug Fixes**

### 🔧 **Fixed: Composite Node Path Construction**
- **Issue**: Composite nodes generated incomplete render paths (e.g., `ViewLayer_composite_v001`)
- **Fixed**: Enhanced `_update_scene_render_path` method to include proper sequence padding and file extensions
- **Result**: Composite nodes now generate complete paths like `ViewLayer_composite_v001.####.png`

### ✨ **What's Improved**
- Added proper sequence numbering (`.####.`) to composite output paths
- Added intelligent file extension detection based on UI output format settings
- Aligned composite node behavior with file output nodes for consistent path generation
- Enhanced error handling and user feedback in version update operator

## 📦 **Installation**

Download `shotput-v1.0.2.zip` and install via Blender → Edit → Preferences → Add-ons → Install

## 🔄 **Upgrade from v1.0.1**

Simply install v1.0.2 over the existing installation. Your scenes will automatically benefit from the improved path generation.

---

## 📚 **Support**

- **Author**: Pete Addington @ THE LINE STUDIO
- **License**: Open Source
- **Support**: Community-driven

---

*Built with ❤️ for the Blender community*
