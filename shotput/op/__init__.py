

from .open_output_folder import OT_Open_Output_Folder
from .create_core_passes import OT_Create_Core_Passes, OT_Create_Linked_Composite
from .create_aov_passes import OT_Create_AOV_Passes
from .create_data_passes import OT_Create_Data_Passes
from .scan_shader_aovs import OT_Scan_Shader_AOVs
from .versioning import OT_Update_Version, OT_Preview_Paths, OT_Token_Help, OT_Load_Preset, OT_Save_Preset
from .lazy_hookup import OT_Lazy_Hookup


import bpy

classes = (
        OT_Open_Output_Folder,
        OT_Create_Core_Passes,
        OT_Create_Linked_Composite,
        OT_Create_AOV_Passes,
        OT_Create_Data_Passes,
        OT_Scan_Shader_AOVs,
        OT_Update_Version,
        OT_Preview_Paths,
        OT_Token_Help,
        OT_Load_Preset,
        OT_Save_Preset,
        OT_Lazy_Hookup,
        )


def register():
  
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)


