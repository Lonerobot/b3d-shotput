"""
Lazy Hook-up Utility for Shotput

This module handles automatic connection of File Output nodes to render layer outputs
based on fuzzy matching rules.
"""

import bpy
from .log import LoggerFactory

logger = LoggerFactory.logger_obj()


def get_render_layers(context):
    """Get all render layers in the scene"""
    render_layers = []
    for view_layer in context.scene.view_layers:
        render_layers.append(view_layer.name)
    return render_layers


def get_render_layer_node(context):
    """
    Get the render layer node to connect to.
    Returns the node and view layer name.
    If there's only one render layer, use it.
    If there are multiple, use the currently selected one from Shotput properties.
    """
    if not context.scene.node_tree:
        return None, None
    
    render_layers = get_render_layers(context)
    
    if len(render_layers) == 0:
        logger.warning("No render layers found in scene")
        return None, None
    
    # If only one render layer, use it
    if len(render_layers) == 1:
        target_layer = render_layers[0]
    else:
        # Use the selected render layer from Shotput properties
        shotput_props = context.scene.shotput
        target_layer = shotput_props.render_layer
        
        # Validate that the selected layer exists
        if target_layer not in render_layers:
            logger.warning(f"Selected render layer '{target_layer}' not found. Available: {render_layers}")
            return None, None
    
    # Find the Render Layers node for this view layer
    compositor = context.scene.node_tree
    for node in compositor.nodes:
        if node.type == 'R_LAYERS' and hasattr(node, 'layer') and node.layer == target_layer:
            return node, target_layer
    
    logger.warning(f"Render Layers node not found for layer '{target_layer}'")
    return None, None


def fuzzy_match_output(output_name, target_names):
    """
    Fuzzy match an output socket name to target pass names.
    
    Args:
        output_name: Name of the render layer output socket
        target_names: List of target pass names to match against
        
    Returns:
        Matched target name or None
    """
    output_lower = output_name.lower()
    
    # Debug logging for cryptomatte channels
    if 'crypto' in output_lower:
        logger.debug(f"Fuzzy matching cryptomatte output '{output_name}' against targets: {target_names}")
    
    # Direct exact matches (case insensitive)
    for target in target_names:
        if output_lower == target.lower():
            if 'crypto' in output_lower:
                logger.debug(f"Exact match found: '{output_name}' -> '{target}'")
            return target
    
    # Special fuzzy matching rules
    fuzzy_rules = {
        'depth': ['z', 'depth'],
        'z': ['z', 'depth'], 
        'image': ['beauty', 'image'],
        'beauty': ['beauty', 'image'],
        'diffuse': ['diffuse', 'diff'],
        'specular': ['specular', 'spec'],
        'normal': ['normal', 'norm'],
        'vector': ['vector', 'motion', 'motionvector'],
        'shadow': ['shadow'],
        'ao': ['ao', 'ambient', 'occlusion', 'ambientocclusion'],
        'reflection': ['reflection', 'refl'],
        'emit': ['emission', 'emit'],
        'sss': ['sss', 'subsurface'],
        'transmission': ['transmission', 'trans'],
        'volume': ['volume', 'vol'],
        'mist': ['mist'],
        'position': ['position', 'pos'],
    }
    
    # Check for exact cryptomatte matches first (case insensitive)
    # These should be exact matches like CryptoObject00 -> cryptoobject00
    for target in target_names:
        target_lower = target.lower()
        if 'crypto' in target_lower and output_lower == target_lower:
            return target
    
    # Special handling for cryptomatte numbered channels - must match numbers exactly
    if 'crypto' in output_lower:
        for target in target_names:
            target_lower = target.lower()
            if 'crypto' in target_lower and output_lower == target_lower:
                # Exact match for numbered cryptomatte channels
                return target
    
    # Check fuzzy rules
    for target in target_names:
        target_lower = target.lower()
        
        # Check if target matches any rule
        for rule_key, rule_values in fuzzy_rules.items():
            if target_lower in rule_values and output_lower in rule_values:
                return target
            
        # Check if output contains target or vice versa
        if target_lower in output_lower or output_lower in target_lower:
            return target
    
    return None


def connect_file_output_to_render_layer(context, file_output_node, target_pass_names=None):
    """
    Connect a File Output node to appropriate render layer outputs.
    
    Args:
        context: Blender context
        file_output_node: The File Output node to connect
        target_pass_names: Optional list of target pass names to match against.
                          If None, will use the node's stored passes or file slot names.
                          
    Returns:
        Dictionary of connections made: {slot_index: (output_socket, pass_name)}
    """
    render_layer_node, layer_name = get_render_layer_node(context)
    if not render_layer_node:
        logger.warning("Cannot connect: no render layer node found")
        return {}

    # Get target pass names
    if target_pass_names is None:
        target_pass_names = []
        
        # Special handling for data pass nodes - expand cryptomatte passes
        is_data_pass_node = file_output_node.name == "Shotput_Data_Passes"
        
        if is_data_pass_node and hasattr(file_output_node, 'shotput_data') and file_output_node.shotput_data.stored_passes:
            # For data passes, expand cryptomatte and map display names to channel names
            for pass_item in file_output_node.shotput_data.stored_passes:
                if pass_item.name.strip():
                    pass_name = pass_item.name.strip()
                    
                    # Handle cryptomatte expansion (same logic as sync operator and create_data_passes)
                    if pass_name == "Cryptomatte Object":
                        target_pass_names.extend(['CryptoObject00', 'CryptoObject01', 'CryptoObject02'])
                    elif pass_name == "Cryptomatte Material":
                        target_pass_names.extend(['CryptoMaterial00', 'CryptoMaterial01', 'CryptoMaterial02'])
                    elif pass_name == "Cryptomatte Asset":
                        target_pass_names.extend(['CryptoAsset00', 'CryptoAsset01', 'CryptoAsset02'])
                    elif pass_name == "Depth":
                        target_pass_names.append("depth")  # Map "Depth" to "depth" for compositing
                    else:
                        # Map display names back to channel names for data passes
                        channel_mapping = {
                            "Mist": "mist",
                            "Normal": "normal", 
                            "Motion Vector": "vector",
                            "Position": "position",
                            "Ambient Occlusion": "occlusion"
                        }
                        channel_name = channel_mapping.get(pass_name, pass_name.lower())
                        target_pass_names.append(channel_name)
        else:
            # Try to get from stored passes first (non-data passes)
            if hasattr(file_output_node, 'shotput_data') and file_output_node.shotput_data.stored_passes:
                target_pass_names = [item.name for item in file_output_node.shotput_data.stored_passes if item.name.strip()]
            
            # Fallback to file slot names
            if not target_pass_names:
                target_pass_names = [slot.path for slot in file_output_node.file_slots if slot.path.strip()]
    
    if not target_pass_names:
        logger.warning("No target pass names available for connection")
        return {}
    
    connections_made = {}
    compositor = context.scene.node_tree
    
    logger.info(f"Attempting to connect File Output node to render layer '{layer_name}'")
    logger.info(f"Target passes: {target_pass_names}")
    logger.info(f"Available outputs: {[output.name for output in render_layer_node.outputs]}")
    
    # For data passes, also log the expansion logic used
    if file_output_node.name == "Shotput_Data_Passes" and target_pass_names:
        logger.debug(f"Data pass node detected - used cryptomatte expansion and channel name mapping")
    
    # Try to match each file slot to an output
    for slot_index, target_pass in enumerate(target_pass_names):
        if slot_index >= len(file_output_node.file_slots):
            logger.debug(f"Skipping slot {slot_index} - exceeds available file slots ({len(file_output_node.file_slots)})")
            break
            
        logger.debug(f"Trying to match slot {slot_index}: '{target_pass}'")
            
        # Find matching output socket
        matched_output = None
        for output_socket in render_layer_node.outputs:
            if fuzzy_match_output(output_socket.name, [target_pass]):
                matched_output = output_socket
                logger.debug(f"Matched render layer output '{output_socket.name}' to target '{target_pass}'")
                break
        
        if matched_output:
            # Make the connection
            try:
                input_socket = file_output_node.inputs[slot_index]
                compositor.links.new(matched_output, input_socket)
                connections_made[slot_index] = (matched_output, target_pass)
                logger.info(f"Connected '{matched_output.name}' -> '{target_pass}' (slot {slot_index})")
            except Exception as e:
                logger.error(f"Failed to connect '{matched_output.name}' to slot {slot_index}: {e}")
        else:
            logger.debug(f"No matching output found for pass '{target_pass}'")
            # List all available outputs that contain 'crypto' for debugging
            crypto_outputs = [out.name for out in render_layer_node.outputs if 'crypto' in out.name.lower()]
            if crypto_outputs and 'crypto' in target_pass.lower():
                logger.debug(f"Available cryptomatte outputs: {crypto_outputs}")
    
    if connections_made:
        logger.info(f"Successfully made {len(connections_made)} connections")
    else:
        logger.warning("No connections could be made")
    
    return connections_made


def connect_composite_to_render_layer(context, composite_node):
    """
    Connect a Composite node to the main render layer image output.
    
    Args:
        context: Blender context
        composite_node: The Composite node to connect
        
    Returns:
        True if connection was made, False otherwise
    """
    render_layer_node, layer_name = get_render_layer_node(context)
    if not render_layer_node:
        logger.warning("Cannot connect composite: no render layer node found")
        return False
    
    # Look for Image output (main beauty pass)
    image_output = None
    for output_socket in render_layer_node.outputs:
        if fuzzy_match_output(output_socket.name, ['image', 'beauty']):
            image_output = output_socket
            break
    
    if not image_output:
        logger.warning("No Image/Beauty output found on render layer node")
        return False
    
    # Connect to composite node's Image input
    try:
        compositor = context.scene.node_tree
        compositor.links.new(image_output, composite_node.inputs['Image'])
        logger.info(f"Connected '{image_output.name}' to Composite node")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Composite node: {e}")
        return False


def should_auto_connect(context):
    """
    Check if lazy hook-up is enabled in Shotput properties.
    
    Args:
        context: Blender context
        
    Returns:
        True if auto-connection should happen, False otherwise
    """
    if not hasattr(context.scene, 'shotput'):
        return False
    
    return context.scene.shotput.lazy_hook_up


def auto_connect_node(context, node, target_pass_names=None):
    """
    Automatically connect a node if lazy hook-up is enabled.
    
    Args:
        context: Blender context
        node: The node to connect (File Output or Composite)
        target_pass_names: Optional target pass names for File Output nodes
        
    Returns:
        True if connections were made, False otherwise
    """
    if not should_auto_connect(context):
        return False
    
    if node.type == 'OUTPUT_FILE':
        connections = connect_file_output_to_render_layer(context, node, target_pass_names)
        return len(connections) > 0
    elif node.type == 'COMPOSITE':
        return connect_composite_to_render_layer(context, node)
    else:
        logger.warning(f"Auto-connect not supported for node type: {node.type}")
        return False
