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
            mode = "selected" if len(target_nodes) < self._count_all_shotput_nodes(tree) else "all"
            self.report({'INFO'}, f"Updated {updated_count} {mode} node(s) to next version")
            logger.info(f"Successfully updated {updated_count} Shotput nodes")
        else:
            self.report({'WARNING'}, "No nodes were updated")
            
        return {'FINISHED'}
    
    def _get_target_nodes(self, tree):
        """Get target nodes: selected Shotput nodes first, all Shotput nodes if none selected"""
        # First, check for selected Shotput nodes
        selected_shotput_nodes = []
        for node in tree.nodes:
            if node.select and self._is_shotput_node(node):
                selected_shotput_nodes.append(node)
        
        if selected_shotput_nodes:
            return selected_shotput_nodes
        
        # If no Shotput nodes are selected, get all Shotput nodes
        all_shotput_nodes = []
        for node in tree.nodes:
            if self._is_shotput_node(node):
                all_shotput_nodes.append(node)
        
        return all_shotput_nodes
    
    def _count_all_shotput_nodes(self, tree):
        """Count all Shotput nodes in the tree"""
        return sum(1 for node in tree.nodes if self._is_shotput_node(node))
    
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
            
            # Calculate next version (no specific version support in streamlined UX)
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


class OT_Token_Help(bpy.types.Operator):
    bl_idname = "shotput.token_help"
    bl_label = "Token Help"
    bl_description = "Show available tokens and their descriptions"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=700)
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Shotput Token Reference", icon='HELP')
        layout.separator()
        
        # Create a dummy parser to get token info
        class DummyProps:
            def __init__(self):
                self.render_layer = "Example"
                self.variant = "v001" 
                self.pass_name = "beauty"
        
        # Core Shotput tokens
        col = layout.column()
        box = col.box()
        box.label(text="Core Shotput Tokens", icon='FILE_FOLDER')
        
        core_tokens = [
            ('workdir', 'Current Blender file directory', 'C:/Projects/MyProject'),
            ('subpath', 'Subpath from preferences', 'blender/renders'),
            ('renderlayer', 'Render layer name', 'Beauty'),
            ('passname', 'Pass name (beauty, diffuse, etc.)', 'beauty'),
            ('variant', 'Version variant', 'v001'),
            ('version', 'Version number', 'v001'),
        ]
        
        for token, desc, example in core_tokens:
            row = box.row()
            split = row.split(factor=0.15)
            split.label(text=f"{{{token}}}", icon='DOT')
            split = split.split(factor=0.6)
            split.label(text=desc)
            split.label(text=f"→ {example}")
        
        # AYON-specific tokens
        box = col.box()
        box.label(text="AYON Integration Tokens", icon='NETWORK_DRIVE')
        
        ayon_tokens = [
            ('project', 'AYON project path', '/projects/MyProject'),
            ('projectname', 'AYON project name', 'MyProject'),
            ('task', 'Current task name', 'modeling'),
            ('folder', 'Folder path', 'assets/characters'),
            ('user', 'Current user', 'artist01'),
        ]
        
        for token, desc, example in ayon_tokens:
            row = box.row()
            split = row.split(factor=0.15)
            split.label(text=f"{{{token}}}", icon='DOT')
            split = split.split(factor=0.6)
            split.label(text=desc)
            split.label(text=f"→ {example}")
        
        # Blender-specific tokens
        box = col.box()
        box.label(text="Blender Context Tokens", icon='BLENDER')
        
        blender_tokens = [
            ('blend_name', 'Current .blend filename', 'scene_001'),
            ('scene_name', 'Active scene name', 'Scene'),
            ('frame', 'Current frame number', '001'),
            ('camera', 'Active camera name', 'Camera'),
        ]
        
        for token, desc, example in blender_tokens:
            row = box.row()
            split = row.split(factor=0.15)
            split.label(text=f"{{{token}}}", icon='DOT')
            split = split.split(factor=0.6)
            split.label(text=desc)
            split.label(text=f"→ {example}")
        
        # Date/time tokens
        box = col.box()
        box.label(text="Date/Time Tokens", icon='TIME')
        
        datetime_tokens = [
            ('date', 'Current date (YYYY-MM-DD)', '2025-08-08'),
            ('time', 'Current time (HH-MM-SS)', '14-30-45'),
        ]
        
        for token, desc, example in datetime_tokens:
            row = box.row()
            split = row.split(factor=0.15)
            split.label(text=f"{{{token}}}", icon='DOT')
            split = split.split(factor=0.6)
            split.label(text=desc)
            split.label(text=f"→ {example}")
        
        # Usage examples
        layout.separator()
        box = layout.box()
        box.label(text="Common Usage Examples", icon='HELP')
        
        examples = [
            "Root Folder: {workdir}/{subpath}/{renderlayer}_{variant}/{version}",
            "File Name: {renderlayer}_{passname}_{variant}",
            "AYON Path: {project}/{folder}/{task}/renders/{version}",
            "Dated Output: {workdir}/renders/{date}/{renderlayer}_{variant}",
        ]
        
        for example in examples:
            row = box.row()
            row.scale_y = 0.8
            row.label(text=f"• {example}")


class OT_Preview_Paths(bpy.types.Operator):
    bl_idname = "shotput.preview_paths"
    bl_label = "Preview Paths"
    bl_description = "Preview resolved paths for current Shotput settings"
    bl_options = {'REGISTER'}
    
    core_path: bpy.props.StringProperty(default="")
    aov_path: bpy.props.StringProperty(default="")
    data_path: bpy.props.StringProperty(default="")
    
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
