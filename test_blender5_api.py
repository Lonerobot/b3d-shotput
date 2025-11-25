"""
Blender 5.0 API Detection Test Script
=======================================

This script probes the compositor API to identify changes between Blender 4.x and 5.0.
Run with: blender --background --python test_blender5_api.py

Key areas to investigate:
1. Composite node availability and behavior
2. File Output node structure changes
3. Group Output node as composite replacement
4. Path template system integration
5. Scene render filepath handling
"""

import bpy
import sys
import json
from typing import Dict, Any, List


def get_blender_version() -> tuple:
    """Get the current Blender version."""
    return bpy.app.version


def check_composite_node() -> Dict[str, Any]:
    """Check if COMPOSITE node type still exists and its properties."""
    result = {
        "exists": False,
        "type_available": False,
        "properties": [],
        "error": None
    }
    
    try:
        # Try to create a compositor tree
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
        
        tree = bpy.context.scene.node_tree
        
        # Check if COMPOSITE is in available node types
        result["type_available"] = 'COMPOSITE' in dir(bpy.types)
        
        # Try to create a composite node
        try:
            comp_node = tree.nodes.new(type='CompositorNodeComposite')
            result["exists"] = True
            
            # Get properties
            result["properties"] = [prop for prop in dir(comp_node) 
                                   if not prop.startswith('_')]
            
            # Check for shotput_data custom property
            result["has_custom_properties"] = hasattr(comp_node, 'shotput_data')
            
            # Clean up
            tree.nodes.remove(comp_node)
            
        except Exception as e:
            result["error"] = f"Cannot create COMPOSITE node: {str(e)}"
            
    except Exception as e:
        result["error"] = f"General error: {str(e)}"
    
    return result


def check_file_output_node() -> Dict[str, Any]:
    """Check File Output node structure and changes."""
    result = {
        "exists": False,
        "properties": [],
        "file_slots_structure": {},
        "base_path_available": True,
        "error": None
    }
    
    try:
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
        
        tree = bpy.context.scene.node_tree
        
        # Create file output node
        try:
            file_node = tree.nodes.new(type='CompositorNodeOutputFile')
            result["exists"] = True
            
            # Get all properties
            result["properties"] = [prop for prop in dir(file_node) 
                                   if not prop.startswith('_')]
            
            # Check base_path
            if hasattr(file_node, 'base_path'):
                result["base_path_available"] = True
                result["base_path_value"] = file_node.base_path
            else:
                result["base_path_available"] = False
            
            # Check file_slots structure
            if hasattr(file_node, 'file_slots'):
                slots = file_node.file_slots
                result["file_slots_structure"] = {
                    "type": str(type(slots)),
                    "length": len(slots),
                    "properties": [prop for prop in dir(slots[0]) 
                                  if len(slots) > 0 and not prop.startswith('_')]
                }
                
                # Add a test slot to check properties
                test_slot = file_node.file_slots.new("test_channel")
                result["file_slot_properties"] = [prop for prop in dir(test_slot) 
                                                  if not prop.startswith('_')]
            
            # Check for format property
            if hasattr(file_node, 'format'):
                result["format_available"] = True
                result["format_properties"] = [prop for prop in dir(file_node.format) 
                                               if not prop.startswith('_')]
            
            # Check for path templates support
            if hasattr(file_node, 'path_template'):
                result["path_template_available"] = True
            
            # Clean up
            tree.nodes.remove(file_node)
            
        except Exception as e:
            result["error"] = f"Cannot create OUTPUT_FILE node: {str(e)}"
            
    except Exception as e:
        result["error"] = f"General error: {str(e)}"
    
    return result


def check_group_output_node() -> Dict[str, Any]:
    """Check Group Output node as potential Composite replacement."""
    result = {
        "exists": False,
        "properties": [],
        "can_output_to_scene": False,
        "error": None
    }
    
    try:
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
        
        tree = bpy.context.scene.node_tree
        
        # Try to create a group output node
        try:
            group_node = tree.nodes.new(type='NodeGroupOutput')
            result["exists"] = True
            
            # Get properties
            result["properties"] = [prop for prop in dir(group_node) 
                                   if not prop.startswith('_')]
            
            # Check if it can output to viewer/scene
            result["has_outputs"] = hasattr(group_node, 'outputs')
            if result["has_outputs"]:
                result["output_count"] = len(group_node.outputs)
            
            # Clean up
            tree.nodes.remove(group_node)
            
        except Exception as e:
            result["error"] = f"Cannot create GROUP_OUTPUT node: {str(e)}"
            
    except Exception as e:
        result["error"] = f"General error: {str(e)}"
    
    return result


def check_compositor_structure() -> Dict[str, Any]:
    """Check overall compositor node tree structure and available node types."""
    result = {
        "compositor_types": [],
        "output_types": [],
        "scene_filepath_tokens": [],
        "error": None
    }
    
    try:
        # Get all compositor node types
        compositor_types = []
        for attr_name in dir(bpy.types):
            if attr_name.startswith('CompositorNode'):
                compositor_types.append(attr_name)
        
        result["compositor_types"] = sorted(compositor_types)
        
        # Filter output-related types
        result["output_types"] = [t for t in compositor_types 
                                  if 'Output' in t or 'Composite' in t]
        
        # Check scene render filepath
        scene = bpy.context.scene
        if hasattr(scene.render, 'filepath'):
            result["render_filepath"] = scene.render.filepath
            result["render_filepath_raw"] = repr(scene.render.filepath)
        
        # Check for path template support in scene
        if hasattr(scene.render, 'use_file_extension'):
            result["use_file_extension"] = scene.render.use_file_extension
        
    except Exception as e:
        result["error"] = f"Error checking compositor: {str(e)}"
    
    return result


def check_path_template_system() -> Dict[str, Any]:
    """Check Blender's native path template/token system."""
    result = {
        "available_tokens": [],
        "token_examples": {},
        "error": None
    }
    
    try:
        # Test common Blender tokens in filepath
        test_tokens = [
            "#",          # Frame number
            "####",       # Padded frame number
            "<f>",        # Frame
            "<scene>",    # Scene name
            "<camera>",   # Camera name
            "<layer>",    # View layer
            "<pass>",     # Render pass
            "//",         # Relative path
        ]
        
        scene = bpy.context.scene
        
        for token in test_tokens:
            try:
                # Try to set filepath with token
                test_path = f"/tmp/render_{token}_test"
                scene.render.filepath = test_path
                
                # Check if it was accepted (basic validation)
                result["token_examples"][token] = {
                    "accepted": True,
                    "set_value": scene.render.filepath
                }
            except Exception as e:
                result["token_examples"][token] = {
                    "accepted": False,
                    "error": str(e)
                }
        
        # Reset filepath
        scene.render.filepath = "/tmp/test"
        
    except Exception as e:
        result["error"] = f"Error testing path templates: {str(e)}"
    
    return result


def check_render_layer_passes() -> Dict[str, Any]:
    """Check render layer pass structure for multi-channel workflows."""
    result = {
        "view_layers": [],
        "available_passes": [],
        "pass_properties": {},
        "error": None
    }
    
    try:
        scene = bpy.context.scene
        
        # Get view layers
        result["view_layers"] = [vl.name for vl in scene.view_layers]
        
        # Get first view layer's passes
        if scene.view_layers:
            vl = scene.view_layers[0]
            
            # Check available passes
            if hasattr(vl, 'use_pass_combined'):
                pass_attrs = [attr for attr in dir(vl) 
                             if attr.startswith('use_pass_')]
                result["available_passes"] = pass_attrs
                
                # Sample a few pass properties
                for pass_attr in pass_attrs[:5]:
                    result["pass_properties"][pass_attr] = getattr(vl, pass_attr)
        
    except Exception as e:
        result["error"] = f"Error checking render passes: {str(e)}"
    
    return result


def main():
    """Run all tests and output results."""
    print("=" * 70)
    print("BLENDER 5.0 API DETECTION TEST")
    print("=" * 70)
    
    version = get_blender_version()
    print(f"\nBlender Version: {version[0]}.{version[1]}.{version[2]}")
    print(f"Full Version String: {bpy.app.version_string}")
    print("\n" + "=" * 70)
    
    tests = [
        ("Composite Node", check_composite_node),
        ("File Output Node", check_file_output_node),
        ("Group Output Node", check_group_output_node),
        ("Compositor Structure", check_compositor_structure),
        ("Path Template System", check_path_template_system),
        ("Render Layer Passes", check_render_layer_passes),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 70)
        try:
            result = test_func()
            results[test_name] = result
            
            # Pretty print important findings
            if "error" in result and result["error"]:
                print(f"  ⚠ ERROR: {result['error']}")
            
            if "exists" in result:
                status = "✓ EXISTS" if result["exists"] else "✗ NOT FOUND"
                print(f"  {status}")
            
            # Print key findings
            for key, value in result.items():
                if key in ["exists", "error"]:
                    continue
                if isinstance(value, (list, dict)) and len(str(value)) > 100:
                    print(f"  {key}: [{len(value)} items]")
                else:
                    print(f"  {key}: {value}")
                    
        except Exception as e:
            print(f"  ⚠ TEST FAILED: {str(e)}")
            results[test_name] = {"error": str(e)}
    
    # Save full results to JSON
    output_file = "blender5_api_test_results.json"
    try:
        # Convert results to JSON-serializable format
        json_results = json.dumps(results, indent=2, default=str)
        with open(output_file, 'w') as f:
            f.write(json_results)
        print(f"\n{'=' * 70}")
        print(f"Full results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠ Could not save JSON results: {str(e)}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
