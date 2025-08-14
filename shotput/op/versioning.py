import bpy

from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.version_utils import VersionUtils

logger = LoggerFactory.logger_obj()


class OT_Update_Version(bpy.types.Operator):
    bl_idname = "shotput.update_version"
    bl_label = "Update Version"
    bl_description = "Update version numbers for Shotput file output nodes (selected nodes, or all if none selected)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        logger.info("Update Version operator executed")
        
        # Get the compositor node tree
        if not context.scene.use_nodes:
            self.report({'ERROR'}, "Compositor nodes are not enabled")
            return {'CANCELLED'}
            
        tree = context.scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Find target nodes: selected first, then all if none selected
        target_nodes = self._get_target_nodes(tree)
        
        if not target_nodes:
            self.report({'WARNING'}, "No Shotput file output nodes found")
            return {'CANCELLED'}
        
        updated_count = 0
        
        for node in target_nodes:
            try:
                if self._update_node_version(node):
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update node {node.name}: {e}")
                continue
        
        if updated_count > 0:
            mode = "selected" if len(target_nodes) < self._count_relevant_shotput_nodes(tree) else "all"
            self.report({'INFO'}, f"Updated {updated_count} {mode} node(s) to next version")
            logger.info(f"Successfully updated {updated_count} Shotput nodes")
            
            # Handle composite node and scene render path update
            self._handle_composite_render_path(context, tree)
        else:
            self.report({'WARNING'}, "No nodes were updated")
            
        return {'FINISHED'}
    
    def _get_target_nodes(self, tree):
        """Get target nodes: selected Shotput nodes first, all Shotput nodes if none selected"""
        # First, check for selected Shotput nodes (File Output and Composite)
        selected_shotput_nodes = []
        for node in tree.nodes:
            if node.select and (self._is_shotput_node(node) or self._is_shotput_composite_node(node)):
                selected_shotput_nodes.append(node)
        
        if selected_shotput_nodes:
            return selected_shotput_nodes
        
        # If no Shotput nodes are selected, get all Shotput nodes
        all_shotput_nodes = []
        for node in tree.nodes:
            if self._is_shotput_node(node) or self._is_shotput_composite_node(node):
                all_shotput_nodes.append(node)
        
        return all_shotput_nodes
    
    def _count_relevant_shotput_nodes(self, tree):
        """Count relevant Shotput nodes: all File Output nodes and only connected Composite nodes"""
        count = 0
        for node in tree.nodes:
            if self._is_shotput_node(node):
                # Count all File Output nodes
                count += 1
            elif self._is_shotput_composite_node(node):
                # Only count Composite nodes that have incoming connections
                if self._has_incoming_connections(node):
                    count += 1
        return count
    
    def _count_all_shotput_nodes(self, tree):
        """Count all Shotput nodes in the tree (File Output and Composite)"""
        return sum(1 for node in tree.nodes if (self._is_shotput_node(node) or self._is_shotput_composite_node(node)))
    
    def _is_shotput_node(self, node):
        """Check if a node is a Shotput file output node"""
        return (node.type == 'OUTPUT_FILE' and 
                hasattr(node, 'shotput_data') and 
                node.name.startswith('Shotput_'))
    
    def _is_shotput_composite_node(self, node):
        """Check if a node is a Shotput composite node"""
        return (node.type == 'COMPOSITE' and 
                hasattr(node, 'shotput_data') and 
                node.name.startswith('Shotput_'))
    
    def _handle_composite_render_path(self, context, tree):
        """Handle composite node validation and scene render path update"""
        try:
            # Find all Shotput composite nodes
            composite_nodes = []
            for node in tree.nodes:
                if self._is_shotput_composite_node(node):
                    composite_nodes.append(node)
            
            if not composite_nodes:
                # No composite nodes found, nothing to do
                logger.debug("No Shotput composite nodes found")
                return
            
            if len(composite_nodes) > 1:
                # Multiple composite nodes - check for connections
                connected_composites = []
                for node in composite_nodes:
                    if self._has_incoming_connections(node):
                        connected_composites.append(node)
                
                if len(connected_composites) > 1:
                    # Multiple connected composites - error
                    node_names = [node.name for node in connected_composites]
                    error_msg = f"Multiple connected Shotput composite nodes found: {', '.join(node_names)}. Only one composite should be connected."
                    self.report({'ERROR'}, error_msg)
                    logger.error(error_msg)
                    return
                elif len(connected_composites) == 1:
                    # Single connected composite - use it
                    composite_node = connected_composites[0]
                else:
                    # No connected composites - nothing to do
                    logger.debug("Multiple Shotput composite nodes found but none are connected")
                    return
            else:
                # Single composite node
                composite_node = composite_nodes[0]
                if not self._has_incoming_connections(composite_node):
                    # Not connected - nothing to do
                    logger.debug("Single Shotput composite node found but not connected")
                    return
            
            # Update scene render path using composite node properties
            self._update_scene_render_path(context, composite_node)
            
        except Exception as e:
            logger.error(f"Error handling composite render path: {e}")
            self.report({'WARNING'}, f"Failed to update scene render path: {e}")
    
    def _has_incoming_connections(self, node):
        """Check if a node has any incoming connections"""
        for input_socket in node.inputs:
            if input_socket.is_linked:
                return True
        return False
    
    def _update_scene_render_path(self, context, composite_node):
        """Update scene render filepath using composite node properties"""
        try:
            node_props = composite_node.shotput_data
            token_parser = TokenParser(node_props)
            
            # Parse the root folder token to get base path
            base_path = token_parser.parse_token(node_props.root_folder_token, passname="composite")
            
            # Parse the file name token
            filename = token_parser.parse_token(node_props.file_name_token, passname="composite")
            
            # Combine to create full render path
            full_path = f"{base_path}/{filename}"
            
            # Update scene render settings
            context.scene.render.filepath = full_path
            
            logger.info(f"Updated scene render filepath to: {full_path}")
            print(f"Shotput: Updated scene render path to: {full_path}")
            
        except Exception as e:
            logger.error(f"Error updating scene render path: {e}")
            raise
    
    def _update_node_version(self, node):
        """Update the version for a specific node"""
        try:
            node_props = node.shotput_data
            token_parser = TokenParser(node_props)
            
            # Calculate next version (no specific version support in streamlined UX)
            new_version = self._calculate_next_version(node_props, token_parser)
            
            # Update node properties
            node_props.version = new_version
            
            # Update paths only for File Output nodes (not Composite nodes)
            if node.type == 'OUTPUT_FILE':
                # Update the base path using the new reconstruction method
                root_token = node_props.root_folder_token
                if root_token:
                    new_base_path = self._reconstruct_path_with_version(root_token, new_version, token_parser)
                    node.base_path = new_base_path
                    logger.debug(f"Updated base path for {node.name}: {new_base_path}")
                
                # Update file slot paths if needed
                self._update_file_slots(node, node_props, token_parser, new_version)
            
            logger.info(f"Updated node {node.name} to version {new_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating node {node.name}: {e}")
            return False
    
    def _calculate_next_version(self, node_props, token_parser):
        """Calculate the next version number for a node based on existing filesystem folders"""
        try:
            # Parse the root folder token to get the base directory structure
            root_token = node_props.root_folder_token
            if not root_token:
                return VersionUtils.versionDefault
            
            # Check if version token exists in the root token
            if '{version}' not in root_token:
                return VersionUtils.versionDefault
            
            # Split the token at {version} to handle it properly
            version_parts = root_token.split('{version}')
            if len(version_parts) != 2:
                logger.warning(f"Invalid version token structure in: {root_token}")
                return VersionUtils.versionDefault
            
            prefix_token = version_parts[0]  # Everything before {version}
            suffix_token = version_parts[1]  # Everything after {version}
            
            # Parse the prefix to get the base directory where version folders should be
            base_path = token_parser.parse_token(prefix_token)
            if not base_path:
                return VersionUtils.versionDefault
            
            # Get the next version based purely on what exists on disk
            next_version = token_parser.get_next_version_for_path(base_path)
            
            logger.debug(f"Version calculation - Base path: {base_path}, Next version: {next_version}")
            return next_version
            
        except Exception as e:
            logger.error(f"Error calculating next version: {e}")
            return VersionUtils.versionDefault
    
    def _update_file_slots(self, node, node_props, token_parser, new_version):
        """Update file slot paths with new version"""
        try:
            file_token = node_props.file_name_token
            if not file_token:
                return
            
            # Update each file slot
            for i, slot in enumerate(node.file_slots):
                # Get the pass name from stored passes if available
                pass_name = None
                if i < len(node_props.stored_passes):
                    pass_name = node_props.stored_passes[i].name
                
                # Parse filename with new version using reconstruction method
                if pass_name:
                    # Create a temporary token string with the pass name override
                    temp_token = file_token.replace('{passname}', pass_name)
                    new_filename = self._reconstruct_path_with_version(temp_token, new_version, token_parser)
                else:
                    new_filename = self._reconstruct_path_with_version(file_token, new_version, token_parser)
                
                slot.path = f"{new_filename}_"
                
        except Exception as e:
            logger.error(f"Error updating file slots: {e}")
    
    def _reconstruct_path_with_version(self, token_string, new_version, token_parser):
        """
        Reconstruct a full path with the new version, handling {version} anywhere in the token string.
        
        Args:
            token_string: Original token string with {version} placeholder
            new_version: New version string (e.g., 'v002')
            token_parser: TokenParser instance for resolving other tokens
            
        Returns:
            Fully resolved path with the new version
        """
        if '{version}' not in token_string:
            # No version token, just parse normally
            return token_parser.parse_token(token_string)
        
        # Split at version token to validate structure
        version_parts = token_string.split('{version}')
        if len(version_parts) != 2:
            logger.warning(f"Invalid version token structure: {token_string}")
            return token_parser.parse_token(token_string)
        
        # Create a temporary token string with the version replaced
        # This preserves the exact token structure and lets the normal parser handle it
        temp_token_string = token_string.replace('{version}', new_version)
        
        # Use a safe token parsing that won't trigger version resolution
        resolved_path = self._parse_token_with_fixed_version(temp_token_string, new_version, token_parser)
        
        logger.debug(f"Reconstructed path: {token_string} -> {resolved_path}")
        return resolved_path
    
    def _parse_token_with_fixed_version(self, token_string, fixed_version, token_parser):
        """
        Parse a token string with a fixed version to prevent double version resolution.
        
        Args:
            token_string: Token string to parse (should not contain {version})
            fixed_version: The fixed version to use if version resolution is encountered
            token_parser: TokenParser instance
            
        Returns:
            Fully resolved path
        """
        # Create a temporary version override in the token parser
        original_version = getattr(token_parser.node_properties, 'version', None) if token_parser.node_properties else None
        
        try:
            # Temporarily override the version in node properties
            if token_parser.node_properties:
                token_parser.node_properties.version = fixed_version
            
            # Parse the token string
            resolved_path = token_parser.parse_token(token_string)
            
            return resolved_path
            
        finally:
            # Restore original version
            if token_parser.node_properties and original_version is not None:
                token_parser.node_properties.version = original_version

class OT_Token_Help(bpy.types.Operator):
    bl_idname = "shotput.token_help"
    bl_label = "Token Help"
    bl_description = "Show available tokens and their descriptions with current values"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=550)
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Shotput Token Reference", icon='HELP')
        layout.separator()
        
        # Create a dummy props object for getting token values
        class DummyProps:
            def __init__(self):
                # Use scene properties if available, otherwise defaults
                scene = context.scene
                shotput_props = getattr(scene, 'shotput', None) if scene else None
                
                self.render_layer = getattr(shotput_props, 'render_layer', None) if shotput_props else None
                if not self.render_layer:
                    self.render_layer = getattr(context, 'view_layer', None).name if hasattr(context, 'view_layer') and context.view_layer else "RenderLayer"
                
                self.variant = getattr(shotput_props, 'variant', 'main') if shotput_props else "main"
                self.pass_name = "beauty"
                self.version = "v001"
        
        # Create token parser to get actual current values
        try:
            dummy_props = DummyProps()
            parser = TokenParser(dummy_props)
            
            # Core Shotput tokens with live values
            col = layout.column()
            box = col.box()
            box.label(text="Core Shotput Tokens", icon='FILE_FOLDER')
            
            # Dynamic descriptions based on environment
            import os
            workdir_desc = "AYON work directory" if os.getenv("AYON_PROJECT_NAME") else "Current Blender directory"
            
            core_tokens = [
                ('workdir', workdir_desc),
                ('subpath', 'Subpath from preferences'),
                ('renderlayer', 'Render layer name'),
                ('passname', 'Pass name (beauty, diffuse, etc.)'),
                ('variant', 'Version variant'),
                ('version', 'Version number'),
            ]
            
            for token, desc in core_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
            # AYON-specific tokens with live values
            box = col.box()
            box.label(text="AYON Integration Tokens", icon='NETWORK_DRIVE')
            
            ayon_tokens = [
                ('project', 'AYON project root'),
                ('projectname', 'AYON project name'),
                ('task', 'Current task name'),
                ('folder', 'Folder path'),
                ('user', 'Current user'),
            ]
            
            for token, desc in ayon_tokens:
                try:
                    value = parser._resolve_token(token)
                    # Show placeholder if value is empty or default
                    if not value or value in ["Unknown_Project", "Unknown_Task", "Unknown_User"]:
                        value = f"(not in AYON)"
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (not available)")
            
            # Blender-specific tokens with live values
            box = col.box()
            box.label(text="Blender Context Tokens", icon='BLENDER')
            
            blender_tokens = [
                ('blend_name', 'Current .blend filename'),
                ('scene_name', 'Active scene name'),
                ('frame', 'Current frame number'),
                ('camera', 'Active camera name'),
            ]
            
            for token, desc in blender_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
            # Date/time tokens with live values
            box = col.box()
            box.label(text="Date/Time Tokens", icon='TIME')
            
            datetime_tokens = [
                ('date', 'Current date (DD-MM-YY)'),
                ('time', 'Current time (HH-MM-SS)'),
            ]
            
            for token, desc in datetime_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", icon='DOT')
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
        except Exception as e:
            # Fallback to static examples if token parsing fails
            layout.label(text="Error loading dynamic values - showing static examples", icon='ERROR')
            layout.separator()
            
            box = layout.box()
            box.label(text="Static Token Examples", icon='FILE_FOLDER')
            
            static_examples = [
                ('workdir', 'Current Blender file directory', 'C:/Projects/MyProject'),
                ('blend_name', 'Current .blend filename', 'scene_001'),
                ('scene_name', 'Active scene name', context.scene.name if context.scene else 'Scene'),
                ('date', 'Current date', '11-08-25'),
                ('time', 'Current time', '14-30-45'),
            ]
            
            for token, desc, example in static_examples:
                row = box.row()
                split = row.split(factor=0.15)
                split.label(text=f"{{{token}}}", icon='DOT')
                split = split.split(factor=0.55)
                split.label(text=desc)
                split.label(text=f"→ {example}")


class OT_Preview_Paths(bpy.types.Operator):
    bl_idname = "shotput.preview_paths"
    bl_label = "Preview Paths"
    bl_description = "Preview resolved paths for current Shotput settings"
    bl_options = {'REGISTER'}
    
    core_path = bpy.props.StringProperty(default="")
    aov_path = bpy.props.StringProperty(default="")
    data_path = bpy.props.StringProperty(default="")
    
    def execute(self, context):
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Create a temporary token parser
        class TempNodeProps:
            def __init__(self, props):
                self.render_layer = getattr(props, 'render_layer', None) or "RenderLayer"
                self.variant = getattr(props, 'variant', None) or "Main"
                self.root_folder_token = getattr(props, 'root_folder_token', None) or "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}"
                self.file_name_token = getattr(props, 'file_name_token', None) or "{renderlayer}_{passname}_{variant}"
                self.pass_name = "Preview"
                self.version = "v001"
        
        try:
            temp_props = TempNodeProps(shotput_props)
            parser = TokenParser(temp_props)
            
            # Generate preview paths for different pass types
            temp_props.pass_name = "beauty"
            self.core_path = f"{parser.parse_token(temp_props.root_folder_token)}/{parser.parse_token(temp_props.file_name_token)}"
            
            temp_props.pass_name = "diffuse"
            self.aov_path = f"{parser.parse_token(temp_props.root_folder_token)}/{parser.parse_token(temp_props.file_name_token)}"
            
            temp_props.pass_name = "depth"
            self.data_path = f"{parser.parse_token(temp_props.root_folder_token)}/{parser.parse_token(temp_props.file_name_token)}"
            
        except Exception as e:
            self.core_path = f"Error: {str(e)}"
            self.aov_path = f"Error: {str(e)}"
            self.data_path = f"Error: {str(e)}"
        
        return context.window_manager.invoke_popup(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Path Preview", icon='PREVIEW_RANGE')
        layout.separator()
        
        # Core passes
        box = layout.box()
        box.label(text="Core Passes:", icon='FILE_FOLDER')
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.core_path)
        
        # AOV passes
        box = layout.box()
        box.label(text="AOV Passes:", icon='FILE_FOLDER')
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.aov_path)
        
        # Data passes
        box = layout.box()
        box.label(text="Data Passes:", icon='FILE_FOLDER')
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.data_path)


classes = (
    OT_Update_Version,
    OT_Token_Help,
    OT_Preview_Paths,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
