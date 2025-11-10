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
            layout.label(text="SHOTPUT_PRESET_PATH not set", icon='ERROR')
            return
        
        from pathlib import Path
        preset_path = Path(env_path)
        
        # If env path is a file, use its directory
        if preset_path.is_file():
            preset_dir = preset_path.parent
        elif preset_path.is_dir():
            preset_dir = preset_path
        else:
            layout.label(text="Invalid SHOTPUT_PRESET_PATH", icon='ERROR')
            return
        
        # Find all JSON files in the directory
        json_files = sorted(preset_dir.glob("*.json"))
        
        if not json_files:
            layout.label(text="No preset files found", icon='INFO')
            return
        
        # Add an operator for each JSON file
        for json_file in json_files:
            op = layout.operator("shotput.load_preset_from_environment", 
                               text=json_file.stem, 
                               icon='PRESET')
            op.preset_filename = json_file.name


# Token menu classes for different fields
class SHOTPUT_MT_TokenMenuRoot(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_root"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "scene.shotput.root_folder_token"
        
        # Core Shotput tokens
        layout.label(text="Core Tokens", icon='FILE_FOLDER')
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        layout.label(text="AYON Tokens", icon='NETWORK_DRIVE')
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        layout.label(text="Blender Tokens", icon='BLENDER')
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        layout.label(text="Date/Time Tokens", icon='TIME')
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuFile(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_file"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "scene.shotput.file_name_token"
        
        # Core Shotput tokens
        layout.label(text="Core Tokens", icon='FILE_FOLDER')
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        layout.label(text="AYON Tokens", icon='NETWORK_DRIVE')
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        layout.label(text="Blender Tokens", icon='BLENDER')
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        layout.label(text="Date/Time Tokens", icon='TIME')
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuNodeRoot(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_node_root"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "node.shotput_data.root_folder_token"
        
        # Core Shotput tokens
        layout.label(text="Core Tokens", icon='FILE_FOLDER')
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        layout.label(text="AYON Tokens", icon='NETWORK_DRIVE')
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        layout.label(text="Blender Tokens", icon='BLENDER')
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        layout.label(text="Date/Time Tokens", icon='TIME')
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path

class SHOTPUT_MT_TokenMenuNodeFile(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_node_file"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "node.shotput_data.file_name_token"
        
        # Core Shotput tokens
        layout.label(text="Core Tokens", icon='FILE_FOLDER')
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # AYON-specific tokens
        layout.label(text="AYON Tokens", icon='NETWORK_DRIVE')
        ayon_tokens = [
            ('project', 'Project Path'),
            ('projectname', 'Project Name'),
            ('task', 'Task Name'),
            ('folder', 'Folder Path'),
            ('user', 'User Name'),
        ]
        for token, label in ayon_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Blender-specific tokens
        layout.label(text="Blender Tokens", icon='BLENDER')
        blender_tokens = [
            ('blendfile', 'Blend File Name'),
            ('scenename', 'Scene Name'),
            ('frame', 'Frame Number'),
            ('camera', 'Camera Name'),
        ]
        for token, label in blender_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
            op.token = token
            op.property_path = prop_path
        
        layout.separator()
        
        # Date/Time tokens
        layout.label(text="Date/Time Tokens", icon='TIME')
        datetime_tokens = [
            ('date', 'Current Date'),
            ('time', 'Current Time'),
        ]
        for token, label in datetime_tokens:
            op = layout.operator("shotput.insert_token", text=label, icon='DOT')
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
        icon_params = custom_icons.get_icon_id_or_fallback('core')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Use custom icon if available, otherwise fallback to built-in
        icon_params = custom_icons.get_icon_id_or_fallback('aov')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

# UIList for stored passes on File Output nodes
class SHOTPUT_UL_StoredPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=True, icon='RENDERLAYERS')

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
        col.label(text="Shotput - Tokenised Render Output System", icon='RENDERLAYERS')
        col.separator(factor=0.5)
        
        # Multi-line description with smaller text
        col.scale_y = 0.8
        col.label(text="Create and update automatic versions for renders")

        # Scene Properties Box - Output Layer and Variant
        box = layout.box()
        box.label(text="Scene Properties", icon='SCENE_DATA')
        box.prop(shotput, "output_layer", text="Output Layer")
        box.prop(shotput, "variant", text="Variant")

        # Update Version - larger button
        row = layout.row()
        row.scale_y = 1.5
        row.operator("shotput.update_version", icon='FILE_REFRESH', text="Update Version")

        # Open Output Folder
        row = layout.row()
        row.operator("shotput.open_output_folder", icon='FOLDER_REDIRECT', text="Open Output Folder")
       
        box = layout.box()
        box.label(text="Create Passes", icon='NODETREE')
        

        
        if shotput.use_render_layer_channels:
            # Render Layer Channels mode - only show Core operator
            row = box.row()
            row.scale_y = 1.5
            icon_params = custom_icons.get_icon_id_or_fallback('core')
            row.operator("shotput.create_core_passes", text="Create All Passes (From Render Layer)", **icon_params)
            
            # Add helpful info
            col = box.column()
            col.scale_y = 0.8
            col.label(text="Creates a shotput file output with all enabled render layer passes", icon="INFO")
            
        else:
            # Manual mode - show all operators
            # 4x1 horizontal layout for operators with increased height
            row = box.row(align=True)
            row.scale_y = 1.5
            icon_core = custom_icons.get_icon_id_or_fallback('core')
            row.operator("shotput.create_core_passes", text="Core", **icon_core)
            row.operator("shotput.create_linked_composite", icon='STRIP_COLOR_07', text="Composite")
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
        box.label(text="Path Tokens", icon='FILE_FOLDER')
        
        # Root folder with token menu and preview paths button
        row = box.row(align=True)
        row.prop(shotput, "root_folder_token", text="Root Folder")
        row.menu("SHOTPUT_MT_token_menu_root", icon='ADD', text="")
        row.operator("shotput.preview_paths", icon='FILE_FOLDER', text="")
        
        # File name with token menu and token help button  
        row = box.row(align=True)
        row.prop(shotput, "file_name_token", text="File Name")
        row.menu("SHOTPUT_MT_token_menu_file", icon='ADD', text="")
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
                    col.operator("shotput.core_pass_add", icon='ADD', text="")
                    col.operator("shotput.core_pass_remove", icon='REMOVE', text="")
                    col.separator()
                    col.operator("shotput.core_pass_move_up", icon='TRIA_UP', text="")
                    col.operator("shotput.core_pass_move_down", icon='TRIA_DOWN', text="")
                
                # Right column - AOV Passes
                aov_col = content_split.column()
                if expand_aov:
                    aov_col.prop(shotput, "aov_override", text="AOV Override")
                  
                    row = aov_col.row()
                    row.template_list("SHOTPUT_UL_AOVPasses", "", shotput, "aov_passes", shotput, "aov_passes_index", rows=3)
                    col = row.column(align=True)
                    col.operator("shotput.aov_pass_add", icon='ADD', text="")
                    col.operator("shotput.aov_pass_remove", icon='REMOVE', text="")
                    col.separator()
                    col.operator("shotput.aov_pass_move_up", icon='TRIA_UP', text="")
                    col.operator("shotput.aov_pass_move_down", icon='TRIA_DOWN', text="")
                    
                    # Scan button for shader AOVs
                    scan_row = aov_col.row()
                    scan_row.operator("shotput.scan_shader_aovs", text="Scan AOVs", icon='VIEWZOOM')

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
        box.label(text="Preset Management", icon='PRESET')
        
        # Preset buttons
        row = box.row()
        row.operator("shotput.load_preset", icon='IMPORT', text="Load Pass Setup")
        
        # Add environment preset menu button if SHOTPUT_PRESET_PATH is set and has JSON files
        if os.environ.get('SHOTPUT_PRESET_PATH'):
            from pathlib import Path
            env_path = Path(os.environ.get('SHOTPUT_PRESET_PATH'))
            preset_dir = env_path.parent if env_path.is_file() else env_path if env_path.is_dir() else None
            
            # Only show button if directory exists and has JSON files
            if preset_dir and preset_dir.exists():
                json_files = list(preset_dir.glob("*.json"))
                if json_files:
                    row.menu("SHOTPUT_MT_preset_environment_menu", icon='PRESET', text="")
        
        row.operator("shotput.save_preset", icon='EXPORT', text="Save Pass Setup")

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
            col.label(text="Shotput Composite Node", icon='INFO')
            col.separator(factor=0.5)
            
            # Multi-line description with smaller text
            col.scale_y = 0.8
            col.label(text="This Composite node will sync the scene's render filepath when 'Update Version' is called")
        else:
            col.label(text="Shotput File Output Node", icon='INFO')
            col.separator(factor=0.)
            
            # Multi-line description with smaller text
            col.scale_y = 0.8
            col.label(text="This File Output node is configured for token-based render pathing.")
  
        # Node Properties Box
        box = layout.box()
        
        # Header row with title and version
        if shotput_data.shotput_version:
            header_row = box.row()
            header_row.label(text="Shotput Properties", icon='SETTINGS')
            # Add some spacing to push version to the right
            header_row.separator()
            version_label = header_row.row()
            version_label.enabled = False  # Make only the version read-only (greyed out)
            version_label.label(text=f"Version: {shotput_data.shotput_version}")
        else:
            box.label(text="Shotput Properties", icon='SETTINGS')
        
        box.prop(shotput_data, "output_layer", text="Output Layer")
        box.prop(shotput_data, "pass_name", text="Pass Name")
        box.prop(shotput_data, "variant", text="Variant")
        
        box.label(text="Path Configuration", icon='FILE_FOLDER')
        
        # Path linking controls
        row = box.row()
        if shotput_data.path_linked:
            row.operator("shotput.toggle_path_linking", 
                        text="Path Linked", 
                        icon='LINKED',
                        depress=True)
        else:
            row.operator("shotput.toggle_path_linking", 
                        text="Enable Path Linking", 
                        icon='UNLINKED',
                        depress=False)
        
        if shotput_data.path_linked:
            # Show path linking UI
            box.prop(shotput_data, "linked_node", text="Linked Node")
            
            # Show the linked node's path if available
            linked_node = shotput_data.node
            if linked_node:
                row = box.row()
                row.label(text=f"Linked Path: {linked_node.base_path}", icon='FILE_FOLDER')
                row.enabled = False  # Make it read-only/grayed out
            else:
                row = box.row()
                row.label(text="No valid linked node selected", icon='ERROR')
                row.enabled = False
            
            # Append path field with consistent layout and token menu
            row = box.row(align=True)
            row.prop(shotput_data, "root_folder_token", text="Append Path")
            row.menu("SHOTPUT_MT_token_menu_node_root", icon='ADD', text="")
            
            # Show backup info if available
            # if shotput_data.root_folder_token_backup:
            #     row = box.row()
            #     row.label(text="Original path backed up", icon='INFO')
            #     row.enabled = False
        else:
            # Normal path configuration with token menu
            row = box.row(align=True)
            row.prop(shotput_data, "root_folder_token", text="Root Folder")
            row.menu("SHOTPUT_MT_token_menu_node_root", icon='ADD', text="")
        
        # File name token is always shown with token menu
        row = box.row(align=True)
        row.prop(shotput_data, "file_name_token", text="File Name")
        row.menu("SHOTPUT_MT_token_menu_node_file", icon='ADD', text="")
        
        # Output Folder Actions and Lazy Hook-up in a single row
        row = box.row()
        row.operator("shotput.open_output_folder", text="Open Output Folder", icon='FOLDER_REDIRECT')
        row.operator("shotput.lazy_hookup", text="Connect to Render Layer", icon='LINKED')
        
        # Create Linked Composite button - only show for File Output nodes
        if node.type == 'OUTPUT_FILE':
            row = box.row()
            row.operator("shotput.create_linked_composite", icon='STRIP_COLOR_07', text="Create Linked Composite Node")
        
        # Stored Passes UIList - only show for File Output nodes (not Composite nodes)
        if node.type == 'OUTPUT_FILE':
            box = layout.box()
            row = box.row()
            expand_stored = shotput_data.expand_stored_ui if hasattr(shotput_data, 'expand_stored_ui') else False
            row.prop(shotput_data, "expand_stored_ui", 
                    icon="TRIA_DOWN" if expand_stored else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
            row.label(text="Output Passes (Advanced)", icon='RENDERLAYERS')
            
            if expand_stored:
                # Sync button (one-way: stored passes -> node slots)
                row = box.row()
                row.operator("shotput.sync_node_passes", text="Sync to Node Slots", icon='FILE_REFRESH')
                
                # UIList with controls
                row = box.row()
                row.template_list("SHOTPUT_UL_StoredPasses", "", shotput_data, "stored_passes", shotput_data, "stored_passes_index", rows=3)
                col = row.column(align=True)
                col.operator("shotput.stored_pass_add", icon='ADD', text="")
                col.operator("shotput.stored_pass_remove", icon='REMOVE', text="")
                col.separator()
                col.operator("shotput.stored_pass_move_up", icon='TRIA_UP', text="")
                col.operator("shotput.stored_pass_move_down", icon='TRIA_DOWN', text="")

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
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

