import bpy
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type

logger = LoggerFactory.logger_obj()

class OT_Create_Core_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_core_passes"
    bl_label = "Create Core Passes"
    bl_description = "Create file output nodes for core passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        logger.info("Create Core Passes operator clicked")
        print("Shotput: Create Core Passes operator executed")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Check if we have core passes to create
        if len(shotput_props.core_passes) == 0:
            self.report({'WARNING'}, "No core passes defined")
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
        file_output.name = f"Shotput_Core_{shotput_props.core_override}"
        file_output.label = f"Core: {shotput_props.core_override}"
        
        # Set node color - darker blue for core passes
        file_output.use_custom_color = True
        file_output.color = (0.25, 0.45, 0.7)  # Darker, more muted blue
        
        # Position the node (find a good spot)
        file_output.location = (400, 0)
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = shotput_props.core_override  # Use core override as pass name
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        # Clear existing stored passes and populate with core passes
        node_props.stored_passes.clear()
        
        # Clear existing file slots (except the first one)
        while len(file_output.file_slots) > 1:
            file_output.file_slots.remove(file_output.file_slots[-1])
        
        # Configure file slots for each core pass using token parser
        for i, core_pass in enumerate(shotput_props.core_passes):
            pass_name = core_pass.name
            
            # Parse the file name token with specific pass name
            filename_token = node_props.file_name_token
            resolved_filename = token_parser.parse_token(filename_token, passname=pass_name)
            
            if i == 0:
                # Use the default slot for the first pass
                file_output.file_slots[0].path = f"{resolved_filename}_"
            else:
                # Add new slots for additional passes
                file_output.file_slots.new(pass_name)
                file_output.file_slots[i].path = f"{resolved_filename}_"
            
            # Add pass to stored passes
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = core_pass.name
        
        # Set file format using override logic (respects UI setting for core passes)
        core_format = get_file_format_for_pass_type("core", shotput_props.output_format)
        file_output.format.file_format = core_format
        
        # Set the base path using the root folder token
        root_folder_token = node_props.root_folder_token
        resolved_base_path = token_parser.parse_token(root_folder_token, passname=shotput_props.core_override)
        file_output.base_path = resolved_base_path
        
        print(f"Shotput: Created core passes node with {len(shotput_props.core_passes)} passes")
        print(f"Shotput: Using format: {core_format} (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {resolved_base_path}")
        logger.info(f"Created core passes file output node with {len(shotput_props.core_passes)} passes at {resolved_base_path}")
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created core passes node with {len(shotput_props.core_passes)} passes")
        
        return {'FINISHED'}
