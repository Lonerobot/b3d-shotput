import bpy
from . import bl_info
import os

from .utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

def get_panel_title():
    """Generate panel title with AYON status if available"""
    base_title = f"THE LINE - Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
    
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
        for pass_item in shotput_data.stored_passes:
            if pass_item.name.strip():  # Only add non-empty names
                desired_passes.append(pass_item.name.strip())
        
        if not desired_passes:
            self.report({'WARNING'}, "No passes defined to sync")
            return {'CANCELLED'}
        
        changes_made = False
        
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
                print(f"Added new slot: '{desired_name}'")
        
        # Handle removed passes (only if we have fewer desired passes than current slots)
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
            
        return {'FINISHED'}

# UIList for passes
class SHOTPUT_UL_CorePasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=True, icon='RENDER_RESULT')

class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=True, icon='IMAGE_RGB')

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
        layout.scale_y = 1.1
        shotput = context.scene.shotput

        # Welcome/Description Box
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Shotput Render Pass Manager", icon='RENDERLAYERS')
        col.separator(factor=0.5)
        
        # Multi-line description with smaller text
        col.scale_y = 0.8
        col.label(text="Create and manage organized File Output")
        col.label(text="nodes for render passes with token-based")
        col.label(text="paths and automated versioning.")
        
        layout.separator()

        # Scene Properties Box - Render Layer and Variant
        box = layout.box()
        box.label(text="Scene Properties", icon='SCENE_DATA')
        box.prop(shotput, "render_layer", text="Render Layer")
        box.prop(shotput, "variant", text="Variant")        # Create Passes Box
        box = layout.box()
        box.label(text="Create Passes", icon='NODETREE')
        row = box.row()
        row.operator("shotput.create_core_passes", icon='RENDERLAYERS', text="Core")
        row.operator("shotput.create_aov_passes", icon='IMAGE_RGB', text="AOV")
        row.operator("shotput.create_data_passes", icon='FILE_BLEND', text="Data")
        
        # Path Management Box
        box = layout.box()
        box.label(text="Path Management", icon='FILE_FOLDER')
        row = box.row()
        row.operator("shotput.update_version", icon='FILE_REFRESH', text="Update Version")
        row.operator("shotput.open_output_folder", icon='FOLDER_REDIRECT', text="")

        # Path Tokens Box - Root Folder and File Name with icon operators
        box = layout.box()
        box.label(text="Path Tokens", icon='FILE_FOLDER')
        
        # Root folder with preview paths button
        row = box.row()
        row.prop(shotput, "root_folder_token", text="Root Folder")
        row.operator("shotput.preview_paths", icon='FILE_FOLDER', text="")
        
        # File name with token help button  
        row = box.row()
        row.prop(shotput, "file_name_token", text="File Name")
        row.operator("shotput.token_help", icon='QUESTION', text="")
        
        # Output Format in compact 2x2 grid
        box.label(text="Output Format")
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        grid.prop_enum(shotput, "output_format", 'PNG')
        grid.prop_enum(shotput, "output_format", 'JPEG')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR')
        grid.prop_enum(shotput, "output_format", 'OPEN_EXR_MULTILAYER')

        # Core Passes UIList (collapsible, closed by default)
        box = layout.box()
        row = box.row()
        expand_core = shotput.expand_core_ui if hasattr(shotput, 'expand_core_ui') else False
        row.prop(shotput, "expand_core_ui", 
                icon="TRIA_DOWN" if expand_core else "TRIA_RIGHT", 
                icon_only=True, emboss=False)
        row.label(text="Core Passes", icon='RENDER_RESULT')
        
        if expand_core:
            box.prop(shotput, "core_override", text="Core Name Override")
            row = box.row()
            row.template_list("SHOTPUT_UL_CorePasses", "", shotput, "core_passes", shotput, "core_passes_index", rows=3)
            col = row.column(align=True)
            col.operator("shotput.core_pass_add", icon='ADD', text="")
            col.operator("shotput.core_pass_remove", icon='REMOVE', text="")
            col.separator()
            col.operator("shotput.core_pass_move_up", icon='TRIA_UP', text="")
            col.operator("shotput.core_pass_move_down", icon='TRIA_DOWN', text="")

        # AOV Passes UIList (collapsible, closed by default)
        box = layout.box()
        row = box.row()
        expand_aov = shotput.expand_aov_ui if hasattr(shotput, 'expand_aov_ui') else False
        row.prop(shotput, "expand_aov_ui", 
                icon="TRIA_DOWN" if expand_aov else "TRIA_RIGHT", 
                icon_only=True, emboss=False)
        row.label(text="AOV Passes", icon='IMAGE_RGB')
        
        if expand_aov:
            box.prop(shotput, "aov_override", text="AOV Name Override")
            
            # Add scan button for shader AOVs
            row = box.row()
            row.operator("shotput.scan_shader_aovs", text="Scan Scene for AOVs", icon='VIEWZOOM')
            
            row = box.row()
            row.template_list("SHOTPUT_UL_AOVPasses", "", shotput, "aov_passes", shotput, "aov_passes_index", rows=3)
            col = row.column(align=True)
            col.operator("shotput.aov_pass_add", icon='ADD', text="")
            col.operator("shotput.aov_pass_remove", icon='REMOVE', text="")
            col.separator()
            col.operator("shotput.aov_pass_move_up", icon='TRIA_UP', text="")
            col.operator("shotput.aov_pass_move_down", icon='TRIA_DOWN', text="")

        # Data Passes Section (collapsible, closed by default)
        box = layout.box()
        row = box.row()
        expand_data = shotput.expand_data_ui if hasattr(shotput, 'expand_data_ui') else False
        row.prop(shotput, "expand_data_ui", 
                icon="TRIA_DOWN" if expand_data else "TRIA_RIGHT", 
                icon_only=True, emboss=False)
        row.label(text="Data Passes", icon='FILE_BLEND')
        
        if expand_data:
            # Basic data passes
            col = box.column(align=True)
            col.prop(shotput, "z", text="Depth")
            col.prop(shotput, "normal", text="Normal")
            col.prop(shotput, "vector", text="Motion Vector")
            col.prop(shotput, "position", text="UV")
            col.prop(shotput, "mist", text="Mist")
            col.prop(shotput, "occlusion", text="Ambient Occlusion")
            
            # Cryptomatte passes
            col.separator()
            col.prop(shotput, "crypto_object", text="Cryptomatte Object")
            col.prop(shotput, "crypto_material", text="Cryptomatte Material")
            col.prop(shotput, "crypto_asset", text="Cryptomatte Asset")

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
        # Only show when a File Output node with shotput_data is selected
        return (context.space_data.type == 'NODE_EDITOR' and
                context.active_node and
                context.active_node.type == 'OUTPUT_FILE' and
                hasattr(context.active_node, 'shotput_data'))
    
    def draw(self, context):
        layout = self.layout
        node = context.active_node
        shotput_data = node.shotput_data
        
        # Description/Help Box
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Shotput File Output Node", icon='INFO')
        col.separator(factor=0.5)
        
        # Multi-line description with smaller text
        col.scale_y = 0.8
        col.label(text="This File Output node is configured for")
        col.label(text="organized render pass management.")
        col.label(text="Paths use token-based naming for")
        col.label(text="consistent project organization.")
        
        layout.separator()
        
        # Node Properties Box
        box = layout.box()
        box.label(text="Shotput Properties", icon='SETTINGS')
        
        # Show Shotput version (read-only)
        if shotput_data.shotput_version:
            row = box.row()
            row.label(text=f"Shotput Version: {shotput_data.shotput_version}", icon='INFO')
            row.enabled = False  # Make it read-only
        
        box.prop(shotput_data, "render_layer", text="Render Layer")
        box.prop(shotput_data, "pass_name", text="Pass Name")
        box.prop(shotput_data, "variant", text="Variant")
        
        # Path Tokens Box
        box = layout.box()
        box.label(text="Path Configuration", icon='FILE_FOLDER')
        box.prop(shotput_data, "root_folder_token", text="Root Folder")
        box.prop(shotput_data, "file_name_token", text="File Name")
        
        # Output Folder Actions
        row = box.row()
        row.operator("shotput.open_output_folder", text="Open Output Folder", icon='FOLDER_REDIRECT')
        
        # Stored Passes UIList
        box = layout.box()
        box.label(text="Output Passes", icon='RENDERLAYERS')
        
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
    SHOTPUT_OT_SyncNodePasses,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

