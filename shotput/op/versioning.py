import bpy
import os
from pathlib import Path

from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.version_utils import VersionUtils
from ..utils.defaults import get_file_format_for_pass_type, load_default_passes, initialize_default_passes
from ..utils import custom_icons
from .. import __version__

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
        
        # Check for multiple composite nodes and capture any warning
        composite_warning = self._check_multiple_composite_nodes(tree)
        
        # Find target nodes: selected first, then all if none selected
        target_nodes = self._get_target_nodes(tree)
        
        if not target_nodes:
            self.report({'WARNING'}, "No Shotput file output nodes found")
            return {'CANCELLED'}
        
        # Validate paths before updating any nodes
        validation_errors = self._validate_node_paths(target_nodes)
        if validation_errors:
            # Report all validation errors to user
            error_summary = f"Path validation failed for {len(validation_errors)} node(s):"
            detailed_errors = []
            for node_name, errors in validation_errors.items():
                detailed_errors.append(f"• {node_name}: {'; '.join(errors)}")
            
            full_error_msg = error_summary + "\n" + "\n".join(detailed_errors)
            self.report({'ERROR'}, full_error_msg)
            logger.error(f"Path validation errors: {validation_errors}")
            return {'CANCELLED'}
        
        # Separate nodes into linked and non-linked for proper update ordering
        non_linked_nodes = []
        linked_nodes = []
        
        for node in target_nodes:
            if hasattr(node, 'shotput_data') and self._is_path_linked(node.shotput_data):
                linked_nodes.append(node)
            else:
                non_linked_nodes.append(node)
        
        updated_count = 0
        
        # Update non-linked nodes first (they provide the base paths for linked nodes)
        for node in non_linked_nodes:
            try:
                if self._update_node_version(node, context):
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update non-linked node {node.name}: {e}")
                continue
        
        # Then update linked nodes (they depend on the non-linked nodes)
        for node in linked_nodes:
            try:
                if self._update_node_version(node, context):
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update linked node {node.name}: {e}")
                continue
        
        if updated_count > 0:
            # Build success message with proper grammar
            if len(target_nodes) < self._count_relevant_shotput_nodes(tree):
                mode_text = f"{updated_count} selected node" + ("s" if updated_count != 1 else "")
            else:
                mode_text = f"all {updated_count} node" + ("s" if updated_count != 1 else "")
            
            # Add path linking info if relevant
            if linked_nodes:
                linked_count = sum(1 for node in linked_nodes if hasattr(node, 'shotput_data') and self._is_path_linked(node.shotput_data))
                if linked_count > 0:
                    mode_text += f" ({linked_count} path-linked)"
            
            success_msg = f"Updated {mode_text} to next version"
            
            # Combine with composite warning if present
            if composite_warning:
                combined_msg = f"{success_msg}. {composite_warning}"
                self.report({'WARNING'}, combined_msg)
            else:
                self.report({'INFO'}, success_msg)
            
            logger.info(f"Successfully updated {updated_count} Shotput nodes ({len(non_linked_nodes)} non-linked, {len(linked_nodes)} linked)")
        else:
            # Combine no updates message with composite warning if present
            if composite_warning:
                combined_msg = f"No nodes were updated. {composite_warning}"
                self.report({'WARNING'}, combined_msg)
            else:
                self.report({'WARNING'}, "No nodes were updated")
        
        # Always try to handle composite node and scene render path update after updating nodes
        # This ensures scene render path gets updated even if composite node wasn't selected
        self._handle_composite_render_path(context, tree)
            
        return {'FINISHED'}
    
    def _validate_node_paths(self, nodes):
        """
        Validate path tokens for all nodes before processing.
        
        Args:
            nodes: List of nodes to validate
            
        Returns:
            Dict mapping node names to lists of validation errors, empty if all valid
        """
        validation_errors = {}
        
        for node in nodes:
            if not hasattr(node, 'shotput_data'):
                continue
                
            node_props = node.shotput_data
            node_errors = []
            
            # Validate root folder token
            root_token = getattr(node_props, 'root_folder_token', '')
            if root_token:
                token_errors = self._validate_token_string(root_token, "Root Folder")
                node_errors.extend(token_errors)
            
            # Validate file name token
            file_token = getattr(node_props, 'file_name_token', '')
            if file_token:
                token_errors = self._validate_token_string(file_token, "File Name")
                node_errors.extend(token_errors)
            
            # Check for linked node validity if path-linked
            if self._is_path_linked(node_props):
                linked_errors = self._validate_linked_node(node_props)
                node_errors.extend(linked_errors)
            
            # Only add to validation_errors if there are actual errors
            if node_errors:
                validation_errors[node.name] = node_errors
        
        return validation_errors
    
    def _validate_token_string(self, token_string, field_name):
        """
        Validate a token string for common issues.
        
        Args:
            token_string: Token string to validate
            field_name: Human-readable field name for error messages
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not token_string.strip():
            return errors  # Empty tokens are allowed
        
        import re
        
        # Check for unmatched braces
        open_braces = token_string.count('{')
        close_braces = token_string.count('}')
        
        if open_braces != close_braces:
            if open_braces > close_braces:
                errors.append(f"{field_name} has {open_braces - close_braces} unmatched opening brace(s) '{{'. Example issue: '{{workdir/{{passname}}'")
            else:
                errors.append(f"{field_name} has {close_braces - open_braces} unmatched closing brace(s) '}}'. Example issue: 'workdir}}/{{passname}}'")
        
        # Check for malformed tokens (braces without content or invalid nesting)
        if '{}' in token_string:
            errors.append(f"{field_name} contains empty token '{{}}'. Tokens must have content like '{{workdir}}'")
        
        # Check for nested braces (not supported)
        if re.search(r'\{[^}]*\{', token_string) or re.search(r'\}[^{]*\}', token_string):
            errors.append(f"{field_name} contains nested or malformed braces. Tokens cannot be nested")
        
        # Check for invalid path characters in the resolved token structure
        # Remove valid tokens temporarily to check the static parts
        temp_string = re.sub(r'\{[^}]+\}', 'TOKEN', token_string)
        
        # Check for invalid characters in non-token parts
        invalid_chars = ['<', '>', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in temp_string:
                errors.append(f"{field_name} contains invalid path character '{char}'. Remove this character")
        
        # Check for double slashes in static parts
        if '//' in temp_string or '\\\\' in temp_string:
            errors.append(f"{field_name} contains double slashes. Use single slashes for path separators")
        
        # Check for tokens that might resolve to problematic paths
        problematic_patterns = [
            (r'\{[^}]*\}/\{[^}]*\}/', "Consider if multiple consecutive tokens create valid paths"),
            (r'^\{[^}]*\}$', "Token-only strings should be validated manually"),
        ]
        
        for pattern, warning in problematic_patterns:
            if re.search(pattern, token_string):
                # These are warnings, not hard errors - maybe skip for now
                pass
        
        return errors
    
    def _validate_linked_node(self, node_props):
        """
        Validate linked node configuration.
        
        Args:
            node_props: Node properties to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        linked_node_name = getattr(node_props, 'linked_node', '')
        if not linked_node_name or linked_node_name == 'NONE':
            errors.append("Path-linked is enabled but no linked node is selected")
            return errors
        
        # Try to find the linked node
        try:
            scene = bpy.context.scene
            if not scene or not scene.node_tree:
                errors.append("Cannot validate linked node: no scene or node tree available")
                return errors
            
            linked_node = scene.node_tree.nodes.get(linked_node_name)
            if not linked_node:
                errors.append(f"Linked node '{linked_node_name}' not found in scene")
            elif linked_node.type != 'OUTPUT_FILE':
                errors.append(f"Linked node '{linked_node_name}' is not a File Output node")
            elif not hasattr(linked_node, 'shotput_data'):
                errors.append(f"Linked node '{linked_node_name}' is not a Shotput node")
            
        except Exception as e:
            errors.append(f"Error validating linked node: {e}")
        
        return errors
    
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
    
    def _check_multiple_composite_nodes(self, tree):
        """Check for multiple composite nodes and return warning message if found"""
        # Count all composite nodes (Shotput and regular)
        shotput_composite_nodes = []
        regular_composite_nodes = []
        
        for node in tree.nodes:
            if node.type == 'COMPOSITE':
                if self._is_shotput_composite_node(node):
                    shotput_composite_nodes.append(node)
                else:
                    regular_composite_nodes.append(node)
        
        total_composite_count = len(shotput_composite_nodes) + len(regular_composite_nodes)
        
        if total_composite_count > 1:
            # Build warning message
            warning_parts = []
            if len(shotput_composite_nodes) > 1:
                warning_parts.append(f"{len(shotput_composite_nodes)} Shotput composite nodes")
            elif len(shotput_composite_nodes) == 1:
                warning_parts.append("1 Shotput composite node")
            
            if len(regular_composite_nodes) > 1:
                warning_parts.append(f"{len(regular_composite_nodes)} regular composite nodes")
            elif len(regular_composite_nodes) == 1:
                warning_parts.append("1 regular composite node")
            
            warning_msg = f"Multiple composite nodes detected: {' and '.join(warning_parts)}. This may cause rendering conflicts."
            
            # Log warning for debugging
            logger.warning(f"Multiple composite nodes found in scene: {len(shotput_composite_nodes)} Shotput, {len(regular_composite_nodes)} regular")
            
            return warning_msg
        
        return None
    
    def _handle_composite_render_path(self, context, tree):
        """Handle composite node validation and scene render path update"""
        try:
            print(f"Shotput: _handle_composite_render_path called")
            
            # Find all Shotput composite nodes
            composite_nodes = []
            for node in tree.nodes:
                if self._is_shotput_composite_node(node):
                    composite_nodes.append(node)
            
            print(f"Shotput: Found {len(composite_nodes)} composite nodes")
            
            if not composite_nodes:
                # No composite nodes found, nothing to do
                logger.debug("No Shotput composite nodes found")
                print(f"Shotput: No composite nodes found, returning")
                return
            
            # Find the composite node to use for scene render path
            composite_node = None
            
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
                candidate_node = composite_nodes[0]
                if self._has_incoming_connections(candidate_node):
                    composite_node = candidate_node
                else:
                    # Not connected - nothing to do
                    logger.debug("Single Shotput composite node found but not connected")
                    return
            
            # Validate that the composite node has proper configuration before updating scene render path
            if composite_node and self._is_composite_node_valid_for_scene_render(composite_node):
                print(f"Shotput: Composite node {composite_node.name} is valid for scene render")
                
                # CRITICAL FIX: Update composite node's version BEFORE updating scene render path
                # This ensures the {version} token resolves to the correct (latest) version
                node_props = composite_node.shotput_data
                
                # If the composite node is path-linked, sync its version from the linked node
                if self._is_path_linked(node_props):
                    linked_node_name = getattr(node_props, 'linked_node', '')
                    if linked_node_name and linked_node_name != 'NONE':
                        scene = context.scene
                        if scene and scene.node_tree:
                            linked_node = scene.node_tree.nodes.get(linked_node_name)
                            if linked_node and hasattr(linked_node, 'shotput_data'):
                                # Sync version from linked node
                                linked_version = getattr(linked_node.shotput_data, 'version', VersionUtils.versionDefault)
                                node_props.version = linked_version
                                logger.info(f"Synced composite node {composite_node.name} version to {linked_version} from linked node {linked_node_name}")
                            else:
                                logger.warning(f"Linked node {linked_node_name} not found, composite version may be incorrect")
                
                # Update scene render path using composite node properties (now with correct version)
                self._update_scene_render_path(context, composite_node)
            else:
                print(f"Shotput: Composite node {composite_node.name if composite_node else 'None'} not valid for scene render path update")
                logger.debug("Composite node found but not valid for scene render path update")
            
        except Exception as e:
            logger.error(f"Error handling composite render path: {e}")
            self.report({'WARNING'}, f"Failed to update scene render path: {e}")
    
    def _is_composite_node_valid_for_scene_render(self, composite_node):
        """Check if a composite node has valid configuration for scene render path"""
        print(f"Shotput: Validating composite node {composite_node.name}")
        
        if not hasattr(composite_node, 'shotput_data'):
            print(f"Shotput: Node {composite_node.name} has no shotput_data")
            return False
        
        node_props = composite_node.shotput_data
        
        # Check if it has a valid file name token
        filename_token = getattr(node_props, 'file_name_token', '')
        if not filename_token or not filename_token.strip():
            print(f"Shotput: Node {composite_node.name} has no filename token: '{filename_token}'")
            logger.debug(f"Composite node {composite_node.name} has no filename token")
            return False
        
        print(f"Shotput: Node {composite_node.name} has filename token: '{filename_token}'")
        
        # If path-linked, validate the linked node exists (but don't require base_path since it gets set during update)
        if hasattr(node_props, 'path_linked') and node_props.path_linked:
            linked_node_name = getattr(node_props, 'linked_node', '')
            
            # If linked_node is NONE, try to get it from backup custom property
            if not linked_node_name or linked_node_name == 'NONE':
                if "shotput_linked_node_backup" in composite_node:
                    backup_name = composite_node["shotput_linked_node_backup"]
                    linked_node_name = backup_name
                else:
                    # Last resort: find any Shotput File Output node, but prioritize by context
                    scene = bpy.context.scene
                    if scene and scene.node_tree:
                        candidate_nodes = []
                        for node in scene.node_tree.nodes:
                            if (node.type == 'OUTPUT_FILE' and 
                                hasattr(node, 'shotput_data') and
                                node.name.startswith('Shotput_')):
                                candidate_nodes.append(node)
                        
                        # If we have candidates, prefer them in this order:
                        # 1. Core nodes (most common link target)
                        # 2. Any other Shotput nodes
                        if candidate_nodes:
                            # Try to find a Core node first
                            for node in candidate_nodes:
                                if 'Core' in node.name:
                                    linked_node_name = node.name
                                    break
                            else:
                                # If no Core node, use the first available
                                linked_node_name = candidate_nodes[0].name
            
            if not linked_node_name or linked_node_name == 'NONE':
                logger.debug(f"Composite node {composite_node.name} is path-linked but has no valid linked node")
                # Show user-friendly warning
                self.report({'WARNING'}, f"Composite node '{composite_node.name}' is set to path-linked but no linked node is selected. Please select a linked File Output node or disable path linking.")
                return False
            
            # Check if linked node exists and is valid
            scene = bpy.context.scene
            if scene and scene.node_tree:
                linked_node = scene.node_tree.nodes.get(linked_node_name)
                if not linked_node or linked_node.type != 'OUTPUT_FILE':
                    # Check if this is because there are no other File Output nodes available
                    file_output_count = 0
                    for node in scene.node_tree.nodes:
                        if node.type == 'OUTPUT_FILE':
                            file_output_count += 1
                    
                    if file_output_count <= 1:
                        # Only the composite node itself exists, no other File Output nodes
                        self.report({'WARNING'}, f"Composite node '{composite_node.name}' is set to path-linked but there are no other File Output nodes available. Please disable path linking as you only have one File Output node.")
                    else:
                        # The linked node was deleted or renamed
                        self.report({'WARNING'}, f"Composite node '{composite_node.name}' is linked to '{linked_node_name}' but this node was not found or is not a File Output node. The linked node may have been deleted or renamed. Please update the linked node selection.")
                    
                    logger.debug(f"Composite node {composite_node.name} linked node {linked_node_name} not found or not File Output")
                    return False
                
                # Check for circular dependency - if the linked node is also path-linked but has no base path
                if hasattr(linked_node, 'base_path'):
                    linked_base_path = linked_node.base_path
                    if not linked_base_path or linked_base_path.strip() == "":
                        # Check if the linked node is also path-linked (which would be a circular dependency)
                        linked_props = getattr(linked_node, 'shotput_data', None)
                        if (linked_props and 
                            hasattr(linked_props, 'path_linked') and 
                            linked_props.path_linked):
                            logger.debug(f"Composite node {composite_node.name} linked to {linked_node_name} which is path-linked but has no base path (circular dependency)")
                            # Show user-friendly warning
                            self.report({'WARNING'}, f"Composite node '{composite_node.name}' is linked to '{linked_node_name}' which is also path-linked but has no base path. This creates a circular dependency. Please set a base path for '{linked_node_name}' or disable its path linking.")
                            return False
            else:
                return False
        else:
            print(f"Shotput: Node {composite_node.name} is not path-linked")
            # Not path-linked, check if it has a valid root folder token
            root_token = getattr(node_props, 'root_folder_token', '')
            if not root_token or not root_token.strip():
                print(f"Shotput: Node {composite_node.name} has no root folder token and is not path-linked: '{root_token}'")
                logger.debug(f"Composite node {composite_node.name} has no root folder token and is not path-linked")
                return False
        
        print(f"Shotput: Node {composite_node.name} passed all validation checks")
        return True
    
    def _has_incoming_connections(self, node):
        """Check if a node has any incoming connections"""
        for input_socket in node.inputs:
            if input_socket.is_linked:
                return True
        return False
    
    def _update_scene_render_path(self, context, composite_node):
        """Update scene render filepath using composite node properties"""
        try:
            from ..utils.defaults import get_sequence_padding
            
            node_props = composite_node.shotput_data
            token_parser = TokenParser(node_props)
            
            # Get the actual pass name from the node properties
            pass_name = getattr(node_props, 'pass_name', 'composite')
            
            # For composite nodes, we need to handle path linking specially
            base_path = ""
            
            print(f"Shotput: Updating scene render path for composite node {composite_node.name}")
            
            # Check if this composite node is path-linked
            if hasattr(node_props, 'path_linked') and node_props.path_linked:
                # Get the linked node's base path
                linked_node_name = getattr(node_props, 'linked_node', '')
                
                # If linked_node is NONE, try to get it from backup custom property
                if not linked_node_name or linked_node_name == 'NONE':
                    if "shotput_linked_node_backup" in composite_node:
                        backup_name = composite_node["shotput_linked_node_backup"]
                        linked_node_name = backup_name
                    else:
                        # Last resort: find any Shotput File Output node, but prioritize by context
                        scene = context.scene
                        if scene and scene.node_tree:
                            candidate_nodes = []
                            for node in scene.node_tree.nodes:
                                if (node.type == 'OUTPUT_FILE' and 
                                    hasattr(node, 'shotput_data') and
                                    node.name.startswith('Shotput_')):
                                    candidate_nodes.append(node)
                            
                            # If we have candidates, prefer them in this order:
                            # 1. Core nodes (most common link target)
                            # 2. Any other Shotput nodes
                            if candidate_nodes:
                                # Try to find a Core node first
                                for node in candidate_nodes:
                                    if 'Core' in node.name:
                                        linked_node_name = node.name
                                        break
                                else:
                                    # If no Core node, use the first available
                                    linked_node_name = candidate_nodes[0].name
                
                if linked_node_name and linked_node_name != 'NONE':
                    scene = context.scene
                    if scene and scene.node_tree:
                        linked_node = scene.node_tree.nodes.get(linked_node_name)
                        if linked_node and hasattr(linked_node, 'base_path'):
                            # Check if the linked node has a valid base path
                            linked_base_path = linked_node.base_path
                            
                            # Validate that the linked node isn't also broken (path-linked with no base_path)
                            if not linked_base_path or linked_base_path.strip() == "":
                                # The linked node has no base path - check if it's also path-linked
                                linked_props = getattr(linked_node, 'shotput_data', None)
                                if (linked_props and 
                                    hasattr(linked_props, 'path_linked') and 
                                    linked_props.path_linked):
                                    # This is a circular dependency - the linked node is also path-linked but has no base
                                    logger.warning(f"Linked node {linked_node_name} is path-linked but has no base path - cannot use for composite render path")
                                    self.report({'WARNING'}, f"Cannot update scene render path: Linked node '{linked_node_name}' is path-linked but has no base path (circular dependency). Please set a base path for '{linked_node_name}' or disable its path linking.")
                                    return
                                else:
                                    # Linked node is a normal Shotput node — try to rebuild from its tokens.
                                    # This handles the case where the user manually cleared the node's
                                    # base_path: we should always be able to resolve it from tokens.
                                    linked_props = getattr(linked_node, 'shotput_data', None)
                                    linked_root_token = getattr(linked_props, 'root_folder_token', '') if linked_props else ''
                                    if linked_root_token:
                                        from ..utils.token_parser import TokenParser as _LinkedTP
                                        _linked_parser = _LinkedTP(linked_props)
                                        linked_base_path = _linked_parser.parse_token(linked_root_token)
                                        logger.info(f"Rebuilt linked node '{linked_node_name}' path from tokens: '{linked_base_path}'")
                                    if not linked_base_path:
                                        logger.warning(f"Linked node {linked_node_name} has no base path and no resolvable tokens")
                                        self.report({'WARNING'}, f"Cannot update scene render path: Linked node '{linked_node_name}' has no base path and no path tokens are configured.")
                                        return
                            
                            # Start with the linked node's base path
                            base_path = linked_base_path
                            
                            # Special handling for multilayer EXR nodes
                            # These have sequence padding (####) in the base_path which needs to be extracted
                            from ..utils.defaults import get_sequence_padding
                            sequence_padding = get_sequence_padding()
                            
                            # Check if the linked node is multilayer EXR format
                            is_linked_multilayer_exr = False
                            if hasattr(linked_node, 'format') and linked_node.format.file_format == 'OPEN_EXR_MULTILAYER':
                                is_linked_multilayer_exr = True
                                print(f"Shotput: Linked node is multilayer EXR format")
                            
                            # If linked node is multilayer EXR, its base_path includes sequence padding and extension
                            # Example: "C:/path/to/file.####" or "C:/path/to/file.####.exr"
                            # We need to extract just the directory path
                            if is_linked_multilayer_exr and sequence_padding in base_path:
                                from pathlib import Path
                                # The base path for multilayer EXR is like: "path/filename.####"
                                # We need to extract the directory only
                                path_obj = Path(base_path)
                                
                                # Check if the path has the sequence padding in the filename
                                if sequence_padding in path_obj.name:
                                    # Extract directory - the parent of the path with ####
                                    base_directory = str(path_obj.parent)
                                    print(f"Shotput: Extracted base directory from multilayer EXR path: '{base_path}' -> '{base_directory}'")
                                    base_path = base_directory
                            
                            # If there's an append path in root_folder_token, add it
                            append_path = getattr(node_props, 'root_folder_token', '')
                            if append_path and append_path.strip():
                                # Parse the append path with tokens
                                parsed_append = token_parser.parse_filename_only(append_path, passname=pass_name)
                                if parsed_append:
                                    # Use Path to properly combine paths
                                    from pathlib import Path
                                    base_path = str(Path(base_path) / parsed_append)
                            
                            logger.info(f"Using linked base path: {base_path}")
                        else:
                            logger.warning(f"Linked node {linked_node_name} found but has no base_path")
                    else:
                        print(f"Shotput: Warning - no scene or node tree available")
                else:
                    print(f"Shotput: Warning - no valid linked node name after checking backup")
            else:
                print(f"Shotput: Composite node is not path-linked")
            
            # If not path-linked or linking failed, parse normally
            if not base_path:
                print(f"Shotput: Falling back to normal token parsing")
                base_path = token_parser.parse_token(node_props.root_folder_token, passname=pass_name)
                print(f"Shotput: Normal parsed base path: {base_path}")
            
            # Parse the file name token (always use filename-only logic for scene render path)
            filename = token_parser.parse_filename_only(node_props.file_name_token, passname=pass_name)
            
            # Get the actual Blender scene render format (not Shotput UI format)
            scene = context.scene
            render_format = scene.render.image_settings.file_format
            
            print(f"Shotput: Detected scene render format: {render_format}")
            
            # Determine if this is a movie format (no sequence padding) or image sequence (needs padding)
            movie_formats = {
                'FFMPEG',      # Includes MP4, MOV, AVI, etc.
                'AVI_JPEG',
                'AVI_RAW',
            }
            
            is_movie_format = render_format in movie_formats
            print(f"Shotput: Is movie format: {is_movie_format}")
            
            # Get appropriate file extension based on Blender's format
            if render_format == 'FFMPEG':
                # For FFMPEG, check the container format
                ffmpeg_format = scene.render.ffmpeg.format
                print(f"Shotput: FFMPEG container format: {ffmpeg_format}")
                ffmpeg_extensions = {
                    'MPEG4': 'mp4',
                    'QUICKTIME': 'mov',
                    'AVI': 'avi',
                    'MKV': 'mkv',
                    'WEBM': 'webm',
                    'OGG': 'ogv',
                }
                file_extension = ffmpeg_extensions.get(ffmpeg_format, 'mp4')
                print(f"Shotput: Using extension: .{file_extension}")
            elif render_format == 'AVI_JPEG':
                file_extension = 'avi'
            elif render_format == 'AVI_RAW':
                file_extension = 'avi'
            elif render_format == 'PNG':
                file_extension = 'png'
            elif render_format in ['JPEG', 'JPEG2000']:
                file_extension = 'jpg'
            elif render_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                file_extension = 'exr'
            elif render_format == 'TIFF':
                file_extension = 'tif'
            elif render_format == 'TARGA':
                file_extension = 'tga'
            elif render_format == 'TARGA_RAW':
                file_extension = 'tga'
            elif render_format == 'BMP':
                file_extension = 'bmp'
            elif render_format == 'HDR':
                file_extension = 'hdr'
            elif render_format == 'IRIS':
                file_extension = 'sgi'
            elif render_format == 'DPX':
                file_extension = 'dpx'
            elif render_format == 'CINEON':
                file_extension = 'cin'
            else:
                # Fallback to PNG for unknown formats
                file_extension = 'png'
                logger.warning(f"Unknown render format '{render_format}', defaulting to .png extension")
            
            # Build the full path based on format type
            # Use Path for proper OS-specific separators
            from pathlib import Path
            base_path_obj = Path(base_path)
            
            if is_movie_format:
                # Movie formats: no sequence padding
                full_path = str(base_path_obj / f"{filename}.{file_extension}")
                logger.info(f"Using movie format '{render_format}' - no sequence padding")
            else:
                # Image sequence formats: include sequence padding
                sequence_padding = get_sequence_padding()
                full_path = str(base_path_obj / f"{filename}.{sequence_padding}.{file_extension}")
                logger.info(f"Using image sequence format '{render_format}' - with padding {sequence_padding}")
            
            # Update scene render settings
            context.scene.render.filepath = full_path
            
            logger.info(f"Updated scene render filepath to: {full_path}")
            
        except Exception as e:
            logger.error(f"Error updating scene render path: {e}")
            raise
    
    def _update_node_version(self, node, context):
        """Update the version for a specific node"""
        try:
            node_props = node.shotput_data
            
            # Check if this node is path-linked
            if self._is_path_linked(node_props):
                return self._update_linked_node_version(node, node_props, context)
            else:
                return self._update_normal_node_version(node, node_props, context)
            
        except Exception as e:
            logger.error(f"Error updating node {node.name}: {e}")
            return False
    
    def _is_path_linked(self, node_props):
        """
        Check if a node is path-linked to another node.
        
        Note: Path linking is NOT used in AYON mode, as AYON provides its own 
        structured path system. If AYON mode is enabled, this returns False 
        regardless of path_linked property state.
        """
        # Check if AYON mode is enabled for this node (takes precedence over path linking)
        if hasattr(node_props, 'use_ayon_output_style') and node_props.use_ayon_output_style:
            # AYON mode is enabled - ignore path linking
            return False
        
        # Standard path linking check
        return (hasattr(node_props, 'path_linked') and 
                getattr(node_props, 'path_linked', False) and
                hasattr(node_props, 'linked_node') and
                getattr(node_props, 'linked_node', '') not in ['', 'NONE'])
    
    def _update_linked_node_version(self, node, node_props, context):
        """Update version for a path-linked node - uses linked node's version"""
        try:
            # Get the linked node
            linked_node_name = getattr(node_props, 'linked_node', '')
            scene = context.scene
            if not scene or not scene.node_tree:
                logger.error("No scene or node tree available")
                return False
            
            linked_node = scene.node_tree.nodes.get(linked_node_name)
            if not linked_node or linked_node.type != 'OUTPUT_FILE':
                logger.error(f"Linked node '{linked_node_name}' not found or not a File Output node")
                return False
            
            # Get linked node's version
            linked_props = linked_node.shotput_data
            linked_version = getattr(linked_props, 'version', VersionUtils.versionDefault)
            
            # Update this node's version to match
            node_props.version = linked_version
            
            # For File Output nodes, update base path using linked path + append path
            if node.type == 'OUTPUT_FILE':
                token_parser = TokenParser(node_props)
                
                # Use the token parser's linked path logic to get the correct base path
                root_token = getattr(node_props, 'root_folder_token', '')
                new_base_path = token_parser._parse_linked_path(root_token)
                
                node.base_path = new_base_path
                logger.debug(f"Updated linked node {node.name} base path: {new_base_path}")
                
                # For linked nodes, only update file slot filenames (not full paths)
                # since the base path is already set correctly from the linked node
                self._update_file_slots_filenames_only(node, node_props, token_parser, linked_version, context)
            
            logger.info(f"Updated linked node {node.name} to version {linked_version} (linked to {linked_node_name})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating linked node {node.name}: {e}")
            return False
    
    def _update_normal_node_version(self, node, node_props, context):
        """Update version for a normal (non-linked) node"""
        try:
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
                self._update_file_slots(node, node_props, token_parser, new_version, context)
            
            logger.info(f"Updated node {node.name} to version {new_version}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating normal node {node.name}: {e}")
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
    
    def _update_node_format(self, node, context):
        """
        Update the node's file format to match the current UI setting.
        
        Args:
            node: The File Output node to update
            context: The Blender context
            
        Returns:
            The updated file format
        """
        pass_type = self._get_pass_type_from_node(node)
        scene = context.scene
        if hasattr(scene, 'shotput'):
            ui_format = scene.shotput.output_format
            # Get the correct format for this pass type
            old_format = node.format.file_format
            correct_format = get_file_format_for_pass_type(pass_type, ui_format)
            # Update the node's format to match
            if old_format != correct_format:
                node.format.file_format = correct_format
                logger.debug(f"Updated node {node.name} format from {old_format} to {correct_format} (pass_type={pass_type}, ui_format={ui_format})")
            return correct_format
        return node.format.file_format
    
    def _update_file_slots(self, node, node_props, token_parser, new_version, context):
        """Update file slot paths with new version"""
        try:
            from ..utils.defaults import get_sequence_padding
            
            file_token = node_props.file_name_token
            if not file_token:
                return
            
            # Get sequence padding from preferences
            sequence_padding = get_sequence_padding()
            
            # Update node format to match UI setting
            # Defensive: capture base_path before format change in case Blender resets it
            _base_path_before_format = node.base_path
            # Note: we do NOT force the format here. If the user manually changed the node's
            # format in the compositor, that choice is respected. Format is only set at
            # creation time by the Create Passes operators.

            # Check the actual node format to determine path logic
            node_format = node.format.file_format
            logger.debug(f"Updating node {node.name} with format {node_format}")
            
            if node_format == 'OPEN_EXR_MULTILAYER':
                # EXR Multilayer: Update base_path with special handling for AYON/complex tokens
                pass_type = node_props.pass_type if hasattr(node_props, 'pass_type') else None
                
                # Parse filename with new version - ALWAYS use normal path logic for filenames
                if pass_type:
                    temp_token = file_token.replace('{passname}', pass_type)
                    new_filename = self._reconstruct_filename_with_version(temp_token, new_version, token_parser)
                else:
                    new_filename = self._reconstruct_filename_with_version(file_token, new_version, token_parser)
                
                # Parse root folder with new version - CRITICAL: Ensure directory-only for multichannel EXR
                # Note: For multichannel EXR, root_token may contain complex AYON tokens like 
                # "{workdir}/{subpath}/{blendfile}" which should resolve to a directory, then we append filename
                root_token = node_props.root_folder_token
                if root_token:
                    # First parse the root token with new version
                    if pass_type:
                        temp_root_token = root_token.replace('{passname}', pass_type)
                        parsed_path = self._reconstruct_path_with_version(temp_root_token, new_version, token_parser)
                    else:
                        parsed_path = self._reconstruct_path_with_version(root_token, new_version, token_parser)
                    
                    # For multichannel EXR: Extract directory from parsed path (remove potential filename)
                    # This matches the fix in token_parser.py _parse_linked_path()
                    from pathlib import Path
                    parsed_path_obj = Path(parsed_path)
                    
                    # Check if parsed path looks like it has a filename (has extension)
                    if parsed_path_obj.suffix and '.' in parsed_path_obj.name:
                        # Path includes filename, extract directory
                        base_dir = parsed_path_obj.parent
                        logger.debug(f"Multichannel EXR: Extracted directory '{base_dir}' from path '{parsed_path}'")
                    else:
                        # Path is already a directory
                        base_dir = parsed_path_obj
                    
                    # Determine if we need passname subdirectory.
                    # Only add a subdirectory when the ENTIRE root_token is literally '{passname}'
                    # (the path-linked composite case: root_folder_token = "{passname}").
                    # When {passname} is embedded in a longer segment like
                    # {outputlayer}_{passname}_{variant}/{version}, it is already
                    # resolved into the directory name above — adding it again would
                    # duplicate the folder and produce a path mismatch vs creation.
                    if root_token.strip() == '{passname}' and pass_type:
                        base_dir = base_dir / pass_type
                        logger.debug(f"Multichannel EXR: Added passname subdirectory '{pass_type}'")
                    
                    # Build final base_path: directory + filename + padding + .exr
                    node.base_path = str(base_dir / f"{new_filename}.{sequence_padding}.exr")
                    logger.debug(f"Updated EXR multilayer base_path to: {node.base_path}")
                
                # For EXR multilayer, file slots should remain as channel names only
                # Don't modify slot paths as they contain channel names, not file paths
                
            else:
                # Single file formats (PNG/JPEG/EXR single): Update individual slot paths
                # Use the node's actual format (not the scene default) to determine file extension
                # Map Blender's node format to file extension
                format_extensions = {
                    'PNG': 'png',
                    'JPEG': 'jpg', 
                    'JPEG2000': 'jp2',
                    'OPEN_EXR': 'exr',
                    'OPEN_EXR_MULTILAYER': 'exr',
                    'TIFF': 'tif',
                    'TARGA': 'tga',
                    'TARGA_RAW': 'tga',
                    'BMP': 'bmp',
                    'IRIS': 'rgb',
                    'RADHDR': 'hdr',
                    'CINEON': 'cin',
                    'DPX': 'dpx',
                    'DDS': 'dds',
                    'WEBP': 'webp'
                }
                file_extension = format_extensions.get(node_format, 'png')
                
                # Update base path for single file formats
                root_token = node_props.root_folder_token
                if root_token:
                    pass_type = node_props.pass_type if hasattr(node_props, 'pass_type') else None
                    if pass_type:
                        temp_root_token = root_token.replace('{passname}', pass_type)
                        new_base_path = self._reconstruct_path_with_version(temp_root_token, new_version, token_parser)
                    else:
                        new_base_path = self._reconstruct_path_with_version(root_token, new_version, token_parser)
                    
                    node.base_path = new_base_path
                
                # Update each file slot path
                for i, slot in enumerate(node.file_slots):
                    # Get the pass name from stored passes if available
                    pass_name = None
                    if i < len(node_props.stored_passes):
                        pass_name = node_props.stored_passes[i].name
                    
                    # Parse filename with new version - ALWAYS use normal path logic for filenames
                    if pass_name:
                        # Create a temporary token string with the pass name override
                        temp_token = file_token.replace('{passname}', pass_name)
                        new_filename = self._reconstruct_filename_with_version(temp_token, new_version, token_parser)
                    else:
                        new_filename = self._reconstruct_filename_with_version(file_token, new_version, token_parser)
                    
                    # Create complete path with sequence padding and extension
                    slot.path = f"{new_filename}.{sequence_padding}.{file_extension}"
                
        except Exception as e:
            logger.error(f"Error updating file slots: {e}")
    
    def _update_file_slots_filenames_only(self, node, node_props, token_parser, new_version, context):
        """Update file slot paths with just filenames (for linked nodes)"""
        try:
            from ..utils.defaults import get_sequence_padding
            
            file_token = node_props.file_name_token
            if not file_token:
                return
            
            # Get sequence padding from preferences
            sequence_padding = get_sequence_padding()
            
            # Note: we do NOT force the format here. If the user manually changed the node's
            # format in the compositor, that choice is respected.

            # Check the actual node format to determine path logic
            node_format = node.format.file_format
            logger.debug(f"Updating linked node {node.name} filenames only with format {node_format}")
            
            if node_format == 'OPEN_EXR_MULTILAYER':
                # EXR Multilayer: Base path should already be set correctly
                # File slots remain as channel names, so nothing to update
                print(f"Shotput: EXR multilayer linked node - base path already set, slots are channel names")
                
            else:
                # Single file formats (PNG/JPEG/EXR single): Update individual slot filenames only
                # Use the node's actual format (not the scene default) to determine file extension
                # Map Blender's node format to file extension
                format_extensions = {
                    'PNG': 'png',
                    'JPEG': 'jpg', 
                    'JPEG2000': 'jp2',
                    'OPEN_EXR': 'exr',
                    'OPEN_EXR_MULTILAYER': 'exr',
                    'TIFF': 'tif',
                    'TARGA': 'tga',
                    'TARGA_RAW': 'tga',
                    'BMP': 'bmp',
                    'IRIS': 'rgb',
                    'RADHDR': 'hdr',
                    'CINEON': 'cin',
                    'DPX': 'dpx',
                    'DDS': 'dds',
                    'WEBP': 'webp'
                }
                file_extension = format_extensions.get(node_format, 'png')
                
                # Update each file slot path with just filename (no full path)
                for i, slot in enumerate(node.file_slots):
                    # Get the pass name from stored passes if available
                    pass_name = None
                    if i < len(node_props.stored_passes):
                        pass_name = node_props.stored_passes[i].name
                    
                    # Parse filename with new version - ALWAYS use normal path logic for filenames
                    if pass_name:
                        # Create a temporary token string with the pass name override
                        temp_token = file_token.replace('{passname}', pass_name)
                        new_filename = self._reconstruct_filename_with_version(temp_token, new_version, token_parser)
                    else:
                        new_filename = self._reconstruct_filename_with_version(file_token, new_version, token_parser)
                    
                    # Create filename-only path with sequence padding and extension (no base path)
                    slot.path = f"{new_filename}.{sequence_padding}.{file_extension}"
                    logger.debug(f"Updated linked node slot {i} to filename: {slot.path}")
                
        except Exception as e:
            logger.error(f"Error updating file slot filenames: {e}")
    
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
    
    def _get_pass_type_from_node(self, node):
        """
        Determine the pass type (core, aov, or data) from a node.
        
        Args:
            node: The File Output node to analyze
            
        Returns:
            String: 'core', 'aov', or 'data'
        """
        from ..utils.pass_mapping import pass_mapping
        
        # Check node name for pass type indicators
        node_name_lower = node.name.lower()
        
        # Data nodes are typically named "Shotput_Data" or contain "data"
        if 'data' in node_name_lower:
            return 'data'
        
        # AOV nodes are typically named "Shotput_AOV" or contain "aov"
        if 'aov' in node_name_lower:
            return 'aov'
        
        # Check if node has shotput_data property with pass_name
        if hasattr(node, 'shotput_data'):
            node_props = node.shotput_data
            pass_name = getattr(node_props, 'pass_name', '').lower()
            
            # Check if this pass name is in the data passes list
            all_data_passes = pass_mapping.get_all_data_passes()
            if any(data_pass in pass_name for data_pass in all_data_passes):
                return 'data'
            
            # Check for aov in pass_name
            if 'aov' in pass_name:
                return 'aov'
        
        # Default to core for all other cases
        return 'core'
    
    def _reconstruct_filename_with_version(self, token_string, new_version, token_parser):
        """
        Reconstruct a filename with the new version, always using filename-only logic.
        
        Args:
            token_string: Original token string with {version} placeholder
            new_version: New version string (e.g., 'v002')
            token_parser: TokenParser instance for resolving other tokens
            
        Returns:
            Fully resolved filename with the new version (filename only, no paths)
        """
        if '{version}' not in token_string:
            # No version token, just parse as filename-only
            return token_parser.parse_filename_only(token_string)
        
        # Split at version token to validate structure
        version_parts = token_string.split('{version}')
        if len(version_parts) != 2:
            logger.warning(f"Invalid version token structure: {token_string}")
            return token_parser.parse_filename_only(token_string)
        
        # Create a temporary token string with the version replaced
        temp_token_string = token_string.replace('{version}', new_version)
        
        # Use filename-only parsing that won't trigger linked path resolution
        resolved_filename = token_parser.parse_filename_only(temp_token_string, version=new_version)
        
        logger.debug(f"Reconstructed filename: {token_string} -> {resolved_filename}")
        return resolved_filename
    
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
        return context.window_manager.invoke_popup(self, width=750)
    
    def draw(self, context):
        layout = self.layout
        
        icon_help_token = custom_icons.get_icon_id_or_fallback('help')
        layout.label(text="Shotput Token Reference", **icon_help_token)
        layout.separator()
        
        # Create a dummy props object for getting token values
        class DummyProps:
            def __init__(self):
                # Use scene properties if available, otherwise defaults
                scene = context.scene
                shotput_props = getattr(scene, 'shotput', None) if scene else None
                
                self.output_layer = getattr(shotput_props, 'output_layer', None) if shotput_props else None
                if not self.output_layer:
                    self.output_layer = getattr(context, 'view_layer', None).name if hasattr(context, 'view_layer') and context.view_layer else "RenderLayer"
                
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
            icon_file_folder_help = custom_icons.get_icon_id_or_fallback('file_folder')
            box.label(text="Core Shotput Tokens", **icon_file_folder_help)
            
            # Dynamic descriptions based on environment
            import os
            workdir_desc = "AYON work directory" if os.getenv("AYON_PROJECT_NAME") else "Current Blender directory"
            
            core_tokens = [
                ('workdir', workdir_desc),
                ('subpath', 'Additional folder path from preferences'),
                ('outputlayer', 'The name of the current output collection for output'),
                ('passname', 'Pass name (Taken from the output channel name)'),
                ('variant', 'Variant Description (Can be any custom text)'),
                ('version', 'Version number'),
            ]
            
            icon_dot_help = custom_icons.get_icon_id_or_fallback('dot')
            for token, desc in core_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.25)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.25)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
            # AYON-specific tokens with live values
            box = col.box()
            icon_ayon = custom_icons.get_icon_id_or_fallback('ayon')
            box.label(text="AYON Integration Tokens", **icon_ayon)
            
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
                    split = row.split(factor=0.3)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.6)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.3)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.6)
                    split.label(text=desc)
                    split.label(text="→ (not available)")
            
            # Blender-specific tokens with live values
            box = col.box()
            icon_blender_help = custom_icons.get_icon_id_or_fallback('blender')
            box.label(text="Blender Context Tokens", **icon_blender_help)
            
            blender_tokens = [
                ('blendfile', 'Current .blend filename'),
                ('scenename', 'Active scene name'),
                ('camera', 'Active camera name'),
            ]
            
            for token, desc in blender_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.3)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.6)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.15)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.55)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
            # Date/time tokens with live values
            box = col.box()
            icon_time_help = custom_icons.get_icon_id_or_fallback('time')
            box.label(text="Date/Time Tokens", **icon_time_help)
            
            datetime_tokens = [
                ('date', 'Current date (DD-MM-YY)'),
                ('time', 'Current time (HH-MM-SS)'),
            ]
            
            for token, desc in datetime_tokens:
                try:
                    value = parser._resolve_token(token)
                    row = box.row()
                    split = row.split(factor=0.3)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.6)
                    split.label(text=desc)
                    split.label(text=f"→ {value}")
                except Exception as e:
                    row = box.row()
                    split = row.split(factor=0.3)
                    split.label(text=f"{{{token}}}", **icon_dot_help)
                    split = split.split(factor=0.6)
                    split.label(text=desc)
                    split.label(text="→ (error)")
            
        except Exception as e:
            # Fallback to static examples if token parsing fails
            icon_error_fallback = custom_icons.get_icon_id_or_fallback('error')
            layout.label(text="Error loading dynamic values - showing static examples", **icon_error_fallback)
            layout.separator()
            
            box = layout.box()
            icon_file_folder_static = custom_icons.get_icon_id_or_fallback('file_folder')
            box.label(text="Static Token Examples", **icon_file_folder_static)
            
            static_examples = [
                ('workdir', 'Current Blender file directory', 'C:/Projects/MyProject'),
                ('blendfile', 'Current .blend filename', 'scene_001'),
                ('scenename', 'Active scene name', context.scene.name if context.scene else 'Scene'),
                ('date', 'Current date', '11-08-25'),
                ('time', 'Current time', '14-30-45'),
            ]
            
            icon_dot_static = custom_icons.get_icon_id_or_fallback('dot')
            for token, desc, example in static_examples:
                row = box.row()
                split = row.split(factor=0.15)
                split.label(text=f"{{{token}}}", **icon_dot_static)
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
                self.output_layer = getattr(props, 'output_layer', None) or "RenderLayer"
                self.variant = getattr(props, 'variant', None) or "Main"
                self.root_folder_token = getattr(props, 'root_folder_token', None) or "{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}"
                self.file_name_token = getattr(props, 'file_name_token', None) or "{outputlayer}_{passname}_{variant}"
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
        
        icon_preview = custom_icons.get_icon_id_or_fallback('preview_range')
        layout.label(text="Path Preview", **icon_preview)
        layout.separator()
        
        # Core passes
        box = layout.box()
        icon_file_folder_preview = custom_icons.get_icon_id_or_fallback('file_folder')
        box.label(text="Core Passes:", **icon_file_folder_preview)
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.core_path)
        
        # AOV passes
        box = layout.box()
        box.label(text="AOV Passes:", **icon_file_folder_preview)
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.aov_path)
        
        # Data passes
        box = layout.box()
        box.label(text="Data Passes:", **icon_file_folder_preview)
        row = box.row()
        row.scale_y = 0.8
        row.label(text=self.data_path)


class OT_Load_Preset(bpy.types.Operator):
    bl_idname = "shotput.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load Shotput preset from JSON file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to the preset file",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        try:
            import json
            from ..utils.defaults import is_valid_shotput_preset, migrate_legacy_tokens
            
            # Load JSON file
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate preset structure
            if not is_valid_shotput_preset(data):
                self.report({'ERROR'}, "Invalid Shotput preset file structure")
                return {'CANCELLED'}
            
            # Migrate legacy tokens
            if 'root_folder_token' in data:
                data['root_folder_token'] = migrate_legacy_tokens(data['root_folder_token'])
            if 'file_name_token' in data:
                data['file_name_token'] = migrate_legacy_tokens(data['file_name_token'])
            
            # Apply preset to scene properties
            scene = context.scene
            if not hasattr(scene, 'shotput'):
                self.report({'ERROR'}, "Shotput properties not found")
                return {'CANCELLED'}
            
            props = scene.shotput
            
            # Clear existing pass collections
            props.core_passes.clear()
            props.aov_passes.clear()
            
            # Load core passes
            for pass_name in data.get("core_passes", []):
                item = props.core_passes.add()
                item.name = pass_name
            
            # Load AOV passes
            for pass_name in data.get("aovs", []):
                item = props.aov_passes.add()
                item.name = pass_name
            
            # Load other properties
            if "output_layer" in data:
                props.output_layer = data["output_layer"]
            if "variant" in data:
                props.variant = data["variant"]
            if "core_override" in data:
                props.core_override = data["core_override"]
            if "aov_override" in data:
                props.aov_override = data["aov_override"]
            if "root_folder_token" in data:
                props.root_folder_token = data["root_folder_token"]
            if "file_name_token" in data:
                props.file_name_token = data["file_name_token"]
            if "default_file_format" in data:
                props.output_format = data["default_file_format"]
            
            # Load data pass boolean properties
            data_passes = data.get("data_passes", [])
            props.z = "z" in data_passes
            props.mist = "mist" in data_passes
            props.normal = "normal" in data_passes
            props.vector = "vector" in data_passes
            props.position = "position" in data_passes
            props.occlusion = "occlusion" in data_passes
            props.crypto_object = "crypto_object" in data_passes
            props.crypto_material = "crypto_material" in data_passes
            props.crypto_asset = "crypto_asset" in data_passes
            
            # Load create_composite_from_core if present (new property)
            if "create_composite_from_core" in data:
                props.create_composite_from_core = data["create_composite_from_core"]
            
            # Load UI expansion states if present (optional)
            if "expand_core_ui" in data:
                props.expand_core_ui = data["expand_core_ui"]
            if "expand_aov_ui" in data:
                props.expand_aov_ui = data["expand_aov_ui"]
            if "expand_data_ui" in data:
                props.expand_data_ui = data["expand_data_ui"]
            
            # Note: file_format_overrides and data_format_settings are loaded automatically
            # by defaults.py when creating nodes - they don't need to be stored on scene props
            
            preset_name = Path(self.filepath).stem
            self.report({'INFO'}, f"Loaded preset '{preset_name}' successfully")
            logger.info(f"Loaded Shotput preset from: {self.filepath}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {str(e)}")
            logger.error(f"Error loading preset: {e}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OT_Save_Preset(bpy.types.Operator):
    bl_idname = "shotput.save_preset"
    bl_label = "Save Preset"
    bl_description = "Save current Shotput settings as JSON preset file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to save the preset file",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        try:
            import json
            from pathlib import Path
            
            scene = context.scene
            if not hasattr(scene, 'shotput'):
                self.report({'ERROR'}, "Shotput properties not found")
                return {'CANCELLED'}
            
            props = scene.shotput
            
            # Build preset data structure
            preset_data = {
                "_info": f"Shotput preset created from Blender scene: {scene.name}",
                "bl_version": __version__,
                "core_passes": [item.name for item in props.core_passes],
                "aovs": [item.name for item in props.aov_passes],
                "data_passes": [],
                "output_layer": props.output_layer,
                "variant": props.variant,
                "core_override": props.core_override,
                "aov_override": props.aov_override,
                "root_folder_token": props.root_folder_token,
                "file_name_token": props.file_name_token,
                "default_file_format": props.output_format,
                "file_format_overrides": {
                    "core": "UI",
                    "aov": "UI",
                    "data": "OPEN_EXR_MULTILAYER"
                },
                "data_format_settings": {
                    "color_depth": "32",
                    "exr_codec": "ZIP"
                },
                "create_composite_from_core": props.create_composite_from_core,
                "expand_core_ui": props.expand_core_ui,
                "expand_aov_ui": props.expand_aov_ui,
                "expand_data_ui": props.expand_data_ui
            }
            
            # Add data passes based on boolean properties
            data_pass_mapping = {
                "z": props.z,
                "mist": props.mist,
                "normal": props.normal,
                "vector": props.vector,
                "position": props.position,
                "occlusion": props.occlusion,
                "crypto_object": props.crypto_object,
                "crypto_material": props.crypto_material,
                "crypto_asset": props.crypto_asset
            }
            
            for pass_name, enabled in data_pass_mapping.items():
                if enabled:
                    preset_data["data_passes"].append(pass_name)
            
            # Ensure the file has .json extension
            filepath = Path(self.filepath)
            if filepath.suffix.lower() != '.json':
                filepath = filepath.with_suffix('.json')
            
            # Write JSON file with nice formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            preset_name = filepath.stem
            self.report({'INFO'}, f"Saved preset '{preset_name}' successfully")
            logger.info(f"Saved Shotput preset to: {filepath}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save preset: {str(e)}")
            logger.error(f"Error saving preset: {e}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        # Set default filename based on output layer and variant
        scene = context.scene
        if hasattr(scene, 'shotput'):
            props = scene.shotput
            output_layer = props.output_layer.lower() if props.output_layer else "default"
            variant = props.variant.lower() if props.variant else "base"
            # Replace any spaces or special characters with underscores for filename safety
            output_layer = "".join(c if c.isalnum() else "_" for c in output_layer)
            variant = "".join(c if c.isalnum() else "_" for c in variant)
            self.filepath = f"shotput_preset_{output_layer}_{variant}.json"
        else:
            # Fallback to timestamp if properties not available
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filepath = f"shotput_preset_{timestamp}.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OT_Load_Preset_From_Env(bpy.types.Operator):
    bl_idname = "shotput.load_preset_from_env"
    bl_label = "Load Preset from Environment Path"
    bl_description = "Load a preset from the SHOTPUT_PRESET_PATH directory"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_file: bpy.props.StringProperty(
        name="Preset File",
        description="Name of the preset file to load"
    )
    
    def execute(self, context):
        """Load the specified preset file"""
        env_path = os.environ.get('SHOTPUT_PRESET_PATH')
        if not env_path:
            self.report({'ERROR'}, "SHOTPUT_PRESET_PATH environment variable is not set")
            return {'CANCELLED'}
        
        preset_path = Path(env_path)
        if preset_path.is_file():
            # If env path is a file, use that directory
            preset_path = preset_path.parent
        
        full_path = preset_path / self.preset_file
        
        if not full_path.exists():
            self.report({'ERROR'}, f"Preset file not found: {full_path}")
            return {'CANCELLED'}
        
        try:
            import json
            with open(full_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # Validate preset structure
            required_keys = ["core_passes", "aovs", "data_passes"]
            if not all(key in preset_data for key in required_keys):
                self.report({'ERROR'}, f"Invalid preset file format. Missing required keys.")
                return {'CANCELLED'}
            
            # Apply the preset using the same logic as initialize_default_passes
            scene = context.scene
            if hasattr(scene, 'shotput'):
                props = scene.shotput
                
                # Clear existing collections
                props.core_passes.clear()
                props.aov_passes.clear()
                
                # Add core passes
                for pass_name in preset_data.get("core_passes", []):
                    item = props.core_passes.add()
                    item.name = pass_name
                
                # Add AOV passes
                for pass_name in preset_data.get("aovs", []):
                    item = props.aov_passes.add()
                    item.name = pass_name
                
                # Set data pass boolean properties from JSON array
                if "data_passes" in preset_data and isinstance(preset_data["data_passes"], list):
                    # Reset all data passes to False first
                    data_pass_properties = [
                        'z', 'mist', 'normal', 'vector', 'position', 'occlusion',
                        'volume_direct', 'volume_indirect',
                        'crypto_object', 'crypto_material', 'crypto_asset'
                    ]
                    for prop_name in data_pass_properties:
                        if hasattr(props, prop_name):
                            setattr(props, prop_name, False)
                    
                    # Enable data passes directly by property name from JSON
                    for prop_name in preset_data["data_passes"]:
                        if hasattr(props, prop_name):
                            setattr(props, prop_name, True)
                
                # Set default scene properties
                if "output_layer" in preset_data:
                    props.output_layer = preset_data["output_layer"]
                if "variant" in preset_data:
                    props.variant = preset_data["variant"]
                if "core_override" in preset_data:
                    props.core_override = preset_data["core_override"]
                if "aov_override" in preset_data:
                    props.aov_override = preset_data["aov_override"]
                if "root_folder_token" in preset_data:
                    props.root_folder_token = preset_data["root_folder_token"]
                if "file_name_token" in preset_data:
                    props.file_name_token = preset_data["file_name_token"]
                if "default_file_format" in preset_data:
                    # Map to output_format enum with Blender's expected values
                    format_map = {
                        "PNG": "PNG",
                        "JPG": "JPEG", 
                        "JPEG": "JPEG",
                        "EXR": "OPEN_EXR",
                        "OPEN_EXR": "OPEN_EXR",
                        "EXR_MULTILAYER": "OPEN_EXR_MULTILAYER",
                        "OPEN_EXR_MULTILAYER": "OPEN_EXR_MULTILAYER"
                    }
                    format_value = format_map.get(preset_data["default_file_format"], "OPEN_EXR")
                    props.output_format = format_value
                
                self.report({'INFO'}, f"Loaded preset: {self.preset_file}")
                logger.info(f"Loaded preset from {full_path}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Shotput properties not found")
                return {'CANCELLED'}
                
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"Invalid JSON file: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error loading preset: {e}")
            logger.error(f"Error loading preset from {full_path}: {e}")
            return {'CANCELLED'}


class SHOTPUT_MT_PresetMenu(bpy.types.Menu):
    bl_label = "Load Preset from Environment"
    bl_idname = "SHOTPUT_MT_preset_menu"
    
    def draw(self, context):
        layout = self.layout
        
        env_path = os.environ.get('SHOTPUT_PRESET_PATH')
        
        if not env_path:
            icon_error_preset = custom_icons.get_icon_id_or_fallback('error')
            layout.label(text="SHOTPUT_PRESET_PATH not set", **icon_error_preset)
            return
        
        preset_path = Path(env_path)
        
        # Handle both file and directory paths
        if preset_path.is_file():
            # If env path points to a file, use its parent directory
            preset_path = preset_path.parent
        
        if not preset_path.exists() or not preset_path.is_dir():
            icon_error_invalid_preset = custom_icons.get_icon_id_or_fallback('error')
            layout.label(text="Invalid preset path", **icon_error_invalid_preset)
            layout.label(text=str(preset_path))
            return
        
        # Find all JSON files in the preset directory
        json_files = sorted(preset_path.glob('*.json'))
        
        if not json_files:
            icon_info_preset = custom_icons.get_icon_id_or_fallback('info')
            layout.label(text="No preset files found", **icon_info_preset)
            layout.label(text=f"in {preset_path.name}")
            return
        
        # Add operators for each preset file
        icon_preset_menu_preset = custom_icons.get_icon_id_or_fallback('preset')
        for json_file in json_files:
            op = layout.operator("shotput.load_preset_from_env", 
                               text=json_file.stem, 
                               **icon_preset_menu_preset)
            op.preset_file = json_file.name


classes = (
    OT_Update_Version,
    OT_Token_Help,
    OT_Preview_Paths,
    OT_Load_Preset,
    OT_Save_Preset,
    OT_Load_Preset_From_Env,
    SHOTPUT_MT_PresetMenu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
