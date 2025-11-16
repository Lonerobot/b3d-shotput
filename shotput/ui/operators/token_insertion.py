"""
Token insertion operator for path fields.
"""
import bpy


class SHOTPUT_OT_InsertToken(bpy.types.Operator):
    bl_idname = "shotput.insert_token"
    bl_label = "Insert Token"
    bl_description = "Insert a token into the path field"
    
    token: bpy.props.StringProperty(name="Token")
    property_path: bpy.props.StringProperty(name="Property Path")
    
    def execute(self, context):
        try:
            # Get the target property based on property_path
            if self.property_path.startswith("scene.shotput."):
                # Scene-level property
                prop_name = self.property_path.replace("scene.shotput.", "")
                shotput = context.scene.shotput
                current_value = getattr(shotput, prop_name, "")
                new_value = current_value + "{" + self.token + "}"
                setattr(shotput, prop_name, new_value)
            elif self.property_path.startswith("node.shotput_data."):
                # Node-level property
                prop_name = self.property_path.replace("node.shotput_data.", "")
                node = context.active_node
                if not node or not hasattr(node, 'shotput_data'):
                    self.report({'ERROR'}, "No Shotput node selected")
                    return {'CANCELLED'}
                shotput_data = node.shotput_data
                current_value = getattr(shotput_data, prop_name, "")
                new_value = current_value + "{" + self.token + "}"
                setattr(shotput_data, prop_name, new_value)
            else:
                self.report({'ERROR'}, f"Unknown property path: {self.property_path}")
                return {'CANCELLED'}
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to insert token: {str(e)}")
            return {'CANCELLED'}


classes = (
    SHOTPUT_OT_InsertToken,
)
