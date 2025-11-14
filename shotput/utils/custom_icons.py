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
    # Pass type icons
    core = 0
    aov = 0
    data = 0
    composite = 0
    
    # Help and information icons
    token_help = 0
    help = 0
    info = 0
    error = 0
    
    # Integration icons
    ayon = 0
    
    # UI control icons
    add = 0
    remove = 0
    tria_up = 0
    tria_down = 0
    tria_right = 0
    tria_left = 0
    
    # File operation icons
    file_folder = 0
    file_refresh = 0
    folder_redirect = 0
    import_icon = 0  # 'import' is a Python keyword
    export = 0
    preset = 0
    
    # Path linking icons
    linked = 0
    unlinked = 0
    
    # Token display icons
    dot = 0
    
    # Category icons
    blender = 0
    time = 0
    network_drive = 0
    
    # Blender context icons
    renderlayers = 0
    scene_data = 0
    settings = 0
    nodetree = 0
    preferences = 0
    render_result = 0
    
    # Miscellaneous icons
    viewzoom = 0
    color = 0
    preview_range = 0
    
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
                
                # Special handling for import_icon -> import.png
                icon_filename = "import.png" if attr == "import_icon" else f"{attr}.png"
                icon_path = icons_dir / icon_filename
                
                if not icon_path.exists():
                    logger.debug(f'Shotput: Icon file not found: {icon_path}')
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
            if not attr.startswith('_') and not callable(getattr(cls, attr)):
                try:
                    current_value = getattr(cls, attr)
                    if isinstance(current_value, int):
                        setattr(cls, attr, 0)
                except AttributeError:
                    pass
    
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
    # Pass type icons
    'core': 'STRIP_COLOR_05',
    'aov': 'STRIP_COLOR_02',
    'data': 'STRIP_COLOR_01',
    'composite': 'STRIP_COLOR_07',
    
    # Help and information icons
    'token_help': 'QUESTION',
    'help': 'HELP',
    'info': 'INFO',
    'error': 'ERROR',
    
    # Integration icons
    'ayon': 'WORLD',
    
    # UI control icons
    'add': 'ADD',
    'remove': 'REMOVE',
    'tria_up': 'TRIA_UP',
    'tria_down': 'TRIA_DOWN',
    'tria_right': 'TRIA_RIGHT',
    'tria_left': 'TRIA_LEFT',
    
    # File operation icons
    'file_folder': 'FILE_FOLDER',
    'file_refresh': 'FILE_REFRESH',
    'folder_redirect': 'FOLDER_REDIRECT',
    'import_icon': 'IMPORT',
    'export': 'EXPORT',
    'preset': 'PRESET',
    
    # Path linking icons
    'linked': 'LINKED',
    'unlinked': 'UNLINKED',
    
    # Token display icons
    'dot': 'DOT',
    
    # Category icons
    'blender': 'BLENDER',
    'time': 'TIME',
    'network_drive': 'NETWORK_DRIVE',
    
    # Blender context icons
    'renderlayers': 'RENDERLAYERS',
    'scene_data': 'SCENE_DATA',
    'settings': 'SETTINGS',
    'nodetree': 'NODETREE',
    'preferences': 'PREFERENCES',
    'render_result': 'RENDER_RESULT',
    
    # Miscellaneous icons
    'viewzoom': 'VIEWZOOM',
    'color': 'COLOR',
    'preview_range': 'PREVIEW_RANGE',
}


def get_icon_id_or_fallback(icon_name):
    """
    Get custom icon ID if available, otherwise return fallback icon name.
    
    Returns a dict that can be unpacked into operator/layout calls:
    - {'icon_value': id} for custom icons
    - {'icon': 'ICON_NAME'} for fallback icons
    
    Usage: layout.operator("op.id", **get_icon_id_or_fallback('core'))
    
    Note: 'import' is mapped to 'import_icon' internally since 'import' is a Python keyword
    """
    # Handle special case for 'import' keyword
    attr_name = 'import_icon' if icon_name == 'import' else icon_name
    
    icon_id = getattr(icons, attr_name, 0)
    if icon_id != 0:
        return {'icon_value': icon_id}
    else:
        fallback = FALLBACK_ICONS.get(attr_name, 'DOT')
        return {'icon': fallback}
