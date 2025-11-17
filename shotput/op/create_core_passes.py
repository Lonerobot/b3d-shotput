import bpy

from .. import __package_name__
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, get_sequence_padding
from ..utils.lazy_hookup import auto_connect_node
from ..utils.color_utils import store_original_node_color
from ..utils.format_validator import validate_png_alpha_channel, apply_png_alpha_channel_fix

logger = LoggerFactory.logger_obj()

class OT_Create_Core_Passes(bpy.types.Operator):
    bl_idname = "shotput.create_core_passes"
    bl_label = "Create Core Passes"
    bl_description = "Create file output nodes for core passes"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if required fields are filled and we have core passes or render layer channels mode"""
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
        
        # If in "Use Render Layer Channels" mode, always enable (we'll scan render layer)
        if shotput.use_render_layer_channels:
            return True
        
        # Otherwise, check we have core passes to create
        return len(shotput.core_passes) > 0
    
    def execute(self, context):
        logger.info("Create Core Passes operator clicked")
        print("Shotput: Create Core Passes operator executed")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Determine passes to create based on mode
        if shotput_props.use_render_layer_channels:
            # Render Layer Channels mode - scan render layer for available outputs
            render_layer_outputs = self._get_render_layer_outputs(context)
            if not render_layer_outputs:
                self.report({'WARNING'}, "No render layer outputs found. Enable some passes in your view layer.")
                return {'CANCELLED'}
            
            # Create pass names from render layer outputs
            core_pass_names = []
            for output_name in render_layer_outputs:
                # Map 'Image' to 'rgba' as specified in requirements
                if output_name.lower() == 'image':
                    core_pass_names.append('rgba')
                else:
                    # Use Blender's output names directly
                    core_pass_names.append(output_name)
            
            area_name = "all_passes"  # Different area name for render layer mode
            print(f"Shotput: Render layer mode - found {len(render_layer_outputs)} outputs: {render_layer_outputs}")
            
        else:
            # Manual mode - use defined core passes
            if len(shotput_props.core_passes) == 0:
                self.report({'WARNING'}, "No core passes defined")
                return {'CANCELLED'}
            
            core_pass_names = [core_pass.name for core_pass in shotput_props.core_passes]
            # Determine area name - use core_override if present, otherwise default to "core"
            area_name = shotput_props.core_override.strip() if shotput_props.core_override.strip() else "core"
        
        # Check if we're in Compositor workspace
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
            print("Shotput: Enabled compositor nodes")
        
        # Get compositor node tree
        tree = context.scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Create node label: output_layer.area.variant (area_name set above based on mode)
        node_label = f"{shotput_props.output_layer}.{area_name}.{shotput_props.variant}"
        
        # Create File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.name = f"Shotput_Core_{area_name}"
        file_output.label = node_label
        
        # Set file format IMMEDIATELY after node creation
        # This must be done before ANY slot operations to prevent format from overriding slot names
        core_format = get_file_format_for_pass_type("core", shotput_props.output_format)
        file_output.format.file_format = core_format
        
        # Validate PNG alpha channel configuration and auto-configure based on film transparency
        is_valid, info_msg = validate_png_alpha_channel(context, core_format)
        if not is_valid:
            # Show info to user about auto-configuration
            self.report({'INFO'}, info_msg)
            print(f"Shotput: {info_msg}")
            
            # Automatically configure color mode to match film transparency setting
            apply_png_alpha_channel_fix(file_output, context)
        
        # Set node color - different colors for different modes
        file_output.use_custom_color = True
        prefs = context.preferences.addons[__package_name__].preferences
        if shotput_props.use_render_layer_channels:
            # Purple color matching render layer node for "Use Render Layer Channels" mode
            file_output.color = prefs.core_render_layer_node_color
        else:
            # Blue color for manual core passes mode
            file_output.color = prefs.core_node_color
        file_output.width = 500  # Set a reasonable width for visibility
        
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
                print(f"Shotput: Positioned core node to the RIGHT of render layer at {new_location}")
            else:
                # Position below other nodes (file outputs stack vertically)
                spacing = max(200, node_height + 50)  # At least 200px or node height + 50px spacing
                new_location = (existing_node.location[0], existing_node.location[1] - spacing)
                print(f"Shotput: Positioned core node BELOW {existing_node.name} at {new_location} (spacing: {spacing})")
            
            file_output.location = new_location
        else:
            # Default position when no existing nodes found
            file_output.location = (400, 0)
            print("Shotput: No existing nodes found, using default position (400, 0)")
        
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
            print("Shotput: Applied AYON-specific output tokens to core node")
        else:
            # No AYON detected, use normal tokens from UI
            node_props.root_folder_token = shotput_props.root_folder_token
            node_props.file_name_token = shotput_props.file_name_token
        
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
            # PNG/JPEG: base_path = rootpath, file_slots = filename_token + .#### + extension
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Map format to file extension
            format_extensions = {
                'PNG': 'png',
                'JPEG': 'jpg'
            }
            file_extension = format_extensions.get(core_format, 'png')
            
            # Configure file slots for each core pass
            for i, pass_name in enumerate(core_pass_names):
                
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
                stored_pass.name = pass_name
                
        elif core_format == 'OPEN_EXR':
            # Single channel EXR: base_path = rootpath, file_slots = filename_token + .#### + extension
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, pass_name in enumerate(core_pass_names):
                
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
                stored_pass.name = pass_name
                
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
            for i, pass_name in enumerate(core_pass_names):
                
                # In render layer mode, pass_name might already be 'rgba' from Image mapping
                # Otherwise convert "Beauty" to "rgba" for Nuke compatibility
                if pass_name.lower() == "beauty":
                    channel_name = "rgba"
                else:
                    channel_name = pass_name.lower()
                
                # Add new slot with desired name (all slots now work properly)
                file_output.file_slots.new(channel_name)
                print(f"Shotput: Added core slot {i}: input='{file_output.inputs[i].name}', slot='{file_output.file_slots[i].path}', expected='{channel_name}'")
                
                # Add pass to stored passes
                stored_pass = node_props.stored_passes.add()
                stored_pass.name = pass_name
        
        else:
            # Fallback for other formats - use the old behavior
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, pass_name in enumerate(core_pass_names):
                
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
                stored_pass.name = pass_name
        
        pass_count = len(core_pass_names)
        mode_desc = "from render layer" if shotput_props.use_render_layer_channels else "manual"
        print(f"Shotput: Created {mode_desc} core passes node '{node_label}' with {pass_count} passes")
        print(f"Shotput: Using format: {core_format} (UI setting: {shotput_props.output_format})")
        print(f"Shotput: Base path set to: {file_output.base_path}")
        logger.info(f"Created {mode_desc} core passes file output node '{node_label}' with {pass_count} passes")
        
        # Create composite node if requested (but not in AYON mode - linking not compatible)
        composite_node = None
        if shotput_props.create_composite_from_core and not node_props.use_ayon_output_style:
            composite_node = self._create_composite_node(context, tree, shotput_props, token_parser, file_output)
        
        # Auto-connect nodes if lazy hook-up is enabled
        auto_connect_node(context, file_output, core_pass_names)
        
        if composite_node:
            auto_connect_node(context, composite_node)
        
        # Select the new core node
        file_output.select = True
        tree.nodes.active = file_output
        
        pass_count = len(core_pass_names)
        mode_desc = "from render layer" if shotput_props.use_render_layer_channels else "manual"
        composite_msg = " and composite node" if composite_node else ""
        self.report({'INFO'}, f"Created {mode_desc} passes node '{node_label}' with {pass_count} passes{composite_msg}")
        
        return {'FINISHED'}
    
    def _get_render_layer_outputs(self, context):
        """
        Scan the active render layer for available outputs.
        Returns a list of output socket names that are available and actually functional.
        Filters out deprecated passes that have no real connection.
        """
        # Try to find a Render Layers node in the compositor
        tree = context.scene.node_tree
        if not tree:
            return []
        
        render_layer_node = None
        created_temporary_node = False
        
        # Look for existing render layer node
        for node in tree.nodes:
            if node.type == 'R_LAYERS':
                render_layer_node = node
                break
        
        if not render_layer_node:
            # No render layer node found, create one temporarily to get outputs
            render_layer_node = tree.nodes.new(type='CompositorNodeRLayers')
            created_temporary_node = True
        
        # Get all output socket names that are actually functional
        available_outputs = []
        view_layer = context.view_layer
        
        for output in render_layer_node.outputs:
            output_name = output.name
            
            # Skip alpha socket (we don't typically need separate alpha)
            if output_name.lower() == 'alpha':
                continue
            
            # Skip deprecated passes - check for "Deprecated" in socket name
            if 'deprecated' in output_name.lower():
                print(f"Shotput: Skipping deprecated pass: {output_name}")
                continue
            
            # Check if the output socket is actually enabled/functional
            # Some passes exist as sockets but aren't available in certain engines
            is_functional = self._is_output_socket_functional(output, render_layer_node, view_layer, context.scene)
            
            if is_functional:
                available_outputs.append(output_name)
            else:
                print(f"Shotput: Skipping non-functional pass: {output_name}")
        
        # ONLY clean up if we explicitly created a temporary node AND it's not connected
        if created_temporary_node and not any(output.is_linked for output in render_layer_node.outputs):
            tree.nodes.remove(render_layer_node)
            print("Shotput: Removed temporary render layer node after scanning")
        
        print(f"Shotput: Found {len(available_outputs)} functional render layer outputs: {available_outputs}")
        return available_outputs
    
    def _is_output_socket_functional(self, output_socket, render_layer_node, view_layer, scene):
        """
        Check if a render layer output socket is actually functional by testing if it's enabled
        and available in the current render engine. This helps filter out passes that exist
        in the socket list but aren't actually supported by the current engine/settings.
        """
        output_name = output_socket.name
        output_lower = output_name.lower()
        render_engine = scene.render.engine
        
        # Always include basic image output
        if output_lower in ['image', 'combined', 'beauty']:
            return True
        
        # Engine-specific filtering for known problematic passes
        if render_engine in ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT']:
            # EEVEE doesn't support these passes even though they might appear as sockets
            if output_lower in ['uv', 'indexob', 'indexma']:
                return False
            
            # EEVEE doesn't support indirect lighting passes
            if 'ind' in output_lower and ('diff' in output_lower or 'gloss' in output_lower or 
                                        'trans' in output_lower or 'subsurface' in output_lower):
                return False
            
            # EEVEE doesn't support volume indirect
            if output_lower == 'volumeind':
                return False
        
        # Check if the pass is actually enabled in view layer settings
        # This ensures we only create outputs for passes the user has explicitly enabled
        return self._is_pass_enabled_in_view_layer(output_name, view_layer, scene)
    
    def _is_pass_enabled_in_view_layer(self, output_name, view_layer, scene):
        """
        Check if a pass is enabled in the view layer settings.
        This is a more targeted check than the previous _is_pass_functional method.
        """
        output_lower = output_name.lower()
        
        # Always include basic outputs
        if output_lower in ['image', 'combined', 'beauty']:
            return True
        
        # Check view layer pass settings - with engine-specific handling
        pass_checks = {
            'depth': 'use_pass_z',
            'z': 'use_pass_z',
            'normal': 'use_pass_normal',
            'vector': 'use_pass_vector',
            'position': 'use_pass_position',
            'mist': 'use_pass_mist',
            'ao': 'use_pass_ambient_occlusion',
            'shadow': 'use_pass_shadow',
            'emit': 'use_pass_emit',
            'env': 'use_pass_environment',
            'diffdir': 'use_pass_diffuse_direct',
            'diffind': 'use_pass_diffuse_indirect',
            'diffcol': 'use_pass_diffuse_color',
            'glossdir': 'use_pass_glossy_direct',
            'glossind': 'use_pass_glossy_indirect',
            'glosscol': 'use_pass_glossy_color',
            'transdir': 'use_pass_transmission_direct',
            'transind': 'use_pass_transmission_indirect',
            'transcol': 'use_pass_transmission_color',
            'subsurfacedir': 'use_pass_subsurface_direct',
            'subsurfaceind': 'use_pass_subsurface_indirect',
            'subsurfacecol': 'use_pass_subsurface_color',
            'indexob': 'use_pass_object_index',
            'indexma': 'use_pass_material_index',
            'uv': 'use_pass_uv',
            'greasepencil': 'use_pass_grease_pencil',
        }
        
        # Engine-specific properties
        cycles_specific = {
            'shadowcatcher': 'use_pass_shadow_catcher',
            'shadow catcher': 'use_pass_shadow_catcher',
            'volumedir': 'use_pass_volume_direct',
            'volumeind': 'use_pass_volume_indirect',
        }
        
        eevee_specific = {
            'transp': 'use_pass_transparent',
            'bloom': 'use_pass_bloom',
            'shadow': 'use_pass_shadow',
            'volumedir': 'use_pass_volume_direct',  # EEVEE also has volume direct
        }
        
        # Check cryptomatte passes
        if 'cryptomatte' in output_lower:
            if 'object' in output_lower:
                return getattr(view_layer, 'use_pass_cryptomatte_object', False)
            elif 'material' in output_lower:
                return getattr(view_layer, 'use_pass_cryptomatte_material', False)
            elif 'asset' in output_lower:
                return getattr(view_layer, 'use_pass_cryptomatte_asset', False)
        
        # Check standard passes
        view_layer_property = pass_checks.get(output_lower)
        if view_layer_property:
            is_enabled = getattr(view_layer, view_layer_property, False)
            print(f"Shotput: Pass '{output_name}' -> property '{view_layer_property}' = {is_enabled}")
            return is_enabled
        
        # Check engine-specific passes
        render_engine = scene.render.engine
        if render_engine == 'CYCLES' and output_lower in cycles_specific:
            property_name = cycles_specific[output_lower]
            # Cycles properties are nested under view_layer.cycles
            is_enabled = getattr(view_layer.cycles, property_name, False) if hasattr(view_layer, 'cycles') else False
            print(f"Shotput: Cycles pass '{output_name}' -> property 'cycles.{property_name}' = {is_enabled}")
            return is_enabled
        elif render_engine in ['BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'] and output_lower in eevee_specific:
            property_name = eevee_specific[output_lower]
            # EEVEE properties are nested under view_layer.eevee
            is_enabled = getattr(view_layer.eevee, property_name, False) if hasattr(view_layer, 'eevee') else False
            print(f"Shotput: EEVEE pass '{output_name}' -> property 'eevee.{property_name}' = {is_enabled}")
            return is_enabled
        
        # For light group passes and other custom passes, assume they're functional if they exist
        # (these are harder to validate and usually user-created)
        if 'light' in output_lower or any(char.isdigit() for char in output_name):
            print(f"Shotput: Including light/custom pass '{output_name}'")
            return True
        
        # For some special passes that might not have direct view layer properties
        # but are still functional if they appear in render layer outputs
        special_passes = {
            'debug sample count': True,
            'noisy image': True,
            'noisy shadow catcher': True, 
            'denoising normal': True,
            'denoising albedo': True,
            'denoising depth': True,
        }
        
        if output_lower in special_passes:
            print(f"Shotput: Including special pass '{output_name}'")
            return True
        
        # Default to False for unknown passes to be conservative
        print(f"Shotput: Unknown pass '{output_name}' - excluding")
        return False
    
    def _is_pass_functional(self, output_name, view_layer, scene):
        """
        Check if a render layer output pass is actually functional.
        In "Use Render Layer Channels" mode, we're more permissive and trust
        that if the render layer has the output, it's probably valid.
        """
        output_lower = output_name.lower()
        
        # Always include basic image output
        if output_lower in ['image', 'beauty', 'combined']:
            return True
        
        # Engine-specific filtering for known problematic passes
        render_engine = scene.render.engine
        
        # UV pass is not available in EEVEE engines
        if output_lower == 'uv':
            return render_engine == 'CYCLES'
        
        # For most other passes in "Use Render Layer Channels" mode,
        # trust that if the render layer socket exists, it's functional.
        # This is simpler and more reliable than trying to validate
        # against complex view layer settings.
        
        # Only filter out passes that are clearly not functional
        # (like deprecated passes, which are already filtered out above)
        
        return True
    
    def _create_composite_node(self, context, tree, shotput_props, token_parser, core_node):
        """Create a Shotput Composite node (actual Blender Composite node for main output)"""
        
        # Create node label using core node properties: output_layer.composite.variant
        node_label = f"{core_node.shotput_data.output_layer}.composite.{core_node.shotput_data.variant}"
        
        # Create Composite node (not File Output) - this routes to main render output
        composite_node = tree.nodes.new(type='CompositorNodeComposite')
        composite_node.name = "Shotput_Composite"
        composite_node.label = node_label
        
        # Set node color - PINK for composite!
        composite_node.use_custom_color = True
        prefs = context.preferences.addons[__package_name__].preferences
        composite_node.color = prefs.composite_node_color
        composite_node.width = 300  # Smaller since it's just routing
        
        # Store the original color for potential path linking visual feedback
        store_original_node_color(composite_node)
        
        # Position the node above the core passes - check if core node exists, otherwise default
        if core_node:
            # Position above the core node with better positioning logic
            node_height = core_node.height if hasattr(core_node, 'height') else 100
            spacing = max(150, node_height + 50)
            composite_node.location = (core_node.location[0], core_node.location[1] + spacing)
            print(f"Shotput: Positioned composite ABOVE core node at {composite_node.location}")
        else:
            # Check if there's any selected node to position relative to
            selected_node = None
            for node in tree.nodes:
                if node.select:
                    selected_node = node
                    break
            
            if selected_node:
                # Get actual node height for better spacing
                node_height = selected_node.height if hasattr(selected_node, 'height') else 100
                
                if selected_node.type == 'R_LAYERS':
                    # Position composite to the right and above render layer
                    x_offset = selected_node.width + 200  # To the right with spacing
                    y_offset = 150  # Slightly above for visual hierarchy
                    composite_node.location = (selected_node.location[0] + x_offset, selected_node.location[1] + y_offset)
                    print(f"Shotput: Positioned composite to the RIGHT and ABOVE render layer at {composite_node.location}")
                else:
                    # Position above other nodes
                    spacing = max(150, node_height + 50)
                    composite_node.location = (selected_node.location[0], selected_node.location[1] + spacing)
                    print(f"Shotput: Positioned composite ABOVE {selected_node.name} at {composite_node.location}")
            else:
                # Default position when no nodes are available
                composite_node.location = (400, 300)
                print("Shotput: No selected nodes found, using default composite position (400, 300)")
        
        # Set up Shotput properties on the composite node
        comp_props = composite_node.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        comp_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy properties from core node (not scene properties)
        comp_props.output_layer = core_node.shotput_data.output_layer
        comp_props.variant = core_node.shotput_data.variant
        comp_props.pass_name = "composite"  # Set pass name to "composite"
        
        # Store normal mode backups from core node BEFORE applying AYON tokens
        comp_props.normal_root_folder_token = core_node.shotput_data.root_folder_token
        comp_props.normal_file_name_token = core_node.shotput_data.file_name_token
        
        # Check if AYON context is detected and enable AYON mode if so
        from ..utils.ayon_utils import apply_ayon_tokens_to_node, is_ayon_context
        if is_ayon_context():
            # Enable AYON mode before applying tokens so the check passes
            comp_props.use_ayon_output_style = True
            print("Shotput: AYON context detected, enabling AYON mode on composite node")
        
        # Apply AYON tokens if AYON is detected (will override root_folder_token and file_name_token)
        ayon_applied = apply_ayon_tokens_to_node(composite_node, comp_props, is_composite=True)
        if ayon_applied:
            print("Shotput: Applied AYON-specific output tokens to composite node")
        else:
            # No AYON detected, use tokens from core node
            comp_props.root_folder_token = core_node.shotput_data.root_folder_token
            comp_props.file_name_token = core_node.shotput_data.file_name_token
        
        # CRITICAL: Inherit version from core node
        # This ensures composite nodes start with the same version as their parent
        if core_node and hasattr(core_node, 'shotput_data'):
            comp_props.version = getattr(core_node.shotput_data, 'version', 'v001')
            print(f"Shotput: Composite inheriting version '{comp_props.version}' from core node")
        else:
            comp_props.version = getattr(shotput_props, 'version', 'v001')
            print(f"Shotput: Composite inheriting version '{comp_props.version}' from scene props")
        
        # Set up path linking to the core node (but only if AYON is NOT enabled)
        # AYON mode defines full paths via tokens, so path linking is incompatible
        if not ayon_applied:
            # First set the full root folder token as if it were created normally
            comp_props.root_folder_token = shotput_props.root_folder_token
            
            # Then enable path linking, which will trigger the backup system
            comp_props.path_linked = True  # Enable path linking by default
            comp_props.root_folder_token_backup = shotput_props.root_folder_token  # Back up the original
            comp_props.linked_node = core_node.name  # Link to the core node
            comp_props.root_folder_token = "{passname}"  # Use dynamic token that resolves to pass_name
        else:
            # In AYON mode, path linking is not used - AYON tokens define the full path
            comp_props.path_linked = False
            print("Shotput: Path linking disabled for composite node in AYON mode")
        
        # Also store the linked node name as a backup custom property
        composite_node["shotput_linked_node_backup"] = core_node.name
        
        # Add single stored pass for composite (for UI consistency)
        comp_props.stored_passes.clear()
        stored_pass = comp_props.stored_passes.add()
        stored_pass.name = "Composite"
        
        print(f"Shotput: Created composite node '{node_label}' (routes to main render output)")
        print(f"Shotput: Composite node path-linked to '{core_node.name}' with 'composite' subfolder")
        logger.info(f"Created composite node '{node_label}' for main output routing, path-linked to {core_node.name}")
        
        return composite_node


class OT_Create_Linked_Composite(bpy.types.Operator):
    """
    Create Linked Composite Node Operator
    
    Creates a composite node that can be linked to an existing File Output node
    or use global UI settings. The composite node routes to the main render output
    and can automatically inherit path structure from a parent File Output node.
    
    Behavior:
    - If a File Output node is selected: Uses its properties and links to it
    - If no node is selected: Uses global UI settings and finds suitable link target
    - Positions composite node above the linked node for clear hierarchy
    - Automatically sets up path linking with backup/restore system
    """
    bl_idname = "shotput.create_linked_composite"
    bl_label = "Create Linked Composite Node"
    bl_description = "Create a composite node linked to the selected File Output node or using global UI settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if required fields are filled and we're in compositor"""
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
        
        return all(required_fields)
    
    def execute(self, context):
        logger.info("Create Linked Composite operator clicked")
        print("Shotput: Create Linked Composite operator executed")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Check if we're in Compositor workspace
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
            print("Shotput: Enabled compositor nodes")
        
        # Get compositor node tree
        tree = context.scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Determine source for properties (selected File Output node or global UI)
        source_props = None
        linked_node = None
        
        # Check if a File Output node is selected
        if (hasattr(context, 'active_node') and context.active_node and 
            context.active_node.type == 'OUTPUT_FILE' and 
            hasattr(context.active_node, 'shotput_data')):
            
            # Check if the selected node is in AYON mode - if so, don't link
            selected_node = context.active_node
            if selected_node.shotput_data.use_ayon_output_style:
                # AYON mode active - don't link to this node
                source_props = shotput_props
                linked_node = None
                print(f"Shotput: Selected node {selected_node.name} is in AYON mode - creating standalone composite")
            else:
                # Use selected File Output node properties
                linked_node = selected_node
                source_props = linked_node.shotput_data
                print(f"Shotput: Using properties from selected File Output node: {linked_node.name}")
            
        else:
            # Use global UI properties
            source_props = shotput_props
            print("Shotput: Using global UI properties")
            
            # When no File Output is selected, create a normal (non-linked) composite
            # Don't try to find a node to link to - this should be a standalone composite
            linked_node = None
            print("Shotput: Creating standalone composite (no linking)")
        
        # Create the composite node
        composite_node = self._create_standalone_composite_node(context, tree, source_props, linked_node)
        
        if not composite_node:
            self.report({'ERROR'}, "Failed to create composite node")
            return {'CANCELLED'}
        
        # Select the new composite node
        composite_node.select = True
        tree.nodes.active = composite_node
        
        # Auto-connect composite node if lazy hook-up is enabled
        if shotput_props.lazy_hook_up:
            auto_connect_node(context, composite_node)
        
        # Report success
        linked_msg = f" (linked to {linked_node.name})" if linked_node else " (no linked node found)"
        self.report({'INFO'}, f"Created linked composite node{linked_msg}")
        
        return {'FINISHED'}
    
    def _create_standalone_composite_node(self, context, tree, source_props, linked_node=None):
        """Create a Shotput Composite node with properties from source"""
        
        # Get output_layer and variant from source
        output_layer = getattr(source_props, 'output_layer', 'ViewLayer')
        variant = getattr(source_props, 'variant', 'Main')
        
        # Create node label: output_layer.composite.variant
        node_label = f"{output_layer}.composite.{variant}"
        
        # Create Composite node (not File Output) - this routes to main render output
        composite_node = tree.nodes.new(type='CompositorNodeComposite')
        composite_node.name = "Shotput_Composite"
        composite_node.label = node_label
        
        # Set node color - PINK for composite!
        composite_node.use_custom_color = True
        prefs = context.preferences.addons[__package_name__].preferences
        composite_node.color = prefs.composite_node_color
        composite_node.width = 220  # Smaller since it's just routing
        
        # Store original color for visual feedback system
        store_original_node_color(composite_node)
        
        # Position the node - use smart positioning based on node type
        if linked_node:
            # Get actual node height for better spacing
            node_height = linked_node.height if hasattr(linked_node, 'height') else 100
            
            if linked_node.type == 'R_LAYERS':
                # Position composite to the right of render layer nodes
                x_offset = linked_node.width + 200  # To the right with spacing
                y_offset = 150  # Slightly above for visual hierarchy
                composite_node.location = (linked_node.location[0] + x_offset, linked_node.location[1] + y_offset)
                print(f"Shotput: Positioned composite to the RIGHT of render layer at {composite_node.location}")
            else:
                # Position above other node types (file outputs, etc.)
                spacing = max(100, node_height + 50)  # At least 100px or node height + 50px spacing
                composite_node.location = (linked_node.location[0], linked_node.location[1] + spacing)
                print(f"Shotput: Positioned composite ABOVE {linked_node.name} at {composite_node.location}")
        else:
            # Check if there's any selected node to position relative to
            selected_node = None
            print("Shotput: Looking for selected nodes...")
            for node in tree.nodes:
                print(f"Shotput: Node '{node.name}' (type: {node.type}) - selected: {node.select}, location: {node.location}")
                if node.select:
                    selected_node = node
                    print(f"Shotput: Found selected node: {node.name} at {node.location}")
                    break
            
            if selected_node:
                # Get actual node height for better spacing
                node_height = selected_node.height if hasattr(selected_node, 'height') else 100
                
                if selected_node.type == 'R_LAYERS':
                    # Position composite to the right of render layer nodes
                    x_offset = selected_node.width + 200  # To the right with spacing  
                    y_offset = 150  # Slightly above for visual hierarchy
                    new_location = (selected_node.location[0] + x_offset, selected_node.location[1] + y_offset)
                    composite_node.location = new_location
                    print(f"Shotput: Positioned composite to the RIGHT of render layer at {new_location}")
                else:
                    # Position above other node types
                    spacing = max(100, node_height + 50)  # At least 100px or node height + 50px spacing
                    new_location = (selected_node.location[0], selected_node.location[1] + spacing)
                    composite_node.location = new_location
                    print(f"Shotput: Positioned composite ABOVE {selected_node.name} at {new_location} (spacing: {spacing})")
            else:
                # Default position when no nodes are selected
                composite_node.location = (400, 300)
                print("Shotput: No selected nodes found, using default position (400, 300)")
        
        # Make this composite node active so enum functions work correctly
        tree.nodes.active = composite_node
        
        # Set up Shotput properties on the composite node
        comp_props = composite_node.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        comp_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy properties from source
        comp_props.output_layer = output_layer
        comp_props.variant = variant
        comp_props.pass_name = "composite"  # Set pass name to "composite"
        
        # Store normal mode backups from source BEFORE applying AYON tokens
        comp_props.normal_root_folder_token = getattr(source_props, 'root_folder_token', '')
        comp_props.normal_file_name_token = getattr(source_props, 'file_name_token', '')
        
        # Check if AYON context is detected and enable AYON mode if so
        from ..utils.ayon_utils import apply_ayon_tokens_to_node, is_ayon_context
        if is_ayon_context():
            # Enable AYON mode before applying tokens so the check passes
            comp_props.use_ayon_output_style = True
            print("Shotput: AYON context detected, enabling AYON mode on composite node")
        
        # Apply AYON tokens if AYON is detected (will override root_folder_token and file_name_token)
        ayon_applied = apply_ayon_tokens_to_node(composite_node, comp_props, is_composite=True)
        if ayon_applied:
            print("Shotput: Applied AYON-specific output tokens to standalone composite node")
        else:
            # No AYON detected, use tokens from source
            comp_props.root_folder_token = getattr(source_props, 'root_folder_token', '')
            comp_props.file_name_token = getattr(source_props, 'file_name_token', '')
        
        # CRITICAL: Inherit version from linked node or source
        # This ensures composite nodes start with the same version as their parent
        if linked_node and hasattr(linked_node, 'shotput_data'):
            comp_props.version = getattr(linked_node.shotput_data, 'version', 'v001')
            print(f"Shotput: Composite inheriting version '{comp_props.version}' from linked node")
        else:
            comp_props.version = getattr(source_props, 'version', 'v001')
            print(f"Shotput: Composite inheriting version '{comp_props.version}' from source props")
        
        # Set up path linking if we have a linked node (but only if AYON is NOT enabled)
        # AYON mode defines full paths via tokens, so path linking is incompatible
        if linked_node and not ayon_applied:
            # First set the full root folder token as if it were created normally
            comp_props.root_folder_token = getattr(source_props, 'root_folder_token', '')
            
            # Then enable path linking, which will trigger the backup system
            comp_props.path_linked = True  # Enable path linking by default
            comp_props.root_folder_token_backup = getattr(source_props, 'root_folder_token', '')  # Back up the original
            
            # Set linked node carefully - the enum might not be updated yet
            try:
                # Force update of the context to ensure enum gets refreshed
                bpy.context.view_layer.update()
                comp_props.linked_node = linked_node.name  # Link to the selected/found node
                print(f"Shotput: Successfully linked composite to '{linked_node.name}'")
            except (TypeError, ValueError) as e:
                print(f"Shotput: Warning - Could not set linked_node enum to '{linked_node.name}': {e}")
                print("Shotput: Path linking will still work via the node property, but UI dropdown may not show the selection")
                # Store the linked node name directly in a custom property as backup
                composite_node["shotput_linked_node_backup"] = linked_node.name
                
            comp_props.root_folder_token = "{passname}"  # Use dynamic token that resolves to pass_name
            
            print(f"Shotput: Composite node path-linked to '{linked_node.name}' with 'composite' subfolder")
        elif not ayon_applied:
            # No linked node and no AYON - use source properties directly
            comp_props.root_folder_token = getattr(source_props, 'root_folder_token', '')
            comp_props.path_linked = False
            print("Shotput: Composite node created without path linking")
        else:
            # AYON applied but no linked node - disable path linking
            comp_props.path_linked = False
            print("Shotput: Composite node created in AYON mode without path linking")
        
        # Add single stored pass for composite (for UI consistency)
        comp_props.stored_passes.clear()
        stored_pass = comp_props.stored_passes.add()
        stored_pass.name = "Composite"
        
        print(f"Shotput: Created composite node '{node_label}' (routes to main render output)")
        logger.info(f"Created standalone composite node '{node_label}'")
        
        return composite_node
