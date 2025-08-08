import bpy

from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, apply_data_format_settings, get_sequence_padding
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
        
        # Collect enabled data passes with proper channel names
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
        enabled_channel_names = []
        
        for prop_name, display_name in data_pass_properties:
            if hasattr(shotput_props, prop_name) and getattr(shotput_props, prop_name):
                enabled_data_passes.append(display_name)
                
                # Handle cryptomatte special cases - create 3 channels per type
                if prop_name == 'crypto_object':
                    enabled_channel_names.extend(['CryptoObject00', 'CryptoObject01', 'CryptoObject02'])
                elif prop_name == 'crypto_material':
                    enabled_channel_names.extend(['CryptoMaterial00', 'CryptoMaterial01', 'CryptoMaterial02'])
                elif prop_name == 'crypto_asset':
                    enabled_channel_names.extend(['CryptoAsset00', 'CryptoAsset01', 'CryptoAsset02'])
                else:
                    # Use the property name directly (no spaces, explicit names)
                    channel_name = prop_name  # z, mist, normal, vector, position, occlusion
                    enabled_channel_names.append(channel_name)
        
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
        
        # Data passes always use "data" as area name (no override)
        area_name = "data"
        
        # Create node label: render_layer.area.variant
        node_label = f"{shotput_props.render_layer}.{area_name}.{shotput_props.variant}"
        
        # Create File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.name = "Shotput_Data_Passes"
        file_output.label = node_label
        
        # Set node color - darker red for data passes
        file_output.use_custom_color = True
        file_output.color = (0.6, 0.25, 0.25)  # Darker, more muted red
        file_output.width = 500
        
        # Position the node (find a good spot)
        file_output.location = (400, -400)  # Offset below AOV passes
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = area_name  # Use "data" as pass name
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        # Clear existing stored passes and populate with enabled data passes
        node_props.stored_passes.clear()
        
        # Clear existing file slots (except the first one)
        while len(file_output.file_slots) > 1:
            file_output.file_slots.remove(file_output.file_slots[-1])
        
        # Set file format using override logic (ALWAYS EXR multilayer for data passes)
        data_format = get_file_format_for_pass_type("data", shotput_props.output_format)
        file_output.format.file_format = data_format
        
        # Apply data-specific format settings (full float precision)
        apply_data_format_settings(file_output)
        
        # Data passes ALWAYS use multichannel EXR format
        sequence_padding = get_sequence_padding()  # Get from preferences
        
        # Multi channel EXR: base_path = rootpath + filename_token + .####, file_slots = channel names only
        resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=area_name)
        resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
        full_base_path = f"{resolved_base_path}/{resolved_filename}.{sequence_padding}"
        file_output.base_path = full_base_path
        
        # Configure file slots for each enabled channel (including cryptomatte expansions)
        for i, channel_name in enumerate(enabled_channel_names):
            if i == 0:
                # Use the default slot for the first channel
                file_output.file_slots[0].path = channel_name
            else:
                # Add new slots for additional channels
                file_output.file_slots.new(channel_name)
                file_output.file_slots[i].path = channel_name
        
        # Store the original data pass names (for UI display)
        for data_pass_name in enabled_data_passes:
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = data_pass_name
        
        print(f"Shotput: Created data passes node '{node_label}' with {len(enabled_data_passes)} passes ({len(enabled_channel_names)} channels)")
        print(f"Shotput: Forced format: {data_format} for full float precision (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {file_output.base_path}")
        print(f"Shotput: Channels: {', '.join(enabled_channel_names)}")
        logger.info(f"Created data passes file output node '{node_label}' with {len(enabled_data_passes)} passes using {data_format}")
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created data passes node '{node_label}' with {len(enabled_data_passes)} passes ({len(enabled_channel_names)} channels)")
        
        return {'FINISHED'}
