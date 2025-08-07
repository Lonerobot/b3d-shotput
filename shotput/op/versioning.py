import bpy
from pathlib import Path

from ..utils.log import LoggerFactory
from ..utils.token_parser import TokenParser
from ..utils.version_utils import VersionUtils

logger = LoggerFactory.logger_obj()


class OT_Update_Version(bpy.types.Operator):
    bl_idname = "shotput.update_version"
    bl_label = "Update Version"
    bl_description = "Update version numbers for Shotput file output nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Operator properties
    target_mode: bpy.props.EnumProperty(
        name="Target",
        description="Which nodes to update",
        items=[
            ('SELECTED', "Selected Node", "Update only the selected Shotput file output node"),
            ('ALL', "All Nodes", "Update all Shotput file output nodes in the scene"),
        ],
        default='SELECTED'
    )
    
    increment_version: bpy.props.BoolProperty(
        name="Increment Version",
        description="Increment to the next version number",
        default=True
    )
    
    specific_version: bpy.props.StringProperty(
        name="Specific Version",
        description="Set a specific version (e.g., v005)",
        default=""
    )
    
    def execute(self, context):
        logger.info(f"Update Version operator clicked - Mode: {self.target_mode}")
        
        # Get the compositor node tree
        if not context.scene.use_nodes:
            self.report({'ERROR'}, "Compositor nodes are not enabled")
            return {'CANCELLED'}
            
        tree = context.scene.node_tree
        if not tree:
            self.report({'ERROR'}, "No compositor node tree found")
            return {'CANCELLED'}
        
        # Find target nodes
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
            self.report({'INFO'}, f"Updated {updated_count} node(s)")
            logger.info(f"Successfully updated {updated_count} Shotput nodes")
        else:
            self.report({'WARNING'}, "No nodes were updated")
            
        return {'FINISHED'}
    
    def _get_target_nodes(self, tree):
        """Get the target nodes based on the selected mode"""
        target_nodes = []
        
        if self.target_mode == 'SELECTED':
            # Get selected node
            if tree.nodes.active and tree.nodes.active.select:
                if self._is_shotput_node(tree.nodes.active):
                    target_nodes.append(tree.nodes.active)
        else:  # ALL mode
            # Get all Shotput nodes
            for node in tree.nodes:
                if self._is_shotput_node(node):
                    target_nodes.append(node)
        
        return target_nodes
    
    def _is_shotput_node(self, node):
        """Check if a node is a Shotput file output node"""
        return (node.type == 'OUTPUT_FILE' and 
                hasattr(node, 'shotput_data') and 
                node.name.startswith('Shotput_'))
    
    def _update_node_version(self, node):
        """Update the version for a specific node"""
        try:
            node_props = node.shotput_data
            token_parser = TokenParser(node_props)
            
            # Determine the new version
            if self.specific_version and self.specific_version.strip():
                # Use specific version
                new_version = self.specific_version.strip()
                if not new_version.startswith('v'):
                    new_version = f"v{new_version}"
            else:
                # Calculate next version
                new_version = self._calculate_next_version(node_props, token_parser)
            
            # Update node properties
            node_props.version = new_version
            
            # Update the base path
            root_token = node_props.root_folder_token
            if root_token:
                new_base_path = token_parser.parse_token(root_token, version=new_version)
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
        """Calculate the next version number for a node"""
        try:
            # Parse the root folder token to get the base directory structure
            root_token = node_props.root_folder_token
            if not root_token:
                return VersionUtils.versionDefault
            
            # Parse without version to get the base path
            base_path_no_version = token_parser.parse_token(
                root_token.replace('/{version}', '').replace('{version}/', '').replace('{version}', '')
            )
            
            # Get next version for this path
            return token_parser.get_next_version_for_path(base_path_no_version)
            
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
                
                # Parse filename with new version
                if pass_name:
                    new_filename = token_parser.parse_token(
                        file_token, 
                        version=new_version,
                        passname=pass_name
                    )
                else:
                    new_filename = token_parser.parse_token(file_token, version=new_version)
                
                slot.path = f"{new_filename}_"
                
        except Exception as e:
            logger.error(f"Error updating file slots: {e}")
    
    def invoke(self, context, event):
        # Show dialog for user input
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "target_mode")
        layout.separator()
        
        layout.prop(self, "increment_version")
        
        if not self.increment_version:
            layout.prop(self, "specific_version")
        
        # Show preview of what will be updated
        tree = context.scene.node_tree
        if tree:
            target_nodes = self._get_target_nodes(tree)
            if target_nodes:
                box = layout.box()
                box.label(text=f"Will update {len(target_nodes)} node(s):")
                for node in target_nodes[:5]:  # Show max 5 nodes
                    box.label(text=f"  • {node.name}", icon='FILE_CACHE')
                if len(target_nodes) > 5:
                    box.label(text=f"  ... and {len(target_nodes) - 5} more")


class OT_Preview_Paths(bpy.types.Operator):
    bl_idname = "shotput.preview_paths"
    bl_label = "Preview Paths"
    bl_description = "Preview resolved paths for current Shotput settings"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Create a temporary token parser
        class TempNodeProps:
            def __init__(self, props):
                self.render_layer = props.render_layer
                self.variant = props.variant
                self.root_folder_token = props.root_folder_token
                self.file_name_token = props.file_name_token
                self.pass_name = "Preview"
        
        temp_props = TempNodeProps(shotput_props)
        parser = TokenParser(temp_props)
        
        # Show preview dialog
        self.preview_data = {
            'core': parser.resolve_full_output_path('core'),
            'aov': parser.resolve_full_output_path('aov'),
            'data': parser.resolve_full_output_path('data')
        }
        
        return context.window_manager.invoke_popup(self, width=600)
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Path Preview", icon='PREVIEW_RANGE')
        layout.separator()
        
        for pass_type, (base_path, filename) in self.preview_data.items():
            box = layout.box()
            box.label(text=f"{pass_type.upper()} Passes:", icon='FILE_FOLDER')
            
            # Base path
            row = box.row()
            row.label(text="Base Path:")
            row = box.row()
            row.scale_y = 0.8
            row.label(text=base_path)
            
            # Filename
            row = box.row()
            row.label(text="Filename:")
            row = box.row()
            row.scale_y = 0.8
            row.label(text=filename)
            
            # Full path
            row = box.row()
            row.label(text="Full Path:")
            row = box.row()
            row.scale_y = 0.8
            full_path = str(Path(base_path) / filename) if base_path and filename else "Invalid"
            row.label(text=full_path)
