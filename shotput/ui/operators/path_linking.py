"""
Path linking toggle operator for Shotput nodes.
"""
import bpy


class SHOTPUT_OT_TogglePathLinking(bpy.types.Operator):
    bl_idname = "shotput.toggle_path_linking"
    bl_label = "Toggle Path Linking"
    bl_description = "Toggle path linking for this File Output node"
    
    def execute(self, context):
        # Get active node (can be File Output or Composite)
        node = context.active_node
        if not node or node.type not in ['OUTPUT_FILE', 'COMPOSITE'] or not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "No valid Shotput node selected")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        
        # Toggle the path linking
        new_state = not shotput_data.path_linked
        
        print(f"Shotput: Toggling path linking from {shotput_data.path_linked} to {new_state} for node {node.name}")
        
        if new_state:
            # Enabling path linking
            if shotput_data.root_folder_token and not shotput_data.root_folder_token_backup:
                # Back up the current root folder token
                shotput_data.root_folder_token_backup = shotput_data.root_folder_token
                print(f"Shotput: Backed up root folder token: {shotput_data.root_folder_token_backup}")
                
                # Set appropriate token based on node type and format
                if (node.name == "Shotput_Data_Passes" and 
                    hasattr(node, 'format') and 
                    node.format.file_format == 'OPEN_EXR_MULTILAYER'):
                    # For data passes with multilayer EXR, include filename token
                    shotput_data.root_folder_token = "{passname}"
                    print(f"Shotput: Set multilayer EXR token: {shotput_data.root_folder_token}")
                else:
                    # Default simple token for other nodes
                    shotput_data.root_folder_token = "{passname}"
                    print(f"Shotput: Set simple token: {shotput_data.root_folder_token}")
        else:
            # Disabling path linking
            if shotput_data.root_folder_token_backup:
                # Restore the backed up root folder token
                shotput_data.root_folder_token = shotput_data.root_folder_token_backup
                print(f"Shotput: Restored root folder token: {shotput_data.root_folder_token}")
                # Clear the backup
                shotput_data.root_folder_token_backup = ""
                print("Shotput: Cleared backup")
            else:
                print("Shotput: No backup found to restore")
        
        # Set the new state
        shotput_data.path_linked = new_state
        print(f"Shotput: Path linking is now: {shotput_data.path_linked}")
        
        return {'FINISHED'}


classes = (
    SHOTPUT_OT_TogglePathLinking,
)
