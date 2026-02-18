# 🎬 Shotput v1.3.1

> **A tokenised render output addon for Blender 4.4+**

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## 🚀 What's New in v1.3.1

### Bug Fixes
- **Fixed multichannel EXR path handling in AYON mode**: Multichannel EXR nodes now correctly handle complex AYON tokens like `{workdir}/{subpath}/{blendfile}` when updating versions
- **Fixed AYON mode precedence**: Path linking is now properly ignored when AYON mode is enabled, preventing false positives
- **Fixed version update operator**: Multichannel EXR nodes in standard and AYON modes now properly extract directory-only paths during version updates

## 📝 v1.3.0 Release Notes

After a lot of testing, this is the first production release for Shotput. Future development will operate in 2 forms -

- **Blender 4x** development will be bug fixes only. The system is working as expected and has been tested successfully within project environments. Blender 4.5 is LTS so this version will be targetted and tested within this Blender version from now on.
- **Blender 5x** - With impeccable timing, there are some sweeping changes surrounding the compositor graph in Blender 5 which mean a rethink and refactor of the addon in order to be required and relevant.
  - Blender has tokenised output now on the file output node
  - Compositor graphs can now be saved and loaded between Blender scenes. This does mean the preset system might be expanded to allow this scenario.

---

## 📦 Installation

1. Download **Shotput-v1.3.1.zip**
2. In Blender: **Edit → Preferences → Add-ons → Install...**
3. Select the downloaded zip
4. Enable the "Shotput" addon
5. Find controls in:
   > **Compositor → Sidebar → Shotput Tab**
   >

---

## 🚨 Known Considerations

- Whilst this addon has been tested, there are always nuances with pathing that might crop up. Please report any bugs or issues you find.

*Built with ❤️ for the Blender community by Lonerobot/THE LINE*
