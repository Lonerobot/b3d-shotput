"""
Lazy Hook-up Utility for Shotput

This module handles automatic connection of File Output nodes to render layer outputs
using the systematic pass mapping system.
"""

import bpy
from .log import LoggerFactory
from .pass_mapping import pass_mapping

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
    If there are multiple, try selected render layer node first, then Shotput properties.
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
        # Multiple render layers - try to find a selected render layer node first
        target_layer = None
        
        # Check if there's a selected render layer node we can use
        for node in context.scene.node_tree.nodes:
            if node.type == 'R_LAYERS' and node.select:
                target_layer = node.layer
                print(f"Shotput: Auto-connect using selected render layer node: {target_layer}")
                break
        
        # If no selected render layer node found, use Shotput properties
        if not target_layer:
            shotput_props = context.scene.shotput
            target_layer = shotput_props.render_layer
            
            # Validate that the selected layer exists
            if target_layer not in render_layers:
                logger.warning(f"Selected render layer '{target_layer}' not found. Available: {render_layers}")
                return None, None
            print(f"Shotput: Auto-connect using render layer from Shotput properties: {target_layer}")
    
    # Find the Render Layers node for this view layer
    compositor = context.scene.node_tree
    for node in compositor.nodes:
        if node.type == 'R_LAYERS' and hasattr(node, 'layer') and node.layer == target_layer:
            return node, target_layer
    
    logger.warning(f"Render Layers node not found for layer '{target_layer}'")
    return None, None


def match_pass_to_output(pass_name, available_outputs, is_data_pass=False):
    """
    Match a Shotput pass name to available render layer outputs using the mapping system.
    
    Args:
        pass_name: Name of the Shotput pass
        available_outputs: List of available render layer output names
        is_data_pass: True if this is a data pass, False for core/AOV passes
        
    Returns:
        List of matched output names (empty if no matches)
    """
    # FIRST: Try exact match (case insensitive) - this handles cryptomatte channels
    # like CryptoObject00 -> CryptoObject00
    for output in available_outputs:
        if output.lower() == pass_name.lower():
            return [output]
    
    # SECOND: Try the new systematic mapping approach
    if is_data_pass:
        # Handle data passes with direct/complex mappings
        if pass_mapping.is_complex_pass(pass_name):
            # Complex passes like cryptomattes
            complex_outputs = pass_mapping.get_complex_pass_outputs(pass_name)
            if complex_outputs:
                return [output for output in complex_outputs if output in available_outputs]
        else:
            # Direct data pass mapping
            mapping = pass_mapping.get_data_pass_mapping(pass_name)
            if mapping:
                _, output_name = mapping
                return [output_name] if output_name in available_outputs else []
    else:
        # Handle core/AOV passes with fuzzy matching
        matches = pass_mapping.find_core_pass_matches(pass_name, available_outputs)
        if matches:
            return matches
    
    # THIRD: Fallback to old-style fuzzy matching for compatibility
    # This handles cases where the systematic mapping doesn't cover everything
    for output in available_outputs:
        if _old_style_fuzzy_match(output.lower(), pass_name.lower()):
            return [output]
    
    return []


def _old_style_fuzzy_match(output_lower, target_lower):
    """
    Legacy fuzzy matching rules for backward compatibility
    """
    # Direct match
    if output_lower == target_lower:
        return True
    
    # Special fuzzy matching rules (from the old system)
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
        # Grease pencil variations  
        'greasepencil': ['gp', 'grease', 'greasepencil', 'line', 'linework', 'lines', 'outline'],
    }
    
    # Check fuzzy rules
    for rule_values in fuzzy_rules.values():
        if target_lower in rule_values and output_lower in rule_values:
            return True
    
    # Check if specific key matches
    for rule_key, rule_values in fuzzy_rules.items():
        if rule_key == output_lower and target_lower in rule_values:
            return True
        if rule_key == target_lower and output_lower in rule_values:
            return True
    
    # Check if target contains output or vice versa (for partial matches)
    if len(target_lower) >= 3 and len(output_lower) >= 3:
        if target_lower in output_lower or output_lower in target_lower:
            return True
    
    return False


def enable_view_layer_pass(context, pass_name):
    """
    Enable the corresponding view layer pass for a Shotput pass.
    
    Args:
        context: Blender context
        pass_name: Shotput pass name
        
    Returns:
        True if successfully enabled, False otherwise
    """
    view_layer_prop = pass_mapping.get_view_layer_property(pass_name)
    if not view_layer_prop:
        return False
    
    try:
        view_layer = context.view_layer
        if hasattr(view_layer, view_layer_prop):
            setattr(view_layer, view_layer_prop, True)
            logger.debug(f"Enabled view layer pass: {view_layer_prop}")
            return True
        else:
            logger.warning(f"View layer property '{view_layer_prop}' not found")
            return False
    except Exception as e:
        logger.error(f"Failed to enable view layer pass {view_layer_prop}: {e}")
        return False


def fuzzy_match_output(output_name, target_names):
    """
    DEPRECATED: Legacy fuzzy matching - use match_pass_to_output instead.
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
    
    # Determine if this is a data pass node for mapping purposes
    is_data_pass_node = file_output_node.name == "Shotput_Data_Passes"
    
    # Try to match each file slot to an output using the new mapping system
    available_output_names = [output.name for output in render_layer_node.outputs]
    
    for slot_index, target_pass in enumerate(target_pass_names):
        if slot_index >= len(file_output_node.file_slots):
            logger.debug(f"Skipping slot {slot_index} - exceeds available file slots ({len(file_output_node.file_slots)})")
            break
            
        logger.debug(f"Trying to match slot {slot_index}: '{target_pass}'")
        
        # Use new systematic matching
        matched_outputs = match_pass_to_output(target_pass, available_output_names, is_data_pass_node)
        
        if matched_outputs:
            # Use the first (preferred) match
            output_name = matched_outputs[0]
            
            # Find the actual output socket
            matched_output_socket = None
            for output_socket in render_layer_node.outputs:
                if output_socket.name == output_name:
                    matched_output_socket = output_socket
                    break
            
            if matched_output_socket:
                # Enable the view layer pass if this is a data pass
                if is_data_pass_node:
                    enable_view_layer_pass(context, target_pass)
                
                # Make the connection
                try:
                    input_socket = file_output_node.inputs[slot_index]
                    compositor.links.new(matched_output_socket, input_socket)
                    connections_made[slot_index] = (matched_output_socket, target_pass)
                    logger.info(f"Connected '{matched_output_socket.name}' -> '{target_pass}' (slot {slot_index})")
                except Exception as e:
                    logger.error(f"Failed to connect '{matched_output_socket.name}' to slot {slot_index}: {e}")
            else:
                logger.warning(f"Output socket '{output_name}' not found in render layer node")
        else:
            logger.debug(f"No matching output found for pass '{target_pass}'")
            # For debugging, show what was available
            if is_data_pass_node and any('crypto' in name.lower() for name in [target_pass]):
                crypto_outputs = [name for name in available_output_names if 'crypto' in name.lower()]
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
