"""
Color utilities for node visual feedback
"""

import bpy


def store_original_node_color(node):
    """Store the original color of a node as a custom property"""
    if hasattr(node, 'color'):
        # Store as comma-separated string
        color_str = f"{node.color[0]:.6f},{node.color[1]:.6f},{node.color[2]:.6f}"
        node["shotput_original_color"] = color_str


def restore_original_node_color(node):
    """Restore the original color of a node from custom property"""
    if "shotput_original_color" in node and hasattr(node, 'color'):
        try:
            color_str = node["shotput_original_color"]
            r, g, b = [float(x) for x in color_str.split(',')]
            node.color = (r, g, b)
            # Clean up the stored color
            del node["shotput_original_color"]
        except (ValueError, KeyError):
            # If parsing fails, don't change the color
            pass


def darken_color(color, factor=0.7):
    """Darken a color by multiplying each component by the factor"""
    return (color[0] * factor, color[1] * factor, color[2] * factor)


def apply_linked_node_color(linked_node, target_node):
    """Apply a darkened version of the linked node's color to the target node"""
    print(f"DEBUG: apply_linked_node_color called: {linked_node.name} -> {target_node.name}")
    
    if hasattr(linked_node, 'color') and hasattr(target_node, 'color'):
        # Store original color first if not already stored
        if "shotput_original_color" not in target_node:
            store_original_node_color(target_node)
            print(f"DEBUG: Stored original color for {target_node.name}")
        
        # Apply darkened version of linked node's color
        darkened_color = darken_color(linked_node.color)
        target_node.color = darkened_color
        target_node.use_custom_color = True
        print(f"DEBUG: Applied color {darkened_color} to {target_node.name}")


def update_node_label_for_linking(node, is_linked=True):
    """Add or remove [PATH-LINKED] from node label"""
    label_suffix = " [PATH-LINKED]"
    
    print(f"DEBUG: update_node_label_for_linking called for {node.name}, is_linked={is_linked}")
    
    if hasattr(node, 'label'):
        current_label = node.label
        print(f"DEBUG: Current label: '{current_label}'")
        
        if is_linked:
            # Add suffix if not already present
            if not current_label.endswith(label_suffix):
                node.label = current_label + label_suffix
                print(f"DEBUG: Updated label to: '{node.label}'")
        else:
            # Remove suffix if present
            if current_label.endswith(label_suffix):
                node.label = current_label[:-len(label_suffix)]
                print(f"DEBUG: Updated label to: '{node.label}'")


def apply_path_linked_visual_feedback(node, linked_node=None):
    """Apply visual feedback for path-linked nodes"""
    print(f"DEBUG: apply_path_linked_visual_feedback called for node {node.name if node else 'None'}")
    
    if linked_node:
        print(f"DEBUG: Applying linked visual feedback to {node.name} linked to {linked_node.name}")
        # Apply color and label changes
        apply_linked_node_color(linked_node, node)
        update_node_label_for_linking(node, is_linked=True)
    else:
        print(f"DEBUG: Removing visual feedback from {node.name}")
        # Remove visual feedback
        restore_original_node_color(node)
        update_node_label_for_linking(node, is_linked=False)
        # Keep custom color enabled so the restored original color is visible
        node.use_custom_color = True
