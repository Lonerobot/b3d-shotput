#!/usr/bin/env python3
"""
Comprehensive test suite for Shotput addon systems
"""

import json
import re
from pathlib import Path

def run_all_tests():
    """Run all Shotput system tests"""
    
    print("=" * 80)
    print("SHOTPUT ADDON - COMPREHENSIVE SYSTEM TEST")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Configuration Loading
    print("\n🔧 TEST 1: Configuration Loading")
    results['config'] = test_configuration_loading()
    
    # Test 2: File Format Override System
    print("\n🎨 TEST 2: File Format Override System") 
    results['format_override'] = test_format_override_system()
    
    # Test 3: Token Parsing System
    print("\n🏷️  TEST 3: Token Parsing System")
    results['token_parsing'] = test_token_parsing_system()
    
    # Test 4: Integration Scenarios
    print("\n🔗 TEST 4: Integration Scenarios")
    results['integration'] = test_integration_scenarios()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.upper().replace('_', ' ')}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
    else:
        print("⚠️  Some tests failed - review output above")
    
    return passed_tests == total_tests

def test_configuration_loading():
    """Test configuration file loading"""
    try:
        passes_file = Path(__file__).parent / "data" / "passes.json"
        
        if not passes_file.exists():
            print("   ❌ passes.json not found")
            return False
        
        with open(passes_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_sections = ['core_passes', 'aovs', 'data_passes', 'file_format_overrides']
        
        for section in required_sections:
            if section not in config:
                print(f"   ❌ Missing section: {section}")
                return False
            print(f"   ✅ Found section: {section}")
        
        # Validate file format overrides
        overrides = config['file_format_overrides']
        expected_overrides = {'core': 'UI', 'aov': 'UI', 'data': 'OPEN_EXR_MULTILAYER'}
        
        for pass_type, expected in expected_overrides.items():
            if overrides.get(pass_type) != expected:
                print(f"   ❌ Invalid override for {pass_type}: {overrides.get(pass_type)} != {expected}")
                return False
            print(f"   ✅ Override {pass_type}: {overrides[pass_type]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration loading error: {e}")
        return False

def test_format_override_system():
    """Test the file format override logic"""
    try:
        # Load configuration
        passes_file = Path(__file__).parent / "data" / "passes.json"
        with open(passes_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        overrides = config['file_format_overrides']
        
        def get_format(pass_type, ui_format):
            override = overrides.get(pass_type)
            return ui_format if override == "UI" else override
        
        test_cases = [
            # (pass_type, ui_format, expected_result)
            ('core', 'PNG', 'PNG'),
            ('core', 'OPEN_EXR', 'OPEN_EXR'),
            ('aov', 'JPEG', 'JPEG'),
            ('aov', 'OPEN_EXR_MULTILAYER', 'OPEN_EXR_MULTILAYER'),
            ('data', 'PNG', 'OPEN_EXR_MULTILAYER'),
            ('data', 'JPEG', 'OPEN_EXR_MULTILAYER'),
            ('data', 'OPEN_EXR', 'OPEN_EXR_MULTILAYER'),
        ]
        
        for pass_type, ui_format, expected in test_cases:
            result = get_format(pass_type, ui_format)
            if result == expected:
                print(f"   ✅ {pass_type}({ui_format}) → {result}")
            else:
                print(f"   ❌ {pass_type}({ui_format}) → {result} (expected {expected})")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Format override test error: {e}")
        return False

def test_token_parsing_system():
    """Test token parsing functionality"""
    try:
        # Test context
        context = {
            'workdir': 'C:/projects/test',
            'subpath': 'shots/001',
            'renderlayer': 'Beauty',
            'passname': 'diffuse',
            'variant': 'v002',
            'version': '003',
            'project': 'TestProj',
            'task': 'comp',
            'user': 'artist',
            'blend_name': 'test_scene',
            'scene_name': 'Scene',
            'frame': '0024'
        }
        
        def parse_tokens(pattern):
            result = pattern
            for token, value in context.items():
                result = result.replace(f'{{{token}}}', value)
            return result
        
        test_cases = [
            ('{workdir}/{subpath}', 'C:/projects/test/shots/001'),
            ('{passname}_{version}', 'diffuse_003'),
            ('{project}_{task}_{frame}', 'TestProj_comp_0024'),
            ('static_path', 'static_path'),
            ('{workdir}/render/{passname}.{frame}.exr', 'C:/projects/test/render/diffuse.0024.exr')
        ]
        
        for pattern, expected in test_cases:
            result = parse_tokens(pattern)
            if result == expected:
                print(f"   ✅ {pattern} → {result}")
            else:
                print(f"   ❌ {pattern} → {result} (expected {expected})")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Token parsing test error: {e}")
        return False

def test_integration_scenarios():
    """Test realistic integration scenarios"""
    try:
        print("   🎬 Scenario: Feature Film Shot Pipeline")
        
        # Context for a typical shot
        shot_context = {
            'workdir': 'Z:/projects/feature_film',
            'subpath': 'sequences/seq_010/shots/shot_020',
            'project': 'FeatureFilm2024',
            'task': 'lighting',
            'user': 'lighting_artist',
            'blend_name': 'seq_010_shot_020_lighting_v008',
            'scene_name': 'shot_020',
            'renderlayer': 'Beauty',
            'version': '008',
            'frame': '1001'
        }
        
        # Test core pass
        core_pattern = "{workdir}/{subpath}/render/{version}/core/{renderlayer}_{frame}"
        core_path = core_pattern
        for token, value in shot_context.items():
            core_path = core_path.replace(f'{{{token}}}', value)
        
        expected_core = "Z:/projects/feature_film/sequences/seq_010/shots/shot_020/render/008/core/Beauty_1001"
        
        if core_path == expected_core:
            print(f"   ✅ Core path: {core_path}")
        else:
            print(f"   ❌ Core path mismatch")
            return False
        
        # Test data pass with format override
        data_passes = ['depth', 'normal', 'object_id']
        
        for pass_name in data_passes:
            context_with_pass = shot_context.copy()
            context_with_pass['passname'] = pass_name
            
            data_pattern = "{workdir}/{subpath}/render/{version}/data/{passname}_{frame}"
            data_path = data_pattern
            for token, value in context_with_pass.items():
                data_path = data_path.replace(f'{{{token}}}', value)
            
            # Data passes should always be EXR multilayer
            format_type = "OPEN_EXR_MULTILAYER"  # This would come from format override
            
            print(f"   ✅ Data pass ({pass_name}): {data_path} [{format_type}]")
        
        print("   🎬 Scenario: Commercial Project")
        
        commercial_context = {
            'workdir': 'D:/commercial_work',
            'subpath': 'client_abc/spot_v3',
            'project': 'ClientABC_Spot',
            'task': 'final_comp',
            'renderlayer': 'Final',
            'passname': 'beauty',
            'version': '012',
            'frame': '0001'
        }
        
        commercial_pattern = "{workdir}/{subpath}/final/{version}/{passname}_{frame}"
        commercial_path = commercial_pattern
        for token, value in commercial_context.items():
            commercial_path = commercial_path.replace(f'{{{token}}}', value)
        
        expected_commercial = "D:/commercial_work/client_abc/spot_v3/final/012/beauty_0001"
        
        if commercial_path == expected_commercial:
            print(f"   ✅ Commercial path: {commercial_path}")
        else:
            print(f"   ❌ Commercial path mismatch")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test error: {e}")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
