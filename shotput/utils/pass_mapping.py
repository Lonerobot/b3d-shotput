"""
Pass Mapping System for Shotput

This module provides a comprehensive mapping between Shotput pass names
and Blender's built-in render layer passes and outputs. It handles:

1. Direct mappings (1:1 correspondence)
2. Complex mappings (multiple outputs per pass)
3. Fuzzy matching with alternatives
4. Engine-specific differences
"""

from typing import Dict, List, Optional, Union, Tuple
from enum import Enum
import re


class PassMappingType(Enum):
    """Types of pass mappings"""
    DIRECT = "direct"           # 1:1 mapping
    COMPLEX = "complex"         # 1:many mapping (e.g., cryptomattes)
    FUZZY = "fuzzy"            # Multiple possible matches
    CONDITIONAL = "conditional" # Depends on engine/settings


class PassMapping:
    """
    Configuration for mapping Shotput passes to Blender render passes
    """
    
    def __init__(self):
        # Direct 1:1 mappings between Shotput data passes and Blender passes
        self.direct_data_mappings = {
            # Shotput name -> (view_layer_property, output_socket_name, description)
            "z": ("use_pass_z", "Depth", "Z-depth information"),
            "mist": ("use_pass_mist", "Mist", "Distance-based mist pass"),
            "normal": ("use_pass_normal", "Normal", "Surface normal vectors"),
            "vector": ("use_pass_vector", "Vector", "Motion vectors"),
            "position": ("use_pass_position", "Position", "World position pass"),
            "occlusion": ("use_pass_ambient_occlusion", "AO", "Ambient occlusion"),
            "uv": ("use_pass_uv", "UV", "UV coordinate pass"),
            "object_index": ("use_pass_object_index", "IndexOB", "Object index pass"),
            "material_index": ("use_pass_material_index", "IndexMA", "Material index pass"),
            "grease_pencil": ("use_pass_grease_pencil", "GreasePencil", "Grease Pencil pass"),
            "volume_direct": ("use_pass_volume_direct", "VolumeDir", "Volume direct illumination"),
            "volume_indirect": ("use_pass_volume_indirect", "VolumeInd", "Volume indirect illumination"),
        }
        
        # Complex mappings - passes that generate multiple outputs
        self.complex_data_mappings = {
            "crypto_object": {
                "type": PassMappingType.COMPLEX,
                "property": "use_pass_cryptomatte_object",
                "outputs": ["CryptoObject00", "CryptoObject01", "CryptoObject02"],
                "description": "Cryptomatte object isolation",
                "output_count": 3
            },
            "crypto_material": {
                "type": PassMappingType.COMPLEX,
                "property": "use_pass_cryptomatte_material", 
                "outputs": ["CryptoMaterial00", "CryptoMaterial01", "CryptoMaterial02"],
                "description": "Cryptomatte material isolation",
                "output_count": 3
            },
            "crypto_asset": {
                "type": PassMappingType.COMPLEX,
                "property": "use_pass_cryptomatte_asset",
                "outputs": ["CryptoAsset00", "CryptoAsset01", "CryptoAsset02"],
                "description": "Cryptomatte asset isolation", 
                "output_count": 3
            }
        }
        
        # Fuzzy mappings for core/beauty passes - multiple possible matches
        self.fuzzy_core_mappings = {
            # Shotput name -> [possible_output_names] (ordered by preference)
            "Beauty": ["Image", "Combined"],  # Primary beauty pass
            "Shadow": ["Shadow"],
            "AO": ["AO", "Ambient Occlusion"],
            "Emission": ["Emit"],
            "Environment": ["Env", "Environment"],
            
            # Diffuse variations
            "Diffuse": ["DiffDir", "DiffInd", "DiffCol"],
            "Diffuse_Direct": ["DiffDir"],
            "Diffuse_Indirect": ["DiffInd"], 
            "Diffuse_Color": ["DiffCol"],
            
            # Glossy/Reflection variations
            "Glossy": ["GlossDir", "GlossInd", "GlossCol"],
            "Glossy_Direct": ["GlossDir"],
            "Glossy_Indirect": ["GlossInd"],
            "Glossy_Color": ["GlossCol"],
            "Reflection": ["GlossInd"],  # Common alias
            
            # Transmission variations
            "Transmission": ["TransDir", "TransInd", "TransCol"],
            "Transmission_Direct": ["TransDir"],
            "Transmission_Indirect": ["TransInd"],
            "Transmission_Color": ["TransCol"],
            
            # Subsurface variations 
            "Subsurface": ["SubsurfaceDir", "SubsurfaceInd", "SubsurfaceCol"],
            "Subsurface_Direct": ["SubsurfaceDir"],
            "Subsurface_Indirect": ["SubsurfaceInd"],
            "Subsurface_Color": ["SubsurfaceCol"],
            "SSS": ["SubsurfaceDir", "SubsurfaceInd"],  # Common alias
            
            # Volume variations (if available)
            "Volume": ["VolumeDir", "VolumeInd"],
            "Volume_Direct": ["VolumeDir"],
            "Volume_Indirect": ["VolumeInd"],
            
            # Grease Pencil variations (for core/AOV usage)
            "GreasePencil": ["GreasePencil", "GP"],
            "GP": ["GreasePencil", "GP"],
            "LinePencil": ["GreasePencil"],
            "LineWork": ["GreasePencil"],
            "Lines": ["GreasePencil"],
            "Outline": ["GreasePencil"],
        }
        
        # Engine-specific mappings (for future use)
        self.engine_specific_mappings = {
            "CYCLES": {
                # Cycles has all passes available
            },
            "BLENDER_EEVEE_NEXT": {
                # Eevee Next has most passes but some differences
            }
        }
        
        # Alternative name patterns for fuzzy matching
        self.name_patterns = {
            # Common naming variations that should be normalized
            r"beauty|combined|rgba|image": "Beauty",
            r"diffuse|diff": "Diffuse", 
            r"specular|spec|glossy|refl": "Glossy",
            r"transmission|trans|refr": "Transmission",
            r"subsurface|sss": "Subsurface",
            r"shadow|shad": "Shadow",
            r"ambient.*occlusion|ao": "AO",
            r"emission|emit": "Emission",
            r"environment|env|world": "Environment",
            r"normal|norm|n": "normal",
            r"depth|z": "z",
            r"motion.*vector|vector|vel": "vector",
            r"position|pos|p": "position",
            r"mist|fog": "mist",
            r"gp|grease.*pencil|line|linework|lines|outline": "GreasePencil",
        }
    
    def get_data_pass_mapping(self, shotput_pass_name: str) -> Optional[Tuple[str, str]]:
        """
        Get the view layer property and output socket for a Shotput data pass
        
        Args:
            shotput_pass_name: The Shotput pass name (e.g., "z", "normal")
            
        Returns:
            Tuple of (view_layer_property, output_socket_name) or None if not found
        """
        # Check direct mappings first
        if shotput_pass_name in self.direct_data_mappings:
            prop, output, _ = self.direct_data_mappings[shotput_pass_name]
            return (prop, output)
        
        # Check complex mappings
        if shotput_pass_name in self.complex_data_mappings:
            mapping = self.complex_data_mappings[shotput_pass_name]
            return (mapping["property"], mapping["outputs"][0])  # Return first output
        
        return None
    
    def get_complex_pass_outputs(self, shotput_pass_name: str) -> Optional[List[str]]:
        """
        Get all output socket names for a complex pass (like cryptomattes)
        
        Args:
            shotput_pass_name: The Shotput pass name
            
        Returns:
            List of output socket names or None if not a complex pass
        """
        if shotput_pass_name in self.complex_data_mappings:
            return self.complex_data_mappings[shotput_pass_name]["outputs"]
        return None
    
    def find_core_pass_matches(self, shotput_pass_name: str, available_outputs: List[str]) -> List[str]:
        """
        Find matching render layer outputs for a core pass using fuzzy matching
        
        Args:
            shotput_pass_name: The Shotput pass name
            available_outputs: List of available render layer output names
            
        Returns:
            List of matching output names (ordered by preference)
        """
        matches = []
        
        # Direct fuzzy mapping lookup
        if shotput_pass_name in self.fuzzy_core_mappings:
            potential_matches = self.fuzzy_core_mappings[shotput_pass_name]
            for match in potential_matches:
                if match in available_outputs:
                    matches.append(match)
        
        # Pattern-based fuzzy matching if no direct matches
        if not matches:
            normalized_name = self._normalize_pass_name(shotput_pass_name)
            if normalized_name and normalized_name != shotput_pass_name:
                # Try the normalized name
                if normalized_name in self.fuzzy_core_mappings:
                    potential_matches = self.fuzzy_core_mappings[normalized_name]
                    for match in potential_matches:
                        if match in available_outputs:
                            matches.append(match)
        
        # Last resort: partial string matching
        if not matches:
            matches = self._partial_string_match(shotput_pass_name, available_outputs)
        
        return matches
    
    def _normalize_pass_name(self, pass_name: str) -> Optional[str]:
        """Normalize pass name using pattern matching"""
        pass_name_lower = pass_name.lower().strip()
        
        for pattern, normalized in self.name_patterns.items():
            if re.search(pattern, pass_name_lower):
                return normalized
        
        return None
    
    def _partial_string_match(self, shotput_name: str, available_outputs: List[str]) -> List[str]:
        """Find partial string matches between Shotput name and available outputs"""
        shotput_lower = shotput_name.lower()
        matches = []
        
        for output in available_outputs:
            output_lower = output.lower()
            
            # Check if any significant part matches
            if (len(shotput_lower) >= 3 and shotput_lower in output_lower) or \
               (len(output_lower) >= 3 and output_lower in shotput_lower):
                matches.append(output)
        
        return matches
    
    def get_all_data_passes(self) -> List[str]:
        """Get all supported Shotput data pass names"""
        return list(self.direct_data_mappings.keys()) + list(self.complex_data_mappings.keys())
    
    def get_all_core_passes(self) -> List[str]:
        """Get all supported Shotput core pass names"""
        return list(self.fuzzy_core_mappings.keys())
    
    def is_complex_pass(self, pass_name: str) -> bool:
        """Check if a pass requires complex multi-output handling"""
        return pass_name in self.complex_data_mappings
    
    def get_view_layer_property(self, shotput_pass_name: str) -> Optional[str]:
        """Get the view layer property name for enabling a pass"""
        mapping = self.get_data_pass_mapping(shotput_pass_name)
        return mapping[0] if mapping else None


# Global instance
pass_mapping = PassMapping()
