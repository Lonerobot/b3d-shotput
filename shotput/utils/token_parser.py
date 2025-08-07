import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import bpy

from .log import LoggerFactory
from .path_utils import PathUtils
from .version_utils import VersionUtils

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
        
        Args:
            token_string: String containing tokens like "{workdir}/{renderlayer}"
            **kwargs: Additional token values to override defaults
            
        Returns:
            Resolved path string
        """
        if not token_string:
            return ""
            
        logger.debug(f"Parsing token string: {token_string}")
        
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
                # Keep the token unresolve if it fails
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
        
        # Remove any remaining unresolved tokens for cleaner output
        cleaned = re.sub(r'\{[^}]+\}', '', cleaned)
        
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
        """Resolve subpath token from node properties"""
        if self.node_properties and hasattr(self.node_properties, 'root_folder_token'):
            # Extract subpath from properties if available
            return getattr(self.node_properties, 'subpath', 'renders')
        return 'renders'
    
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
            if path.exists():
                latest_version = VersionUtils.getVersionFolders(path, latest=True)
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
            
        # Parse tokens
        root_token = getattr(self.node_properties, 'root_folder_token', '') if self.node_properties else ''
        file_token = getattr(self.node_properties, 'file_name_token', '') if self.node_properties else ''
        
        base_path = self.parse_token(root_token, **overrides) if root_token else ""
        filename = self.parse_token(file_token, **overrides) if file_token else ""
        
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
        """Resolve current date in YYYY-MM-DD format"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
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
            'date': 'Current date (YYYY-MM-DD)',
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
