import subprocess
import bpy

from pathlib import Path
from ..utils.path_utils import PathUtils
from ..utils.common import ShowMessageBox

from ..utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

class OT_Open_Output_Folder(bpy.types.Operator):
    bl_idname = "tl.open_output_folder"
    bl_description  = "Opens the current shot render root folder"
    bl_label = "Output Directory"
    bl_options = {'REGISTER', 'UNDO'}
    
    # opens the directory of the current render path
    def openFolder(self, context):       

        props = context.scene.Render_Setup_Properties                
        render_output_root = Path (props.render_output_root)

        logger.info (f'Open Folder - {render_output_root}')
        if render_output_root.exists():
            subprocess.call(f'explorer {str(render_output_root)}, shell=True')
        else:
            ShowMessageBox( message=f"There wasn't a directory at {render_output_root}. Perhaps wait for the render to complete? " , title= "No Directory Present")
    
    def execute(self, context):
        self.openFolder(context)
        return {'FINISHED'}    
        
