"""
Blender 5.0 File Output Node Investigation
============================================

Investigate the new structure of CompositorNodeOutputFile in Blender 5.0

Run with: blender --background --python test_file_output_node_5x.py
"""

import bpy


def investigate_file_output_node():
    """Investigate CompositorNodeOutputFile structure"""
    print("=" * 70)
    print("FILE OUTPUT NODE INVESTIGATION")
    print("=" * 70)
    
    # Create a compositor tree
    comp_tree = bpy.data.node_groups.new(
        name="TestCompositor",
        type='CompositorNodeTree'
    )
    
    # Create File Output node
    file_node = comp_tree.nodes.new(type='CompositorNodeOutputFile')
    
    print(f"\nFile Output Node Created: {file_node.name}")
    print(f"Type: {file_node.type}")
    
    # Get all attributes
    print(f"\n{'=' * 70}")
    print(f"ALL ATTRIBUTES:")
    print(f"{'=' * 70}")
    
    attributes = {}
    for attr in sorted(dir(file_node)):
        if attr.startswith('_'):
            continue
        try:
            value = getattr(file_node, attr)
            attr_type = type(value).__name__
            attributes[attr] = attr_type
            
            # Print interesting ones
            if not callable(value):
                print(f"  {attr:<40} = {attr_type}")
                
                # Show value for simple types
                if attr_type in ['str', 'int', 'float', 'bool']:
                    print(f"    └─ value: {value}")
                    
        except Exception as e:
            attributes[attr] = f"ERROR: {e}"
    
    # Specifically look for path-related attributes
    print(f"\n{'=' * 70}")
    print(f"PATH-RELATED ATTRIBUTES:")
    print(f"{'=' * 70}")
    
    path_keywords = ['path', 'base', 'dir', 'folder', 'output', 'file']
    for attr in sorted(attributes.keys()):
        for keyword in path_keywords:
            if keyword in attr.lower():
                print(f"  {attr:<40} = {attributes[attr]}")
                try:
                    value = getattr(file_node, attr)
                    if not callable(value):
                        print(f"    └─ value: {value}")
                except:
                    pass
                break
    
    # Check file_slots
    print(f"\n{'=' * 70}")
    print(f"FILE SLOTS:")
    print(f"={'=' * 70}")
    
    if hasattr(file_node, 'file_slots'):
        print(f"  file_slots exists: {type(file_node.file_slots)}")
        print(f"  Number of slots: {len(file_node.file_slots)}")
        
        if len(file_node.file_slots) > 0:
            slot = file_node.file_slots[0]
            print(f"\n  First slot attributes:")
            for attr in sorted(dir(slot)):
                if not attr.startswith('_'):
                    try:
                        value = getattr(slot, attr)
                        if not callable(value):
                            print(f"    {attr:<36} = {value}")
                    except:
                        pass
    else:
        print(f"  ✗ file_slots not found")
    
    # Check format
    print(f"\n{'=' * 70}")
    print(f"FORMAT SETTINGS:")
    print(f"{'=' * 70}")
    
    if hasattr(file_node, 'format'):
        print(f"  format exists: {type(file_node.format)}")
        format_obj = file_node.format
        for attr in sorted(dir(format_obj)):
            if not attr.startswith('_'):
                try:
                    value = getattr(format_obj, attr)
                    if not callable(value):
                        print(f"    {attr:<36} = {value}")
                except:
                    pass
    else:
        print(f"  ✗ format not found")
    
    # Try to set properties we used to use
    print(f"\n{'=' * 70}")
    print(f"TESTING PROPERTY SETTERS:")
    print(f"{'=' * 70}")
    
    # Test 1: base_path (Blender 4.x)
    print(f"\n  Test: file_node.base_path = '//renders/'")
    try:
        file_node.base_path = "//renders/"
        print(f"    ✓ SUCCESS")
        print(f"    value: {file_node.base_path}")
    except AttributeError as e:
        print(f"    ✗ FAILED: {e}")
        
        # Look for alternatives
        print(f"\n    Looking for alternatives...")
        for attr in ['path', 'directory', 'folder', 'output_path']:
            if hasattr(file_node, attr):
                print(f"      Found: file_node.{attr}")
                try:
                    value = getattr(file_node, attr)
                    print(f"        Type: {type(value)}")
                    print(f"        Value: {value}")
                    
                    # Try to set it
                    setattr(file_node, attr, "//test/")
                    print(f"        ✓ Can set value")
                    new_value = getattr(file_node, attr)
                    print(f"        New value: {new_value}")
                except Exception as set_error:
                    print(f"        ✗ Cannot set: {set_error}")
                except:
                    pass
    
    # Test 2: file_slots[].path (Blender 4.x)
    print(f"\n  Test: file_node.file_slots[0].path = 'beauty'")
    if hasattr(file_node, 'file_slots') and len(file_node.file_slots) > 0:
        try:
            file_node.file_slots[0].path = "beauty"
            print(f"    ✓ SUCCESS")
            print(f"    value: {file_node.file_slots[0].path}")
        except AttributeError as e:
            print(f"    ✗ FAILED: {e}")
    else:
        print(f"    ⚠ SKIPPED: No file_slots available")
    
    # Test 3: Check inputs (maybe path is an input now?)
    print(f"\n{'=' * 70}")
    print(f"NODE INPUTS:")
    print(f"{'=' * 70}")
    
    if hasattr(file_node, 'inputs'):
        print(f"  Number of inputs: {len(file_node.inputs)}")
        for i, inp in enumerate(file_node.inputs):
            print(f"\n  Input {i}: {inp.name}")
            print(f"    Type: {inp.type}")
            print(f"    Identifier: {inp.identifier}")
            
            # Check for path-related inputs
            if 'path' in inp.name.lower() or 'file' in inp.name.lower():
                print(f"    ⚠ PATH-RELATED INPUT FOUND!")
    
    # Cleanup
    bpy.data.node_groups.remove(comp_tree)
    
    print(f"\n{'=' * 70}")
    print(f"INVESTIGATION COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    investigate_file_output_node()
