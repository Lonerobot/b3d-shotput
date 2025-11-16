import bpy
from . import bl_info
from . import __release_stage__
import os

from .utils.log import LoggerFactory
from .utils import custom_icons

logger = LoggerFactory.logger_obj()

def get_panel_title():
    """Generate panel title with AYON status if available"""
    base_title = f"THE LINE - Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}-{__release_stage__}"
    
    # Check if AYON environment is present
    if os.getenv("AYON_PROJECT_NAME"):
        return f"{base_title} - AYON Enabled"
    
    return base_title

class SHOTPUT_OT_CorePassAdd(bpy.types.Operator):
    bl_idname = "shotput.core_pass_add"
    bl_label = "Add Core Pass"
    def execute(self, context):
        shotput = context.scene.shotput
        item = shotput.core_passes.add()
        item.name = f"item{len(shotput.core_passes)}"
        shotput.core_passes_index = len(shotput.core_passes) - 1
        return {'FINISHED'}

class SHOTPUT_OT_CorePassRemove(bpy.types.Operator):
    bl_idname = "shotput.core_pass_remove"
    bl_label = "Remove Core Pass"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.core_passes_index
        if shotput.core_passes and idx < len(shotput.core_passes):
            shotput.core_passes.remove(idx)
            shotput.core_passes_index = max(0, idx - 1)
        return {'FINISHED'}

class SHOTPUT_OT_CorePassMoveUp(bpy.types.Operator):
    bl_idname = "shotput.core_pass_move_up"
    bl_label = "Move Core Pass Up"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.core_passes_index
        if idx > 0:
            shotput.core_passes.move(idx, idx - 1)
            shotput.core_passes_index -= 1
        return {'FINISHED'}

class SHOTPUT_OT_CorePassMoveDown(bpy.types.Operator):
    bl_idname = "shotput.core_pass_move_down"
    bl_label = "Move Core Pass Down"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.core_passes_index
        if idx < len(shotput.core_passes) - 1:
            shotput.core_passes.move(idx, idx + 1)
            shotput.core_passes_index += 1
        return {'FINISHED'}

class SHOTPUT_OT_AOVPassAdd(bpy.types.Operator):
    bl_idname = "shotput.aov_pass_add"
    bl_label = "Add AOV Pass"
    def execute(self, context):
        shotput = context.scene.shotput
        item = shotput.aov_passes.add()
        item.name = f"item{len(shotput.aov_passes)}"
        shotput.aov_passes_index = len(shotput.aov_passes) - 1
        return {'FINISHED'}

class SHOTPUT_OT_AOVPassRemove(bpy.types.Operator):
    bl_idname = "shotput.aov_pass_remove"
    bl_label = "Remove AOV Pass"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.aov_passes_index
        if shotput.aov_passes and idx < len(shotput.aov_passes):
            shotput.aov_passes.remove(idx)
            shotput.aov_passes_index = max(0, idx - 1)
        return {'FINISHED'}

class SHOTPUT_OT_AOVPassMoveUp(bpy.types.Operator):
    bl_idname = "shotput.aov_pass_move_up"
    bl_label = "Move AOV Pass Up"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.aov_passes_index
        if idx > 0:
            shotput.aov_passes.move(idx, idx - 1)
            shotput.aov_passes_index -= 1
        return {'FINISHED'}

class SHOTPUT_OT_AOVPassMoveDown(bpy.types.Operator):
    bl_idname = "shotput.aov_pass_move_down"
    bl_label = "Move AOV Pass Down"
    def execute(self, context):
        shotput = context.scene.shotput
        idx = shotput.aov_passes_index
        if idx < len(shotput.aov_passes) - 1:
            shotput.aov_passes.move(idx, idx + 1)
            shotput.aov_passes_index += 1
        return {'FINISHED'}

def get_active_file_output_node(context):
    """Helper function to get active File Output node from context"""
    active_node = None
    
    # Try context.active_node first
    if hasattr(context, 'active_node') and context.active_node:
        active_node = context.active_node
    # Try getting from space data
    elif context.space_data and hasattr(context.space_data, 'node_tree'):
        node_tree = context.space_data.node_tree
        if node_tree and hasattr(node_tree.nodes, 'active'):
            active_node = node_tree.nodes.active
    # Try getting from scene node tree (compositor)
    elif hasattr(context.scene, 'node_tree') and context.scene.node_tree:
        node_tree = context.scene.node_tree
        if hasattr(node_tree.nodes, 'active'):
            active_node = node_tree.nodes.active
    # If still no node, try to find any selected File Output node
    elif hasattr(context.scene, 'node_tree') and context.scene.node_tree:
        node_tree = context.scene.node_tree
        for node in node_tree.nodes:
            if node.type == 'OUTPUT_FILE' and node.select and hasattr(node, 'shotput_data'):
                active_node = node
                break
    
    return active_node if active_node and active_node.type == 'OUTPUT_FILE' else None

# Operators for managing stored passes on File Output nodes
class SHOTPUT_OT_StoredPassAdd(bpy.types.Operator):
    bl_idname = "shotput.stored_pass_add"
    bl_label = "Add Stored Pass"
    bl_description = "Add a new pass to this File Output node"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node:
            self.report({'ERROR'}, "No File Output node selected")
            return {'CANCELLED'}
        if not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "Selected node is not a Shotput File Output node")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        item = shotput_data.stored_passes.add()
        item.name = f"Pass{len(shotput_data.stored_passes)}"
        shotput_data.stored_passes_index = len(shotput_data.stored_passes) - 1
        return {'FINISHED'}

class SHOTPUT_OT_StoredPassRemove(bpy.types.Operator):
    bl_idname = "shotput.stored_pass_remove"
    bl_label = "Remove Stored Pass"
    bl_description = "Remove the selected pass from this File Output node"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node:
            self.report({'ERROR'}, "No File Output node selected")
            return {'CANCELLED'}
        if not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "Selected node is not a Shotput File Output node")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        idx = shotput_data.stored_passes_index
        if shotput_data.stored_passes and idx < len(shotput_data.stored_passes):
            # Just remove from stored passes - sync separately
            shotput_data.stored_passes.remove(idx)
            shotput_data.stored_passes_index = max(0, idx - 1)
            
        return {'FINISHED'}

class SHOTPUT_OT_StoredPassMoveUp(bpy.types.Operator):
    bl_idname = "shotput.stored_pass_move_up"
    bl_label = "Move Stored Pass Up"
    bl_description = "Move the selected pass up in the list"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node or not hasattr(node, 'shotput_data'):
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        idx = shotput_data.stored_passes_index
        if idx > 0:
            shotput_data.stored_passes.move(idx, idx - 1)
            shotput_data.stored_passes_index -= 1
            
        return {'FINISHED'}

class SHOTPUT_OT_StoredPassMoveDown(bpy.types.Operator):
    bl_idname = "shotput.stored_pass_move_down"
    bl_label = "Move Stored Pass Down"
    bl_description = "Move the selected pass down in the list"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node or not hasattr(node, 'shotput_data'):
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        idx = shotput_data.stored_passes_index
        if idx < len(shotput_data.stored_passes) - 1:
            shotput_data.stored_passes.move(idx, idx + 1)
            shotput_data.stored_passes_index += 1
            
        return {'FINISHED'}

class SHOTPUT_OT_TogglePathLinking(bpy.types.Operator):
    bl_idname = "shotput.toggle_path_linking"
    bl_label = "Toggle Path Linking"
    bl_description = "Toggle path linking for this File Output node"
    
    def execute(self, context):
        # Get active node (can be File Output or Composite)
        node = context.active_node
        if not node or node.type not in ['OUTPUT_FILE', 'COMPOSITE'] or not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "No valid Shotput node selected")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        
        # Toggle the path linking
        new_state = not shotput_data.path_linked
        
        print(f"Shotput: Toggling path linking from {shotput_data.path_linked} to {new_state} for node {node.name}")
        
        if new_state:
            # Enabling path linking
            if shotput_data.root_folder_token and not shotput_data.root_folder_token_backup:
                # Back up the current root folder token
                shotput_data.root_folder_token_backup = shotput_data.root_folder_token
                print(f"Shotput: Backed up root folder token: {shotput_data.root_folder_token_backup}")
                
                # Set appropriate token based on node type and format
                if (node.name == "Shotput_Data_Passes" and 
                    hasattr(node, 'format') and 
                    node.format.file_format == 'OPEN_EXR_MULTILAYER'):
                    # For data passes with multilayer EXR, include filename token
                    shotput_data.root_folder_token = "{passname}"
                    print(f"Shotput: Set multilayer EXR token: {shotput_data.root_folder_token}")
                else:
                    # Default simple token for other nodes
                    shotput_data.root_folder_token = "{passname}"
                    print(f"Shotput: Set simple token: {shotput_data.root_folder_token}")
        else:
            # Disabling path linking
            if shotput_data.root_folder_token_backup:
                # Restore the backed up root folder token
                shotput_data.root_folder_token = shotput_data.root_folder_token_backup
                print(f"Shotput: Restored root folder token: {shotput_data.root_folder_token}")
                # Clear the backup
                shotput_data.root_folder_token_backup = ""
                print("Shotput: Cleared backup")
            else:
                print("Shotput: No backup found to restore")
        
        # Set the new state
        shotput_data.path_linked = new_state
        print(f"Shotput: Path linking is now: {shotput_data.path_linked}")
        
        return {'FINISHED'}

class SHOTPUT_OT_InsertToken(bpy.types.Operator):
    bl_idname = "shotput.insert_token"
    bl_label = "Insert Token"
    bl_description = "Insert a token into the path field"
    
    token: bpy.props.StringProperty(name="Token")
    property_path: bpy.props.StringProperty(name="Property Path")
    
    def execute(self, context):
        try:
            # Get the target property based on property_path
            if self.property_path.startswith("scene.shotput."):
                # Scene-level property
                prop_name = self.property_path.replace("scene.shotput.", "")
                shotput = context.scene.shotput
                current_value = getattr(shotput, prop_name, "")
                new_value = current_value + "{" + self.token + "}"
                setattr(shotput, prop_name, new_value)
            elif self.property_path.startswith("node.shotput_data."):
                # Node-level property
                prop_name = self.property_path.replace("node.shotput_data.", "")
                node = context.active_node
                if not node or not hasattr(node, 'shotput_data'):
                    self.report({'ERROR'}, "No Shotput node selected")
                    return {'CANCELLED'}
                shotput_data = node.shotput_data
                current_value = getattr(shotput_data, prop_name, "")
                new_value = current_value + "{" + self.token + "}"
                setattr(shotput_data, prop_name, new_value)
            else:
                self.report({'ERROR'}, f"Unknown property path: {self.property_path}")
                return {'CANCELLED'}
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to insert token: {str(e)}")
            return {'CANCELLED'}

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
            from pathlib import Path
            from .utils.defaults import is_valid_shotput_preset
            
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

class SHOTPUT_MT_PresetEnvironmentMenu(bpy.types.Menu):
    """Menu listing available preset files from SHOTPUT_PRESET_PATH"""
    bl_idname = "SHOTPUT_MT_preset_environment_menu"
    bl_label = "Load from Environment"
    
    def draw(self, context):
        layout = self.layout
        
        # Get the environment path
        env_path = os.environ.get('SHOTPUT_PRESET_PATH')
        if not env_path:
            icon_error_env = custom_icons.get_icon_id_or_fallback('error')
            layout.label(text="SHOTPUT_PRESET_PATH not set", **icon_error_env)
            return
        
        from pathlib import Path
        preset_path = Path(env_path)
        
        # If env path is a file, use its directory
        if preset_path.is_file():
            preset_dir = preset_path.parent
        elif preset_path.is_dir():
            preset_dir = preset_path
        else:
            icon_error_invalid = custom_icons.get_icon_id_or_fallback('error')
            layout.label(text="Invalid SHOTPUT_PRESET_PATH", **icon_error_invalid)
            return
        
        # Find all JSON files in the directory
        json_files = sorted(preset_dir.glob("*.json"))
        
        if not json_files:
            icon_info_env = custom_icons.get_icon_id_or_fallback('info')
            layout.label(text="No preset files found", **icon_info_env)
            return
        
        # Add an operator for each JSON file
        icon_preset_env = custom_icons.get_icon_id_or_fallback('preset')
        for json_file in json_files:
            op = layout.operator("shotput.load_preset_from_environment", 
                               text=json_file.stem, 
                               **icon_preset_env)
            op.preset_filename = json_file.name


# Token menu classes for different fields
class SHOTPUT_MT_TokenMenuRoot(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_root"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "scene.shotput.root_folder_token"
        
        # Core Shotput tokens
        icon_file_folder_token = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon_file_folder_token)
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        icon_dot = custom_icons.get_icon_id_or_fallback('dot')
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        icon_network = custom_icons.get_icon_id_or_fallback('network_drive')
        layout.label(text="AYON Tokens", **icon_network)
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        icon_blender = custom_icons.get_icon_id_or_fallback('blender')
        layout.label(text="Blender Tokens", **icon_blender)
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        icon_time = custom_icons.get_icon_id_or_fallback('time')
        layout.label(text="Date/Time Tokens", **icon_time)
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuFile(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_file"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "scene.shotput.file_name_token"
        
        # Core Shotput tokens
        icon_file_folder_token2 = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon_file_folder_token2)
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        icon_dot2 = custom_icons.get_icon_id_or_fallback('dot')
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot2)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        icon_network2 = custom_icons.get_icon_id_or_fallback('network_drive')
        layout.label(text="AYON Tokens", **icon_network2)
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot2)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        icon_blender2 = custom_icons.get_icon_id_or_fallback('blender')
        layout.label(text="Blender Tokens", **icon_blender2)
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot2)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        icon_time2 = custom_icons.get_icon_id_or_fallback('time')
        layout.label(text="Date/Time Tokens", **icon_time2)
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot2)
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuNodeRoot(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_node_root"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "node.shotput_data.root_folder_token"
        
        # Core Shotput tokens
        icon_file_folder_token3 = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon_file_folder_token3)
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        icon_dot3 = custom_icons.get_icon_id_or_fallback('dot')
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot3)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        icon_network3 = custom_icons.get_icon_id_or_fallback('network_drive')
        layout.label(text="AYON Tokens", **icon_network3)
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot3)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        icon_blender3 = custom_icons.get_icon_id_or_fallback('blender')
        layout.label(text="Blender Tokens", **icon_blender3)
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot3)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        icon_time3 = custom_icons.get_icon_id_or_fallback('time')
        layout.label(text="Date/Time Tokens", **icon_time3)
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot3)
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuNodeFile(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_node_file"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "node.shotput_data.file_name_token"
        
        # Core Shotput tokens
        icon_file_folder_token4 = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon_file_folder_token4)
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        icon_dot4 = custom_icons.get_icon_id_or_fallback('dot')
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot4)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        icon_network4 = custom_icons.get_icon_id_or_fallback('network_drive')
        layout.label(text="AYON Tokens", **icon_network4)
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot4)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        icon_blender4 = custom_icons.get_icon_id_or_fallback('blender')
        layout.label(text="Blender Tokens", **icon_blender4)
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot4)
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        icon_time4 = custom_icons.get_icon_id_or_fallback('time')
        layout.label(text="Date/Time Tokens", **icon_time4)
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot4)
            op.token = token
            op.property_path = prop_path

class SHOTPUT_OT_SyncNodePasses(bpy.types.Operator):
    bl_idname = "shotput.sync_node_passes"
    bl_label = "Sync Node Passes"
    bl_description = "Sync the stored passes list to the actual File Output node slots (non-destructive)"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node:
            self.report({'ERROR'}, "No File Output node selected")
            return {'CANCELLED'}
        if not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "Selected node is not a Shotput File Output node")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        
        # Get current node slot names
        current_slots = []
        for i, file_slot in enumerate(node.file_slots):
            current_slots.append(file_slot.path)
        
        # Get desired pass names from stored_passes
        desired_passes = []
        is_data_pass_node = node.name == "Shotput_Data_Passes"
        
        for pass_item in shotput_data.stored_passes:
            if pass_item.name.strip():  # Only add non-empty names
                pass_name = pass_item.name.strip()
                
                # Handle data pass cryptomatte expansion
                if is_data_pass_node:
                    if pass_name == "Cryptomatte Object":
                        desired_passes.extend(['CryptoObject00', 'CryptoObject01', 'CryptoObject02'])
                    elif pass_name == "Cryptomatte Material":
                        desired_passes.extend(['CryptoMaterial00', 'CryptoMaterial01', 'CryptoMaterial02'])
                    elif pass_name == "Cryptomatte Asset":
                        desired_passes.extend(['CryptoAsset00', 'CryptoAsset01', 'CryptoAsset02'])
                    elif pass_name == "Depth":
                        desired_passes.append("depth")  # Map "Depth" to "depth" for compositing
                    else:
                        # Map display names back to channel names for data passes
                        channel_mapping = {
                            "Mist": "mist",
                            "Normal": "normal", 
                            "Motion Vector": "vector",
                            "Position": "position",
                            "Ambient Occlusion": "occlusion"
                        }
                        channel_name = channel_mapping.get(pass_name, pass_name.lower())
                        desired_passes.append(channel_name)
                else:
                    # Non-data passes, use pass name directly
                    desired_passes.append(pass_name)
        
        if not desired_passes:
            self.report({'WARNING'}, "No passes defined to sync")
            return {'CANCELLED'}

        changes_made = False
        
        # Special handling for EXR multilayer format (data passes)
        if is_data_pass_node and node.format.file_format == 'OPEN_EXR_MULTILAYER':
            # For EXR multilayer, we need to recreate slots like in create_data_passes.py
            print("Shotput: Sync - EXR multilayer detected, using slot recreation approach")
            
            # Clear all existing slots and recreate them
            # This ensures proper input/slot name synchronization for EXR multilayer
            while len(node.file_slots) > 0:
                try:
                    node.inputs.remove(node.inputs[-1])
                except (RuntimeError, IndexError, ValueError):
                    break
            
            # Recreate all slots with desired names
            for desired_name in desired_passes:
                node.file_slots.new(desired_name)
                print(f"Shotput: Recreated slot: '{desired_name}'")
            
            changes_made = True
        else:
            # Standard slot renaming for non-EXR multilayer formats
            # Rename existing slots to match desired names
            for i, desired_name in enumerate(desired_passes):
                if i < len(node.file_slots):
                    current_name = node.file_slots[i].path
                    if current_name != desired_name:
                        node.file_slots[i].path = desired_name
                        changes_made = True
                        print(f"Renamed slot {i}: '{current_name}' -> '{desired_name}'")
                else:
                    # Add new slot for this pass
                    node.file_slots.new(desired_name)
                    changes_made = True
                    print(f"Added new slot: '{desired_name}'")        # Handle removed passes (only if we have fewer desired passes than current slots)
        if len(desired_passes) < len(node.file_slots):
            # We have fewer desired passes than current slots
            # Rebuild file slots to match desired passes (simpler and more reliable)
            
            # Check if any of the slots to be removed have connections
            has_connections = False
            for i in range(len(desired_passes), len(node.file_slots)):
                slot = node.file_slots[i]
                if any(link.to_socket == slot for link in node.id_data.links):
                    has_connections = True
                    print(f"Keeping connected slot {i}: '{slot.path}'")
                    break
            
            # Only rebuild if no connections would be lost
            if not has_connections:
                print(f"Rebuilding file slots to match {len(desired_passes)} desired passes")
                # Clear all slots and rebuild with desired passes
                node.file_slots.clear()
                for pass_name in desired_passes:
                    node.file_slots.new(pass_name)
                changes_made = True
            else:
                print("Keeping extra slots to preserve connections")
        
        if changes_made:
            self.report({'INFO'}, f"Synced {len(desired_passes)} passes to node slots")
        else:
            self.report({'INFO'}, "Node slots already match stored passes")
        
        # Update node label based on current Shotput properties
        self._update_node_label(node, shotput_data)
            
        return {'FINISHED'}
    
    def _update_node_label(self, node, shotput_data):
        """Update the node label based on current Shotput properties"""
        try:
            # Get the current properties
            output_layer = getattr(shotput_data, 'output_layer', 'ViewLayer')
            pass_name = getattr(shotput_data, 'pass_name', 'Pass')
            variant = getattr(shotput_data, 'variant', 'MAIN')
            
            # Generate new label in the standard format
            new_label = f"{output_layer}.{pass_name}.{variant}"
            
            # Only update if the label has changed
            if node.label != new_label:
                old_label = node.label
                node.label = new_label
                print(f"Shotput: Updated node label: '{old_label}' -> '{new_label}'")
                
        except Exception as e:
            print(f"Shotput: Error updating node label: {e}")

# UIList for passes
class SHOTPUT_UL_CorePasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Use custom icon if available, otherwise fallback to built-in
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Use custom icon if available, otherwise fallback to built-in
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

# UIList for stored passes on File Output nodes
class SHOTPUT_UL_StoredPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

class TL_PT_Shotput_UI(bpy.types.Panel):
    bl_label = get_panel_title()
    bl_category = "Shotput"
    bl_context = "output"
    bl_order = 2
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
        
    def draw(self, context):
        layout = self.layout
        # layout.scale_y = 1.1
        shotput = context.scene.shotput

        # Welcome/Description Box
        box = layout.box()
        col = box.column(align=True)
        
        # Show AYON icon if AYON is enabled
        if os.getenv("AYON_PROJECT_NAME"):
            icon_ayon = custom_icons.get_icon_id_or_fallback('ayon')
            col.label(text="Shotput - Tokenised Render Output System", **icon_ayon)
        else:
            icon_renderlayers = custom_icons.get_icon_id_or_fallback('renderlayers')
            col.label(text="Shotput - Tokenised Render Output System", **icon_renderlayers)
        
        col.separator(factor=0.5)
        
        # Multi-line description with smaller text
        col.scale_y = 0.8
        col.label(text="Create and update automatic versions for renders")

        # Scene Properties Box - Output Layer and Variant
        box = layout.box()
        icon_scene = custom_icons.get_icon_id_or_fallback('scene_data')
        box.label(text="Output Node Properties", **icon_scene)
        box.prop(shotput, "output_layer", text="Output Layer")
        box.prop(shotput, "variant", text="Variant")

        # Update Version - larger button
        
        # v1.1.2 seeing if removing these in favour of the menu update is better UX
        # row = layout.row()
        # row.scale_y = 1.5
        # icon_refresh = custom_icons.get_icon_id_or_fallback('file_refresh')
        # row.operator("shotput.update_version", text="Update Version", **icon_refresh)

        # # Open Output Folder
        # row = layout.row()
        # icon_folder = custom_icons.get_icon_id_or_fallback('folder_redirect')
        # row.operator("shotput.open_output_folder", text="Open Output Folder", **icon_folder)
       
        box = layout.box()
        icon_nodetree = custom_icons.get_icon_id_or_fallback('nodetree')
        box.label(text="Create Passes", **icon_nodetree)
        

        
        if shotput.use_render_layer_channels:
            # Render Layer Channels mode - only show Core operator
            row = box.row()
            row.scale_y = 1.5
            icon_params = custom_icons.get_icon_id_or_fallback('core')
            row.operator("shotput.create_core_passes", text="Create All Passes (From Render Layer)", **icon_params)
            
            # Add helpful info
            col = box.column()
            col.scale_y = 0.8
            icon_info = custom_icons.get_icon_id_or_fallback('info')
            col.label(text="Creates a shotput file output with all enabled render layer passes", **icon_info)
            
        else:
            # Manual mode - show all operators
            # 4x1 horizontal layout for operators with increased height
            row = box.row(align=True)
            row.scale_y = 1.5
            icon_core = custom_icons.get_icon_id_or_fallback('core')
            row.operator("shotput.create_core_passes", text="Core", **icon_core)
            icon_comp = custom_icons.get_icon_id_or_fallback('composite')
            row.operator("shotput.create_linked_composite", text="Composite", **icon_comp)
            icon_aov = custom_icons.get_icon_id_or_fallback('aov')
            row.operator("shotput.create_aov_passes", text="AOV", **icon_aov)
            icon_data = custom_icons.get_icon_id_or_fallback('data')
            row.operator("shotput.create_data_passes", text="Data", **icon_data)
        
        # Only show these options in manual mode
        if not shotput.use_render_layer_channels:
            box.prop(shotput, "create_composite_from_core", text="Create Linked Composite Node from Core")
            
        box.prop(shotput, "lazy_hook_up", text="Auto-Connect to Render Layer")
        # Add the "Use Render Layer Channels" checkbox
        box.prop(shotput, "use_render_layer_channels", text="Use Render Layer Channels")

        # Path Tokens Box - Root Folder and File Name with icon operators
        box = layout.box()
        icon_file_folder = custom_icons.get_icon_id_or_fallback('file_folder')
        box.label(text="Path Tokens", **icon_file_folder)
        
        # Root folder with token menu and preview paths button
        row = box.row(align=True)
        row.prop(shotput, "root_folder_token", text="Root Folder")
        icon_add = custom_icons.get_icon_id_or_fallback('add')
        row.menu("SHOTPUT_MT_token_menu_root", text="", **icon_add)
        icon_file_folder2 = custom_icons.get_icon_id_or_fallback('file_folder')
        row.operator("shotput.preview_paths", text="", **icon_file_folder2)
        
        # File name with token menu and token help button  
        row = box.row(align=True)
        row.prop(shotput, "file_name_token", text="File Name")
        icon_add2 = custom_icons.get_icon_id_or_fallback('add')
        row.menu("SHOTPUT_MT_token_menu_file", text="", **icon_add2)
        icon_help = custom_icons.get_icon_id_or_fallback('token_help')
        row.operator("shotput.token_help", text="", **icon_help)
        
        # Output Format in compact 2x2 grid
        box.label(text="Output Format")
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.prop_enum(shotput, "output_format", 'PNG')
        grid.prop_enum(shotput, "output_format", 'JPEG')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR_MULTILAYER')

        # Only show pass selection sections in manual mode
        if not shotput.use_render_layer_channels:
            # Core and AOV Passes side by side
            box = layout.box()
            
            # Header row with both expand toggles
            row = box.row()
            expand_core = shotput.expand_core_ui if hasattr(shotput, 'expand_core_ui') else False
            expand_aov = shotput.expand_aov_ui if hasattr(shotput, 'expand_aov_ui') else False
            
            # Core header (left half)
            split = row.split(factor=0.5)
            core_row = split.row()
            core_row.prop(shotput, "expand_core_ui", 
                         icon="TRIA_DOWN" if expand_core else "TRIA_RIGHT", 
                         icon_only=True, emboss=False)
            icon_core = custom_icons.get_icon_id_or_fallback('core')
            core_row.label(text="Core Passes", **icon_core)
            
            # AOV header (right half)
            aov_row = split.row()
            aov_row.prop(shotput, "expand_aov_ui", 
                        icon="TRIA_DOWN" if expand_aov else "TRIA_RIGHT", 
                        icon_only=True, emboss=False)
            icon_aov = custom_icons.get_icon_id_or_fallback('aov')
            aov_row.label(text="AOV Passes", **icon_aov)
            
            # Content row - split into two columns
            if expand_core or expand_aov:
                content_split = box.split(factor=0.5)
                
                # Left column - Core Passes
                core_col = content_split.column()
                if expand_core:
                    core_col.prop(shotput, "core_override", text="Core Override")
                    row = core_col.row()
                    row.template_list("SHOTPUT_UL_CorePasses", "", shotput, "core_passes", shotput, "core_passes_index", rows=3)
                    col = row.column(align=True)
                    icon_add_core = custom_icons.get_icon_id_or_fallback('add')
                    col.operator("shotput.core_pass_add", text="", **icon_add_core)
                    icon_remove_core = custom_icons.get_icon_id_or_fallback('remove')
                    col.operator("shotput.core_pass_remove", text="", **icon_remove_core)
                    col.separator()
                    icon_up_core = custom_icons.get_icon_id_or_fallback('tria_up')
                    col.operator("shotput.core_pass_move_up", text="", **icon_up_core)
                    icon_down_core = custom_icons.get_icon_id_or_fallback('tria_down')
                    col.operator("shotput.core_pass_move_down", text="", **icon_down_core)
                
                # Right column - AOV Passes
                aov_col = content_split.column()
                if expand_aov:
                    aov_col.prop(shotput, "aov_override", text="AOV Override")
                  
                    row = aov_col.row()
                    row.template_list("SHOTPUT_UL_AOVPasses", "", shotput, "aov_passes", shotput, "aov_passes_index", rows=3)
                    col = row.column(align=True)
                    icon_add_aov = custom_icons.get_icon_id_or_fallback('add')
                    col.operator("shotput.aov_pass_add", text="", **icon_add_aov)
                    icon_remove_aov = custom_icons.get_icon_id_or_fallback('remove')
                    col.operator("shotput.aov_pass_remove", text="", **icon_remove_aov)
                    col.separator()
                    icon_up_aov = custom_icons.get_icon_id_or_fallback('tria_up')
                    col.operator("shotput.aov_pass_move_up", text="", **icon_up_aov)
                    icon_down_aov = custom_icons.get_icon_id_or_fallback('tria_down')
                    col.operator("shotput.aov_pass_move_down", text="", **icon_down_aov)
                    
                    # Scan button for shader AOVs
                    scan_row = aov_col.row()
                    icon_zoom = custom_icons.get_icon_id_or_fallback('viewzoom')
                    scan_row.operator("shotput.scan_shader_aovs", text="Scan AOVs", **icon_zoom)

            # Data Passes Section (collapsible, closed by default)
            box = layout.box()
            row = box.row()
            expand_data = shotput.expand_data_ui if hasattr(shotput, 'expand_data_ui') else False
            row.prop(shotput, "expand_data_ui", 
                    icon="TRIA_DOWN" if expand_data else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            icon_data = custom_icons.get_icon_id_or_fallback('data')
            row.label(text="Data Passes", **icon_data)
            
            if expand_data:
                # Basic data passes in 3x2 grid with toggle buttons
                box.label(text="Basic Passes")
                grid = box.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
                grid.prop(shotput, "z", text="Depth", toggle=True)
                grid.prop(shotput, "normal", text="Normal", toggle=True)
                grid.prop(shotput, "vector", text="Vector", toggle=True)
                grid.prop(shotput, "position", text="UV", toggle=True)
                grid.prop(shotput, "mist", text="Mist", toggle=True)
                grid.prop(shotput, "occlusion", text="AO", toggle=True)
                
                # Volume passes with label and 2x1 grid
                box.separator()
                box.label(text="Volume")
                volume_grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
                volume_grid.prop(shotput, "volume_direct", text="Direct", toggle=True)
                volume_grid.prop(shotput, "volume_indirect", text="Indirect", toggle=True)
                
                # Cryptomatte passes with label and 3x1 grid
                box.separator()
                box.label(text="Cryptomatte")
                crypto_grid = box.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
                crypto_grid.prop(shotput, "crypto_object", text="Object", toggle=True)
                crypto_grid.prop(shotput, "crypto_material", text="Material", toggle=True)
                crypto_grid.prop(shotput, "crypto_asset", text="Asset", toggle=True)

        # Preset Management Box
        box = layout.box()
        icon_preset = custom_icons.get_icon_id_or_fallback('preset')
        box.label(text="Preset Management", **icon_preset)
        
        # Preset buttons
        row = box.row()
        
        # Add environment preset menu button if SHOTPUT_PRESET_PATH is set and has JSON files
        if os.environ.get('SHOTPUT_PRESET_PATH'):
            from pathlib import Path
            env_path = Path(os.environ.get('SHOTPUT_PRESET_PATH'))
            preset_dir = env_path.parent if env_path.is_file() else env_path if env_path.is_dir() else None
            
            # Only show button if directory exists and has JSON files
            if preset_dir and preset_dir.exists():
                json_files = list(preset_dir.glob("*.json"))
                if json_files:
                    icon_preset_menu = custom_icons.get_icon_id_or_fallback('preset')
                    row.menu("SHOTPUT_MT_preset_environment_menu", text="Load From Env", **icon_preset_menu)
        
        icon_import = custom_icons.get_icon_id_or_fallback('import')
        row.operator("shotput.load_preset", text="Load Pass Setup", **icon_import)
        

        icon_export = custom_icons.get_icon_id_or_fallback('export')
        row.operator("shotput.save_preset", text="Save Pass Setup", **icon_export)

# Node panel for File Output nodes with Shotput data
class TL_PT_Shotput_Node_UI(bpy.types.Panel):
    bl_label = "Shotput Output"
    bl_idname = "TL_PT_shotput_node_ui"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # Only show when a File Output or Composite node with shotput_data is selected
        return (context.space_data.type == 'NODE_EDITOR' and
                context.active_node and
                context.active_node.type in ['OUTPUT_FILE', 'COMPOSITE'] and
                hasattr(context.active_node, 'shotput_data'))
    
    def draw(self, context):
        layout = self.layout
        node = context.active_node
        shotput_data = node.shotput_data
        
        # Description/Help Box - different for File Output vs Composite nodes
        box = layout.box()
        col = box.column(align=True)
        
        if node.type == 'COMPOSITE':
            icon_info_comp = custom_icons.get_icon_id_or_fallback('info')
            col.label(text="Shotput Composite Node", **icon_info_comp)
            col.separator(factor=0.5)
            
            # Multi-line description with smaller text
            col.scale_y = 0.8
            col.label(text="This Composite node will sync the scene's render filepath when 'Update Version' is called")
        else:
            icon_info_file = custom_icons.get_icon_id_or_fallback('info')
            col.label(text="Shotput File Output Node", **icon_info_file)
            col.separator(factor=0.)
            
            # Multi-line description with smaller text
            col.scale_y = 0.8
            col.label(text="This File Output node is configured for token-based render pathing.")
  
        # Node Properties Box
        box = layout.box()
        
        # Header row with title and version
        if shotput_data.shotput_version:
            header_row = box.row()
            icon_settings_header = custom_icons.get_icon_id_or_fallback('settings')
            header_row.label(text="Shotput Properties", **icon_settings_header)
            # Add some spacing to push version to the right
            header_row.separator()
            version_label = header_row.row()
            version_label.enabled = False  # Make only the version read-only (greyed out)
            version_label.label(text=f"Version: {shotput_data.shotput_version}")
        else:
            icon_settings = custom_icons.get_icon_id_or_fallback('settings')
            box.label(text="Shotput Properties", **icon_settings)
        
        box.prop(shotput_data, "output_layer", text="Output Layer")
        box.prop(shotput_data, "pass_name", text="Pass Name")
        box.prop(shotput_data, "variant", text="Variant")
        
        # AYON Mode Toggle - only show if AYON is detected
        import os
        ayon_detected = bool(os.getenv("AYON_PROJECT_NAME"))
        if ayon_detected:
            row = box.row()
            icon_ayon = custom_icons.get_icon_id_or_fallback('ayon')
            if shotput_data.use_ayon_output_style:
                row.prop(shotput_data, "use_ayon_output_style", 
                        text="AYON Mode", 
                        toggle=True,
                        icon_value=icon_ayon.get('icon_value', 0) if isinstance(icon_ayon, dict) else 0)
            else:
                row.prop(shotput_data, "use_ayon_output_style", 
                        text="AYON Mode (Off)", 
                        toggle=True,
                        icon='CANCEL')
        
        icon_file_folder_path = custom_icons.get_icon_id_or_fallback('file_folder')
        box.label(text="Path Configuration", **icon_file_folder_path)
        
        # Path linking controls
        row = box.row()
        if shotput_data.path_linked:
            icon_linked = custom_icons.get_icon_id_or_fallback('linked')
            row.operator("shotput.toggle_path_linking", 
                        text="Path Linked", 
                        depress=True,
                        **icon_linked)
        else:
            icon_unlinked = custom_icons.get_icon_id_or_fallback('unlinked')
            row.operator("shotput.toggle_path_linking", 
                        text="Enable Path Linking", 
                        depress=False,
                        **icon_unlinked)
        
        if shotput_data.path_linked:
            # Show path linking UI
            box.prop(shotput_data, "linked_node", text="Linked Node")
            
            # Show the linked node's path if available
            linked_node = shotput_data.node
            if linked_node:
                row = box.row()
                icon_file_folder_linked = custom_icons.get_icon_id_or_fallback('file_folder')
                row.label(text=f"Linked Path: {linked_node.base_path}", **icon_file_folder_linked)
                row.enabled = False  # Make it read-only/grayed out
            else:
                row = box.row()
                icon_error = custom_icons.get_icon_id_or_fallback('error')
                row.label(text="No valid linked node selected", **icon_error)
                row.enabled = False
            
            # Append path field with consistent layout and token menu
            row = box.row(align=True)
            row.prop(shotput_data, "root_folder_token", text="Append Path")
            icon_add_node = custom_icons.get_icon_id_or_fallback('add')
            row.menu("SHOTPUT_MT_token_menu_node_root", text="", **icon_add_node)
            
            # Show backup info if available
            # if shotput_data.root_folder_token_backup:
            #     row = box.row()
            #     row.label(text="Original path backed up", icon='INFO')
            #     row.enabled = False
        else:
            # Normal path configuration with token menu
            # Make read-only if AYON mode is enabled
            row = box.row(align=True)
            if ayon_detected and shotput_data.use_ayon_output_style:
                row.enabled = False
                row.prop(shotput_data, "root_folder_token", text="Root Folder (AYON)")
            else:
                row.prop(shotput_data, "root_folder_token", text="Root Folder")
                icon_add_node2 = custom_icons.get_icon_id_or_fallback('add')
                row.menu("SHOTPUT_MT_token_menu_node_root", text="", **icon_add_node2)
        
        # File name token - make read-only if AYON mode is enabled
        row = box.row(align=True)
        if ayon_detected and shotput_data.use_ayon_output_style:
            row.enabled = False
            row.prop(shotput_data, "file_name_token", text="File Name (AYON)")
        else:
            row.prop(shotput_data, "file_name_token", text="File Name")
            icon_add_node3 = custom_icons.get_icon_id_or_fallback('add')
            row.menu("SHOTPUT_MT_token_menu_node_file", text="", **icon_add_node3)
        
        # Output Folder Actions and Lazy Hook-up in a single row
        row = box.row()
        icon_folder_node = custom_icons.get_icon_id_or_fallback('folder_redirect')
        row.operator("shotput.open_output_folder", text="Open Output Folder", **icon_folder_node)
        icon_linked_node = custom_icons.get_icon_id_or_fallback('linked')
        row.operator("shotput.lazy_hookup", text="Connect to Render Layer", **icon_linked_node)
        
        # Create Linked Composite button - only show for File Output nodes
        if node.type == 'OUTPUT_FILE':
            row = box.row()
            icon_composite = custom_icons.get_icon_id_or_fallback('composite')
            row.operator("shotput.create_linked_composite", text="Create Linked Composite Node", **icon_composite)
        
        # Stored Passes UIList - only show for File Output nodes (not Composite nodes)
        if node.type == 'OUTPUT_FILE':
            box = layout.box()
            row = box.row()
            expand_stored = shotput_data.expand_stored_ui if hasattr(shotput_data, 'expand_stored_ui') else False
            row.prop(shotput_data, "expand_stored_ui", 
                    icon="TRIA_DOWN" if expand_stored else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            icon_render_stored = custom_icons.get_icon_id_or_fallback('renderlayers')
            row.label(text="Output Passes (Advanced)", **icon_render_stored)
            
            if expand_stored:
                # Sync button (one-way: stored passes -> node slots)
                row = box.row()
                icon_sync = custom_icons.get_icon_id_or_fallback('file_refresh')
                row.operator("shotput.sync_node_passes", text="Sync to Node Slots", **icon_sync)
                
                # UIList with controls
                row = box.row()
                row.template_list("SHOTPUT_UL_StoredPasses", "", shotput_data, "stored_passes", shotput_data, "stored_passes_index", rows=3)
                col = row.column(align=True)
                icon_add_stored = custom_icons.get_icon_id_or_fallback('add')
                col.operator("shotput.stored_pass_add", text="", **icon_add_stored)
                icon_remove_stored = custom_icons.get_icon_id_or_fallback('remove')
                col.operator("shotput.stored_pass_remove", text="", **icon_remove_stored)
                col.separator()
                icon_up_stored = custom_icons.get_icon_id_or_fallback('tria_up')
                col.operator("shotput.stored_pass_move_up", text="", **icon_up_stored)
                icon_down_stored = custom_icons.get_icon_id_or_fallback('tria_down')
                col.operator("shotput.stored_pass_move_down", text="", **icon_down_stored)


class NODE_MT_shotput(bpy.types.Menu):
    """Shotput menu for compositor workspace"""
    bl_label = "Shotput"
    bl_idname = "NODE_MT_shotput"
    
    def draw(self, context):
        layout = self.layout
        
        icon_refresh_menu = custom_icons.get_icon_id_or_fallback('file_refresh')
        layout.operator("shotput.update_version", text="Update Version", **icon_refresh_menu)
        icon_folder_menu = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.operator("shotput.open_output_folder", text="Open Output Folder", **icon_folder_menu)
        layout.separator()
        icon_renderlayers_menu = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.operator("shotput.build_render_layers", text="Build Render Layers from View", **icon_renderlayers_menu)


class SHOTPUT_OT_BuildRenderLayers(bpy.types.Operator):
    """Create render layer nodes for each view layer in the scene"""
    bl_idname = "shotput.build_render_layers"
    bl_label = "View Layers To Render Layers"
    bl_description = "Create a render layer node for each view layer in the scene, positioned and aligned"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if we're in compositor"""
        return (context.space_data and 
                context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'CompositorNodeTree')
    
    def execute(self, context):
        logger.info("Build Render Layers operator executed")
        print("Shotput: Build Render Layers from View operator executed")
        
        # Get scene and compositor tree
        scene = context.scene
        if not scene.use_nodes:
            scene.use_nodes = True
            print("Shotput: Enabled compositor nodes")
        
        tree = scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Get all view layers from the scene
        view_layers = scene.view_layers
        if not view_layers or len(view_layers) == 0:
            self.report({'WARNING'}, "No view layers found in scene")
            return {'CANCELLED'}
        
        # Starting position for the first node
        start_x = 0
        start_y = 0
        
        # Node spacing
        spacing_y = 300  # Vertical spacing between nodes
        
        # Create a render layer node for each view layer
        created_nodes = []
        for i, view_layer in enumerate(view_layers):
            # Create render layer node
            render_node = tree.nodes.new(type='CompositorNodeRLayers')
            render_node.name = f"Render Layers - {view_layer.name}"
            render_node.label = view_layer.name
            
            # Set the view layer (scene property)
            render_node.layer = view_layer.name
            
            # Position the node - stack vertically
            render_node.location = (start_x, start_y - (i * spacing_y))
            
            created_nodes.append(render_node)
            print(f"Shotput: Created render layer node for '{view_layer.name}' at {render_node.location}")
        
        # Select all created nodes
        for node in tree.nodes:
            node.select = False
        for node in created_nodes:
            node.select = True
        
        # Set the first node as active
        if created_nodes:
            tree.nodes.active = created_nodes[0]
        
        self.report({'INFO'}, f"Created {len(created_nodes)} render layer nodes")
        return {'FINISHED'}


def menu_func_compositor(self, context):
    """Draw function to add Shotput menu to compositor header - only shows in compositor"""
    # Only show in compositor node editor
    if context.space_data and context.space_data.type == 'NODE_EDITOR':
        if context.space_data.tree_type == 'CompositorNodeTree':
            self.layout.menu(NODE_MT_shotput.bl_idname)


classes = (
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    SHOTPUT_UL_StoredPasses,
    TL_PT_Shotput_UI,
    TL_PT_Shotput_Node_UI,
    SHOTPUT_OT_CorePassAdd,
    SHOTPUT_OT_CorePassRemove,
    SHOTPUT_OT_CorePassMoveUp,
    SHOTPUT_OT_CorePassMoveDown,
    SHOTPUT_OT_AOVPassAdd,
    SHOTPUT_OT_AOVPassRemove,
    SHOTPUT_OT_AOVPassMoveUp,
    SHOTPUT_OT_AOVPassMoveDown,
    SHOTPUT_OT_StoredPassAdd,
    SHOTPUT_OT_StoredPassRemove,
    SHOTPUT_OT_StoredPassMoveUp,
    SHOTPUT_OT_StoredPassMoveDown,
    SHOTPUT_OT_TogglePathLinking,
    SHOTPUT_OT_SyncNodePasses,
    SHOTPUT_OT_InsertToken,
    SHOTPUT_OT_LoadPresetFromEnvironment,
    SHOTPUT_MT_TokenMenuRoot,
    SHOTPUT_MT_TokenMenuFile,
    SHOTPUT_MT_TokenMenuNodeRoot,
    SHOTPUT_MT_TokenMenuNodeFile,
    SHOTPUT_MT_PresetEnvironmentMenu,
    NODE_MT_shotput,
    SHOTPUT_OT_BuildRenderLayers,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add Shotput menu to compositor header (append to show after core menus)
    bpy.types.NODE_HT_header.append(menu_func_compositor)

def unregister():
    # Remove Shotput menu from compositor header
    bpy.types.NODE_HT_header.remove(menu_func_compositor)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

