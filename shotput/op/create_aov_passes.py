import bpy

from ..utils.log import LoggerFactory
from ..utils.defaults import get_file_format_for_pass_type
logger = LoggerFactory.logger_obj()

class OT_Create_AOV_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_aov_passes"
    bl_label = "Create AOV Passes"
    bl_description = "Create file output nodes for AOV passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        logger.info("Create AOV Passes operator clicked")
        print("Shotput: Create AOV Passes operator executed")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Check if we have AOV passes to create
        if len(shotput_props.aov_passes) == 0:
            self.report({'WARNING'}, "No AOV passes defined")
            return {'CANCELLED'}
        
        # Check if we're in Compositor workspace
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
            print("Shotput: Enabled compositor nodes")
        
        # Get compositor node tree
        tree = context.scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Create File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.name = f"Shotput_AOV_{shotput_props.aov_override}"
        file_output.label = f"AOV: {shotput_props.aov_override}"
        
        # Set node color - darker orange for AOV passes
        file_output.use_custom_color = True
        file_output.color = (0.7, 0.4, 0.2)  # Darker, more muted orange
        
        # Position the node (find a good spot)
        file_output.location = (400, -200)  # Offset below core passes
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = shotput_props.aov_override  # Use AOV override as pass name
        
        # Clear existing stored passes and populate with AOV passes
        node_props.stored_passes.clear()
        
        # Clear existing file slots (except the first one)
        while len(file_output.file_slots) > 1:
            file_output.file_slots.remove(file_output.file_slots[-1])
        
        # Configure file slots for each AOV pass
        for i, aov_pass in enumerate(shotput_props.aov_passes):
            if i == 0:
                # Use the default slot for the first pass
                file_output.file_slots[0].path = f"{shotput_props.aov_override}_{aov_pass.name}_"
            else:
                # Add new slots for additional passes
                file_output.file_slots.new(aov_pass.name)
                file_output.file_slots[i].path = f"{shotput_props.aov_override}_{aov_pass.name}_"
            
            # Add pass to stored passes
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = aov_pass.name
        
        # Set file format using override logic (respects UI setting for AOV passes)
        aov_format = get_file_format_for_pass_type("aov", shotput_props.output_format)
        file_output.format.file_format = aov_format
        
        print(f"Shotput: Created AOV passes node with {len(shotput_props.aov_passes)} passes")
        print(f"Shotput: Using format: {aov_format} (UI setting: {shotput_props.output_format})")
        logger.info(f"Created AOV passes file output node with {len(shotput_props.aov_passes)} passes")
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created AOV passes node with {len(shotput_props.aov_passes)} passes")
        
        return {'FINISHED'}
