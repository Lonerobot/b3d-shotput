#!/usr/bin/env python3
"""
Test script for the Shotput Token Parser system
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import the token parser
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_token_parser():
    """Test the token parser with mock data"""
    
    print("=" * 60)
    print("SHOTPUT TOKEN PARSER TEST")
    print("=" * 60)
    
    try:
        # Mock the bpy module for testing
        import unittest.mock as mock
        
        # Create mock bpy context
        mock_context = mock.MagicMock()
        mock_context.scene.name = "Scene"
        mock_context.scene.frame_current = 42
        mock_context.view_layer.name = "ViewLayer"
        
        # Mock bpy data
        mock_data = mock.MagicMock()
        mock_data.filepath = str(Path.cwd() / "test_project.blend")
        
        with mock.patch.dict('sys.modules', {'bpy': mock.MagicMock()}):
            # Mock bpy module
            bpy_mock = sys.modules['bpy']
            bpy_mock.context = mock_context
            bpy_mock.data = mock_data
            
            # Now import the token parser
            from utils.token_parser import TokenParser, parse_shotput_tokens
            
            # Mock node properties
            class MockNodeProperties:
                def __init__(self):
                    self.render_layer = "MainLayer"
                    self.pass_name = "Beauty"
                    self.variant = "final"
                    self.subpath = "renders/blender"
            
            node_props = MockNodeProperties()
            
            # Create token parser
            parser = TokenParser(node_props)
            
            print("\n📋 Available Tokens:")
            available_tokens = parser.get_available_tokens()
            for token, description in available_tokens.items():
                print(f"  {{{token}}} - {description}")
            
            print("\n🔧 Testing Token Resolution:")
            
            # Test individual tokens
            test_tokens = [
                'workdir',
                'renderlayer', 
                'passname',
                'variant',
                'version',
                'blend_name',
                'scene_name',
                'frame',
                'date',
                'time'
            ]
            
            for token in test_tokens:
                try:
                    resolved = parser._resolve_token(token)
                    print(f"  {{{token}}} → '{resolved}'")
                except Exception as e:
                    print(f"  {{{token}}} → ERROR: {e}")
            
            print("\n🎯 Testing Complete Token Strings:")
            
            # Test the full token strings from your specification
            root_folder_token = "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}"
            file_name_token = "{renderlayer}_{passname}_{variant}"
            
            print(f"\nRoot Folder Token: {root_folder_token}")
            resolved_root = parser.parse_token(root_folder_token)
            print(f"Resolved Root: {resolved_root}")
            
            print(f"\nFile Name Token: {file_name_token}")  
            resolved_filename = parser.parse_token(file_name_token)
            print(f"Resolved Filename: {resolved_filename}")
            
            # Test validation
            print(f"\n✅ Validation Test:")
            valid, unknown = parser.validate_token_string(root_folder_token)
            print(f"Root folder token valid: {valid}")
            if unknown:
                print(f"Unknown tokens: {unknown}")
                
            valid, unknown = parser.validate_token_string(file_name_token)
            print(f"Filename token valid: {valid}")
            if unknown:
                print(f"Unknown tokens: {unknown}")
            
            # Test with overrides
            print(f"\n🔄 Testing with Token Overrides:")
            custom_resolved = parser.parse_token(
                root_folder_token,
                variant="custom",
                version="v005"
            )
            print(f"With overrides (variant='custom', version='v005'): {custom_resolved}")
            
            # Test convenience function
            print(f"\n⚡ Testing Convenience Function:")
            convenience_result = parse_shotput_tokens(
                "{renderlayer}_{passname}_{frame}",
                node_props,
                frame="0123"
            )
            print(f"Convenience function result: {convenience_result}")
            
            print(f"\n✅ Token Parser Test Complete!")
            return True
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_token_parser()
    sys.exit(0 if success else 1)
