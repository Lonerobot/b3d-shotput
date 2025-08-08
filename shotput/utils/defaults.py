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
    """Load default passes from JSON file, checking ENV var first"""
    print("Shotput: load_default_passes() called")
    
    # Check for environment variable first
    env_path = os.environ.get('SHOTPUT_PRESET_PATH')
    if env_path:
        print(f"Shotput: Found SHOTPUT_PRESET_PATH: {env_path}")
        env_path = Path(env_path)
        if env_path.exists():
            if env_path.is_file():
                # Direct file path
                json_files = [env_path]
            else:
                # Directory path - search for JSON files
                json_files = list(env_path.glob('*.json'))
        else:
            json_files = []
            print(f"Shotput: Environment path does not exist: {env_path}")
    else:
        # Fallback to addon's default JSON file
        addon_dir = Path(__file__).parent.parent
        default_path = addon_dir / "data" / "default_passes.json"
        json_files = [default_path]
        print(f"Shotput: Using default JSON path: {default_path}")
    
    print(f"Shotput: Found {len(json_files)} JSON files to try")
    
    # Try each JSON file until we find a valid Shotput preset
    for json_path in json_files:
        print(f"Shotput: Trying to load: {json_path}")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if is_valid_shotput_preset(data):
                    print(f"Shotput: Loaded preset from {json_path}")
                    return data
                else:
                    print(f"Shotput: Skipping invalid preset structure in {json_path}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Shotput: Could not read {json_path}: {e}")
            continue
    
    # If no valid preset found, return fallback defaults
    print("Shotput: No valid preset found, using fallback defaults")
    return {
        "_info": "Fallback defaults - no valid preset found",
        "core_passes": ["Beauty", "Diffuse", "Specular"],
        "aovs": ["Ambient Occlusion", "Shadow"],
        "data_passes": ["z", "normal", "crypto_object"],
        "render_layer": "ViewLayer",
        "variant": "v001",
        "core_override": "Core",
        "aov_override": "AOV",
        "root_folder_token": "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}",
        "file_name_token": "{renderlayer}_{passname}_{variant}",
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
        scene = bpy.context.scene
        if hasattr(scene, 'shotput'):
            props = scene.shotput
            defaults = load_default_passes()
            
            if defaults:
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
                
                # Set default scene properties
                if "render_layer" in defaults:
                    props.render_layer = defaults["render_layer"]
                if "variant" in defaults:
                    props.variant = defaults["variant"]
                if "core_override" in defaults:
                    props.core_override = defaults["core_override"]
                if "aov_override" in defaults:
                    props.aov_override = defaults["aov_override"]
                if "root_folder_token" in defaults:
                    props.root_folder_token = defaults["root_folder_token"]
                if "file_name_token" in defaults:
                    props.file_name_token = defaults["file_name_token"]
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
                    
    except Exception as e:
        print(f"Shotput: Error initializing default passes: {e}")
        import traceback
        traceback.print_exc()
