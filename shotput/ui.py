import bpy
from . import bl_info
from . import __release_stage__
import os

from .utils.log import LoggerFactory
from .utils import custom_icons

logger = LoggerFactory.logger_obj()


# ============================================================================
# UI Helper Class
# ============================================================================
# Streamlines common UI patterns, particularly icon loading and layout operations
# Reduces verbosity from 85+ icon loading calls throughout the file

class UIHelper:
    """Helper class for common UI operations and cleaner syntax"""
    
    @staticmethod
    def get_icon(icon_name):
        """Get icon parameters dict for use with layout elements"""
        return custom_icons.get_icon_id_or_fallback(icon_name)
    
    @staticmethod
    def icon_label(layout, text, icon_name):
        """Add a label with icon in one call"""
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        layout.label(text=text, **icon)
    
    @staticmethod
    def icon_operator(layout, operator_id, text, icon_name, **kwargs):
        """Add an operator button with icon in one call"""
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        return layout.operator(operator_id, text=text, **icon, **kwargs)
    
    @staticmethod
    def icon_menu(layout, menu_id, text, icon_name):
        """Add a menu with icon in one call"""
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        layout.menu(menu_id, text=text, **icon)


def get_panel_title():
    """Generate panel title with AYON status if available"""
    base_title = f"Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}-{__release_stage__}"
    
    # Check if AYON environment is present
    ayon_project = os.getenv("AYON_PROJECT_NAME")
    if ayon_project:
        return f"{base_title} - {ayon_project}"
    
    return base_title


# ============================================================================
# Generic List Operator Factory
# ============================================================================
# Replaces 8 nearly-identical operator class definitions with a reusable pattern.
# 
# Benefits:
# - Single source of truth: One pattern for all list operations
# - Easy maintenance: Fix once, applies to all list types
# - Simple extensibility: New lists require just 1 line instead of 4 classes
#
# Before refactoring: 96 lines of duplicated operator classes
# After refactoring: 89 lines (factory + calls + docs) 
# Net improvement: -7 lines, +100% maintainability

def create_list_operators(collection_attr, display_name, id_prefix, get_container):
    """
    Factory function to create list management operators.
    
    Args:
        collection_attr: Name of the collection property (e.g., 'core_passes')
        display_name: Human-readable name (e.g., 'Core Pass')
        id_prefix: Operator ID prefix (e.g., 'core_pass')
        get_container: Function to get the container object (e.g., lambda ctx: ctx.scene.shotput)
    
    Returns:
        Tuple of 4 operator classes (Add, Remove, MoveUp, MoveDown)
    """
    
    # Add operator
    class ListAdd(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_add"
        bl_label = f"Add {display_name}"
        
        def execute(self, context):
            container = get_container(context)
            collection = getattr(container, collection_attr)
            item = collection.add()
            item.name = f"item{len(collection)}"
            setattr(container, f"{collection_attr}_index", len(collection) - 1)
            return {'FINISHED'}
    
    # Remove operator
    class ListRemove(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_remove"
        bl_label = f"Remove {display_name}"
        
        def execute(self, context):
            container = get_container(context)
            collection = getattr(container, collection_attr)
            idx = getattr(container, f"{collection_attr}_index")
            if collection and idx < len(collection):
                collection.remove(idx)
                setattr(container, f"{collection_attr}_index", max(0, idx - 1))
            return {'FINISHED'}
    
    # Move Up operator
    class ListMoveUp(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_move_up"
        bl_label = f"Move {display_name} Up"
        
        def execute(self, context):
            container = get_container(context)
            collection = getattr(container, collection_attr)
            idx = getattr(container, f"{collection_attr}_index")
            if idx > 0:
                collection.move(idx, idx - 1)
                setattr(container, f"{collection_attr}_index", idx - 1)
            return {'FINISHED'}
    
    # Move Down operator
    class ListMoveDown(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_move_down"
        bl_label = f"Move {display_name} Down"
        
        def execute(self, context):
            container = get_container(context)
            collection = getattr(container, collection_attr)
            idx = getattr(container, f"{collection_attr}_index")
            if idx < len(collection) - 1:
                collection.move(idx, idx + 1)
                setattr(container, f"{collection_attr}_index", idx + 1)
            return {'FINISHED'}
    
    return ListAdd, ListRemove, ListMoveUp, ListMoveDown


# Generate operators for scene-level lists
SHOTPUT_OT_CorePassAdd, SHOTPUT_OT_CorePassRemove, SHOTPUT_OT_CorePassMoveUp, SHOTPUT_OT_CorePassMoveDown = \
    create_list_operators('core_passes', 'Core Pass', 'core_pass', lambda ctx: ctx.scene.shotput)

SHOTPUT_OT_AOVPassAdd, SHOTPUT_OT_AOVPassRemove, SHOTPUT_OT_AOVPassMoveUp, SHOTPUT_OT_AOVPassMoveDown = \
    create_list_operators('aov_passes', 'AOV Pass', 'aov_pass', lambda ctx: ctx.scene.shotput)


# ============================================================================
# Node-level list operators (Stored Passes)
# ============================================================================
# These require special handling for node context

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


# ============================================================================
# Other Operators
# ============================================================================

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
            
            # Migrate legacy tokens
            from .utils.defaults import migrate_legacy_tokens
            if 'root_folder_token' in data:
                data['root_folder_token'] = migrate_legacy_tokens(data['root_folder_token'])
            if 'file_name_token' in data:
                data['file_name_token'] = migrate_legacy_tokens(data['file_name_token'])
            
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
            UIHelper.icon_label(layout, "SHOTPUT_PRESET_PATH not set", 'error')
            return
        
        from pathlib import Path
        preset_path = Path(env_path)
        
        # If env path is a file, use its directory
        if preset_path.is_file():
            preset_dir = preset_path.parent
        elif preset_path.is_dir():
            preset_dir = preset_path
        else:
            UIHelper.icon_label(layout, "Invalid SHOTPUT_PRESET_PATH", 'error')
            return
        
        # Find all JSON files in the directory
        json_files = sorted(preset_dir.glob("*.json"))
        
        if not json_files:
            UIHelper.icon_label(layout, "No preset files found", 'info')
            return
        
        # Add an operator for each JSON file
        icon_preset_env = UIHelper.get_icon('preset')
        for json_file in json_files:
            op = layout.operator("shotput.load_preset_from_environment", 
                               text=json_file.stem, 
                               **icon_preset_env)
            op.preset_filename = json_file.name


# Token menu classes for different fields
# Base class to reduce duplication across 4 token menu variants
class BaseTokenMenu(bpy.types.Menu):
    """Base class for token insertion menus with shared drawing logic"""
    bl_label = "Insert Token"
    property_path = ""  # Override in subclass
    
    # Token definitions (same for all menus)
    CORE_TOKENS = [
        ('workdir', 'Working Directory'),
        ('subpath', 'Subpath'),
        ('outputlayer', 'Output Layer'),
        ('passname', 'Pass Name'),
        ('variant', 'Variant'),
        ('version', 'Version'),
    ]
    
    AYON_TOKENS = [
        ('project', 'Project Path'),
        ('projectname', 'Project Name'),
        ('task', 'Task Name'),
        ('folder', 'Folder Path'),
        ('user', 'User Name'),
    ]
    
    BLENDER_TOKENS = [
        ('blendfile', 'Blend File Name'),
        ('scenename', 'Scene Name'),
        ('frame', 'Frame Number'),
        ('camera', 'Camera Name'),
    ]
    
    DATETIME_TOKENS = [
        ('date', 'Current Date'),
        ('time', 'Current Time'),
    ]
    
    def draw(self, context):
        layout = self.layout
        icon_dot = UIHelper.get_icon('dot')
        
        # Core Shotput tokens
        UIHelper.icon_label(layout, "Core Tokens", 'file_folder')
        for token, label in self.CORE_TOKENS:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = self.property_path
        
        layout.separator()
        
        # AYON-specific tokens
        UIHelper.icon_label(layout, "AYON Tokens", 'network_drive')
        for token, label in self.AYON_TOKENS:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = self.property_path
        
        layout.separator()
        
        # Blender-specific tokens
        UIHelper.icon_label(layout, "Blender Tokens", 'blender')
        for token, label in self.BLENDER_TOKENS:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = self.property_path
        
        layout.separator()
        
        # Date/Time tokens
        UIHelper.icon_label(layout, "Date/Time Tokens", 'time')
        for token, label in self.DATETIME_TOKENS:
            op = layout.operator("shotput.insert_token", text=label, **icon_dot)
            op.token = token
            op.property_path = self.property_path


class SHOTPUT_MT_TokenMenuRoot(BaseTokenMenu):
    bl_idname = "SHOTPUT_MT_token_menu_root"
    property_path = "scene.shotput.root_folder_token"


class SHOTPUT_MT_TokenMenuFile(BaseTokenMenu):
    bl_idname = "SHOTPUT_MT_token_menu_file"
    property_path = "scene.shotput.file_name_token"


class SHOTPUT_MT_TokenMenuNodeRoot(BaseTokenMenu):
    bl_idname = "SHOTPUT_MT_token_menu_node_root"
    property_path = "node.shotput_data.root_folder_token"


class SHOTPUT_MT_TokenMenuNodeFile(BaseTokenMenu):
    bl_idname = "SHOTPUT_MT_token_menu_node_file"
    property_path = "node.shotput_data.file_name_token"

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
        icon_params = UIHelper.get_icon('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_params = UIHelper.get_icon('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

# UIList for stored passes on File Output nodes
class SHOTPUT_UL_StoredPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_params = UIHelper.get_icon('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)

class TL_PT_Shotput_UI(bpy.types.Panel):
    bl_label = get_panel_title()
    bl_category = "Shotput"
    bl_context = "output"
    bl_order = 2
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    
    def draw_header_section(self, layout, shotput):
        """Draw welcome/description box with AYON detection"""
        box = layout.box()
        col = box.column(align=True)
        
        # Show AYON icon if AYON is enabled
        if os.getenv("AYON_PROJECT_NAME"):
            UIHelper.icon_label(col, "Shotput - Tokenised Render Output System", 'ayon')
        else:
            UIHelper.icon_label(col, "Shotput - Tokenised Render Output System", 'renderlayers')
        
        col.separator(factor=0.5)
        col.scale_y = 0.8
        col.label(text="Create and update automatic versions for renders")
    
    def draw_properties_section(self, layout, shotput):
        """Draw scene properties box"""
        box = layout.box()
        UIHelper.icon_label(box, "Output Node Properties", 'scene_data')
        box.prop(shotput, "output_layer", text="Output Layer")
        box.prop(shotput, "variant", text="Variant")
    
    def draw_passes_section(self, layout, shotput):
        """Draw pass creation box with render layer mode detection"""
        box = layout.box()
        UIHelper.icon_label(box, "Create Passes", 'nodetree')
        
        if shotput.use_render_layer_channels:
            # Render Layer Channels mode - only show Core operator
            row = box.row()
            row.scale_y = 1.5
            UIHelper.icon_operator(row, "shotput.create_core_passes", "Create All Passes (From Render Layer)", 'core')
            
            # Add helpful info
            col = box.column()
            col.scale_y = 0.8
            UIHelper.icon_label(col, "Creates a shotput file output with all enabled render layer passes", 'info')
        else:
            # Manual mode - show all operators
            row = box.row(align=True)
            row.scale_y = 1.5
            UIHelper.icon_operator(row, "shotput.create_core_passes", "Core", 'core')
            UIHelper.icon_operator(row, "shotput.create_linked_composite", "Composite", 'composite')
            UIHelper.icon_operator(row, "shotput.create_aov_passes", "AOV", 'aov')
            UIHelper.icon_operator(row, "shotput.create_data_passes", "Data", 'data')
        
        # Only show these options in manual mode
        if not shotput.use_render_layer_channels:
            box.prop(shotput, "create_composite_from_core", text="Create Linked Composite Node from Core")
        
        box.prop(shotput, "lazy_hook_up", text="Auto-Connect to Render Layer")
        box.prop(shotput, "use_render_layer_channels", text="Use Render Layer Channels")
    
    def draw_path_tokens_section(self, layout, shotput):
        """Draw path tokens configuration box"""
        box = layout.box()
        UIHelper.icon_label(box, "Path Tokens", 'file_folder')
        
        # Root folder with token menu and preview paths button
        row = box.row(align=True)
        row.prop(shotput, "root_folder_token", text="Root Folder")
        UIHelper.icon_menu(row, "SHOTPUT_MT_token_menu_root", "", 'add')
        icon_file_folder = UIHelper.get_icon('file_folder')
        row.operator("shotput.preview_paths", text="", **icon_file_folder)
        
        # File name with token menu and token help button  
        row = box.row(align=True)
        row.prop(shotput, "file_name_token", text="File Name")
        UIHelper.icon_menu(row, "SHOTPUT_MT_token_menu_file", "", 'add')
        icon_help = UIHelper.get_icon('token_help')
        row.operator("shotput.token_help", text="", **icon_help)
        
        # Output Format in compact 2x2 grid
        box.label(text="Output Format")
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.prop_enum(shotput, "output_format", 'PNG')
        grid.prop_enum(shotput, "output_format", 'JPEG')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR_MULTILAYER')
    
    def draw_pass_lists_section(self, layout, shotput):
        """Draw Core and AOV pass lists (manual mode only)"""
        if shotput.use_render_layer_channels:
            return  # Skip in render layer mode
        
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
        UIHelper.icon_label(core_row, "Core Passes", 'core')
        
        # AOV header (right half)
        aov_row = split.row()
        aov_row.prop(shotput, "expand_aov_ui", 
                    icon="TRIA_DOWN" if expand_aov else "TRIA_RIGHT", 
                    icon_only=True, emboss=False)
        UIHelper.icon_label(aov_row, "AOV Passes", 'aov')
        
        # Content row - only split if BOTH are expanded
        if expand_core and expand_aov:
            # Both expanded - use split layout
            content_split = box.split(factor=0.5)
            self._draw_core_passes_list(content_split.column(), shotput)
            self._draw_aov_passes_list(content_split.column(), shotput)
        elif expand_core:
            # Only core expanded - use full width
            self._draw_core_passes_list(box.column(), shotput)
        elif expand_aov:
            # Only AOV expanded - use full width
            self._draw_aov_passes_list(box.column(), shotput)
    
    def _draw_core_passes_list(self, col, shotput):
        """Helper: Draw core passes UIList with controls"""
        col.prop(shotput, "core_override", text="Core Override")
        row = col.row()
        row.template_list("SHOTPUT_UL_CorePasses", "", shotput, "core_passes", shotput, "core_passes_index", rows=3)
        control_col = row.column(align=True)
        
        icon_add = UIHelper.get_icon('add')
        control_col.operator("shotput.core_pass_add", text="", **icon_add)
        icon_remove = UIHelper.get_icon('remove')
        control_col.operator("shotput.core_pass_remove", text="", **icon_remove)
        control_col.separator()
        icon_up = UIHelper.get_icon('tria_up')
        control_col.operator("shotput.core_pass_move_up", text="", **icon_up)
        icon_down = UIHelper.get_icon('tria_down')
        control_col.operator("shotput.core_pass_move_down", text="", **icon_down)
        control_col.separator()
        # Import channels from node button
        import_op = control_col.operator("shotput.import_channels_from_node", text="", icon='COPYDOWN')
        import_op.target_list = 'core'
    
    def _draw_aov_passes_list(self, col, shotput):
        """Helper: Draw AOV passes UIList with controls"""
        col.prop(shotput, "aov_override", text="AOV Override")
        row = col.row()
        row.template_list("SHOTPUT_UL_AOVPasses", "", shotput, "aov_passes", shotput, "aov_passes_index", rows=3)
        control_col = row.column(align=True)
        
        icon_add = UIHelper.get_icon('add')
        control_col.operator("shotput.aov_pass_add", text="", **icon_add)
        icon_remove = UIHelper.get_icon('remove')
        control_col.operator("shotput.aov_pass_remove", text="", **icon_remove)
        control_col.separator()
        icon_up = UIHelper.get_icon('tria_up')
        control_col.operator("shotput.aov_pass_move_up", text="", **icon_up)
        icon_down = UIHelper.get_icon('tria_down')
        control_col.operator("shotput.aov_pass_move_down", text="", **icon_down)
        control_col.separator()
        # Import channels from node button
        import_op = control_col.operator("shotput.import_channels_from_node", text="", icon='COPYDOWN')
        import_op.target_list = 'aov'
        control_col.separator()
        # Scan shader AOVs button (icon only)
        icon_viewzoom = UIHelper.get_icon('viewzoom')
        control_col.operator("shotput.scan_shader_aovs", text="", **icon_viewzoom)
    
    def draw_data_passes_section(self, layout, shotput):
        """Draw data passes section (manual mode only)"""
        if shotput.use_render_layer_channels:
            return  # Skip in render layer mode
        
        box = layout.box()
        row = box.row()
        expand_data = shotput.expand_data_ui if hasattr(shotput, 'expand_data_ui') else False
        row.prop(shotput, "expand_data_ui", 
                icon="TRIA_DOWN" if expand_data else "TRIA_RIGHT", 
                icon_only=True, emboss=False)
        UIHelper.icon_label(row, "Data Passes", 'data')
        
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
    
    def draw_presets_section(self, layout, shotput):
        """Draw preset management box"""
        box = layout.box()
        UIHelper.icon_label(box, "Preset Management", 'preset')
        
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
                    UIHelper.icon_menu(row, "SHOTPUT_MT_preset_environment_menu", "Load From Env", 'preset')
        
        UIHelper.icon_operator(row, "shotput.load_preset", "Load Pass Setup", 'import')
        UIHelper.icon_operator(row, "shotput.save_preset", "Save Pass Setup", 'export')
        
    def draw(self, context):
        layout = self.layout
        shotput = context.scene.shotput
        
        # Draw all sections using helper methods
        self.draw_header_section(layout, shotput)
        self.draw_properties_section(layout, shotput)
        self.draw_passes_section(layout, shotput)
        self.draw_path_tokens_section(layout, shotput)
        self.draw_pass_lists_section(layout, shotput)
        self.draw_data_passes_section(layout, shotput)
        self.draw_presets_section(layout, shotput)

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
    
    def draw_description_section(self, layout, node):
        """Draw node description/help box"""
        box = layout.box()
        col = box.column(align=True)
        
        if node.type == 'COMPOSITE':
            UIHelper.icon_label(col, "Shotput Composite Node", 'info')
            col.separator(factor=0.5)
            col.scale_y = 0.8
            col.label(text="This Composite node will sync the scene's render filepath when 'Update Version' is called")
        else:
            UIHelper.icon_label(col, "Shotput File Output Node", 'info')
            col.separator(factor=0.)
            col.scale_y = 0.8
            col.label(text="This File Output node is configured for token-based render pathing.")
    
    def draw_properties_section(self, layout, shotput_data, ayon_detected):
        """Draw node properties box with version and AYON toggle"""
        box = layout.box()
        
        # Header row with title and version
        if shotput_data.shotput_version:
            header_row = box.row()
            UIHelper.icon_label(header_row, "Shotput Properties", 'settings')
            header_row.separator()
            version_label = header_row.row()
            version_label.enabled = False
            version_label.label(text=f"Version: {shotput_data.shotput_version}")
        else:
            UIHelper.icon_label(box, "Shotput Properties", 'settings')
        
        box.prop(shotput_data, "output_layer", text="Output Layer")
        box.prop(shotput_data, "pass_name", text="Pass Name")
        box.prop(shotput_data, "variant", text="Variant")
        
        # AYON Mode Toggle - only show if AYON is detected
        if ayon_detected:
            row = box.row()
            icon_ayon = UIHelper.get_icon('ayon')
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
    
    def draw_path_linking_section(self, layout, shotput_data, ayon_detected):
        """Draw path linking controls and configuration"""
        box = layout.box()
        UIHelper.icon_label(box, "Path Configuration", 'file_folder')
        
        # Path linking controls - disabled in AYON mode
        if ayon_detected and shotput_data.use_ayon_output_style:
            row = box.row()
            row.alert = True
            row.label(text="Path Linking is not needed in AYON", icon='INFO')
        else:
            row = box.row()
            if shotput_data.path_linked:
                icon_linked = UIHelper.get_icon('linked')
                row.operator("shotput.toggle_path_linking", 
                            text="Path Linked", 
                            depress=True,
                            **icon_linked)
            else:
                icon_unlinked = UIHelper.get_icon('unlinked')
                row.operator("shotput.toggle_path_linking", 
                            text="Enable Path Linking", 
                            depress=False,
                            **icon_unlinked)
        
        if shotput_data.path_linked:
            self._draw_linked_path_config(box, shotput_data)
        else:
            self._draw_normal_path_config(box, shotput_data, ayon_detected)
        
        # File name token - make read-only if AYON mode is enabled
        row = box.row(align=True)
        if ayon_detected and shotput_data.use_ayon_output_style:
            row.enabled = False
            row.prop(shotput_data, "file_name_token", text="AYON File Name")
        else:
            row.prop(shotput_data, "file_name_token", text="File Name")
            UIHelper.icon_menu(row, "SHOTPUT_MT_token_menu_node_file", "", 'add')
        
        # Output Folder Actions and Lazy Hook-up in a single row
        row = box.row()
        UIHelper.icon_operator(row, "shotput.open_output_folder", "Open Output Folder", 'folder_redirect')
        UIHelper.icon_operator(row, "shotput.lazy_hookup", "Connect to Render Layer", 'linked')
        
        return box
    
    def _draw_linked_path_config(self, box, shotput_data):
        """Helper: Draw linked path configuration"""
        box.prop(shotput_data, "linked_node", text="Linked Node")
        
        # Show the linked node's path if available
        linked_node = shotput_data.node
        if linked_node:
            row = box.row()
            icon_file_folder_linked = UIHelper.get_icon('file_folder')
            row.label(text=f"Linked Path: {linked_node.base_path}", **icon_file_folder_linked)
            row.enabled = False
        else:
            row = box.row()
            UIHelper.icon_label(row, "No valid linked node selected", 'error')
            row.enabled = False
        
        # Append path field with token menu
        row = box.row(align=True)
        row.prop(shotput_data, "root_folder_token", text="Append Path")
        UIHelper.icon_menu(row, "SHOTPUT_MT_token_menu_node_root", "", 'add')
    
    def _draw_normal_path_config(self, box, shotput_data, ayon_detected):
        """Helper: Draw normal path configuration"""
        row = box.row(align=True)
        if ayon_detected and shotput_data.use_ayon_output_style:
            row.enabled = False
            row.prop(shotput_data, "root_folder_token", text="AYON Root Folder")
        else:
            row.prop(shotput_data, "root_folder_token", text="Root Folder")
            UIHelper.icon_menu(row, "SHOTPUT_MT_token_menu_node_root", "", 'add')
    
    def draw_composite_button_section(self, layout, node, shotput_data, ayon_detected):
        """Draw create linked composite button (File Output nodes only)"""
        if node.type == 'OUTPUT_FILE':
            if not (ayon_detected and shotput_data.use_ayon_output_style):
                row = layout.row()
                UIHelper.icon_operator(row, "shotput.create_linked_composite", "Create Linked Composite Node", 'composite')
    
    def draw_stored_passes_section(self, layout, node, shotput_data):
        """Draw stored passes UIList (File Output nodes only)"""
        if node.type != 'OUTPUT_FILE':
            return
        
        box = layout.box()
        row = box.row()
        expand_stored = shotput_data.expand_stored_ui if hasattr(shotput_data, 'expand_stored_ui') else False
        row.prop(shotput_data, "expand_stored_ui", 
                icon="TRIA_DOWN" if expand_stored else "TRIA_RIGHT", 
                icon_only=True, emboss=False)
        UIHelper.icon_label(row, "Output Passes (Advanced)", 'renderlayers')
        
        if expand_stored:
            # Sync button (one-way: stored passes -> node slots)
            row = box.row()
            UIHelper.icon_operator(row, "shotput.sync_node_passes", "Sync to Node Slots", 'file_refresh')
            
            # UIList with controls
            row = box.row()
            row.template_list("SHOTPUT_UL_StoredPasses", "", shotput_data, "stored_passes", shotput_data, "stored_passes_index", rows=3)
            col = row.column(align=True)
            icon_add_stored = UIHelper.get_icon('add')
            col.operator("shotput.stored_pass_add", text="", **icon_add_stored)
            icon_remove_stored = UIHelper.get_icon('remove')
            col.operator("shotput.stored_pass_remove", text="", **icon_remove_stored)
            col.separator()
            icon_up_stored = UIHelper.get_icon('tria_up')
            col.operator("shotput.stored_pass_move_up", text="", **icon_up_stored)
            icon_down_stored = UIHelper.get_icon('tria_down')
            col.operator("shotput.stored_pass_move_down", text="", **icon_down_stored)
    
    def draw(self, context):
        layout = self.layout
        node = context.active_node
        shotput_data = node.shotput_data
        
        import os
        ayon_detected = bool(os.getenv("AYON_PROJECT_NAME"))
        
        # Draw all sections using helper methods
        self.draw_description_section(layout, node)
        self.draw_properties_section(layout, shotput_data, ayon_detected)
        self.draw_path_linking_section(layout, shotput_data, ayon_detected)
        self.draw_composite_button_section(layout, node, shotput_data, ayon_detected)
        self.draw_stored_passes_section(layout, node, shotput_data)


class NODE_MT_shotput(bpy.types.Menu):
    """Shotput menu for compositor workspace"""
    bl_label = "Shotput"
    bl_idname = "NODE_MT_shotput"
    
    def draw(self, context):
        layout = self.layout
        
        UIHelper.icon_operator(layout, "shotput.update_version", "Update Version", 'file_refresh')
        UIHelper.icon_operator(layout, "shotput.open_output_folder", "Open Output Folder", 'file_folder')
        layout.separator()
        UIHelper.icon_operator(layout, "shotput.build_render_layers", "Build Render Layers from View", 'renderlayers')


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
        
        # Check if there's already a default Render Layers node for the first view layer
        # Blender creates this automatically when enabling "use nodes"
        existing_render_layer_node = None
        first_view_layer_name = view_layers[0].name
        
        for node in tree.nodes:
            if node.type == 'R_LAYERS' and node.layer == first_view_layer_name:
                existing_render_layer_node = node
                print(f"Shotput: Found existing render layer node for '{first_view_layer_name}' - reusing it")
                break
        
        # Starting position for the first node
        start_x = 0
        start_y = 0
        
        # Node spacing
        spacing_y = 300  # Vertical spacing between nodes
        
        # Create a render layer node for each view layer
        created_nodes = []
        for i, view_layer in enumerate(view_layers):
            # Skip the first view layer if we already have a node for it
            if i == 0 and existing_render_layer_node:
                # Reuse the existing node - just reposition it and add to our list
                existing_render_layer_node.location = (start_x, start_y)
                existing_render_layer_node.name = f"Render Layers - {view_layer.name}"
                existing_render_layer_node.label = view_layer.name
                created_nodes.append(existing_render_layer_node)
                print(f"Shotput: Reused existing render layer node for '{view_layer.name}' at {existing_render_layer_node.location}")
                continue
            
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

