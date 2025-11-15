import bpy
import json
import os
from pathlib import Path

from .log import LoggerFactory
logger = LoggerFactory.logger_obj()


def is_valid_shotput_preset(data):
    """Check if JSON data has the required Shotput structure"""
    required_keys = ["core_passes", "aovs", "data_passes"]
    if not isinstance(data, dict):
        return False
    
    # Check for required keys
    for key in required_keys:
        if key not in data:
            return False
        if not isinstance(data[key], list):
            return False
    
    return True


def load_default_passes():
    """Load default passes from JSON file if SHOTPUT_PRESET_PATH is set"""
    # Only load if environment variable is set (project-specific presets)
    env_path = os.environ.get('SHOTPUT_PRESET_PATH')
    if not env_path:
        logger.debug("SHOTPUT_PRESET_PATH not set, will use addon preferences for tokens")
        # No environment variable set - return minimal defaults
        # Note: root_folder_token and file_name_token are intentionally omitted
        # so that addon preferences will be used instead
        return {
            "core_passes": [],
            "aovs": [],
            "data_passes": [],
            "output_layer": "ViewLayer",
            "variant": "v001",
            "core_override": "Core",
            "aov_override": "AOV",
            "default_file_format": "OPEN_EXR"
        }
    
    logger.info(f"SHOTPUT_PRESET_PATH is set to: {env_path}")
    
    # Environment variable is set - try to load the preset
    env_path = Path(env_path)
    json_files = []
    
    if env_path.exists():
        if env_path.is_file():
            logger.info(f"SHOTPUT_PRESET_PATH points to file: {env_path}")
            json_files = [env_path]
        else:
            # Directory path - search for JSON files
            logger.info(f"SHOTPUT_PRESET_PATH points to directory, searching for JSON files")
            json_files = list(env_path.glob('*.json'))
            logger.info(f"Found {len(json_files)} JSON files: {[f.name for f in json_files]}")
    else:
        logger.warning(f"SHOTPUT_PRESET_PATH does not exist: {env_path}")
    
    # Try each JSON file until we find a valid Shotput preset
    for json_path in json_files:
        try:
            logger.debug(f"Attempting to load preset from: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if is_valid_shotput_preset(data):
                    logger.info(f"Successfully loaded valid preset from {json_path}")
                    return data
                else:
                    logger.debug(f"File {json_path.name} is not a valid Shotput preset (missing required keys)")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.debug(f"Could not read {json_path}: {e}")
            continue
    
    # If we get here, SHOTPUT_PRESET_PATH was set but no valid preset found
    logger.warning(f"SHOTPUT_PRESET_PATH set to '{env_path}' but no valid preset found, will use addon preferences for tokens")
    # Return minimal defaults without tokens so addon preferences will be used
    return {
        "core_passes": [],
        "aovs": [],
        "data_passes": [],
        "output_layer": "ViewLayer",
        "variant": "v001",
        "core_override": "Core",
        "aov_override": "AOV",
        "default_file_format": "OPEN_EXR"
    }


def get_file_format_for_pass_type(pass_type: str, ui_format: str = "OPEN_EXR") -> str:
    """
    Get the appropriate file format for a given pass type.
    
    Args:
        pass_type: Type of pass ('core', 'aov', 'data')
        ui_format: The format selected in the UI
        
    Returns:
        Blender file format string
    """
    try:
        # For data passes, use the preference override
        if pass_type == "data":
            try:
                from .. import __package_name__
                prefs = bpy.context.preferences.addons[__package_name__].preferences
                return prefs.data_node_format_override
            except Exception as e:
                logger.warning(f"Could not get data format preference, using fallback: {e}")
                return "OPEN_EXR_MULTILAYER"
        
        # For core and aov passes, use JSON configuration
        defaults = load_default_passes()
        format_overrides = defaults.get("file_format_overrides", {})
        
        override = format_overrides.get(pass_type, "UI")
        
        if override == "UI":
            # Use the UI-specified format
            return ui_format
        else:
            # Use the override format
            return override
            
    except Exception as e:
        logger.error(f"Error getting file format for {pass_type}: {e}")
        # Fallback logic
        if pass_type == "data":
            return "OPEN_EXR_MULTILAYER"
        else:
            return ui_format


def get_sequence_padding() -> str:
    """
    Get the sequence padding string from preferences.
    
    Returns:
        Padding string like "####" based on preference setting
    """
    try:
        from .. import __package_name__
        prefs = bpy.context.preferences.addons[__package_name__].preferences
        padding_count = prefs.sequence_padding
        return "#" * padding_count
    except Exception as e:
        logger.warning(f"Could not get sequence padding preference, using default: {e}")
        return "####"


def get_subpath_token_value() -> str:
    """
    Get the subpath token value from preferences.
    
    Returns:
        Subpath value for {subpath} token
    """
    try:
        from .. import __package_name__
        prefs = bpy.context.preferences.addons[__package_name__].preferences
        return prefs.subpath_token_value
    except Exception as e:
        logger.warning(f"Could not get subpath token value, using default: {e}")
        return "blender/renders"


def get_default_root_folder_token() -> str:
    """
    Get the default root folder token from preferences.
    
    Returns:
        Default root folder token pattern
    """
    try:
        from .. import __package_name__
        prefs = bpy.context.preferences.addons[__package_name__].preferences
        return prefs.default_root_folder_token
    except Exception as e:
        logger.warning(f"Could not get default root folder token, using fallback: {e}")
        return "{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}"


def get_default_file_name_token() -> str:
    """
    Get the default file name token from preferences.
    
    Returns:
        Default file name token pattern
    """
    try:
        from .. import __package_name__
        prefs = bpy.context.preferences.addons[__package_name__].preferences
        return prefs.default_file_name_token
    except Exception as e:
        logger.warning(f"Could not get default file name token, using fallback: {e}")
        return "{outputlayer}_{passname}_{variant}"


def apply_data_format_settings(file_output_node):
    """
    Apply specific format settings for data passes (full float precision).
    
    Args:
        file_output_node: The File Output node to configure
    """
    try:
        defaults = load_default_passes()
        data_settings = defaults.get("data_format_settings", {})
        
        # Apply data-specific settings
        if hasattr(file_output_node.format, 'color_depth'):
            file_output_node.format.color_depth = data_settings.get("color_depth", "32")
        
        if hasattr(file_output_node.format, 'exr_codec'):
            file_output_node.format.exr_codec = data_settings.get("exr_codec", "ZIP")
            
        logger.debug("Applied data format settings for full float precision")
        
    except Exception as e:
        logger.error(f"Error applying data format settings: {e}")


def initialize_default_passes():
    """Initialize default passes for the scene"""
    try:
        logger.info("Initializing default passes from SHOTPUT_PRESET_PATH")
        scene = bpy.context.scene
        if hasattr(scene, 'shotput'):
            props = scene.shotput
            defaults = load_default_passes()
            
            if defaults:
                logger.debug(f"Applying preset with {len(defaults.get('core_passes', []))} core passes, "
                           f"{len(defaults.get('aovs', []))} AOV passes, "
                           f"{len(defaults.get('data_passes', []))} data passes")
                
                # Clear existing collections
                props.core_passes.clear()
                props.aov_passes.clear()
                
                # Add core passes
                for pass_name in defaults.get("core_passes", []):
                    item = props.core_passes.add()
                    item.name = pass_name
                
                # Add AOV passes
                for pass_name in defaults.get("aovs", []):
                    item = props.aov_passes.add()
                    item.name = pass_name
                
                # Set data pass boolean properties from JSON array
                if "data_passes" in defaults and isinstance(defaults["data_passes"], list):
                    # Reset all data passes to False first
                    data_pass_properties = [
                        'z', 'mist', 'normal', 'vector', 'position', 'occlusion',
                        'crypto_object', 'crypto_material', 'crypto_asset'
                    ]
                    for prop_name in data_pass_properties:
                        if hasattr(props, prop_name):
                            setattr(props, prop_name, False)
                    
                    # Enable data passes directly by property name from JSON
                    for prop_name in defaults["data_passes"]:
                        if hasattr(props, prop_name):
                            setattr(props, prop_name, True)
                
                # Set default scene properties with proper precedence:
                # 1. JSON preset (if provided) - highest priority
                # 2. Addon preferences - middle priority
                # 3. Hardcoded defaults - lowest priority (already in property definition)
                
                # Check if we have a JSON preset (SHOTPUT_PRESET_PATH was set and valid preset found)
                has_json_preset = os.environ.get('SHOTPUT_PRESET_PATH') is not None
                
                if "output_layer" in defaults:
                    props.output_layer = defaults["output_layer"]
                if "variant" in defaults:
                    props.variant = defaults["variant"]
                if "core_override" in defaults:
                    props.core_override = defaults["core_override"]
                if "aov_override" in defaults:
                    props.aov_override = defaults["aov_override"]
                
                # Token handling with precedence
                if "root_folder_token" in defaults:
                    # JSON preset provides token - use it (highest priority)
                    props.root_folder_token = defaults["root_folder_token"]
                elif not has_json_preset:
                    # No JSON preset - use addon preferences (middle priority)
                    props.root_folder_token = get_default_root_folder_token()
                # else: keep hardcoded default from property definition (lowest priority)
                
                if "file_name_token" in defaults:
                    # JSON preset provides token - use it (highest priority)
                    props.file_name_token = defaults["file_name_token"]
                elif not has_json_preset:
                    # No JSON preset - use addon preferences (middle priority)
                    props.file_name_token = get_default_file_name_token()
                # else: keep hardcoded default from property definition (lowest priority)
                
                if "default_file_format" in defaults:
                    # Map to output_format enum with Blender's expected values
                    format_map = {
                        "PNG": "PNG",
                        "JPG": "JPEG", 
                        "JPEG": "JPEG",
                        "EXR": "OPEN_EXR",
                        "OPEN_EXR": "OPEN_EXR",
                        "EXR_MULTILAYER": "OPEN_EXR_MULTILAYER",
                        "OPEN_EXR_MULTILAYER": "OPEN_EXR_MULTILAYER"
                    }
                    format_value = format_map.get(defaults["default_file_format"], "OPEN_EXR")
                    props.output_format = format_value
                
                logger.info("Successfully initialized default passes")
        else:
            logger.warning("Scene does not have shotput properties")
                    
    except Exception as e:
        logger.error(f"Error initializing default passes: {e}")
        print(f"Shotput: Error initializing default passes: {e}")
        import traceback
        traceback.print_exc()


def ensure_scene_tokens_from_preferences():
    """
    Ensure scene properties use addon preference defaults if not already customized.
    
    This should be called when the UI is first accessed to ensure that
    scene properties reflect user's preference settings rather than hardcoded defaults.
    
    Only updates tokens if they are still at hardcoded default values.
    """
    try:
        scene = bpy.context.scene
        if not hasattr(scene, 'shotput'):
            return
        
        props = scene.shotput
        
        # Check if we have a JSON preset loaded
        has_json_preset = os.environ.get('SHOTPUT_PRESET_PATH') is not None
        
        # Only update if no JSON preset (preferences should take precedence over hardcoded defaults)
        if not has_json_preset:
            # Get preference defaults
            pref_root_token = get_default_root_folder_token()
            pref_file_token = get_default_file_name_token()
            
            # Hardcoded defaults from property definition
            hardcoded_root = "{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}"
            hardcoded_file = "{outputlayer}_{passname}_{variant}"
            
            # Update if still at hardcoded default (user hasn't customized)
            if props.root_folder_token == hardcoded_root and pref_root_token != hardcoded_root:
                props.root_folder_token = pref_root_token
                logger.debug(f"Updated scene root_folder_token from preferences: {pref_root_token}")
            
            if props.file_name_token == hardcoded_file and pref_file_token != hardcoded_file:
                props.file_name_token = pref_file_token
                logger.debug(f"Updated scene file_name_token from preferences: {pref_file_token}")
    
    except Exception as e:
        logger.warning(f"Could not update scene tokens from preferences: {e}")

