"""
Custom Icons Manager for Shotput Addon

This module handles loading and managing custom icons for the Shotput addon.
It provides a clean API for accessing custom icon IDs throughout the UI.

Inspired by the UniV addon's icon system: https://github.com/Oxicid/UniV
"""

import bpy
import os
from pathlib import Path

from .log import LoggerFactory
logger = LoggerFactory.logger_obj()


class icons:
    """
    Interface for accessing custom icons.
    
    Icon names must match the names of the corresponding PNG files.
    Usage: layout.operator("op.id", icon_value=icons.core)
    """
    _icons_ = None
    
    # Icon IDs (will be set during registration)
    core = 0
    aov = 0
    data = 0
    token_help = 0
    
    @classmethod
    def register_icons_(cls):
        """Register custom icons and load them into preview collection"""
        from bpy.utils import previews
        
        if cls._icons_:
            cls.unregister_icons_()
        cls._icons_ = previews.new()
        
        # Get icons directory
        addon_dir = Path(__file__).parent.parent
        icons_dir = addon_dir / "assets" / "icons"
        
        # Icon names must match PNG filenames
        loaded_count = 0
        for attr in dir(cls):
            if not attr.startswith('_'):
                if not isinstance(getattr(cls, attr), int):
                    logger.debug(f'Shotput: Attribute {attr} is not an icon_id')
                    continue
                
                icon_path = icons_dir / f"{attr}.png"
                if not icon_path.exists():
                    logger.warning(f'Shotput: Icon file not found: {icon_path}')
                    continue
                
                try:
                    icon = cls._icons_.load(attr, str(icon_path), 'IMAGE')
                    # Force load icons (Blender quirk workaround)
                    _ = icon.icon_pixels[0]
                    setattr(cls, attr, icon.icon_id)
                    loaded_count += 1
                    logger.debug(f"Shotput: Loaded custom icon: {attr} (id={icon.icon_id})")
                except Exception as e:
                    logger.warning(f'Shotput: Failed to load icon {attr}: {e}')
        
        if loaded_count > 0:
            logger.info(f"Shotput: Custom icons registered successfully ({loaded_count} icons loaded)")
        else:
            logger.warning("Shotput: No custom icons were loaded - using fallback icons")
    
    @classmethod
    def reset_icon_value_(cls):
        """Reset all icon IDs to 0"""
        for attr in dir(cls):
            if not attr.startswith('_'):
                setattr(cls, attr, 0)
    
    @classmethod
    def unregister_icons_(cls):
        """Unregister and clean up custom icons"""
        from bpy.utils import previews
        try:
            if cls._icons_:
                previews.remove(cls._icons_)
        except KeyError:
            logger.debug("Shotput: Preview collection already removed")
        except Exception as e:
            logger.error(f"Shotput: Error unregistering icons: {e}")
        
        cls.reset_icon_value_()
        cls._icons_ = None


# Module-level registration functions for backward compatibility
def register():
    """Register custom icons"""
    icons.register_icons_()


def unregister():
    """Unregister custom icons"""
    icons.unregister_icons_()


# Fallback icon mapping for when custom icons aren't loaded
FALLBACK_ICONS = {
    'core': 'STRIP_COLOR_05',
    'aov': 'STRIP_COLOR_02',
    'data': 'STRIP_COLOR_01',
    'token_help': 'QUESTION',
}


def get_icon_id_or_fallback(icon_name):
    """
    Get custom icon ID if available, otherwise return fallback icon name.
    
    Returns a dict that can be unpacked into operator/layout calls:
    - {'icon_value': id} for custom icons
    - {'icon': 'ICON_NAME'} for fallback icons
    
    Usage: layout.operator("op.id", **get_icon_id_or_fallback('core'))
    """
    icon_id = getattr(icons, icon_name, 0)
    if icon_id != 0:
        return {'icon_value': icon_id}
    else:
        fallback = FALLBACK_ICONS.get(icon_name, 'DOT')
        return {'icon': fallback}
