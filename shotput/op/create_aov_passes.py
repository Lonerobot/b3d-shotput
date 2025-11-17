import bpy

from .. import __package_name__
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, get_sequence_padding
from ..utils.lazy_hookup import auto_connect_node
from ..utils.color_utils import store_original_node_color
from ..utils.format_validator import validate_png_alpha_channel, apply_png_alpha_channel_fix
logger = LoggerFactory.logger_obj()

class OT_Create_AOV_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_aov_passes"
    bl_label = "Create AOV Passes"
    bl_description = "Create file output nodes for AOV passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if required fields are filled and we have AOV passes"""
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
        
        # Check we have AOV passes to create
        return len(shotput.aov_passes) > 0
    
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
        
        # Determine area name - use aov_override if present, otherwise default to "aov"
        area_name = shotput_props.aov_override.strip() if shotput_props.aov_override.strip() else "aov"
        
        # Create node label: output_layer.area.variant
        node_label = f"{shotput_props.output_layer}.{area_name}.{shotput_props.variant}"
        
        # Create File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.name = f"Shotput_AOV_{area_name}"
        file_output.label = node_label
        
        # Set file format IMMEDIATELY after node creation
        # This must be done before ANY slot operations to prevent format from overriding slot names
        aov_format = get_file_format_for_pass_type("aov", shotput_props.output_format)
        file_output.format.file_format = aov_format
        
        # Validate PNG alpha channel configuration and warn user if needed
        is_valid, warning_msg = validate_png_alpha_channel(context, aov_format)
        if not is_valid:
            # Show warning to user
            self.report({'WARNING'}, warning_msg)
            print(f"Shotput: {warning_msg}")
            
            # Automatically fix the issue by setting RGBA mode
            if apply_png_alpha_channel_fix(file_output, context):
                fix_msg = "Automatically set PNG to RGBA mode to preserve alpha channel"
                self.report({'INFO'}, fix_msg)
                print(f"Shotput: {fix_msg}")
        
        # Set node color - darker orange for AOV passes
        file_output.use_custom_color = True
        prefs = context.preferences.addons[__package_name__].preferences
        file_output.color = prefs.aov_node_color
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
            print(f"Shotput: Using existing Shotput node: {existing_node.name}")
        
        if existing_node:
            # Get actual node height for better spacing
            node_height = existing_node.height if hasattr(existing_node, 'height') else 100
            
            # Position based on selected node type and target node type
            if existing_node.type == 'R_LAYERS':
                # Position to the right of render layer nodes (file outputs go to the right)
                x_offset = existing_node.width + 200  # To the right with spacing
                y_offset = 0  # Same Y level initially
                new_location = (existing_node.location[0] + x_offset, existing_node.location[1] + y_offset)
                print(f"Shotput: Positioned AOV node to the RIGHT of render layer at {new_location}")
            else:
                # Position below other nodes (file outputs stack vertically)
                spacing = max(200, node_height + 50)  # At least 200px or node height + 50px spacing
                new_location = (existing_node.location[0], existing_node.location[1] - spacing)
                print(f"Shotput: Positioned AOV node BELOW {existing_node.name} at {new_location} (spacing: {spacing})")
            
            file_output.location = new_location
        else:
            # Default position when no existing nodes found
            file_output.location = (400, -200)
            print("Shotput: No existing nodes found, using default position (400, -200)")
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        node_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy scene properties to node
        node_props.output_layer = shotput_props.output_layer
        node_props.variant = shotput_props.variant
        node_props.pass_name = area_name  # Use area name as pass name
        
        # Store UI tokens as normal mode backups BEFORE applying AYON tokens
        node_props.normal_root_folder_token = shotput_props.root_folder_token
        node_props.normal_file_name_token = shotput_props.file_name_token
        
        # Apply AYON tokens if AYON is detected (will override root_folder_token and file_name_token)
        from ..utils.ayon_utils import apply_ayon_tokens_to_node
        if apply_ayon_tokens_to_node(file_output, node_props, is_composite=False):
            print("Shotput: Applied AYON-specific output tokens to AOV node")
        else:
            # No AYON detected, use normal tokens from UI
            node_props.root_folder_token = shotput_props.root_folder_token
            node_props.file_name_token = shotput_props.file_name_token
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        # Clear existing stored passes and populate with AOV passes
        node_props.stored_passes.clear()
        
        # Clear existing file slots (except the first one) - use correct Blender API
        while len(file_output.file_slots) > 1:
            try:
                # Remove via the input socket, not the file slot directly
                file_output.inputs.remove(file_output.inputs[-1])
            except (RuntimeError, IndexError, ValueError):
                # If removal fails, break and work with what we have
                break
        
        # Format-specific pathing logic
        sequence_padding = get_sequence_padding()  # Get from preferences
        
        if aov_format in ['PNG', 'JPEG']:
            # PNG/JPEG: base_path = rootpath, file_slots = filename_token + .#### + extension
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Map format to file extension
            format_extensions = {
                'PNG': 'png',
                'JPEG': 'jpg'
            }
            file_extension = format_extensions.get(aov_format, 'png')
            
            # Configure file slots for each AOV pass
            for i, aov_pass in enumerate(shotput_props.aov_passes):
                pass_name = aov_pass.name
                
                # Parse the file name token with specific pass name
                resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=pass_name)
                file_slot_path = f"{resolved_filename}.{sequence_padding}.{file_extension}"
                
                if i == 0:
                    # Use the default slot for the first pass
                    file_output.file_slots[0].path = file_slot_path
                else:
                    # Add new slots for additional passes
                    file_output.file_slots.new(pass_name)
                    file_output.file_slots[i].path = file_slot_path
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = aov_pass.name
                
        elif aov_format == 'OPEN_EXR':
            # Single channel EXR: base_path = rootpath, file_slots = filename_token + .#### + extension
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each AOV pass
            for i, aov_pass in enumerate(shotput_props.aov_passes):
                pass_name = aov_pass.name
                
                # Parse the file name token with specific pass name
                resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=pass_name)
                file_slot_path = f"{resolved_filename}.{sequence_padding}.exr"
                
                if i == 0:
                    # Use the default slot for the first pass
                    file_output.file_slots[0].path = file_slot_path
                else:
                    # Add new slots for additional passes
                    file_output.file_slots.new(pass_name)
                    file_output.file_slots[i].path = file_slot_path
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = aov_pass.name
                
        elif aov_format == 'OPEN_EXR_MULTILAYER':
            # Multi channel EXR: base_path = rootpath + filename_token + .####, file_slots = channel names only
            resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=area_name)
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            full_base_path = f"{resolved_base_path}/{resolved_filename}.{sequence_padding}"
            file_output.base_path = full_base_path

            # EXR MULTILAYER FIRST SLOT FIX: Remove the default first slot entirely
            # The default first slot has a bug where input name and slot path don't sync
            # By removing and recreating it, the new slot behaves properly (like a "second" slot)
            if len(file_output.file_slots) > 0:
                print("Shotput: Removing problematic default first slot for EXR multilayer (AOV passes)")
                file_output.inputs.remove(file_output.inputs[0])
                print(f"Shotput: After removal: {len(file_output.file_slots)} slots remaining")

            # Configure file slots for each AOV pass using the working slot recreation approach
            for i, aov_pass in enumerate(shotput_props.aov_passes):
                pass_name = aov_pass.name
                
                # Convert "Beauty" to "rgba" for Nuke compatibility (though unlikely in AOV)
                channel_name = "rgba" if pass_name.lower() == "beauty" else pass_name.lower()
                
                # Add new slot with desired name (all slots now work properly)
                file_output.file_slots.new(channel_name)
                print(f"Shotput: Added AOV slot {i}: input='{file_output.inputs[i].name}', slot='{file_output.file_slots[i].path}', expected='{channel_name}'")
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = aov_pass.name
        
        else:
            # Fallback for other formats - use the old behavior
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each AOV pass
            for i, aov_pass in enumerate(shotput_props.aov_passes):
                pass_name = aov_pass.name
                
                # Parse the file name token with specific pass name
                resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=pass_name)
                
                if i == 0:
                    # Use the default slot for the first pass
                    file_output.file_slots[0].path = f"{resolved_filename}_"
                else:
                    # Add new slots for additional passes
                    file_output.file_slots.new(pass_name)
                    file_output.file_slots[i].path = f"{resolved_filename}_"
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = aov_pass.name
        
        print(f"Shotput: Created AOV passes node '{node_label}' with {len(shotput_props.aov_passes)} passes")
        print(f"Shotput: Using format: {aov_format} (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {file_output.base_path}")
        logger.info(f"Created AOV passes file output node '{node_label}' with {len(shotput_props.aov_passes)} passes")
        
        # Auto-connect node if lazy hook-up is enabled
        aov_pass_names = [aov_pass.name for aov_pass in shotput_props.aov_passes]
        auto_connect_node(context, file_output, aov_pass_names)
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created AOV passes node '{node_label}' with {len(shotput_props.aov_passes)} passes")
        
        return {'FINISHED'}
