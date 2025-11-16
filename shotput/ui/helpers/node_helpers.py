"""
Helper functions for working with nodes in the compositor.
"""
import bpy


def get_active_file_output_node(context):
    """Helper function to get active File Output node from context
    
    Args:
        context: Blender context
        
    Returns:
        Active File Output node if found, None otherwise
    """
    active_node = None
    
    # Try context.active_node first
    if hasattr(context, 'active_node') and context.active_node:
        active_node = context.active_node
    # Try getting from space data
    elif context.space_data and hasattr(context.space_data, 'node_tree'):
        node_tree = context.space_data.node_tree
        if node_tree and hasattr(node_tree.nodes, 'active'):
            active_node = node_tree.nodes.active
    # Try getting from scene node tree (compositor)
    elif hasattr(context.scene, 'node_tree') and context.scene.node_tree:
        node_tree = context.scene.node_tree
        if hasattr(node_tree.nodes, 'active'):
            active_node = node_tree.nodes.active
    # If still no node, try to find any selected File Output node
    elif hasattr(context.scene, 'node_tree') and context.scene.node_tree:
        node_tree = context.scene.node_tree
        for node in node_tree.nodes:
            if node.type == 'OUTPUT_FILE' and node.select and hasattr(node, 'shotput_data'):
                active_node = node
                break
    
    return active_node if active_node and active_node.type == 'OUTPUT_FILE' else None


def update_node_label(node, shotput_data):
    """Update the node label based on Shotput properties
    
    Args:
        node: Blender node to update
        shotput_data: Shotput property group attached to node
    """
    try:
        # Get the current properties
        output_layer = getattr(shotput_data, 'output_layer', 'ViewLayer')
        pass_name = getattr(shotput_data, 'pass_name', 'Pass')
        variant = getattr(shotput_data, 'variant', 'MAIN')
        
        # Generate new label in the standard format
        new_label = f"{output_layer}.{pass_name}.{variant}"
        
        # Only update if the label has changed
        if node.label != new_label:
            old_label = node.label
            node.label = new_label
            print(f"Shotput: Updated node label: '{old_label}' -> '{new_label}'")
            
    except Exception as e:
        print(f"Shotput: Error updating node label: {e}")
