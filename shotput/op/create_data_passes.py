import bpy

from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, apply_data_format_settings, get_sequence_padding
from ..utils.lazy_hookup import auto_connect_node
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
            ('occlusion', 'Occlusion'),
            ('crypto_object', 'Cryptomatte Object'),
            ('crypto_material', 'Cryptomatte Material'),
            ('crypto_asset', 'Cryptomatte Asset')
        ]
        
        enabled_data_passes = []
        enabled_channel_names = []
        
        for prop_name, display_name in data_pass_properties:
            if hasattr(shotput_props, prop_name) and getattr(shotput_props, prop_name):
                enabled_data_passes.append(display_name)
                
                # Enable the corresponding view layer pass
                view_layer = context.view_layer
                if prop_name == 'z':
                    view_layer.use_pass_z = True
                elif prop_name == 'mist':
                    view_layer.use_pass_mist = True
                elif prop_name == 'normal':
                    view_layer.use_pass_normal = True
                elif prop_name == 'vector':
                    view_layer.use_pass_vector = True
                elif prop_name == 'position':
                    view_layer.use_pass_position = True
                elif prop_name == 'occlusion':
                    view_layer.use_pass_ambient_occlusion = True
                elif prop_name == 'crypto_object':
                    view_layer.use_pass_cryptomatte_object = True
                elif prop_name == 'crypto_material':
                    view_layer.use_pass_cryptomatte_material = True
                elif prop_name == 'crypto_asset':
                    view_layer.use_pass_cryptomatte_asset = True
                
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
        
        # Set file format IMMEDIATELY after node creation (ALWAYS EXR multilayer for data passes)
        # This must be done before ANY slot operations to prevent format from overriding slot names
        data_format = get_file_format_for_pass_type("data", shotput_props.output_format)
        file_output.format.file_format = data_format
        
        # Apply data-specific format settings (full float precision)
        apply_data_format_settings(file_output)
        
        # Set node color - darker red for data passes
        file_output.use_custom_color = True
        file_output.color = (0.6, 0.25, 0.25)  # Darker, more muted red
        file_output.width = 500
        
        # Position the node (find a good spot)
        file_output.location = (400, -400)  # Offset below AOV passes
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        node_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = area_name  # Use "data" as pass name
        node_props.pass_type = "DATA"  # Set the pass type
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        # Clear existing stored passes and populate with enabled data passes
        node_props.stored_passes.clear()
          # Data passes ALWAYS use multichannel EXR format
        sequence_padding = get_sequence_padding()  # Get from preferences

        # Multi channel EXR: base_path = rootpath + filename_token + .####, file_slots = channel names only
        resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=area_name)
        resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
        full_base_path = f"{resolved_base_path}/{resolved_filename}.{sequence_padding}"
        file_output.base_path = full_base_path

        # Store the channel names that will actually be used in file slots (for manual hook-up)
        for channel_name in enabled_channel_names:
            # Map certain channels to better names for compositing (same logic as file slots)
            if channel_name == "z":
                display_name = "depth"
            elif channel_name == "occlusion":
                display_name = "ao"
            else:
                display_name = channel_name
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = display_name

        # ============================================================================
        # CRITICAL: Do ALL slot operations at the very end, after everything else is set
        # This ensures that no other property changes can interfere with slot naming
        # ============================================================================
        
        print("Shotput: Configuring file slots as final step...")
        
        # Clear existing file slots (except the first one) - use correct Blender API
        # NOTE: file_slots.remove() expects a socket, not a file slot
        # We need to remove via the actual socket inputs
        while len(file_output.file_slots) > 1:
            try:
                # Remove via the socket, not the file slot directly
                file_output.inputs.remove(file_output.inputs[-1])
            except (RuntimeError, IndexError, ValueError):
                # If removal fails, break and work with what we have
                break

        # EXR MULTILAYER FIRST SLOT FIX: Remove the default first slot entirely
        # The default first slot has a bug where input name and slot path don't sync
        # By removing and recreating it, the new slot behaves properly (like a "second" slot)
        if len(file_output.file_slots) > 0:
            print("Shotput: Removing problematic default first slot for EXR multilayer")
            file_output.inputs.remove(file_output.inputs[0])
            print(f"Shotput: After removal: {len(file_output.file_slots)} slots remaining")

        # Configure file slots for each enabled channel using the working slot recreation approach
        for i, channel_name in enumerate(enabled_channel_names):
            # Map certain channels to better names for compositing
            if channel_name == "z":
                display_name = "depth"
            elif channel_name == "occlusion":
                display_name = "ao"
            else:
                display_name = channel_name
            
            # Add new slot with desired name (all slots now work properly)
            new_slot = file_output.file_slots.new(display_name)
            print(f"Shotput: Added slot {i}: input='{file_output.inputs[i].name}', slot='{file_output.file_slots[i].path}', expected='{display_name}'")

        # Force a scene update to ensure slot names persist
        bpy.context.view_layer.update()
        
        # Double-check that the first slot name stuck (and force it again if needed)
        if len(enabled_channel_names) > 0:
            first_display_name = "depth" if enabled_channel_names[0] == "z" else enabled_channel_names[0]
            current_first_input = file_output.inputs[0].name
            current_first_slot = file_output.file_slots[0].path
            
            if current_first_input != first_display_name:
                print(f"Shotput: WARNING - First input reverted to '{current_first_input}', forcing to '{first_display_name}'")
                file_output.inputs[0].name = first_display_name
                print(f"Shotput: First input corrected to: '{file_output.inputs[0].name}'")
            
            # Final verification: both input and slot should match
            final_input = file_output.inputs[0].name
            final_slot = file_output.file_slots[0].path
            print(f"Shotput: Final verification: input='{final_input}', slot='{final_slot}'")
          # Final verification of slot paths
        final_slot_paths = [slot.path for slot in file_output.file_slots]
        final_input_names = [inp.name for inp in file_output.inputs]
        
        # Create display list of actual channel names used in slots
        display_channel_names = []
        for name in enabled_channel_names:
            if name == "z":
                display_channel_names.append("depth")
            elif name == "occlusion":
                display_channel_names.append("ao")
            else:
                display_channel_names.append(name)

        print(f"Shotput: Created data passes node '{node_label}' with {len(enabled_data_passes)} passes ({len(enabled_channel_names)} channels)")
        print(f"Shotput: Forced format: {data_format} for full float precision (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {file_output.base_path}")
        print(f"Shotput: Final slot paths: {final_slot_paths}")
        print(f"Shotput: Final input names: {final_input_names}")
        print(f"Shotput: Expected channels: {display_channel_names}")
        logger.info(f"Created data passes file output node '{node_label}' with {len(enabled_data_passes)} passes using {data_format}")
        
        # Auto-connect node if lazy hook-up is enabled
        # Use the display channel names for data passes
        auto_connect_node(context, file_output, display_channel_names)
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created data passes node '{node_label}' with {len(enabled_data_passes)} passes ({len(enabled_channel_names)} channels)")
        
        return {'FINISHED'}