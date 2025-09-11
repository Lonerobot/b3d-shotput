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
        
        # Determine which render layer to use
        target_render_layer = None
        original_render_layer = None
        
        # If multiple render layers, try to find a selected render layer node first
        if len(render_layers) > 1:
            # Check if there's a selected render layer node we can use
            for node in context.scene.node_tree.nodes:
                if node.type == 'R_LAYERS' and node.select and node != active_node:
                    target_render_layer = node.layer
                    print(f"Shotput: Found selected render layer node using layer: {target_render_layer}")
                    break
            
            # If no selected render layer node found, check Shotput properties
            if not target_render_layer:
                shotput_props = context.scene.shotput
                if shotput_props.render_layer and shotput_props.render_layer in render_layers:
                    target_render_layer = shotput_props.render_layer
                    print(f"Shotput: Using render layer from Shotput properties: {target_render_layer}")
                else:
                    self.report({'ERROR'}, 
                               f"Multiple render layers found ({', '.join(render_layers)}). "
                               "Please select a render layer node alongside the file output")
                    return {'CANCELLED'}
        else:
            # Single render layer, use it
            target_render_layer = render_layers[0]
            print(f"Shotput: Using single available render layer: {target_render_layer}")
        
        # Temporarily set the Shotput render layer property if needed
        shotput_props = context.scene.shotput
        if shotput_props.render_layer != target_render_layer:
            original_render_layer = shotput_props.render_layer
            shotput_props.render_layer = target_render_layer
            print(f"Shotput: Temporarily set render layer to '{target_render_layer}'")
        
        # Connect based on node type
        try:
            if active_node.type == 'OUTPUT_FILE':
                connections = connect_file_output_to_render_layer(context, active_node)
                if connections:
                    connection_count = len(connections)
                    self.report({'INFO'}, f"Connected {connection_count} output(s) to File Output node using layer '{target_render_layer}'")
                    logger.info(f"Manual lazy hook-up: connected {connection_count} outputs from layer '{target_render_layer}'")
                else:
                    self.report({'WARNING'}, f"No matching outputs found to connect from layer '{target_render_layer}'")
                    
            elif active_node.type == 'COMPOSITE':
                success = connect_composite_to_render_layer(context, active_node)
                if success:
                    self.report({'INFO'}, f"Connected Image output to Composite node from layer '{target_render_layer}'")
                    logger.info(f"Manual lazy hook-up: connected to Composite node from layer '{target_render_layer}'")
                else:
                    self.report({'WARNING'}, f"Could not connect to Composite node from layer '{target_render_layer}'")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Connection failed: {str(e)}")
            logger.error(f"Manual lazy hook-up failed: {e}")
            return {'CANCELLED'}
            
        finally:
            # Restore original render layer property if we changed it
            if original_render_layer is not None:
                shotput_props.render_layer = original_render_layer
                print(f"Shotput: Restored render layer to '{original_render_layer}'")


classes = (
    OT_Lazy_Hookup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
