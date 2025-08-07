
import bpy

from dataclasses import dataclass
from pathlib import Path
import os

from .version_utils import VersionUtils
from .common import ShowMessageBox

from .log import LoggerFactory
logger = LoggerFactory.logger_obj()

from .. import preferences

@dataclass
class OutputPathProperties:
    """Class like access to package path components, avoiding splitting operations."""
    path_root = str
    work_render_root = str
    full_path = str
    # filename_stub = str
    filetype = str
    filename = str
    version = str
    version_number = int
    pass_name = str
    layer_name = str
    variant_name = str
    aov_name = str
    folder_path = str
    shot = str
    task = str
    project = str
    workfile_name = str
    workdir = str
    project_short_code = str
    user = str
    host = str
    task_start = int
    task_end = int

class OutputPathUtils():

    # this function needs commenting and probably tidying up a bit, it's horrible
    """
    the blender file output node name, always [short_code].[layer_name].[variant] 

    aov_name = the pass AOV output name


    """

    @staticmethod
    def GetOutputFileData(context,
                         project_short_code="projName",
                         layer_name="RenderLayer",                         
                         variant="Main",
                         aov_name="unsupplied",
                         subfolder="renders",
                         format="exr",
                         version=None,
                         ):
        
        scene = context.scene
        props = scene.Render_Setup_Properties

        oProps = OutputPathProperties()

        # AYON uses Folders now, this might need handling differently 
        oProps.folder_path = props.folder_name 
        # drop the last path element to get the traditionally named asset/shot
        oProps.shot = Path(props.folder_name).name

        oProps.task = props.task_name

        # project_short_code comes from the JSON template
        oProps.project = props.full_project_name

        #  workdir will get the full path the the current directory
        oProps.workdir = props.work_path_name
        oProps.host = "Blender"
        oProps.user = props.user_name
        oProps.task_start = scene.frame_start         
        oProps.task_end = scene.frame_end        

        if oProps:
            oProps.layer_name = layer_name
            oProps.variant_name = variant
            oProps.aov_name = aov_name

            oProps.pass_name = f'{oProps.layer_name}_{oProps.variant_name}'
            work_render_root = Path( oProps.workdir ) / subfolder / oProps.host

            if version:
                next_version = VersionUtils.getVersionString(version, up=False)
            else:
                current_version = VersionUtils.getVersionFolders(work_render_root)
                next_version = VersionUtils.getVersionString(current_version)

            # logger.debug(f'Next Render Version for { oProps.folder_path}:{oProps.task} is {next_version}')

            oProps.filename = f"{oProps.pass_name}_{oProps.aov_name}.{next_version}.####.{format}" 
            # oProps.filename_stub =  f"{oProps.shot}_{oProps.pass_name}"
            oProps.path_root = str( work_render_root / next_version / oProps.pass_name )
            oProps.full_path = str( work_render_root / next_version / oProps.pass_name / oProps.filename)         
            oProps.filetype = format 

            oProps.work_render_root =  str( work_render_root )

            oProps.version = next_version
            oProps.version_number = int(next_version.lstrip("v"))
            oProps.project_short_code = project_short_code
            oProps.workfile_name = bpy.path.basename(bpy.data.filepath)

            # logger.debug(
            #     f'{project_short_code}.{layer_name}.{aov_name} Output Path - {oProps.fullPath}')
            return oProps

        else:
            defaultPath = bpy.context.scene.render.filepath
            dirname = os.path.dirname(defaultPath)
            if not dirname.endswith(('/', '\\')):
                dirname += "/"
            if not dirname:
                dirname = os.path.expanduser('~') + "/"
            fileName = "output"
            fullPath = dirname + fileName
            return fullPath

    @staticmethod
    def setMetaData(context):
        scene = context.scene
        scene.render.metadata_input = 'SCENE'

        metadata_params = ['use_stamp_date', 'use_stamp_time',
                           'use_stamp_render_time', 'use_stamp_frame',
                           'use_stamp_frame_range', 'use_stamp_memory',
                           'use_stamp_hostname', 'use_stamp_camera',
                           'use_stamp_lens', 'use_stamp_scene',
                           'use_stamp_filename', 'use_stamp_note']

        for setting in metadata_params:
            setattr(scene.render, f'{setting}', True)

        # disabled due to render border system
        # if scene.camera:
        #     cam_name = scene.camera.name
        #     note_str = f'Camera Name : {cam_name}'
        #     scene.render.stamp_note_text = note_str

    @staticmethod
    def SetupFlamencoOutput(context, name=None, root=None):
        scene = context.scene
        prefs = preferences.get(context)
        debug_notfound = 'Flamenco is not installed or configured - Please enable the Addon in the Blender settings.'
        debug_cant_connect = 'It was not possible to connect to the Flamenco Manager- Please check the IP Address in the Blender settings.'

        if bpy.ops.flamenco and hasattr(bpy.ops.flamenco, 'ping_manager'):
            try:
                if bpy.ops.flamenco.ping_manager():                    
                    scene.flamenco_job_name = name
                    scene.flamenco_job_priority = 50
                    scene.flamenco_job_type = prefs.flamenco_job_type
                    scene.flamenco_job_settings.render_output_root = root
                    bpy.ops.flamenco.eval_setting(
                        setting_key="render_output_path", setting_eval="str(Path(abspath(settings.render_output_root), 'beauty_####'))")
                    bpy.ops.flamenco.eval_setting(
                        setting_key="frames", setting_eval="f'{C.scene.frame_start}-{C.scene.frame_end}'")
                    
                else:
                    ShowMessageBox(debug_cant_connect,
                                   'Flamenco Render Config', 'ERROR')
            except:
                ShowMessageBox(
                    debug_notfound, 'Flamenco Render Config', 'ERROR')
        else:
            ShowMessageBox(debug_notfound, 'Flamenco Render Config', 'ERROR')


    @staticmethod
    def SetupFlamencoPublish(context, jobType="The-Line-Ayon-Ftrack-Publish", ):
        scene = context.scene
        debug_notfound = 'Flamenco is not installed or configured - Please enable the Addon in the Blender settings.'
        debug_cant_connect = 'It was not possible to connect to the Flamenco Manager- Please check the IP Address in the Blender settings.'

        if bpy.ops.flamenco and hasattr(bpy.ops.flamenco, 'ping_manager'):
            try:
                if bpy.ops.flamenco.ping_manager():                    
                    scene.flamenco_job_type = jobType
                    bpy.ops.flamenco.eval_setting(
                        setting_key="publish_data_root", setting_eval="C.scene.Render_Setup_Properties.render_output_root")
                else:
                    ShowMessageBox(debug_cant_connect,
                                   'Flamenco Render Config', 'ERROR')
            except:
                ShowMessageBox(
                    "Error setting the Publish Job Settings", 'Flamenco Render Config', 'ERROR')
        else:
            ShowMessageBox(debug_notfound, 'Flamenco Render Config', 'ERROR')


