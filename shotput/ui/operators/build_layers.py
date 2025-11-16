"""
Build render layer nodes operator.
"""
import bpy
from ...utils.log import LoggerFactory

logger = LoggerFactory.logger_obj()


class SHOTPUT_OT_BuildRenderLayers(bpy.types.Operator):
    """Create render layer nodes for each view layer in the scene"""
    bl_idname = "shotput.build_render_layers"
    bl_label = "View Layers To Render Layers"
    bl_description = "Create a render layer node for each view layer in the scene, positioned and aligned"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if we're in compositor"""
        return (context.space_data and 
                context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'CompositorNodeTree')
    
    def execute(self, context):
        logger.info("Build Render Layers operator executed")
        print("Shotput: Build Render Layers from View operator executed")
        
        # Get scene and compositor tree
        scene = context.scene
        if not scene.use_nodes:
            scene.use_nodes = True
            print("Shotput: Enabled compositor nodes")
        
        tree = scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Get all view layers from the scene
        view_layers = scene.view_layers
        if not view_layers or len(view_layers) == 0:
            self.report({'WARNING'}, "No view layers found in scene")
            return {'CANCELLED'}
        
        # Starting position for the first node
        start_x = 0
        start_y = 0
        
        # Node spacing
        spacing_y = 300  # Vertical spacing between nodes
        
        # Create a render layer node for each view layer
        created_nodes = []
        for i, view_layer in enumerate(view_layers):
            # Create render layer node
            render_node = tree.nodes.new(type='CompositorNodeRLayers')
            render_node.name = f"Render Layers - {view_layer.name}"
            render_node.label = view_layer.name
            
            # Set the view layer (scene property)
            render_node.layer = view_layer.name
            
            # Position the node - stack vertically
            render_node.location = (start_x, start_y - (i * spacing_y))
            
            created_nodes.append(render_node)
            print(f"Shotput: Created render layer node for '{view_layer.name}' at {render_node.location}")
        
        # Select all created nodes
        for node in tree.nodes:
            node.select = False
        for node in created_nodes:
            node.select = True
        
        # Set the first node as active
        if created_nodes:
            tree.nodes.active = created_nodes[0]
        
        self.report({'INFO'}, f"Created {len(created_nodes)} render layer nodes")
        return {'FINISHED'}


classes = (
    SHOTPUT_OT_BuildRenderLayers,
)
