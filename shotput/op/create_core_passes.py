import bpy
from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.defaults import get_file_format_for_pass_type, get_sequence_padding
from ..utils.lazy_hookup import auto_connect_node
from ..utils.color_utils import store_original_node_color

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
        
        # Store the original color for potential path linking visual feedback
        store_original_node_color(file_output)
        
        # Position the node (find a good spot)
        file_output.location = (400, 0)
        
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
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
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
                stored_pass.name = core_pass.name
                
        elif core_format == 'OPEN_EXR':
            # Single channel EXR: base_path = rootpath, file_slots = filename_token + .#### + extension
            resolved_base_path = token_parser.parse_token(node_props.root_folder_token, passname=area_name)
            file_output.base_path = resolved_base_path
            
            # Configure file slots for each core pass
            for i, core_pass in enumerate(shotput_props.core_passes):
                pass_name = core_pass.name
                
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
        
        # Create composite node if requested
        composite_node = None
        if shotput_props.create_composite_from_core:
            composite_node = self._create_composite_node(context, tree, shotput_props, token_parser, file_output)
        
        # Auto-connect nodes if lazy hook-up is enabled
        core_pass_names = [core_pass.name for core_pass in shotput_props.core_passes]
        auto_connect_node(context, file_output, core_pass_names)
        
        if composite_node:
            auto_connect_node(context, composite_node)
        
        # Select the new core node
        file_output.select = True
        tree.nodes.active = file_output
        
        composite_msg = " and composite node" if composite_node else ""
        self.report({'INFO'}, f"Created core passes node '{node_label}' with {len(shotput_props.core_passes)} passes{composite_msg}")
        
        return {'FINISHED'}
    
    def _create_composite_node(self, context, tree, shotput_props, token_parser, core_node):
        """Create a Shotput Composite node (actual Blender Composite node for main output)"""
        
        # Create node label: render_layer.composite.variant
        node_label = f"{shotput_props.render_layer}.composite.{shotput_props.variant}"
        
        # Create Composite node (not File Output) - this routes to main render output
        composite_node = tree.nodes.new(type='CompositorNodeComposite')
        composite_node.name = "Shotput_Composite"
        composite_node.label = node_label
        
        # Set node color - PINK for composite!
        composite_node.use_custom_color = True
        composite_node.color = (0.8, 0.4, 0.8)  # Pink color
        composite_node.width = 300  # Smaller since it's just routing
        
        # Store the original color for potential path linking visual feedback
        store_original_node_color(composite_node)
        
        # Position the node above the core passes (same X, higher Y)
        composite_node.location = (400, 300)
        
        # Set up Shotput properties on the composite node
        comp_props = composite_node.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        comp_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy scene properties to composite node
        comp_props.render_layer = shotput_props.render_layer
        comp_props.variant = shotput_props.variant
        comp_props.file_name_token = shotput_props.file_name_token
        comp_props.pass_name = "composite"  # Set pass name to "composite"
        
        # Set up path linking to the core node (but make it toggleable)
        # First set the full root folder token as if it were created normally
        comp_props.root_folder_token = shotput_props.root_folder_token
        
        # Then enable path linking, which will trigger the backup system
        comp_props.path_linked = True  # Enable path linking by default
        comp_props.root_folder_token_backup = shotput_props.root_folder_token  # Back up the original
        comp_props.linked_node = core_node.name  # Link to the core node
        comp_props.root_folder_token = "{passname}"  # Use dynamic token that resolves to pass_name
        
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
    bl_label = "Create Linked Composite Node from Core"
    bl_description = "Create a composite node linked to the selected File Output node or using global UI settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Must be in Compositor workspace
        return (context.space_data and 
                context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'CompositorNodeTree')
    
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
            
            # Use selected File Output node properties
            linked_node = context.active_node
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
        composite_node = self._create_standalone_composite_node(tree, source_props, linked_node)
        
        if not composite_node:
            self.report({'ERROR'}, "Failed to create composite node")
            return {'CANCELLED'}
        
        # Select the new composite node
        composite_node.select = True
        tree.nodes.active = composite_node
        
        # Report success
        linked_msg = f" (linked to {linked_node.name})" if linked_node else " (no linked node found)"
        self.report({'INFO'}, f"Created linked composite node{linked_msg}")
        
        return {'FINISHED'}
    
    def _create_standalone_composite_node(self, tree, source_props, linked_node=None):
        """Create a Shotput Composite node with properties from source"""
        
        # Get render layer and variant from source
        render_layer = getattr(source_props, 'render_layer', 'RenderLayer')
        variant = getattr(source_props, 'variant', 'Main')
        
        # Create node label: render_layer.composite.variant
        node_label = f"{render_layer}.composite.{variant}"
        
        # Create Composite node (not File Output) - this routes to main render output
        composite_node = tree.nodes.new(type='CompositorNodeComposite')
        composite_node.name = "Shotput_Composite"
        composite_node.label = node_label
        
        # Set node color - PINK for composite!
        composite_node.use_custom_color = True
        composite_node.color = (0.8, 0.4, 0.8)  # Pink color
        composite_node.width = 300  # Smaller since it's just routing
        
        # Store original color for visual feedback system
        store_original_node_color(composite_node)
        
        # Position the node - above linked node if available, otherwise default position
        if linked_node:
            # Position above the linked node
            composite_node.location = (linked_node.location[0], linked_node.location[1] + 300)
        else:
            # Default position
            composite_node.location = (400, 300)
        
        # Make this composite node active so enum functions work correctly
        tree.nodes.active = composite_node
        
        # Set up Shotput properties on the composite node
        comp_props = composite_node.shotput_data
        
        # Set the Shotput version
        from .. import bl_info
        comp_props.shotput_version = f"{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}"
        
        # Copy properties from source
        comp_props.render_layer = render_layer
        comp_props.variant = variant
        comp_props.file_name_token = getattr(source_props, 'file_name_token', '')
        comp_props.pass_name = "composite"  # Set pass name to "composite"
        
        # Set up path linking if we have a linked node
        if linked_node:
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
        else:
            # No linked node - use source properties directly
            comp_props.root_folder_token = getattr(source_props, 'root_folder_token', '')
            comp_props.path_linked = False
            print("Shotput: Composite node created without path linking")
        
        # Add single stored pass for composite (for UI consistency)
        comp_props.stored_passes.clear()
        stored_pass = comp_props.stored_passes.add()
        stored_pass.name = "Composite"
        
        print(f"Shotput: Created composite node '{node_label}' (routes to main render output)")
        logger.info(f"Created standalone composite node '{node_label}'")
        
        return composite_node
