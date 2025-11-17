"""
Format validation utilities for Shotput.

Provides validation functions to check format settings against render settings,
particularly for ensuring proper alpha channel configuration.
"""

import bpy
from .log import LoggerFactory

logger = LoggerFactory.logger_obj()


def validate_png_alpha_channel(context, file_format):
    """
    Validate PNG format settings against film transparency settings.
    
    PNG format can output as RGB (no alpha) or RGBA (with alpha).
    This validator ensures the color mode matches film transparency:
    - Film transparency ON -> RGBA (preserve alpha channel)
    - Film transparency OFF -> RGB (no alpha needed)
    
    Args:
        context: Blender context
        file_format: The file format string (e.g., 'PNG', 'JPEG', 'OPEN_EXR')
        
    Returns:
        tuple: (is_valid, warning_message)
            is_valid: True if no issues detected, False if configuration needed
            warning_message: String describing what will be fixed, or empty if no issues
    """
    # Only validate PNG format
    if file_format != 'PNG':
        return True, ""
    
    # Check film transparency setting
    film_transparent = context.scene.render.film_transparent
    
    # Determine appropriate action based on film transparency
    if film_transparent:
        warning_msg = (
            "PNG format selected with Film Transparency enabled. "
            "Automatically setting PNG to RGBA mode to preserve alpha channel."
        )
        logger.warning(warning_msg)
        return False, warning_msg
    else:
        # Film transparency disabled - ensure RGB mode for efficiency
        warning_msg = (
            "PNG format selected with Film Transparency disabled. "
            "Automatically setting PNG to RGB mode (no alpha channel needed)."
        )
        logger.info(warning_msg)
        return False, warning_msg


def apply_png_alpha_channel_fix(file_output_node, context):
    """
    Automatically configure PNG format to match film transparency settings.
    
    Sets RGBA when film transparency is enabled, or RGB when disabled.
    This helper can be called after creating a File Output node to ensure
    proper alpha channel configuration for PNG format.
    
    Args:
        file_output_node: The File Output node to configure
        context: Blender context
        
    Returns:
        bool: True if configuration was applied, False otherwise
    """
    try:
        # Only apply to PNG format
        if file_output_node.format.file_format != 'PNG':
            return False
        
        # Configure color mode based on film transparency setting
        film_transparent = context.scene.render.film_transparent
        
        if film_transparent:
            # Set color mode to RGBA to preserve alpha channel
            file_output_node.format.color_mode = 'RGBA'
            logger.info("Applied RGBA color mode to PNG output node (film transparency enabled)")
        else:
            # Set color mode to RGB when alpha is not needed
            file_output_node.format.color_mode = 'RGB'
            logger.info("Applied RGB color mode to PNG output node (film transparency disabled)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying PNG alpha channel fix: {e}")
        return False
