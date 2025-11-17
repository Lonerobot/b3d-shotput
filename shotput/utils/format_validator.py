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
    If film transparency is enabled, the user likely wants RGBA output.
    If film transparency is disabled, RGB output is typically appropriate.
    
    Args:
        context: Blender context
        file_format: The file format string (e.g., 'PNG', 'JPEG', 'OPEN_EXR')
        
    Returns:
        tuple: (is_valid, warning_message)
            is_valid: True if no issues detected, False if there's a mismatch
            warning_message: String describing the issue, or empty string if no issues
    """
    # Only validate PNG format
    if file_format != 'PNG':
        return True, ""
    
    # Check film transparency setting
    film_transparent = context.scene.render.film_transparent
    
    # PNG defaults to RGB in Blender's File Output node
    # If film transparency is enabled, user probably wants RGBA output
    if film_transparent:
        warning_msg = (
            "PNG format selected with Film Transparency enabled. "
            "PNG will default to RGB mode. Consider manually setting "
            "color mode to RGBA in the node's format settings to preserve alpha channel."
        )
        logger.warning(warning_msg)
        return False, warning_msg
    
    # No issues detected
    return True, ""


def apply_png_alpha_channel_fix(file_output_node, context):
    """
    Automatically configure PNG format to use RGBA when film transparency is enabled.
    
    This is a helper function that can be called after creating a File Output node
    to ensure proper alpha channel configuration for PNG format.
    
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
        
        # Check if film transparency is enabled
        if not context.scene.render.film_transparent:
            return False
        
        # Set color mode to RGBA to preserve alpha channel
        file_output_node.format.color_mode = 'RGBA'
        logger.info("Applied RGBA color mode to PNG output node (film transparency enabled)")
        return True
        
    except Exception as e:
        logger.error(f"Error applying PNG alpha channel fix: {e}")
        return False
