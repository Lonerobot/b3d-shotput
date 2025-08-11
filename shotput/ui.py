



import bpy
from . import bl_info
from . import preferences

from .utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

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

# UIList for passes
class SHOTPUT_UL_CorePasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=True, icon='RENDER_RESULT')

class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=True, icon='IMAGE_RGB')

class TL_PT_Shotput_UI(bpy.types.Panel):
    bl_label = f"THE LINE - Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
    bl_category = "Shotput"
    bl_context = "output"
    bl_order = 2
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.1
        shotput = context.scene.shotput

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
        row.operator("shotput.preview_paths", icon='PREVIEW_RANGE', text="Preview Paths")
        row.operator("shotput.token_help", icon='HELP', text="Token Help")
        row = box.row()
        row.operator("shotput.update_version", icon='FILE_REFRESH', text="Update Version")

        # Path Tokens Box - Root Folder and File Name
        box = layout.box()
        box.label(text="Path Tokens", icon='FILE_FOLDER')
        box.prop(shotput, "root_folder_token", text="Root Folder")
        box.prop(shotput, "file_name_token", text="File Name")
        box.prop(shotput, "output_format", text="Output Format", expand=True)

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

# UIList for stored passes on File Output nodes
class SHOTPUT_UL_StoredPasses(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='RENDERLAYERS')

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
        
        # Node Properties Box
        box = layout.box()
        box.label(text="Shotput Properties", icon='SETTINGS')
        box.prop(shotput_data, "render_layer", text="Render Layer")
        box.prop(shotput_data, "pass_name", text="Pass Name")
        box.prop(shotput_data, "variant", text="Variant")
        
        # Path Tokens Box
        box = layout.box()
        box.label(text="Path Configuration", icon='FILE_FOLDER')
        box.prop(shotput_data, "root_folder_token", text="Root Folder")
        box.prop(shotput_data, "file_name_token", text="File Name")
        
        # Stored Passes UIList
        box = layout.box()
        box.label(text="Output Passes", icon='RENDERLAYERS')
        row = box.row()
        row.template_list("SHOTPUT_UL_StoredPasses", "", shotput_data, "stored_passes", shotput_data, "stored_passes_index", rows=3)

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
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

