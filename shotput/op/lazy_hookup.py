"""
Lazy Hook-up Operator for Shotput

This operator handles manual connection of File Output nodes to render layer outputs.
"""

import bpy
from ..utils.lazy_hookup import (
    connect_file_output_to_render_layer,
    connect_composite_to_render_layer,
    get_render_layers
)
from ..utils.log import LoggerFactory

logger = LoggerFactory.logger_obj()


class OT_Lazy_Hookup(bpy.types.Operator):
    bl_idname = "shotput.lazy_hookup"
    bl_label = "Connect to Render Layer"
    bl_description = "Connect selected File Output or Composite node to render layer outputs using fuzzy matching"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Must be in compositor with an active node
        if not context.space_data or context.space_data.type != 'NODE_EDITOR':
            return False
        if context.space_data.tree_type != 'CompositorNodeTree':
            return False
        if not context.active_node:
            return False
        
        # Must be a File Output or Composite node
        return context.active_node.type in ['OUTPUT_FILE', 'COMPOSITE']
    
    def execute(self, context):
        active_node = context.active_node
        
        if not active_node:
            self.report({'ERROR'}, "No active node selected")
            return {'CANCELLED'}
        
        # Check if there are render layers available
        render_layers = get_render_layers(context)
        if not render_layers:
            self.report({'ERROR'}, "No render layers found in scene")
            return {'CANCELLED'}
        
        # If multiple render layers and none selected in Shotput properties
        if len(render_layers) > 1:
            shotput_props = context.scene.shotput
            if not shotput_props.render_layer or shotput_props.render_layer not in render_layers:
                self.report({'ERROR'}, 
                           f"Multiple render layers found ({', '.join(render_layers)}). "
                           "Please select one in Shotput properties.")
                return {'CANCELLED'}
        
        # Connect based on node type
        try:
            if active_node.type == 'OUTPUT_FILE':
                connections = connect_file_output_to_render_layer(context, active_node)
                if connections:
                    connection_count = len(connections)
                    self.report({'INFO'}, f"Connected {connection_count} output(s) to File Output node")
                    logger.info(f"Manual lazy hook-up: connected {connection_count} outputs")
                else:
                    self.report({'WARNING'}, "No matching outputs found to connect")
                    
            elif active_node.type == 'COMPOSITE':
                success = connect_composite_to_render_layer(context, active_node)
                if success:
                    self.report({'INFO'}, "Connected Image output to Composite node")
                    logger.info("Manual lazy hook-up: connected to Composite node")
                else:
                    self.report({'WARNING'}, "Could not connect to Composite node")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Connection failed: {str(e)}")
            logger.error(f"Manual lazy hook-up failed: {e}")
            return {'CANCELLED'}


classes = (
    OT_Lazy_Hookup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
