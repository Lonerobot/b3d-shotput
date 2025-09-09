import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import bpy

from .log import LoggerFactory
from .path_utils import PathUtils
from .version_utils import VersionUtils
from .defaults import get_subpath_token_value

logger = LoggerFactory.logger_obj()


class TokenParser:
    """
    Token parsing system for Shotput file output paths.
    
    Converts tokens like {workdir}, {renderlayer}, {passname}, etc. into actual file paths
    for File Output nodes.
    
    Usage:
        parser = TokenParser(node_properties)
        root_path = parser.parse_token("{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}")
        filename = parser.parse_token("{renderlayer}_{passname}_{variant}")
    """
    
    def __init__(self, node_properties=None):
        """
        Initialize the token parser with node properties.
        
        Args:
            node_properties: ShotputFileOutputProperties from the current file output node
        """
        self.node_properties = node_properties
        self.path_utils = PathUtils()
        self._token_cache = {}
        
        # Initialize token resolvers
        self._init_token_resolvers()
    
    def _init_token_resolvers(self):
        """Initialize the token resolver functions"""
        self.token_resolvers = {
            # Core Shotput tokens
            'workdir': self._resolve_workdir,
            'subpath': self._resolve_subpath,
            'renderlayer': self._resolve_renderlayer,
            'passname': self._resolve_passname,
            'variant': self._resolve_variant,
            'version': self._resolve_version,
            
            # AYON-specific tokens via PathUtils
            'project': self._resolve_project,
            'projectname': self._resolve_project_name,
            'task': self._resolve_task,
            'folder': self._resolve_folder,
            'user': self._resolve_user,
            
            # Blender-specific tokens
            'blend_name': self._resolve_blend_name,
            'scene_name': self._resolve_scene_name,
            'frame': self._resolve_frame,
            'camera': self._resolve_camera,
            
            # Date/time tokens
            'date': self._resolve_date,
            'time': self._resolve_time,
        }
    
    def parse_token(self, token_string: str, **kwargs) -> str:
        """
        Parse a token string and return the resolved path.
        Handles path linking - if node is path-linked, uses linked node's path as base.
        
        Args:
            token_string: String containing tokens like "{workdir}/{renderlayer}"
            **kwargs: Additional token values to override defaults
            
        Returns:
            Resolved path string
        """
        if not token_string:
            return ""
            
        logger.debug(f"Parsing token string: {token_string}")
        
        # Check if this node is path-linked and handle accordingly
        if self._is_path_linked():
            return self._parse_linked_path(token_string, **kwargs)
        else:
            return self._parse_normal_path(token_string, **kwargs)
    
    def parse_filename_only(self, token_string: str, **kwargs) -> str:
        """
        Parse a token string as filename-only (never uses linked path logic).
        
        This method always resolves tokens without path components,
        regardless of whether the node is linked or not. Use this for
        file slot patterns that should only contain filenames.
        
        Args:
            token_string: String containing filename tokens like "{renderlayer}_{passname}_{variant}"
            **kwargs: Additional token values to override defaults
            
        Returns:
            Resolved filename string (no path separators)
        """
        if not token_string:
            return ""
            
        logger.debug(f"Parsing filename-only token string: {token_string}")
        return self._parse_normal_path(token_string, **kwargs)
    
    def _is_path_linked(self) -> bool:
        """Check if the current node is path-linked to another node"""
        if not self.node_properties:
            return False
        return (hasattr(self.node_properties, 'path_linked') and 
                getattr(self.node_properties, 'path_linked', False) and
                hasattr(self.node_properties, 'linked_node') and
                getattr(self.node_properties, 'linked_node', '') not in ['', 'NONE'])
    
    def _parse_linked_path(self, token_string: str, **kwargs) -> str:
        """
        Parse path for a linked node - uses linked node's base path + optional append path.
        
        Args:
            token_string: String to append to linked path (may contain tokens)
            **kwargs: Additional token values to override defaults
            
        Returns:
            Resolved path string combining linked base + appended path
        """
        # Clear cache to ensure fresh token resolution
        self.clear_cache()
        
        # Get the linked node's base path
        linked_base_path = self._get_linked_node_base_path()
        
        # If token_string is empty, just return the linked path
        if not token_string.strip():
            logger.debug(f"Using linked base path only: {linked_base_path}")
            return linked_base_path
        
        # Parse the token_string normally (it may contain tokens to resolve)
        appended_path = self._parse_normal_path(token_string, **kwargs)
        
        # Combine linked base path with appended path
        if appended_path:
            # Use Path to properly join paths
            combined_path = str(Path(linked_base_path) / appended_path)
            logger.debug(f"Combined linked path '{linked_base_path}' + '{appended_path}' = '{combined_path}'")
            return combined_path
        else:
            logger.debug(f"Using linked base path only: {linked_base_path}")
            return linked_base_path
    
    def _get_linked_node_base_path(self) -> str:
        """Get the base path from the linked File Output node"""
        if not self.node_properties:
            return ""
        
        linked_node_name = getattr(self.node_properties, 'linked_node', '')
        if not linked_node_name or linked_node_name == 'NONE':
            return ""
        
        # Get the linked node from the scene
        scene = bpy.context.scene
        if not scene or not scene.node_tree:
            logger.error("No scene or node tree available for linked path resolution")
            return ""
        
        linked_node = scene.node_tree.nodes.get(linked_node_name)
        if not linked_node or linked_node.type != 'OUTPUT_FILE':
            logger.error(f"Linked node '{linked_node_name}' not found or not a File Output node")
            return ""
        
        # Return the linked node's base_path
        base_path = getattr(linked_node, 'base_path', '')
        logger.debug(f"Retrieved linked node base path: {base_path}")
        return base_path
    
    def _parse_normal_path(self, token_string: str, **kwargs) -> str:
        """
        Parse a token string normally (non-linked mode).
        
        Args:
            token_string: String containing tokens like "{workdir}/{renderlayer}"
            **kwargs: Additional token values to override defaults
            
        Returns:
            Resolved path string
        """
        # Clear cache if overrides are provided to ensure fresh resolution
        if kwargs:
            self.clear_cache()
            
        # Find all tokens in the string
        tokens = re.findall(r'\{([^}]+)\}', token_string)
        resolved_string = token_string
        
        for token in tokens:
            try:
                # Check if override provided
                if token in kwargs:
                    value = str(kwargs[token])
                else:
                    # Resolve token using registered resolvers
                    value = self._resolve_token(token)
                
                # Replace token in string
                resolved_string = resolved_string.replace(f'{{{token}}}', value)
                logger.debug(f"Resolved token '{token}' to '{value}'")
                
            except Exception as e:
                logger.error(f"Failed to resolve token '{token}': {e}")
                # Keep the token unresolved if it fails
                continue
        
        # Clean up the path and ensure it's valid
        resolved_path = self._clean_path(resolved_string)
        logger.debug(f"Final resolved path: {resolved_path}")
        
        return resolved_path
    
    def _resolve_token(self, token: str) -> str:
        """Resolve a single token to its value"""
        if token in self._token_cache:
            return self._token_cache[token]
            
        if token in self.token_resolvers:
            value = self.token_resolvers[token]()
            self._token_cache[token] = value
            return value
        else:
            logger.warning(f"Unknown token: {token}")
            return f"{{{token}}}"  # Return unresolved token
    
    def _clean_path(self, path_string: str) -> str:
        """Clean and normalize the path string"""
        if not path_string:
            return ""
            
        # Convert to Path object for proper handling
        path = Path(path_string)
        
        # Clean up any double slashes or invalid characters
        cleaned = str(path).replace('\\\\', '\\').replace('//', '/')
        
        # Handle any remaining unresolved tokens more carefully
        # Instead of removing them completely, replace with a placeholder
        # to preserve path structure
        def replace_unresolved_token(match):
            token = match.group(1)
            logger.warning(f"Unresolved token in path: {{{token}}}")
            return f"UNRESOLVED_{token.upper()}"
        
        cleaned = re.sub(r'\{([^}]+)\}', replace_unresolved_token, cleaned)
        
        return cleaned
    
    # Core Shotput token resolvers
    def _resolve_workdir(self) -> str:
        """Resolve workdir token - AYON_WORKDIR or current blend file location"""
        ayon_workdir = os.getenv("AYON_WORKDIR")
        if ayon_workdir:
            return str(Path(ayon_workdir))
        
        # Fallback to blend file directory
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            return str(Path(blend_filepath).parent)
        
        # Last resort - user's Documents folder
        return str(Path.home() / "Documents" / "Blender")
    
    def _resolve_subpath(self) -> str:
        """Resolve subpath token from addon preferences"""
        return get_subpath_token_value()
    
    def _resolve_renderlayer(self) -> str:
        """Resolve render layer token from node properties"""
        if self.node_properties and hasattr(self.node_properties, 'render_layer'):
            return getattr(self.node_properties, 'render_layer', 'RenderLayer')
        
        # Fallback to active view layer
        if hasattr(bpy.context, 'view_layer') and bpy.context.view_layer:
            return bpy.context.view_layer.name
        
        return 'RenderLayer'
    
    def _resolve_passname(self) -> str:
        """Resolve pass name token from node properties"""
        if self.node_properties and hasattr(self.node_properties, 'pass_name'):
            return getattr(self.node_properties, 'pass_name', 'Beauty')
        return 'Beauty'
    
    def _resolve_variant(self) -> str:
        """Resolve variant token from node properties"""
        if self.node_properties and hasattr(self.node_properties, 'variant'):
            return getattr(self.node_properties, 'variant', 'main')
        return 'main'
    
    def _resolve_version(self) -> str:
        """Resolve version token using VersionUtils - calculates next version without creating folders"""
        if self.node_properties:
            # Try to get existing version from properties
            existing_version = getattr(self.node_properties, 'version', None)
            if existing_version:
                return existing_version
        
        # Use VersionUtils to determine version
        try:
            # Get the base output directory to check for existing versions
            base_dir = Path(self._resolve_workdir()) / self._resolve_subpath()
            folder_name = f"{self._resolve_renderlayer()}_{self._resolve_passname()}_{self._resolve_variant()}"
            version_dir = base_dir / folder_name
            
            # Get latest version WITHOUT creating any directories
            # This is crucial to avoid throwing off version calculations
            latest_version = VersionUtils.getVersionFolders(version_dir, latest=True) if version_dir.exists() else None
            
            if latest_version:
                # Get next version
                return VersionUtils.getVersionString(latest_version, up=True)
            else:
                # Return default version
                return VersionUtils.versionDefault
                
        except Exception as e:
            logger.error(f"Error resolving version: {e}")
            return VersionUtils.versionDefault
    
    def get_next_version_for_path(self, base_path: str) -> str:
        """
        Calculate the next version for a specific path without creating directories.
        
        Args:
            base_path: The base path to check for existing versions
            
        Returns:
            Next version string (e.g., 'v002')
        """
        try:
            path = Path(base_path)
            
            # Check if the path exists or create it to check for version folders
            if path.exists():
                # Directory exists, check for version folders
                latest_version = VersionUtils.getVersionFolders(path, latest=True)
                if latest_version:
                    return VersionUtils.getVersionString(latest_version, up=True)
                else:
                    # Directory exists but no version folders found
                    return VersionUtils.versionDefault
            else:
                # Directory doesn't exist yet, start with default version
                # But first check if any version folders were already created in the base path
                # This can happen if Blender created the output directory during rendering
                if path.parent.exists():
                    # Check if any version directories exist in the parent that match our pattern
                    for item in path.parent.iterdir():
                        if item.is_dir() and item.name == path.name:
                            # Found our target directory, check for versions
                            latest_version = VersionUtils.getVersionFolders(item, latest=True)
                            if latest_version:
                                return VersionUtils.getVersionString(latest_version, up=True)
                
                return VersionUtils.versionDefault
                
        except Exception as e:
            logger.error(f"Error calculating next version for {base_path}: {e}")
            return VersionUtils.versionDefault
    
    def resolve_full_output_path(self, pass_type: str = "core", pass_name: str = None) -> tuple[str, str]:
        """
        Resolve the complete output path (base + filename) for a specific pass.
        
        Args:
            pass_type: Type of pass ('core', 'aov', 'data')
            pass_name: Specific pass name to override
            
        Returns:
            (base_path, filename) tuple
        """
        # Override pass name if provided
        overrides = {}
        if pass_name:
            overrides['passname'] = pass_name
            
        # Set pass type specific overrides
        if pass_type == "core" and self.node_properties:
            overrides['passname'] = getattr(self.node_properties, 'core_override', 'BEAUTY')
        elif pass_type == "aov" and self.node_properties:
            overrides['passname'] = getattr(self.node_properties, 'aov_override', 'UTILITY')
        elif pass_type == "data":
            overrides['passname'] = "Data"
            
        # Parse tokens - handle linked vs normal nodes differently
        root_token = getattr(self.node_properties, 'root_folder_token', '') if self.node_properties else ''
        file_token = getattr(self.node_properties, 'file_name_token', '') if self.node_properties else ''
        
        # For base path: use linked logic if path-linked, otherwise normal
        if self._is_path_linked():
            base_path = self._parse_linked_path(root_token, **overrides)
        else:
            base_path = self._parse_normal_path(root_token, **overrides) if root_token else ""
        
        # For filename: ALWAYS use normal logic (never use linked path for filenames)
        filename = self._parse_normal_path(file_token, **overrides) if file_token else ""
        
        return base_path, filename
    
    # AYON-specific token resolvers
    def _resolve_project(self) -> str:
        """Resolve project path token using PathUtils"""
        return self.path_utils.get_project_path()
    
    def _resolve_project_name(self) -> str:
        """Resolve project name token using PathUtils"""
        return self.path_utils.get_project_name() or "Unknown_Project"
    
    def _resolve_task(self) -> str:
        """Resolve task name token using PathUtils"""
        return self.path_utils.get_task_name() or "Unknown_Task"
    
    def _resolve_folder(self) -> str:
        """Resolve folder path token using PathUtils"""
        return self.path_utils.get_folder_path() or ""
    
    def _resolve_user(self) -> str:
        """Resolve user name token using PathUtils"""
        return self.path_utils.get_user() or "Unknown_User"
    
    # Blender-specific token resolvers
    def _resolve_blend_name(self) -> str:
        """Resolve blend file name without extension"""
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            return Path(blend_filepath).stem
        return "untitled"
    
    def _resolve_scene_name(self) -> str:
        """Resolve active scene name"""
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            return bpy.context.scene.name
        return "Scene"
    
    def _resolve_frame(self) -> str:
        """Resolve current frame number"""
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            return f"{bpy.context.scene.frame_current:04d}"
        return "0001"
    
    def _resolve_camera(self) -> str:
        """Resolve active camera name"""
        if hasattr(bpy.context, 'scene') and bpy.context.scene and bpy.context.scene.camera:
            return bpy.context.scene.camera.name
        return "Camera"
    
    # Date/time token resolvers
    def _resolve_date(self) -> str:
        """Resolve current date in DD-MM-YY format (UK style)"""
        from datetime import datetime
        return datetime.now().strftime("%d-%m-%y")
    
    def _resolve_time(self) -> str:
        """Resolve current time in HH-MM-SS format"""
        from datetime import datetime
        return datetime.now().strftime("%H-%M-%S")
    
    def clear_cache(self):
        """Clear the token resolution cache"""
        self._token_cache.clear()
        logger.debug("Token cache cleared")
    
    def get_available_tokens(self) -> Dict[str, str]:
        """Get a dictionary of all available tokens and their descriptions"""
        return {
            # Core Shotput tokens
            'workdir': 'Working directory (AYON_WORKDIR or blend file location)',
            'subpath': 'Render output subdirectory',
            'renderlayer': 'Render layer name',
            'passname': 'Pass name (Beauty, Core, AOV, Data)',
            'variant': 'Variant name',
            'version': 'Version string (v001, v002, etc.)',
            
            # AYON-specific tokens
            'project': 'AYON project path',
            'projectname': 'AYON project name',
            'task': 'AYON task name',
            'folder': 'AYON folder path',
            'user': 'Current user name',
            
            # Blender-specific tokens
            'blend_name': 'Blend file name (without extension)',
            'scene_name': 'Active scene name',
            'frame': 'Current frame number (4 digits)',
            'camera': 'Active camera name',
            
            # Date/time tokens
            'date': 'Current date (DD-MM-YY)',
            'time': 'Current time (HH-MM-SS)',
        }
    
    def validate_token_string(self, token_string: str) -> tuple[bool, list[str]]:
        """
        Validate a token string and return any unknown tokens.
        
        Args:
            token_string: String to validate
            
        Returns:
            (is_valid, unknown_tokens)
        """
        tokens = re.findall(r'\{([^}]+)\}', token_string)
        unknown_tokens = [token for token in tokens if token not in self.token_resolvers]
        
        return len(unknown_tokens) == 0, unknown_tokens


# Convenience function for quick token parsing
def parse_shotput_tokens(token_string: str, node_properties=None, **kwargs) -> str:
    """
    Convenience function to parse Shotput tokens.
    
    Args:
        token_string: String containing tokens
        node_properties: Optional ShotputFileOutputProperties
        **kwargs: Additional token overrides
        
    Returns:
        Resolved path string
    """
    parser = TokenParser(node_properties)
    return parser.parse_token(token_string, **kwargs)
