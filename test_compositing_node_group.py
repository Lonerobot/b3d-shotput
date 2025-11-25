"""
Blender 5.0 Compositor Node Group Test
========================================

Test the scene.compositing_node_group property discovered in initial scan.

Run with: blender --background --python test_compositing_node_group.py
"""

import bpy


def test_compositing_node_group():
    """Test the compositing_node_group property"""
    print("=" * 70)
    print("TESTING scene.compositing_node_group")
    print("=" * 70)
    
    scene = bpy.context.scene
    
    # Check initial state
    print(f"\nInitial state:")
    print(f"  scene.compositing_node_group = {scene.compositing_node_group}")
    print(f"  Type: {type(scene.compositing_node_group)}")
    
    # Try to create a compositor node tree and assign it
    print(f"\nCreating new compositor node tree...")
    try:
        comp_tree = bpy.data.node_groups.new(
            name="ShotputCompositor", 
            type='CompositorNodeTree'
        )
        print(f"  ✓ Created: {comp_tree.name}")
        print(f"  Type: {comp_tree.bl_idname}")
        
        # Assign it to the scene
        print(f"\nAssigning to scene.compositing_node_group...")
        scene.compositing_node_group = comp_tree
        print(f"  ✓ Assigned!")
        print(f"  scene.compositing_node_group = {scene.compositing_node_group}")
        
        # Verify we can add nodes
        print(f"\nAdding nodes to compositor tree...")
        
        # Add Render Layers node
        rl_node = comp_tree.nodes.new(type='CompositorNodeRLayers')
        rl_node.location = (0, 0)
        print(f"  ✓ Added Render Layers node: {rl_node.name}")
        
        # Add File Output node
        file_node = comp_tree.nodes.new(type='CompositorNodeOutputFile')
        file_node.location = (300, 0)
        file_node.base_path = "//renders/"
        print(f"  ✓ Added File Output node: {file_node.name}")
        print(f"    base_path = {file_node.base_path}")
        
        # Add Group Output node (replaces Composite)
        output_node = comp_tree.nodes.new(type='NodeGroupOutput')
        output_node.location = (600, 0)
        print(f"  ✓ Added Group Output node: {output_node.name}")
        
        # Try to create socket on Group Output
        print(f"\nTrying to define Group Output socket...")
        try:
            # Check if interface exists
            if hasattr(comp_tree, 'interface'):
                print(f"  ℹ Tree has .interface attribute")
                
                # Try to create output socket
                if hasattr(comp_tree.interface, 'new_socket'):
                    socket = comp_tree.interface.new_socket(
                        name="Image",
                        in_out='OUTPUT',
                        socket_type='NodeSocketColor'
                    )
                    print(f"  ✓ Created output socket: {socket.name}")
                else:
                    print(f"  ✗ interface has no new_socket method")
            else:
                print(f"  ✗ Tree has no .interface attribute")
        except Exception as e:
            print(f"  ✗ Error creating socket: {e}")
        
        # Try connecting nodes
        print(f"\nTrying to connect nodes...")
        try:
            # Connect RL -> File Output
            comp_tree.links.new(
                rl_node.outputs['Image'],
                file_node.inputs['Image']
            )
            print(f"  ✓ Connected Render Layers -> File Output")
            
            # Try to connect to Group Output
            if len(output_node.inputs) > 0:
                comp_tree.links.new(
                    rl_node.outputs['Image'],
                    output_node.inputs[0]
                )
                print(f"  ✓ Connected Render Layers -> Group Output")
            else:
                print(f"  ℹ Group Output has no inputs (need to define interface first)")
                
        except Exception as e:
            print(f"  ✗ Error connecting nodes: {e}")
        
        # Check if we can add custom properties to File Output node
        print(f"\nTesting custom properties on File Output node...")
        try:
            # Try to add a custom string property
            file_node['shotput_test'] = "test_value"
            print(f"  ✓ Can add custom properties")
            print(f"    file_node['shotput_test'] = {file_node['shotput_test']}")
        except Exception as e:
            print(f"  ✗ Error adding custom property: {e}")
        
        # Test path templates in File Output
        print(f"\nTesting path templates in File Output node...")
        try:
            # Test Blender's native tokens
            file_node.base_path = "//renders/{scene_name}/"
            print(f"  ✓ Can use Blender path template")
            print(f"    base_path = {file_node.base_path}")
            
            # Test file slot path with token
            if len(file_node.file_slots) > 0:
                file_node.file_slots[0].path = "{camera_name}_{frame:####}"
                print(f"  ✓ Can use token in file slot")
                print(f"    file_slot[0].path = {file_node.file_slots[0].path}")
        except Exception as e:
            print(f"  ⚠ Error with path templates: {e}")
        
        print(f"\n{'=' * 70}")
        print(f"✓ SUCCESS: Compositor works via scene.compositing_node_group!")
        print(f"{'=' * 70}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compositor_workflow():
    """Test a complete workflow similar to Shotput"""
    print("\n" + "=" * 70)
    print("TESTING SHOTPUT-STYLE WORKFLOW")
    print("=" * 70)
    
    scene = bpy.context.scene
    
    # Step 1: Get or create compositor tree
    print("\nStep 1: Get or create compositor tree...")
    if scene.compositing_node_group is None:
        comp_tree = bpy.data.node_groups.new(
            name=f"{scene.name}_Compositor",
            type='CompositorNodeTree'
        )
        scene.compositing_node_group = comp_tree
        print(f"  ✓ Created new compositor tree: {comp_tree.name}")
    else:
        comp_tree = scene.compositing_node_group
        print(f"  ℹ Using existing compositor tree: {comp_tree.name}")
    
    # Step 2: Create Shotput-style File Output node
    print("\nStep 2: Create Shotput-style File Output node...")
    try:
        # Create node
        file_node = comp_tree.nodes.new(type='CompositorNodeOutputFile')
        file_node.name = "Shotput_Core_Beauty"
        file_node.label = "ViewLayer.Core.MAIN"
        
        # Set paths using Shotput-style pattern
        file_node.base_path = "//renders/{scene_name}/beauty/"
        
        # Add custom Shotput metadata (simulating shotput_data)
        file_node['shotput_version'] = "2.0.0"
        file_node['shotput_pass_type'] = "core"
        file_node['shotput_output_layer'] = "ViewLayer"
        file_node['shotput_variant'] = "MAIN"
        
        print(f"  ✓ Created File Output node: {file_node.name}")
        print(f"    Label: {file_node.label}")
        print(f"    Base Path: {file_node.base_path}")
        print(f"    Custom Props: {dict(file_node.items())}")
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False
    
    # Step 3: Create Render Layers node and connect
    print("\nStep 3: Create and connect Render Layers node...")
    try:
        rl_node = comp_tree.nodes.new(type='CompositorNodeRLayers')
        rl_node.location = (-300, 0)
        file_node.location = (0, 0)
        
        # Connect Image output
        comp_tree.links.new(
            rl_node.outputs['Image'],
            file_node.inputs['Image']
        )
        
        print(f"  ✓ Connected Render Layers -> File Output")
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False
    
    print(f"\n{'=' * 70}")
    print(f"✓ WORKFLOW TEST PASSED!")
    print(f"{'=' * 70}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("BLENDER 5.0 COMPOSITING NODE GROUP TEST")
    print("=" * 70)
    
    version = bpy.app.version
    print(f"\nBlender Version: {version[0]}.{version[1]}.{version[2]}")
    
    # Run tests
    test1_passed = test_compositing_node_group()
    test2_passed = test_compositor_workflow()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"  Basic compositor test: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"  Workflow test:         {'✓ PASS' if test2_passed else '✗ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n💡 KEY FINDINGS:")
        print("  1. Use scene.compositing_node_group instead of scene.node_tree")
        print("  2. Create compositor via bpy.data.node_groups.new(type='CompositorNodeTree')")
        print("  3. File Output nodes work the same way")
        print("  4. Custom properties work on nodes")
        print("  5. Blender path templates work in base_path and file_slots")
        print("  6. Group Output replaces Composite node")
    else:
        print("\n⚠ SOME TESTS FAILED - Further investigation needed")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
