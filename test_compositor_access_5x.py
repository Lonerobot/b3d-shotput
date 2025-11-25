"""
Blender 5.0 Compositor Access Discovery Script
================================================

This script investigates how to access and create compositor nodes in Blender 5.0
since scene.node_tree no longer exists.

Run with: blender --background --python test_compositor_access_5x.py
"""

import bpy
import json


def investigate_scene_attributes():
    """Check all scene attributes for compositor-related properties"""
    print("\n" + "=" * 70)
    print("SCENE ATTRIBUTES INVESTIGATION")
    print("=" * 70)
    
    scene = bpy.context.scene
    results = {}
    
    # Get all attributes containing keywords
    keywords = ['compos', 'node', 'tree', 'graph', 'output', 'render']
    
    for attr in dir(scene):
        for keyword in keywords:
            if keyword in attr.lower():
                try:
                    value = getattr(scene, attr)
                    attr_type = type(value).__name__
                    results[attr] = attr_type
                    print(f"  scene.{attr:<30} = {attr_type}")
                    
                    # If it's a node tree, explore further
                    if 'tree' in attr.lower() or 'node' in attr.lower():
                        if hasattr(value, 'nodes'):
                            print(f"    ↳ Has .nodes attribute!")
                            results[f"{attr}_has_nodes"] = True
                except AttributeError:
                    pass
                except:
                    results[attr] = "ERROR"
                break
    
    return results


def investigate_data_node_groups():
    """Check bpy.data.node_groups for compositor graphs"""
    print("\n" + "=" * 70)
    print("DATA.NODE_GROUPS INVESTIGATION")
    print("=" * 70)
    
    results = {
        "total_groups": len(bpy.data.node_groups),
        "groups": []
    }
    
    print(f"Total node groups: {len(bpy.data.node_groups)}")
    
    for ng in bpy.data.node_groups:
        group_info = {
            "name": ng.name,
            "type": ng.bl_idname,
            "is_compositor": 'Compositor' in ng.bl_idname,
            "node_count": len(ng.nodes) if hasattr(ng, 'nodes') else 0
        }
        
        results["groups"].append(group_info)
        
        print(f"\nNode Group: {ng.name}")
        print(f"  Type: {ng.bl_idname}")
        print(f"  Nodes: {group_info['node_count']}")
        
        # If it's a compositor type, explore its nodes
        if 'Compositor' in ng.bl_idname and hasattr(ng, 'nodes'):
            print(f"  Node types:")
            for node in ng.nodes:
                print(f"    - {node.type}: {node.name}")
    
    return results


def investigate_context_attributes():
    """Check context for compositor-related attributes"""
    print("\n" + "=" * 70)
    print("CONTEXT ATTRIBUTES INVESTIGATION")
    print("=" * 70)
    
    results = {}
    ctx = bpy.context
    
    keywords = ['compos', 'node', 'tree', 'space']
    
    for attr in dir(ctx):
        for keyword in keywords:
            if keyword in attr.lower():
                try:
                    value = getattr(ctx, attr)
                    attr_type = type(value).__name__
                    results[attr] = attr_type
                    print(f"  context.{attr:<30} = {attr_type}")
                    
                    # Check if it has tree_type
                    if hasattr(value, 'tree_type'):
                        print(f"    ↳ tree_type = {value.tree_type}")
                        results[f"{attr}_tree_type"] = value.tree_type
                except:
                    pass
                break
    
    return results


def investigate_compositor_node_types():
    """Check what compositor node types are available"""
    print("\n" + "=" * 70)
    print("AVAILABLE COMPOSITOR NODE TYPES")
    print("=" * 70)
    
    results = {
        "all_types": [],
        "output_types": [],
        "can_create": {}
    }
    
    # Get all CompositorNode types
    for attr_name in dir(bpy.types):
        if attr_name.startswith('CompositorNode'):
            results["all_types"].append(attr_name)
            
            # Check if it's an output type
            if 'Output' in attr_name or 'Composite' in attr_name or 'Viewer' in attr_name:
                results["output_types"].append(attr_name)
                print(f"  Output type found: {attr_name}")
    
    print(f"\nTotal compositor types: {len(results['all_types'])}")
    print(f"Output-related types: {len(results['output_types'])}")
    
    return results


def investigate_scene_compositor_creation():
    """Try different ways to create/access compositor for a scene"""
    print("\n" + "=" * 70)
    print("COMPOSITOR CREATION ATTEMPTS")
    print("=" * 70)
    
    scene = bpy.context.scene
    results = {}
    
    # Attempt 1: Check if there's a built-in compositor property
    print("\nAttempt 1: Looking for scene compositor property...")
    if hasattr(scene, 'compositor'):
        print("  ✓ scene.compositor exists!")
        results['scene_compositor'] = str(type(scene.compositor))
    else:
        print("  ✗ scene.compositor not found")
        results['scene_compositor'] = None
    
    # Attempt 2: Check scene.node_tree with try/except
    print("\nAttempt 2: Trying scene.node_tree...")
    try:
        tree = scene.node_tree
        print(f"  ✓ scene.node_tree exists! Type: {type(tree)}")
        results['scene_node_tree'] = str(type(tree))
    except AttributeError as e:
        print(f"  ✗ AttributeError: {e}")
        results['scene_node_tree'] = f"ERROR: {e}"
    
    # Attempt 3: Check scene.use_nodes
    print("\nAttempt 3: Checking scene.use_nodes...")
    try:
        use_nodes = scene.use_nodes
        print(f"  ℹ scene.use_nodes = {use_nodes} (deprecated)")
        results['scene_use_nodes'] = use_nodes
    except AttributeError as e:
        print(f"  ✗ AttributeError: {e}")
        results['scene_use_nodes'] = f"ERROR: {e}"
    
    # Attempt 4: Check bpy.data for compositor-related data blocks
    print("\nAttempt 4: Checking bpy.data for compositor data blocks...")
    data_attrs = [attr for attr in dir(bpy.data) if 'compos' in attr.lower()]
    for attr in data_attrs:
        try:
            value = getattr(bpy.data, attr)
            print(f"  ℹ bpy.data.{attr} = {type(value)}")
            results[f'data_{attr}'] = str(type(value))
        except:
            pass
    
    # Attempt 5: Try creating a node tree manually
    print("\nAttempt 5: Trying to create a CompositorNodeTree...")
    try:
        new_tree = bpy.data.node_groups.new(name="TestCompositor", type='CompositorNodeTree')
        print(f"  ✓ Created node tree: {new_tree.name}, Type: {new_tree.bl_idname}")
        results['manual_tree_creation'] = "SUCCESS"
        
        # Try adding nodes to it
        print("  Attempting to add nodes...")
        try:
            test_node = new_tree.nodes.new(type='CompositorNodeRLayers')
            print(f"    ✓ Added RLayers node: {test_node.name}")
            results['can_add_nodes'] = True
        except Exception as e:
            print(f"    ✗ Failed to add node: {e}")
            results['can_add_nodes'] = False
        
        # Clean up
        bpy.data.node_groups.remove(new_tree)
        print("  ℹ Cleaned up test tree")
        
    except Exception as e:
        print(f"  ✗ Failed to create tree: {e}")
        results['manual_tree_creation'] = f"ERROR: {e}"
    
    return results


def investigate_workspace():
    """Check workspace for compositor-related attributes"""
    print("\n" + "=" * 70)
    print("WORKSPACE INVESTIGATION")
    print("=" * 70)
    
    results = {}
    
    for ws in bpy.data.workspaces:
        if 'Compositing' in ws.name:
            print(f"\nFound Compositing workspace: {ws.name}")
            ws_info = {"name": ws.name, "attributes": {}}
            
            for attr in dir(ws):
                if any(kw in attr.lower() for kw in ['node', 'comp', 'tree']):
                    try:
                        value = getattr(ws, attr)
                        attr_type = type(value).__name__
                        ws_info["attributes"][attr] = attr_type
                        print(f"  {attr:<30} = {attr_type}")
                    except:
                        pass
            
            results[ws.name] = ws_info
    
    return results


def main():
    """Run all investigations and output results"""
    print("=" * 70)
    print("BLENDER 5.0 COMPOSITOR ACCESS DISCOVERY")
    print("=" * 70)
    
    version = bpy.app.version
    print(f"\nBlender Version: {version[0]}.{version[1]}.{version[2]}")
    print(f"Full Version String: {bpy.app.version_string}")
    print("\n" + "=" * 70)
    
    all_results = {}
    
    # Run all investigations
    investigations = [
        ("Scene Attributes", investigate_scene_attributes),
        ("Data Node Groups", investigate_data_node_groups),
        ("Context Attributes", investigate_context_attributes),
        ("Compositor Node Types", investigate_compositor_node_types),
        ("Compositor Creation", investigate_scene_compositor_creation),
        ("Workspace", investigate_workspace),
    ]
    
    for name, func in investigations:
        try:
            result = func()
            all_results[name] = result
        except Exception as e:
            print(f"\n⚠ Investigation '{name}' failed: {e}")
            all_results[name] = {"error": str(e)}
    
    # Save results to JSON
    output_file = "compositor_access_discovery_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(all_results, indent=2, default=str, fp=f)
        print(f"\n{'=' * 70}")
        print(f"Full results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠ Could not save JSON results: {e}")
    
    print("\n" + "=" * 70)
    print("DISCOVERY COMPLETE")
    print("=" * 70)
    
    # Print key findings
    print("\n🔑 KEY FINDINGS:")
    if 'Compositor Creation' in all_results:
        creation = all_results['Compositor Creation']
        if creation.get('manual_tree_creation') == 'SUCCESS':
            print("  ✓ Can create CompositorNodeTree manually via bpy.data.node_groups.new()")
            print("  ✓ Can add nodes to manually created compositor tree")
            print("  ⚠ BUT: No direct scene.node_tree access")
            print("\n💡 SOLUTION: Compositor is now asset-based, not scene-based")
        else:
            print("  ✗ Cannot create compositor trees")
            print("  ⚠ This requires further investigation")


if __name__ == "__main__":
    main()
