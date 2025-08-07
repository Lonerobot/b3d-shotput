#!/usr/bin/env python3
"""
Test script for Shotput file format override system
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_format_override_system():
    """Test the file format override system"""
    
    print("=" * 60)
    print("SHOTPUT FILE FORMAT OVERRIDE TEST")
    print("=" * 60)
    
    try:
        # Import the defaults module
        from utils.defaults import get_file_format_for_pass_type, apply_data_format_settings
        
        print("\n📋 Testing File Format Override Logic:")
        
        # Test different UI formats
        ui_formats = ["PNG", "JPEG", "OPEN_EXR", "OPEN_EXR_MULTILAYER"]
        pass_types = ["core", "aov", "data"]
        
        for ui_format in ui_formats:
            print(f"\n🎛️  UI Format: {ui_format}")
            for pass_type in pass_types:
                try:
                    resolved_format = get_file_format_for_pass_type(pass_type, ui_format)
                    status_icon = "🔒" if resolved_format != ui_format else "✅"
                    print(f"    {status_icon} {pass_type.upper()}: {resolved_format}")
                except Exception as e:
                    print(f"    ❌ {pass_type.upper()}: ERROR - {e}")
        
        print("\n📊 Override Summary:")
        print("✅ = Uses UI setting")
        print("🔒 = Override applied")
        
        print("\n🔍 Expected Behavior:")
        print("  • CORE passes: Should use UI setting")
        print("  • AOV passes: Should use UI setting") 
        print("  • DATA passes: Should ALWAYS use OPEN_EXR_MULTILAYER")
        
        print("\n✅ File Format Override Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_format_override_system()
    sys.exit(0 if success else 1)
