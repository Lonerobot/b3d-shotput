import bpy

from ..utils.log import LoggerFactory
from ..utils.defaults import get_file_format_for_pass_type, apply_data_format_settings
logger = LoggerFactory.logger_obj()

class OT_Create_Data_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_data_passes"
    bl_label = "Create Data Passes"
    bl_description = "Create file output nodes for data passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        logger.info("Create Data Passes operator clicked")
        print("Shotput: Create Data Passes operator executed")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Collect enabled data passes
        data_pass_properties = [
            ('z', 'Depth'),
            ('mist', 'Mist'),
            ('normal', 'Normal'),
            ('vector', 'Motion Vector'),
            ('position', 'Position'),
            ('occlusion', 'Ambient Occlusion'),
            ('crypto_object', 'Cryptomatte Object'),
            ('crypto_material', 'Cryptomatte Material'),
            ('crypto_asset', 'Cryptomatte Asset')
        ]
        
        enabled_data_passes = []
        for prop_name, display_name in data_pass_properties:
            if hasattr(shotput_props, prop_name) and getattr(shotput_props, prop_name):
                enabled_data_passes.append(display_name)
        
        # Check if we have data passes to create
        if len(enabled_data_passes) == 0:
            self.report({'WARNING'}, "No data passes enabled")
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
        file_output.name = "Shotput_Data_Passes"
        file_output.label = "Data: Passes"
        
        # Set node color - darker red for data passes
        file_output.use_custom_color = True
        file_output.color = (0.6, 0.25, 0.25)  # Darker, more muted red
        
        # Position the node (find a good spot)
        file_output.location = (400, -400)  # Offset below AOV passes
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = "Data"  # Use "Data" as pass name
        
        # Clear existing stored passes and populate with enabled data passes
        node_props.stored_passes.clear()
        
        # Clear existing file slots (except the first one)
        while len(file_output.file_slots) > 1:
            file_output.file_slots.remove(file_output.file_slots[-1])
        
        # Configure file slots for each enabled data pass
        for i, data_pass_name in enumerate(enabled_data_passes):
            if i == 0:
                # Use the default slot for the first pass
                file_output.file_slots[0].path = f"Data_{data_pass_name}_"
            else:
                # Add new slots for additional passes
                file_output.file_slots.new(data_pass_name)
                file_output.file_slots[i].path = f"Data_{data_pass_name}_"
            
            # Add pass to stored passes
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = data_pass_name
        
        # Set file format using override logic (ALWAYS EXR multilayer for data passes)
        data_format = get_file_format_for_pass_type("data", shotput_props.output_format)
        file_output.format.file_format = data_format
        
        # Apply data-specific format settings (full float precision)
        apply_data_format_settings(file_output)
        
        print(f"Shotput: Created data passes node with {len(enabled_data_passes)} passes")
        print(f"Shotput: Forced format: {data_format} for full float precision (UI setting: {shotput_props.output_format})")
        logger.info(f"Created data passes file output node with {len(enabled_data_passes)} passes using {data_format}")
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created data passes node with {len(enabled_data_passes)} passes")
        
        return {'FINISHED'}
