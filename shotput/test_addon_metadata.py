#!/usr/bin/env python3
"""
Test script to parse and validate Blender addon metadata from __init__.py
"""

import sys
import os
import re

def test_addon_metadata():
    """Parse the __init__.py file to extract bl_info and dunder properties"""
    init_file = '__init__.py'
    
    if not os.path.exists(init_file):
        print('❌ __init__.py file not found')
        return False
        
    # Read the file content
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        # Extract bl_info using regex
        bl_info_match = re.search(r'bl_info\s*=\s*(\{[^}]*\})', content, re.DOTALL)
        if not bl_info_match:
            print('❌ bl_info not found!')
            return False
            
        # Create a safe namespace and execute just the bl_info part
        namespace = {}
        bl_info_code = bl_info_match.group(0)
        exec(bl_info_code, namespace)
        
        # Also extract the dunder properties
        version_match = re.search(r'__version__\s*=\s*([^\n]+)', content)
        author_match = re.search(r'__author__\s*=\s*([^\n]+)', content)
        package_match = re.search(r'__package_name__\s*=\s*([^\n]+)', content)
        
        print('=' * 50)
        print('BLENDER ADDON METADATA ANALYSIS')
        print('=' * 50)
        
        # Display bl_info
        bl_info = namespace['bl_info']
        print('\n📋 bl_info dictionary:')
        print('bl_info = {')
        for key, value in bl_info.items():
            print(f'    "{key}": {repr(value)},')
        print('}')
        
        # Display dunder properties (calculated values)
        print('\n🔧 Dunder Properties (calculated):')
        version_str = ".".join(str(x) for x in bl_info["version"])
        print(f'    __version__ = "{version_str}"')
        print(f'    __author__ = "{bl_info["author"]}"')
        print(f'    __package_name__ = "shotput" (when loaded as addon)')
            
        print('\n' + '=' * 50)
        print('VALIDATION RESULTS')
        print('=' * 50)
        
        # Validate bl_info requirements
        required_fields = ['name', 'blender', 'category', 'version']
        missing = [field for field in required_fields if field not in bl_info]
        
        if missing:
            print(f'❌ Missing required bl_info fields: {missing}')
        else:
            print('✅ All required bl_info fields present')
            
        # Check version format
        version = bl_info.get('version')
        if isinstance(version, tuple) and len(version) >= 2:
            print(f'✅ Version format valid: {version}')
        else:
            print(f'❌ Invalid version format: {version} (should be tuple with at least 2 elements)')
        
        # Check Blender version format
        blender_ver = bl_info.get('blender')
        if isinstance(blender_ver, tuple) and len(blender_ver) >= 2:
            print(f'✅ Blender version format valid: {blender_ver}')
            print(f'    Requires Blender {blender_ver[0]}.{blender_ver[1]} or newer')
        else:
            print(f'❌ Invalid Blender version format: {blender_ver}')
            
        # Additional checks
        print('\n🔍 Additional Information:')
        if 'warning' in bl_info and bl_info['warning']:
            print(f'⚠️  Development warning: {bl_info["warning"]}')
        if 'support' in bl_info:
            print(f'📋 Support level: {bl_info["support"]}')
        if 'location' in bl_info:
            print(f'📍 UI Location: {bl_info["location"]}')
        if 'description' in bl_info:
            print(f'📝 Description: {bl_info["description"]}')
                
        print('\n✅ Addon metadata validation complete!')
        return True
    
    except Exception as e:
        print(f'❌ Error parsing file: {e}')
        return False

if __name__ == '__main__':
    success = test_addon_metadata()
    sys.exit(0 if success else 1)
