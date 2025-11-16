import bpy

from .. import __package_name__
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, apply_data_format_settings, get_sequence_padding
from ..utils.lazy_hookup import auto_connect_node
from ..utils.color_utils import store_original_node_color
from ..utils.pass_mapping import pass_mapping
logger = LoggerFactory.logger_obj()

class OT_Create_Data_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_data_passes"
    bl_label = "Create Data Passes"
    bl_description = "Create file output nodes for data passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if required fields are filled and we have data passes"""
        if not (context.space_data and 
                context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'CompositorNodeTree'):
            return False
        
        shotput = context.scene.shotput
        
        # Check required fields
        required_fields = [
            shotput.output_layer.strip(),
            shotput.variant.strip(),
            shotput.root_folder_token.strip(),
            shotput.file_name_token.strip()
        ]
        
        if not all(required_fields):
            return False
        
        # Check if any data pass is enabled
        # NOTE: Cryptomatte order matches Blender's render layer output order: object, asset, material
        data_pass_properties = [
            'z', 'mist', 'normal', 'vector', 'position', 'occlusion', 'volume_direct', 'volume_indirect',
            'crypto_object', 'crypto_asset', 'crypto_material'
        ]
        
        return any(getattr(shotput, prop_name, False) for prop_name in data_pass_properties)
    
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
        # NOTE: Cryptomatte order matches Blender's render layer output order: object, asset, material
        data_pass_properties = [
            ('z', 'Depth'),
            ('mist', 'Mist'),
            ('normal', 'Normal'),
            ('vector', 'Motion Vector'),
            ('position', 'Position'),
            ('occlusion', 'Ambient Occlusion'),
            ('volume_direct', 'Volume Direct'),
            ('volume_indirect', 'Volume Indirect'),
            ('crypto_object', 'Cryptomatte Object'),
            ('crypto_asset', 'Cryptomatte Asset'),
            ('crypto_material', 'Cryptomatte Material')
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
                elif prop_name == 'volume_direct':
                    view_layer.use_pass_volume_direct = True
                elif prop_name == 'volume_indirect':
                    view_layer.use_pass_volume_indirect = True
                elif prop_name == 'crypto_object':
                    view_layer.use_pass_cryptomatte_object = True
                elif prop_name == 'crypto_material':
                    view_layer.use_pass_cryptomatte_material = True
                elif prop_name == 'crypto_asset':
                    view_layer.use_pass_cryptomatte_asset = True
                
                # Handle cryptomatte special cases - create 3 channels per type
                # NOTE: Channel order matches Blender's render layer output order: object, asset, material
                if prop_name == 'crypto_object':
                    enabled_channel_names.extend(['CryptoObject00', 'CryptoObject01', 'CryptoObject02'])
                elif prop_name == 'crypto_asset':
                    enabled_channel_names.extend(['CryptoAsset00', 'CryptoAsset01', 'CryptoAsset02'])
                elif prop_name == 'crypto_material':
                    enabled_channel_names.extend(['CryptoMaterial00', 'CryptoMaterial01', 'CryptoMaterial02'])
                else:
                    # Use pass mapping to get the correct output socket name
                    mapping = pass_mapping.get_data_pass_mapping(prop_name)
                    if mapping:
                        _, output_socket_name = mapping
                        enabled_channel_names.append(output_socket_name)
                    else:
                        # Fallback to property name for unmapped passes
                        enabled_channel_names.append(prop_name)
        
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
        
        # Create node label: output_layer.area.variant
        node_label = f"{shotput_props.output_layer}.{area_name}.{shotput_props.variant}"
        
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
        prefs = context.preferences.addons[__package_name__].preferences
        file_output.color = prefs.data_node_color
        file_output.width = 500
        
        # Store the original color for potential path linking visual feedback
        store_original_node_color(file_output)
        
        # Position the node - check for existing nodes to position relative to them
        existing_node = None
        
        # First priority: Look for any selected node
        print("Shotput: Looking for selected nodes...")
        for node in tree.nodes:
            print(f"Shotput: Node '{node.name}' (type: {node.type}) - selected: {node.select}, location: {node.location}")
            if node.select:
                existing_node = node
                print(f"Shotput: Found selected node: {node.name} at {node.location}")
                break
        
        # Second priority: If no selected nodes found, look for existing Shotput nodes
        if not existing_node:
            print("Shotput: No selected nodes found, looking for existing Shotput nodes...")
            for node in tree.nodes:
                if (node.type == 'OUTPUT_FILE' and 
                    hasattr(node, 'shotput_data') and 
                    node.name.startswith('Shotput_')):
                    existing_node = node
                    print(f"Shotput: Found existing Shotput node: {node.name} at {node.location}")
                    break
        else:
            print(f"Shotput: Using selected node: {existing_node.name}")
        
        if existing_node:
            # Get actual node height for better spacing
            node_height = existing_node.height if hasattr(existing_node, 'height') else 100
            
            # Position based on selected node type and target node type
            if existing_node.type == 'R_LAYERS':
                # Position to the right of render layer nodes (file outputs go to the right)
                x_offset = existing_node.width + 200  # To the right with spacing
                y_offset = 0  # Same Y level initially
                new_location = (existing_node.location[0] + x_offset, existing_node.location[1] + y_offset)
                print(f"Shotput: Positioned data node to the RIGHT of render layer at {new_location}")
            else:
                # Position below other nodes (file outputs stack vertically)
                spacing = max(400, node_height + 50)  # At least 400px or node height + 50px spacing (more for data)
                new_location = (existing_node.location[0], existing_node.location[1] - spacing)
                print(f"Shotput: Positioned data node BELOW {existing_node.name} at {new_location} (spacing: {spacing})")
            
            file_output.location = new_location
        else:
            # Default position when no existing nodes found
            file_output.location = (400, -400)
            print("Shotput: No existing nodes found, using default position (400, -400)")
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        node_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy scene properties to node
        node_props.output_layer = shotput_props.output_layer
        node_props.variant = shotput_props.variant
        node_props.pass_name = area_name  # Use "data" as pass name
        
        # Store UI tokens as normal mode backups BEFORE applying AYON tokens
        node_props.normal_root_folder_token = shotput_props.root_folder_token
        node_props.normal_file_name_token = shotput_props.file_name_token
        
        # Apply AYON tokens if AYON is detected (will override root_folder_token and file_name_token)
        from ..utils.ayon_utils import apply_ayon_tokens_to_node
        if apply_ayon_tokens_to_node(file_output, node_props, is_composite=False):
            print("Shotput: Applied AYON-specific output tokens to data node")
        else:
            # No AYON detected, use normal tokens from UI
            node_props.root_folder_token = shotput_props.root_folder_token
            node_props.file_name_token = shotput_props.file_name_token
        
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

        # Store the original data pass names (for UI display)
        for data_pass_name in enabled_data_passes:
            stored_pass = node_props.stored_passes.add()
            stored_pass.name = data_pass_name

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
            display_name = "depth" if channel_name == "z" else channel_name
            
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
        display_channel_names = ["depth" if name == "z" else name for name in enabled_channel_names]

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