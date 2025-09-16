import bpy

from . import __package_name__
from .utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

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

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        layout.use_property_decorate = False     
 
        # General Settings
        box = layout.box()
        box.label(text="General Settings", icon="PREFERENCES")
        col = box.column(align=True)

        col.prop(self, "auto_create_version_folders")
        
        # Core Pass Settings
        box = layout.box()
        box.label(text="Pass Settings", icon="RENDER_RESULT")
        col = box.column(align=True)

        col.prop(self, "subpath_token_value")
        col.prop(self, "sequence_padding")   
        col.prop(self, "data_node_format_override")


def get(context: bpy.types.Context) -> ShotputPreferences:
    """Return the add-on preferences."""
    prefs = context.preferences.addons[__package_name__].preferences
    return prefs

classes = (
    ShotputPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
