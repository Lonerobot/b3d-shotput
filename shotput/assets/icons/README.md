# Shotput Custom Icons

This directory contains custom icons for the Shotput Blender addon. These icons replace the built-in Blender STRIP_COLOR icons to provide a unique branded look for the addon.

## Current Icons

| Icon File | Usage | Theme Color | Replaces |
|-----------|-------|-------------|----------|
| `core.png` | Core passes (beauty renders) | Blue (#3478B4) | STRIP_COLOR_05 |
| `aov.png` | AOV passes (additional render elements) | Orange (#C86E32) | STRIP_COLOR_02 |
| `data.png` | Data passes (technical/compositing data) | Red/Magenta (#B43250) | STRIP_COLOR_01 |
| `token_help.png` | Token help button | Green (#3C9664) | QUESTION |

## Icon Specifications

- **Format**: PNG with transparency (RGBA)
- **Size**: 64x64 pixels (recommended minimum for quality)
- **Color Depth**: 8-bit per channel
- **Usage**: Automatically loaded by `shotput/utils/custom_icons.py`

## Placeholder Icons

The current icons are simple placeholder designs with:
- Colored background matching the theme
- White letter indicating the icon type (C, A, D, ?)
- White border for visual consistency
- Suitable compression for small file size

## Replacing Icons

To update these icons with custom designs:

1. Create your icon design at 64x64px or larger (will be scaled by Blender)
2. Export as PNG with transparency
3. Replace the corresponding file in this directory
4. Restart Blender or reload the addon to see changes
5. Icon names **must match** the filename exactly (case-sensitive)

## Implementation

The custom icons system is inspired by the [UniV addon](https://github.com/Oxicid/UniV) and uses Blender's `bpy.utils.previews` API:

```python
from shotput.utils.custom_icons import icons

# In UI code:
layout.operator("shotput.create_core_passes", icon_value=icons.core)
```

If an icon fails to load, the system automatically falls back to the original built-in Blender icons, ensuring the UI always works.

## Technical Details

- Icons are loaded during addon registration
- Stored in a preview collection managed by Blender
- Icon IDs are cached as class attributes for fast access
- Fallback mechanism ensures graceful degradation
- No performance impact on Blender startup or UI rendering

## Credits

Current placeholder icons created by GitHub Copilot.
Future professional icons can be designed by the addon maintainer or community contributors.
