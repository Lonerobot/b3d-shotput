import subprocess
import bpy

from pathlib import Path
from ..utils.path_utils import PathUtils
from ..utils.token_parser import TokenParser

from ..utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()


def show_message_box(message="", title="Message Box", icon='INFO'):
    """Show a popup message box to the user"""
    def draw(self, context):
        self.layout.label(text=message)
    
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

class OT_Open_Output_Folder(bpy.types.Operator):
    bl_idname = "shotput.open_output_folder"
    bl_description = "Opens the output folder for Shotput file output nodes. Uses the active node if selected, otherwise opens the first available Shotput node's folder"
    bl_label = "Open Output Folder"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Property to specify what type of folder to open
    folder_type: bpy.props.EnumProperty(
        name="Folder Type",
        description="Type of folder to open",
        items=[
            ('OUTPUT', 'Output Folder', 'Open output folder from node'),
            ('PRESET', 'Preset Path', 'Open preset path from environment variable'),
        ],
        default='OUTPUT'
    )
    
    @classmethod
    def poll(cls, context):
        """Enable this operator when there are Shotput file output nodes in the scene or when opening preset path."""
        # Always allow preset path opening (will be handled in execute)
        return True
    
    def openPresetPath(self, context):
        """Open the SHOTPUT_PRESET_PATH folder from environment variable."""
        import os
        
        preset_path = os.getenv("SHOTPUT_PRESET_PATH")
        
        if not preset_path:
            show_message_box(
                message="SHOTPUT_PRESET_PATH environment variable is not set.\n\nSet this variable to specify a custom location for Shotput preset files.",
                title="Preset Path Not Set",
                icon='INFO'
            )
            self.report({'WARNING'}, "SHOTPUT_PRESET_PATH environment variable not set")
            return {'CANCELLED'}
        
        # Convert to Path object
        preset_dir = Path(preset_path)
        
        if preset_dir.exists():
            # Open the folder using Windows explorer
            subprocess.run(['explorer', str(preset_dir)], check=False)
            self.report({'INFO'}, f"Opened preset path: {preset_dir}")
            logger.info(f"Opened SHOTPUT_PRESET_PATH: {preset_dir}")
            return {'FINISHED'}
        else:
            # Try to create the directory if it doesn't exist
            try:
                preset_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(['explorer', str(preset_dir)], check=False)
                self.report({'INFO'}, f"Created and opened preset path: {preset_dir}")
                logger.info(f"Created and opened SHOTPUT_PRESET_PATH: {preset_dir}")
                return {'FINISHED'}
            except Exception as e:
                show_message_box(
                    message=f"Preset path doesn't exist and couldn't be created:\n{preset_dir}\n\nError: {str(e)}",
                    title="Directory Not Found"
                )
                self.report({'ERROR'}, f"Could not access or create preset path: {preset_dir}")
                return {'CANCELLED'}
    
    def openFolder(self, context):
        """Open the output folder for the active Shotput file output node or prompt to select one."""
        tree = context.scene.node_tree
        active_node = tree.nodes.active
        
        # Find the target node - either the active one or the first Shotput file output node
        target_node = None
        
        # Check if active node is a valid Shotput file output node
        if (active_node and 
            active_node.type == 'OUTPUT_FILE' and 
            hasattr(active_node, 'shotput_data') and 
            active_node.shotput_data.root_folder_token):
            target_node = active_node
        else:
            # Find the first Shotput file output node in the scene
            shotput_nodes = []
            for node in tree.nodes:
                if (node.type == 'OUTPUT_FILE' and 
                    hasattr(node, 'shotput_data') and 
                    node.shotput_data.root_folder_token):
                    shotput_nodes.append(node)
            
            if not shotput_nodes:
                self.report({'ERROR'}, "No Shotput file output nodes found in the scene")
                return {'CANCELLED'}
            elif len(shotput_nodes) == 1:
                target_node = shotput_nodes[0]
            else:
                # Multiple nodes found - use the first one but inform the user
                target_node = shotput_nodes[0]
                self.report({'INFO'}, f"Multiple Shotput nodes found. Opening folder for '{target_node.name}'. Select a specific node for more precise control.")
        
        if not target_node:
            self.report({'ERROR'}, "No valid Shotput file output node found")
            return {'CANCELLED'}
        
        # Get the Shotput properties from the target node
        node_props = target_node.shotput_data
        
        if not node_props.root_folder_token:
            self.report({'ERROR'}, f"No root folder token found in node '{target_node.name}'")
            return {'CANCELLED'}
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        try:
            # Parse the root folder token to get the actual path
            resolved_root_path = token_parser.parse_token(
                node_props.root_folder_token, 
                passname=node_props.pass_name
            )
            
            logger.info(f'Open Folder - Resolved path for node "{target_node.name}": {resolved_root_path}')
            print(f"Shotput: Resolved root folder path for '{target_node.name}': {resolved_root_path}")
            
            # Convert to Path object and check if it exists
            output_path = Path(resolved_root_path)
            
            if output_path.exists():
                # Open the folder using Windows explorer
                subprocess.run(['explorer', str(output_path)], check=False)
                self.report({'INFO'}, f"Opened folder: {output_path}")
            else:
                # Try to create the directory structure if it doesn't exist
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['explorer', str(output_path)], check=False)
                    self.report({'INFO'}, f"Created and opened folder: {output_path}")
                except Exception as e:
                    show_message_box(
                        message=f"Directory doesn't exist and couldn't be created:\n{output_path}\n\nError: {str(e)}", 
                        title="Directory Not Found"
                    )
                    self.report({'ERROR'}, f"Could not access or create directory: {output_path}")
                    
        except Exception as e:
            logger.error(f"Error parsing root folder token: {str(e)}")
            show_message_box(
                message=f"Error parsing root folder token:\n{node_props.root_folder_token}\n\nError: {str(e)}", 
                title="Token Parsing Error"
            )
            self.report({'ERROR'}, f"Error parsing root folder token: {str(e)}")
    
    def execute(self, context):
        if self.folder_type == 'PRESET':
            return self.openPresetPath(context)
        elif self.folder_type == 'OUTPUT':
            # Check if we can open output folder (need nodes)
            if not context.scene.use_nodes or not context.scene.node_tree:
                self.report({'ERROR'}, "No compositor nodes available")
                return {'CANCELLED'}
            
            # Check if there are any Shotput file output nodes
            tree = context.scene.node_tree
            has_shotput_nodes = False
            for node in tree.nodes:
                if (node.type == 'OUTPUT_FILE' and 
                    hasattr(node, 'shotput_data') and 
                    node.shotput_data.root_folder_token):
                    has_shotput_nodes = True
                    break
            
            if not has_shotput_nodes:
                self.report({'ERROR'}, "No Shotput file output nodes found in the scene")
                return {'CANCELLED'}
            
            self.openFolder(context)
            return {'FINISHED'}
        
        return {'CANCELLED'}    
        
