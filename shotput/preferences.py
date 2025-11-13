import bpy

from . import __package_name__
from .utils.log import LoggerFactory
from .utils import custom_icons
logger = LoggerFactory.logger_obj()

class SHOTPUT_OT_restore_node_colors(bpy.types.Operator):
    """Restore node colors to default values"""
    bl_idname = "shotput.restore_node_colors"
    bl_label = "Restore Default Colors"
    bl_description = "Reset all node colors to their default values"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        prefs = context.preferences.addons[__package_name__].preferences
        
        # Restore default colors
        prefs.core_node_color = (0.25, 0.45, 0.7)  # Blue
        prefs.core_render_layer_node_color = (0.510, 0.204, 0.294)  # Purple
        prefs.aov_node_color = (0.7, 0.4, 0.2)  # Orange
        prefs.data_node_color = (0.6, 0.25, 0.25)  # Red
        prefs.composite_node_color = (0.8, 0.4, 0.8)  # Pink
        
        self.report({'INFO'}, "Node colors restored to defaults")
        return {'FINISHED'}

class ShotputPreferences(bpy.types.AddonPreferences):
    """Preferences class: Preferences for the Shotput add-on"""
    bl_idname = __package_name__

    # versioning preferences
    auto_create_version_folders: bpy.props.BoolProperty(
        name="Auto-Create Version Folders",
        description="Automatically create version directories when calculating next version (may affect version calculations)",
        default=False
    )
    
    # shotput output preferences
    subpath_token_value: bpy.props.StringProperty(
        name="Subpath Token Value",
        description="Value to use for the {subpath} token in output paths",
        default="renders/blender"
    )
    
    sequence_padding: bpy.props.IntProperty(
        name="Sequence Padding",
        description="Number of digits for frame sequence padding (e.g., 4 = ####)",
        default=4,
        min=1,
        max=10
    )
    
    data_node_format_override: bpy.props.EnumProperty(
        name="Data Node Format Override",
        description="Force data passes to use this format (overrides UI setting)",
        items=[
            ('OPEN_EXR_MULTILAYER', 'EXR Multilayer', 'OpenEXR Multilayer format (recommended for data passes)'),
            ('OPEN_EXR', 'EXR Single', 'OpenEXR single channel format'),
            ('PNG', 'PNG', 'PNG format'),
            ('TIFF', 'TIFF', 'TIFF format')
        ],
        default='OPEN_EXR_MULTILAYER'
    )
    
    # Node color preferences
    core_node_color: bpy.props.FloatVectorProperty(
        name="Core Node Color",
        description="Color for core pass nodes (manual mode)",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.25, 0.45, 0.7)  # Blue
    )
    
    core_render_layer_node_color: bpy.props.FloatVectorProperty(
        name="Core Render Layer Node Color",
        description="Color for core pass nodes (render layer mode)",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.510, 0.204, 0.294)  # Purple
    )
    
    aov_node_color: bpy.props.FloatVectorProperty(
        name="AOV Node Color",
        description="Color for AOV pass nodes",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.7, 0.4, 0.2)  # Orange
    )
    
    data_node_color: bpy.props.FloatVectorProperty(
        name="Data Node Color",
        description="Color for data pass nodes",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.6, 0.25, 0.25)  # Red
    )
    
    composite_node_color: bpy.props.FloatVectorProperty(
        name="Composite Node Color",
        description="Color for composite nodes",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(0.8, 0.4, 0.8)  # Pink
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        layout.use_property_decorate = False     
 
        # General Settings
        box = layout.box()
        icon_preferences = custom_icons.get_icon_id_or_fallback('preferences')
        box.label(text="General Settings", **icon_preferences)
        col = box.column(align=True)
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Auto-Create Version Folders:")
        split.prop(self, "auto_create_version_folders", text="")
        
        # Core Pass Settings
        box = layout.box()
        icon_render_result = custom_icons.get_icon_id_or_fallback('render_result')
        box.label(text="Pass Settings", **icon_render_result)
        col = box.column(align=True)
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Subpath Token Value:")
        split.prop(self, "subpath_token_value", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Sequence Padding:")
        split.prop(self, "sequence_padding", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Data Node Format Override:")
        split.prop(self, "data_node_format_override", text="")
        
        # Node Color Settings
        box = layout.box()
        row = box.row()
        icon_color = custom_icons.get_icon_id_or_fallback('color')
        row.label(text="Node Colors", **icon_color)
        icon_refresh_prefs = custom_icons.get_icon_id_or_fallback('file_refresh')
        row.operator("shotput.restore_node_colors", text="Restore Defaults", **icon_refresh_prefs)
        
        col = box.column(align=True)
        
        # Use split layout for compact color swatches
        split = col.split(factor=0.5, align=True)
        split.label(text="Core Node Color:")
        split.prop(self, "core_node_color", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Core Render Layer Node Color:")
        split.prop(self, "core_render_layer_node_color", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="AOV Node Color:")
        split.prop(self, "aov_node_color", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Data Node Color:")
        split.prop(self, "data_node_color", text="")
        
        split = col.split(factor=0.5, align=True)
        split.label(text="Composite Node Color:")
        split.prop(self, "composite_node_color", text="")


def get(context: bpy.types.Context) -> ShotputPreferences:
    """Return the add-on preferences."""
    prefs = context.preferences.addons[__package_name__].preferences
    return prefs

classes = (
    SHOTPUT_OT_restore_node_colors,
    ShotputPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
