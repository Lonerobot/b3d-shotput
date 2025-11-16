"""
Preset loading operator from environment path.
"""
import bpy
import os
from pathlib import Path

from ...utils.log import LoggerFactory

logger = LoggerFactory.logger_obj()


class SHOTPUT_OT_LoadPresetFromEnvironment(bpy.types.Operator):
    """Load a preset file from the SHOTPUT_PRESET_PATH environment directory"""
    bl_idname = "shotput.load_preset_from_environment"
    bl_label = "Load Preset from Environment"
    bl_description = "Load a preset from the SHOTPUT_PRESET_PATH directory"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_filename: bpy.props.StringProperty(
        name="Preset File",
        description="Preset file to load"
    )
    
    def execute(self, context):
        try:
            import json
            from ...utils.defaults import is_valid_shotput_preset
            
            # Get the environment path
            env_path = os.environ.get('SHOTPUT_PRESET_PATH')
            if not env_path:
                self.report({'ERROR'}, "SHOTPUT_PRESET_PATH environment variable not set")
                return {'CANCELLED'}
            
            # Build full path to preset file
            preset_path = Path(env_path)
            if preset_path.is_file():
                # If env path points to a file, use its directory
                preset_path = preset_path.parent / self.preset_filename
            else:
                # If env path is a directory, use it directly
                preset_path = preset_path / self.preset_filename
            
            if not preset_path.exists():
                self.report({'ERROR'}, f"Preset file not found: {preset_path}")
                return {'CANCELLED'}
            
            # Load JSON file
            with open(preset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate preset structure
            if not is_valid_shotput_preset(data):
                self.report({'ERROR'}, "Invalid Shotput preset file structure")
                return {'CANCELLED'}
            
            # Apply preset to scene properties (same logic as OT_Load_Preset)
            scene = context.scene
            if not hasattr(scene, 'shotput'):
                self.report({'ERROR'}, "Shotput properties not found")
                return {'CANCELLED'}
            
            props = scene.shotput
            
            # Clear existing pass collections
            props.core_passes.clear()
            props.aov_passes.clear()
            
            # Load core passes
            for pass_name in data.get("core_passes", []):
                item = props.core_passes.add()
                item.name = pass_name
            
            # Load AOV passes
            for pass_name in data.get("aovs", []):
                item = props.aov_passes.add()
                item.name = pass_name
            
            # Load data passes checkboxes
            # Handle both old format (list) and new format (dict)
            data_passes = data.get("data_passes", {})
            if isinstance(data_passes, list):
                # Old format: list of pass names - enable them as checkboxes
                for pass_name in data_passes:
                    if hasattr(props, pass_name):
                        setattr(props, pass_name, True)
            elif isinstance(data_passes, dict):
                # New format: dict with explicit True/False values
                props.z = data_passes.get("z", False)
                props.mist = data_passes.get("mist", False)
                props.normal = data_passes.get("normal", False)
                props.vector = data_passes.get("vector", False)
                props.position = data_passes.get("position", False)
                props.occlusion = data_passes.get("occlusion", False)
                props.volume_direct = data_passes.get("volume_direct", False)
                props.volume_indirect = data_passes.get("volume_indirect", False)
                props.crypto_object = data_passes.get("crypto_object", False)
                props.crypto_material = data_passes.get("crypto_material", False)
                props.crypto_asset = data_passes.get("crypto_asset", False)
            
            # Load path tokens
            if "root_folder_token" in data:
                props.root_folder_token = data["root_folder_token"]
            if "file_name_token" in data:
                props.file_name_token = data["file_name_token"]
            
            # Load format
            if "default_file_format" in data:
                props.output_format = data["default_file_format"]
            
            # Load other properties
            if "output_layer" in data:
                props.output_layer = data["output_layer"]
            elif "render_layer" in data:  # Backward compatibility
                props.output_layer = data["render_layer"]
            if "variant" in data:
                props.variant = data["variant"]
            if "core_override" in data:
                props.core_override = data["core_override"]
            if "aov_override" in data:
                props.aov_override = data["aov_override"]
            
            preset_name = Path(self.preset_filename).stem
            self.report({'INFO'}, f"Loaded preset '{preset_name}' from environment")
            logger.info(f"Loaded Shotput preset from environment: {preset_path}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {str(e)}")
            logger.error(f"Error loading preset from environment: {e}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        # This gets called when the operator is invoked
        # Just execute directly since the filename is already set
        return self.execute(context)


classes = (
    SHOTPUT_OT_LoadPresetFromEnvironment,
)
