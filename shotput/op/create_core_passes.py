import bpy
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, get_sequence_padding

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
        
        # Determine area name - use core_override if present, otherwise default to "core"
        area_name = shotput_props.core_override.strip() if shotput_props.core_override.strip() else "core"
        
        # Create node label: render_layer.area.variant
        node_label = f"{shotput_props.render_layer}.{area_name}.{shotput_props.variant}"
        
        # Create File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.name = f"Shotput_Core_{area_name}"
        file_output.label = node_label
        
        # Set file format IMMEDIATELY after node creation
        # This must be done before ANY slot operations to prevent format from overriding slot names
        core_format = get_file_format_for_pass_type("core", shotput_props.output_format)
        file_output.format.file_format = core_format
        
        # Set node color - darker blue for core passes
        file_output.use_custom_color = True
        file_output.color = (0.25, 0.45, 0.7)  # Darker, more muted blue
        file_output.width = 500  # Set a reasonable width for visibility
        
        # Position the node (find a good spot)
        file_output.location = (400, 0)
        
        # Set up Shotput properties on the node
        node_props = file_output.shotput_data
        
        # Copy scene properties to node
        node_props.render_layer = shotput_props.render_layer
        node_props.variant = shotput_props.variant
        node_props.root_folder_token = shotput_props.root_folder_token
        node_props.file_name_token = shotput_props.file_name_token
        node_props.pass_name = area_name  # Use area name as pass name
        
        # Initialize token parser with node properties
        token_parser = TokenParser(node_props)
        
        # Clear existing stored passes and populate with core passes
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
        
        if core_format in ['PNG', 'JPEG']:
            # PNG/JPEG: base_path = rootpath, file_slots = filename_token + channel + .####
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
                # Convert "Beauty" to "rgba" for Nuke compatibility
                channel_name = "rgba" if pass_name.lower() == "beauty" else pass_name.lower()
                
                # Parse the file name token with specific pass name
                resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=pass_name)
                file_slot_path = f"{resolved_filename}_{channel_name}.{sequence_padding}"
                
                if i == 0:
                    # Use the default slot for the first pass
                    file_output.file_slots[0].path = file_slot_path
                else:
                    # Add new slots for additional passes
                    file_output.file_slots.new(pass_name)
                    file_output.file_slots[i].path = file_slot_path
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = core_pass.name
                
        elif core_format == 'OPEN_EXR':
            # Single channel EXR: base_path = rootpath, file_slots = filename_token + channel + .####
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
                # Convert "Beauty" to "rgba" for Nuke compatibility
                channel_name = "rgba" if pass_name.lower() == "beauty" else pass_name.lower()
                
                # Parse the file name token with specific pass name
                resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=pass_name)
                file_slot_path = f"{resolved_filename}_{channel_name}.{sequence_padding}"
                
                if i == 0:
                    # Use the default slot for the first pass
                    file_output.file_slots[0].path = file_slot_path
                else:
                    # Add new slots for additional passes
                    file_output.file_slots.new(pass_name)
                    file_output.file_slots[i].path = file_slot_path
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = core_pass.name
                
        elif core_format == 'OPEN_EXR_MULTILAYER':
            # Multi channel EXR: base_path = rootpath + filename_token + .####, file_slots = channel names only
            resolved_filename = token_parser.parse_token(node_props.file_name_token, passname=area_name)
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            full_base_path = f"{resolved_base_path}/{resolved_filename}.{sequence_padding}"
            file_output.base_path = full_base_path

            # EXR MULTILAYER FIRST SLOT FIX: Remove the default first slot entirely
            # The default first slot has a bug where input name and slot path don't sync
            # By removing and recreating it, the new slot behaves properly (like a "second" slot)
            if len(file_output.file_slots) > 0:
                print("Shotput: Removing problematic default first slot for EXR multilayer (core passes)")
                file_output.inputs.remove(file_output.inputs[0])
                print(f"Shotput: After removal: {len(file_output.file_slots)} slots remaining")

            # Configure file slots for each core pass using the working slot recreation approach
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
                # Convert "Beauty" to "rgba" for Nuke compatibility
                channel_name = "rgba" if pass_name.lower() == "beauty" else pass_name.lower()
                
                # Add new slot with desired name (all slots now work properly)
                file_output.file_slots.new(channel_name)
                print(f"Shotput: Added core slot {i}: input='{file_output.inputs[i].name}', slot='{file_output.file_slots[i].path}', expected='{channel_name}'")
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = core_pass.name
        
        else:
            # Fallback for other formats - use the old behavior
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
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
                stored_pass.name = core_pass.name
        
        print(f"Shotput: Created core passes node '{node_label}' with {len(shotput_props.core_passes)} passes")
        print(f"Shotput: Using format: {core_format} (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {file_output.base_path}")
        logger.info(f"Created core passes file output node '{node_label}' with {len(shotput_props.core_passes)} passes")
        
        # Select the new node
        file_output.select = True
        tree.nodes.active = file_output
        
        self.report({'INFO'}, f"Created core passes node '{node_label}' with {len(shotput_props.core_passes)} passes")
        
        return {'FINISHED'}
