r'''
  _____ _  _ ___   _	___ _  _ ___			
 |_   _| || | __| | |  |_ _| \| | __|   		
_______________________________________          
   |_| |_||_|___| |____|___|_|\_|___|   		
                                                
    _   _  _ ___ __  __   _ _____ ___ ___  _  _ 
   /_\ | \| |_ _|  \/  | /_\_   _|_ _/ _ \| \| |
  / _ \| .` || || |\/| |/ _ \| |  | | (_) | .` |
 /_/ \_\_|\_|___|_|  |_/_/ \_\_| |___\___/|_|\_|


Init Operators

To add a new one you need to...

1.  Add the py file to this directory
2.  Register the class name in this file
3.  Add the line :
         box.operator(OPERATOR_NAME.bl_idname, icon='RENDERLAYERS') 
    To the panel operator ui.py 
'''

from .open_output_folder import OT_Open_Output_Folder
from .create_core_passes import OT_Create_Core_Passes
from .create_aov_passes import OT_Create_AOV_Passes
from .create_data_passes import OT_Create_Data_Passes
from .versioning import OT_Update_Version, OT_Preview_Paths, OT_Token_Help


import bpy

classes = (
        OT_Open_Output_Folder,
        OT_Create_Core_Passes,
        OT_Create_AOV_Passes,
        OT_Create_Data_Passes,
        OT_Update_Version,
        OT_Preview_Paths,
        OT_Token_Help,
        )


def register():
  
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)


