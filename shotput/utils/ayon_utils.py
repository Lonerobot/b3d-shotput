import os
import bpy

from .log import LoggerFactory
logger = LoggerFactory.logger_obj()


def is_ayon_context():
    """
    Check if we're running in an AYON pipeline context.
    
    Returns:
        bool: True if AYON environment variables are detected
    """
    ayon_project = os.getenv("AYON_PROJECT_NAME")
    ayon_workdir = os.getenv("AYON_WORKDIR")
    
    is_ayon = bool(ayon_project and ayon_workdir)
    
    if is_ayon:
        logger.debug(f"AYON context detected: project='{ayon_project}', workdir='{ayon_workdir}'")
    else:
        logger.debug("No AYON context detected")
    
    return is_ayon


def should_use_ayon_tokens(node_properties=None):
    """
    Determine if AYON tokens should be used for a specific node.
    
    Args:
        node_properties: ShotputFileOutputProperties from the node
        
    Returns:
        bool: True if AYON tokens should be used
    """
    # Check if we're in AYON context
    if not is_ayon_context():
        return False
    
    # Check if node has AYON override disabled
    if node_properties and hasattr(node_properties, 'use_ayon_output_style'):
        if not node_properties.use_ayon_output_style:
            logger.debug("AYON context detected but node has AYON output style disabled")
            return False
    
    logger.debug("AYON tokens will be used")
    return True


def get_ayon_tokens(is_composite=False):
    """
    Get AYON-specific tokens from preferences.
    
    Args:
        is_composite: If True, returns composite-specific tokens
        
    Returns:
        tuple: (root_folder_token, file_name_token)
    """
    try:
        from .. import __package_name__
        prefs = bpy.context.preferences.addons[__package_name__].preferences
        
        if is_composite:
            root_token = prefs.ayon_composite_root_folder_token
            file_token = prefs.ayon_composite_file_name_token
        else:
            root_token = prefs.ayon_root_folder_token
            file_token = prefs.ayon_file_name_token
        
        logger.debug(f"Retrieved AYON tokens (composite={is_composite}): root='{root_token}', file='{file_token}'")
        return root_token, file_token
        
    except Exception as e:
        logger.error(f"Error getting AYON tokens from preferences: {e}")
        # Return sensible defaults
        if is_composite:
            return "{workdir}/{subpath}/{blendfile}", "/tmp/tmp"
        else:
            return "{workdir}/{subpath}/{blendfile}", "{outputlayer}_{passname}_{variant}"


def apply_ayon_tokens_to_node(node, node_properties, is_composite=False):
    """
    Apply AYON-specific tokens to a node's properties.
    
    Args:
        node: The File Output or Composite node
        node_properties: ShotputFileOutputProperties from the node
        is_composite: Whether this is a composite node
        
    Returns:
        bool: True if AYON tokens were applied
    """
    # Check if AYON context exists
    if not is_ayon_context():
        return False
    
    # Enable AYON mode by default when node is created in AYON context
    if not hasattr(node_properties, 'use_ayon_output_style'):
        logger.warning("Node properties missing 'use_ayon_output_style' attribute")
        return False
    
    # Check if AYON mode is enabled (defaults to True)
    if not node_properties.use_ayon_output_style:
        logger.debug("AYON context detected but node has AYON output style disabled")
        return False
    
    # Get AYON tokens from preferences
    root_token, file_token = get_ayon_tokens(is_composite)
    
    # Backup current tokens as "normal" tokens before applying AYON tokens
    if node_properties.root_folder_token and not node_properties.normal_root_folder_token:
        node_properties.normal_root_folder_token = node_properties.root_folder_token
    if node_properties.file_name_token and not node_properties.normal_file_name_token:
        node_properties.normal_file_name_token = node_properties.file_name_token
    
    # Apply AYON tokens
    node_properties.root_folder_token = root_token
    node_properties.file_name_token = file_token
    
    logger.info(f"Applied AYON tokens to node '{node.name}' (composite={is_composite})")
    logger.debug(f"  Root token: {root_token}")
    logger.debug(f"  File token: {file_token}")
    return True
