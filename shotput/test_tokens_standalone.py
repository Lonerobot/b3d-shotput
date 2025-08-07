#!/usr/bin/env python3
"""
Test script for token parsing validation (standalone)
"""

import re
from pathlib import Path

def parse_token_standalone(token_string, test_context=None):
    """Standalone token parser for testing"""
    
    # Define test values
    default_context = {
        'workdir': 'C:/projects/my_project',
        'subpath': 'shots/shot_010',
        'renderlayer': 'ViewLayer',
        'passname': 'beauty',
        'variant': 'v001',
        'version': '001',
        'project': 'TestProject',
        'task': 'lighting',
        'user': 'pete',
        'blend_name': 'shot_010_lighting',
        'scene_name': 'Scene',
        'frame': '0001'
    }
    
    context = test_context or default_context
    
    # Find all tokens in the string
    token_pattern = r'\{([^}]+)\}'
    tokens = re.findall(token_pattern, token_string)
    
    result = token_string
    for token in tokens:
        if token in context:
            result = result.replace(f'{{{token}}}', str(context[token]))
        else:
            result = result.replace(f'{{{token}}}', f'<UNKNOWN:{token}>')
    
    return result

def test_token_parsing():
    """Test token parsing functionality"""
    
    print("=" * 60)
    print("SHOTPUT TOKEN PARSING TEST (Standalone)")
    print("=" * 60)
    
    # Test patterns from common use cases
    test_patterns = [
        "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}",
        "{project}_{task}_{blend_name}_{passname}_{frame}",
        "{workdir}/render/{version}/{passname}",
        "{user}_{project}_{scene_name}_{renderlayer}",
        "{workdir}/output/{subpath}/{passname}_{version}.{frame}.exr"
    ]
    
    print("\n🔧 Testing Token Resolution:")
    
    for i, pattern in enumerate(test_patterns, 1):
        print(f"\n{i}. Pattern: {pattern}")
        resolved = parse_token_standalone(pattern)
        print(f"   Result:  {resolved}")
    
    print("\n🎯 Testing Edge Cases:")
    
    # Test with unknown tokens
    edge_cases = [
        "{unknown_token}/{passname}",
        "{workdir}/{missing}/{passname}",
        "no_tokens_here",
        "{workdir}",
        "{project}_{unknown}_{task}"
    ]
    
    for pattern in edge_cases:
        resolved = parse_token_standalone(pattern)
        status = "✅" if "<UNKNOWN:" not in resolved else "⚠️"
        print(f"   {status} {pattern} → {resolved}")
    
    print("\n📊 Token Types Available:")
    tokens = [
        "workdir", "subpath", "renderlayer", "passname", "variant", "version",
        "project", "task", "user", "blend_name", "scene_name", "frame"
    ]
    
    for token in tokens:
        print(f"   • {{{token}}}")
    
    print("\n✅ Token Parsing Test Complete!")
    return True

if __name__ == '__main__':
    test_token_parsing()
