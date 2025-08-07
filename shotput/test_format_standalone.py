#!/usr/bin/env python3
"""
Standalone test for file format override logic (no bpy dependency)
"""

import json
from pathlib import Path

def load_passes_config():
    """Load the passes.json configuration"""
    passes_file = Path(__file__).parent / "data" / "passes.json"
    try:
        with open(passes_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading passes.json: {e}")
        return None

def get_file_format_for_pass_type(pass_type, ui_format):
    """Standalone version of format override logic"""
    passes_config = load_passes_config()
    if not passes_config:
        return ui_format
    
    file_format_overrides = passes_config.get("file_format_overrides", {})
    override_format = file_format_overrides.get(pass_type)
    
    if override_format == "UI":
        return ui_format
    elif override_format:
        return override_format
    else:
        return ui_format

def test_format_override_system():
    """Test the file format override system"""
    
    print("=" * 60)
    print("SHOTPUT FILE FORMAT OVERRIDE TEST (Standalone)")
    print("=" * 60)
    
    print("\n📋 Testing File Format Override Logic:")
    
    # Test different UI formats
    ui_formats = ["PNG", "JPEG", "OPEN_EXR", "OPEN_EXR_MULTILAYER"]
    pass_types = ["core", "aov", "data"]
    
    for ui_format in ui_formats:
        print(f"\n🎛️  UI Format: {ui_format}")
        for pass_type in pass_types:
            resolved_format = get_file_format_for_pass_type(pass_type, ui_format)
            status_icon = "🔒" if resolved_format != ui_format else "✅"
            print(f"    {status_icon} {pass_type.upper()}: {resolved_format}")
    
    print("\n📊 Override Summary:")
    print("✅ = Uses UI setting")
    print("🔒 = Override applied")
    
    print("\n🔍 Expected Behavior:")
    print("  • CORE passes: Should use UI setting")
    print("  • AOV passes: Should use UI setting") 
    print("  • DATA passes: Should ALWAYS use OPEN_EXR_MULTILAYER")
    
    # Load and display current configuration
    print("\n📄 Current Configuration (passes.json):")
    passes_config = load_passes_config()
    if passes_config:
        overrides = passes_config.get("file_format_overrides", {})
        for pass_type, override in overrides.items():
            print(f"  {pass_type}: {override}")
    
    print("\n✅ File Format Override Test Complete!")
    return True

if __name__ == '__main__':
    test_format_override_system()
