import bpy
import subprocess
from pathlib import Path
import os
import logging

from . import __package_name__
from .utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

_template_enum_items = []

# # 
# def enum_items():
#     # _template_enum_items.clear()
#     _template_enum_items = get_templates()
#     if len(_template_enum_items) == 0:
#         _template_enum_items.append(
#             ("No Project render templates found", "Nope", ""))
#     return _template_enum_items


class OT_Open_Render_Template_Dir(bpy.types.Operator):
    bl_idname = "shotput.open_render_templates"
    bl_label = "Open Render Template Directory"
    bl_description = "Opens the current render template directory."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = get(context)
        template_dir = get_template_directory(prefs)
        if template_dir and Path(template_dir).exists():
            subprocess.call(f'explorer "{template_dir}"', shell=True)
            self.report({'INFO'}, f"Opened directory: {template_dir}")
        else:
            self.report({'WARNING'}, "Template directory not found")
            return {'CANCELLED'}
        return {'FINISHED'}


def get_template_directory(prefs):
    """ 
    Formats a version specific path so we can have different templates for Blender versions 
    Currently returns the setup for the current render engine if there is no project configuration found
    This way the studio default can be used if needed outside of Pype   
    """
    try:
        project_path = Path(prefs.project_path)

        if project_path.exists():
            template_path = project_path / prefs.template_subpath
            return str(template_path)
        else:
            logger.info(f'The template does not exist in the following directory - {project_path}')
            return ""
    except Exception as e:
        logger.error(f"Error getting template directory: {e}")
        return ""


def get_templates(self, context):
    """Get available template files"""
    items = []
    try:
        prefs = get(context)
        template_dir = Path(get_template_directory(prefs))
        if template_dir.exists():
            template_files = list(template_dir.glob('*.json'))
            if template_files:
                for t in template_files:
                    items.append((t.stem, t.stem, ""))
        
        if not items:
            items.append(("NONE", "No Templates Found", "No JSON templates found in directory"))
            
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        items.append(("ERROR", "Error Loading Templates", str(e)))
        
    return items


def get_project_path(prefs):
    AYON_server_root = os.getenv("AYON_PROJECT_ROOT_WORK") 
    AYON_project = os.getenv("AYON_PROJECT_NAME")

    # logger.debug(f'render output setup - AYON_project - {AYON_project} AYON_server_root - {AYON_server_root}')
    
    if AYON_server_root and AYON_project:  
        project_path = Path() / AYON_server_root / AYON_project
        # logger.debug(f'Render Setup Preferences - get_project_path - {project_path}')
        return str(project_path)
    else:
        return ""

def get_output_prefixes(prefs):  
    """Get output prefixes from template - currently disabled"""
    return ""




class ShotputPreferences(bpy.types.AddonPreferences):
    """Preferences class: Preferences for the Shotput add-on"""

    bl_idname = "shotput"

    project_path: bpy.props.StringProperty(
        name="Project Path",
        description="The main project location folder",
        default="",
        get=get_project_path,
    )

    template_prefixes: bpy.props.StringProperty(
        name="Template Prefixes",
        description="",
        default="",
        get=get_output_prefixes,
    )

    template_subpath: bpy.props.StringProperty(
        name="Template Subpath",
        description="Subdirectory for the render template.json",
        default="tools/pipeline/blender/_templates",
    )

    template_path: bpy.props.StringProperty(
        name="Template Path",
        description="Location of the pathing schema file",
        default="",
        get=get_template_directory,
    )

    output_subpath: bpy.props.StringProperty(
        name="Output Subpath",
        description="output subpath to be added to the current shot/task output",
        default="renders/blender",
    )

    flamenco_job_type: bpy.props.StringProperty(
        name="Flamenco Jobtype",
        description="Force this job type for Flamenco Submission",
        default="The-Line-Production",
    )

    # enable debug mode
    toggle_debug_mode:  bpy.props.BoolProperty(
        name="Enable Debugging Mode (Increases the messages sent to the console)",
        description="Enable debugging mode",
        default=True,
       update=lambda self, context: self.set_logging_preference()
    )
    
    # versioning preferences
    auto_create_version_folders: bpy.props.BoolProperty(
        name="Auto-Create Version Folders",
        description="Automatically create version directories when calculating next version (may affect version calculations)",
        default=False
    )

    enum_templates: bpy.props.EnumProperty(
        name="Template Schema",
        description="Select the File",
        items=get_templates,
    )

    def set_logging_preference(self):
        if self.toggle_debug_mode:
            LoggerFactory.set_level(logging.DEBUG)
            logger.debug("Debug Logger Enabled")
        else:
            LoggerFactory.set_level(logging.INFO)

        logger.info(f'Updated Logging Level - {logger.level}')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        prefs = get(context)
        layout.use_property_decorate = False
        col = self.layout.column(align=True)

        row = col.row(align=True)
        row.prop(self, "enum_templates")
        row.operator(OT_Open_Render_Template_Dir.bl_idname,
                     text="", icon="FOLDER_REDIRECT")

        def text_row(parent, text, label):
            split = parent.split(factor=0.2)
            split.label(text=text)
            split.label(text=label)

        text_row(col, "Project Path:", prefs.project_path)
        text_row(col, "Template Path:", prefs.template_path)
        col.separator()

        col.prop(self, "template_subpath")
        # col.prop(self, "output_subpath")
        col.prop(self, "flamenco_job_type")
        col.prop(self, "toggle_debug_mode")
        col.separator()
        col.prop(self, "auto_create_version_folders")


def get(context: bpy.types.Context) -> ShotputPreferences:
    """Return the add-on preferences."""
    prefs = context.preferences.addons[__package_name__].preferences
    return prefs

classes = (
    ShotputPreferences,
    OT_Open_Render_Template_Dir,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
