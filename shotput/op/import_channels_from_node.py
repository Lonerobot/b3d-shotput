import bpy

from ..utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

class OT_Import_Channels_From_Node(bpy.types.Operator):
    bl_idname = "shotput.import_channels_from_node"
    bl_label = "Import Channels from Node"
    bl_description = "Import channels from the selected File Output node and add them to the Shotput pass list. Clears existing passes before importing"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Property to specify target list: 'core' or 'aov'
    target_list: bpy.props.EnumProperty(
        name="Target List",
        description="Which pass list to import channels into",
        items=[
            ('core', "Core Passes", "Import into Core Passes list"),
            ('aov', "AOV Passes", "Import into AOV Passes list"),
        ],
        default='core'
    )
    
    def execute(self, context):
        logger.info(f"Import Channels from Node operator clicked (target: {self.target_list})")
        print(f"Shotput: Import Channels from Node operator executed (target: {self.target_list})")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Try to get the active/selected file output node
        active_node = self._get_active_file_output_node(context)
        
        if not active_node:
            self.report({'ERROR'}, "No File Output node selected. Please select a File Output node in the compositor")
            return {'CANCELLED'}
        
        # Read channels from the node
        channels = self._read_channels_from_node(active_node)
        
        if not channels:
            self.report({'INFO'}, f"No channels found in node '{active_node.name}'")
            return {'FINISHED'}
        
        # Determine target collection based on target_list property
        if self.target_list == 'core':
            target_collection = shotput_props.core_passes
            target_index_attr = 'core_passes_index'
            list_name = "Core Passes"
        else:  # 'aov'
            target_collection = shotput_props.aov_passes
            target_index_attr = 'aov_passes_index'
            list_name = "AOV Passes"
        
        # Clear existing passes in the target list
        target_collection.clear()
        print(f"Shotput: Cleared existing {list_name}")
        
        # Add imported channels to the target list
        added_count = 0
        for channel_name in channels:
            new_pass = target_collection.add()
            new_pass.name = channel_name
            added_count += 1
            print(f"Shotput: Added channel to {list_name}: '{channel_name}'")
        
        # Update the index to the last added item
        if added_count > 0:
            setattr(shotput_props, target_index_attr, len(target_collection) - 1)
        
        logger.info(f"Imported {added_count} channels from node '{active_node.name}' into {list_name}")
        
        self.report({'INFO'}, f"Imported {added_count} channels from '{active_node.name}' into {list_name}")
        
        return {'FINISHED'}
    
    def _get_active_file_output_node(self, context):
        """Get the active or selected File Output node from the compositor"""
        active_node = None
        
        # Try context.active_node first
        if hasattr(context, 'active_node') and context.active_node:
            active_node = context.active_node
        # Try getting from space data
        elif context.space_data and hasattr(context.space_data, 'node_tree'):
            node_tree = context.space_data.node_tree
            if node_tree and hasattr(node_tree.nodes, 'active'):
                active_node = node_tree.nodes.active
        # Try getting from scene node tree (compositor)
        elif hasattr(context.scene, 'node_tree') and context.scene.node_tree:
            node_tree = context.scene.node_tree
            if hasattr(node_tree.nodes, 'active'):
                active_node = node_tree.nodes.active
        
        # Validate it's a File Output node
        if active_node and active_node.type == 'OUTPUT_FILE':
            return active_node
        
        # If no active node or active node is not File Output, try to find any selected File Output node
        if hasattr(context.scene, 'node_tree') and context.scene.node_tree:
            node_tree = context.scene.node_tree
            for node in node_tree.nodes:
                if node.type == 'OUTPUT_FILE' and node.select:
                    return node
        
        return None
    
    def _read_channels_from_node(self, node):
        """
        Read channels from a File Output node.
        Prioritizes Shotput stored_passes if available, otherwise reads from file_slots.
        """
        channels = []
        
        # First, try to read from Shotput stored_passes (if it's a Shotput node)
        if hasattr(node, 'shotput_data') and hasattr(node.shotput_data, 'stored_passes'):
            shotput_data = node.shotput_data
            print(f"Shotput: Reading from Shotput stored_passes in node '{node.name}'")
            
            for pass_item in shotput_data.stored_passes:
                if pass_item.name.strip():
                    channel_name = self._clean_channel_name(pass_item.name.strip())
                    if channel_name:
                        channels.append(channel_name)
                        print(f"Shotput: Found stored pass: '{pass_item.name}' -> '{channel_name}'")
        
        # Fallback: Read from file_slots (works for both Shotput and standard File Output nodes)
        if not channels and hasattr(node, 'file_slots'):
            print(f"Shotput: Reading from file_slots in node '{node.name}'")
            
            for file_slot in node.file_slots:
                if file_slot.path.strip():
                    channel_name = self._clean_channel_name(file_slot.path.strip())
                    if channel_name:
                        channels.append(channel_name)
                        print(f"Shotput: Found file slot: '{file_slot.path}' -> '{channel_name}'")
        
        return channels
    
    def _clean_channel_name(self, raw_name):
        """
        Clean up channel names by removing file extensions, frame numbers, and path elements.
        Makes them suitable for use as pass names.
        """
        if not raw_name:
            return ""
        
        cleaned = raw_name.strip()
        
        # Remove path separators - take only the filename part
        if '/' in cleaned:
            cleaned = cleaned.split('/')[-1]
        if '\\' in cleaned:
            cleaned = cleaned.split('\\')[-1]
        
        # Remove common file extensions
        extensions_to_remove = [
            '.png', '.jpg', '.jpeg', '.exr', '.tif', '.tiff',
            '.PNG', '.JPG', '.JPEG', '.EXR', '.TIF', '.TIFF'
        ]
        for ext in extensions_to_remove:
            if cleaned.endswith(ext):
                cleaned = cleaned[:-len(ext)]
                break
        
        # Remove frame number patterns like .#### or .0001
        import re
        # Match patterns like .#### or .0001 at the end
        cleaned = re.sub(r'\.\#+$', '', cleaned)  # Remove .####
        cleaned = re.sub(r'\.\d{3,}$', '', cleaned)  # Remove .001, .0001, etc.
        
        # Remove common prefixes that might come from node names
        prefixes_to_remove = [
            "Shotput_",
            "shotput_",
            "Output_",
            "output_",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Replace spaces and special characters with underscores
        cleaned = cleaned.replace(" ", "_")
        cleaned = cleaned.replace("-", "_")
        
        # Remove multiple consecutive underscores
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        
        # Remove leading/trailing underscores
        cleaned = cleaned.strip("_")
        
        return cleaned if cleaned else ""
