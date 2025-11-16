"""
Generic list management operators for Shotput property collections.
Provides Add, Remove, MoveUp, MoveDown operators with minimal code duplication.
"""
import bpy


def create_list_operators(collection_name, display_name, id_prefix, get_data_func):
    """Factory function to create list management operators
    
    Args:
        collection_name: Name of the collection property (e.g., 'core_passes')
        display_name: Human-readable name (e.g., 'Core Pass')
        id_prefix: Prefix for operator IDs (e.g., 'core_pass')
        get_data_func: Function to get the data container from context
                      (returns object with collection and index properties)
    
    Returns:
        Tuple of (Add, Remove, MoveUp, MoveDown) operator classes
    """
    
    class GenericAdd(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_add"
        bl_label = f"Add {display_name}"
        bl_description = f"Add a new {display_name.lower()} to the list"
        
        def execute(self, context):
            data = get_data_func(context)
            if not data:
                return {'CANCELLED'}
            
            collection = getattr(data, collection_name)
            item = collection.add()
            item.name = f"item{len(collection)}"
            setattr(data, f"{collection_name}_index", len(collection) - 1)
            return {'FINISHED'}
    
    class GenericRemove(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_remove"
        bl_label = f"Remove {display_name}"
        bl_description = f"Remove the selected {display_name.lower()} from the list"
        
        def execute(self, context):
            data = get_data_func(context)
            if not data:
                return {'CANCELLED'}
            
            collection = getattr(data, collection_name)
            idx = getattr(data, f"{collection_name}_index")
            
            if collection and idx < len(collection):
                collection.remove(idx)
                setattr(data, f"{collection_name}_index", max(0, idx - 1))
            
            return {'FINISHED'}
    
    class GenericMoveUp(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_move_up"
        bl_label = f"Move {display_name} Up"
        bl_description = f"Move the selected {display_name.lower()} up in the list"
        
        def execute(self, context):
            data = get_data_func(context)
            if not data:
                return {'CANCELLED'}
            
            collection = getattr(data, collection_name)
            idx = getattr(data, f"{collection_name}_index")
            
            if idx > 0:
                collection.move(idx, idx - 1)
                setattr(data, f"{collection_name}_index", idx - 1)
            
            return {'FINISHED'}
    
    class GenericMoveDown(bpy.types.Operator):
        bl_idname = f"shotput.{id_prefix}_move_down"
        bl_label = f"Move {display_name} Down"
        bl_description = f"Move the selected {display_name.lower()} down in the list"
        
        def execute(self, context):
            data = get_data_func(context)
            if not data:
                return {'CANCELLED'}
            
            collection = getattr(data, collection_name)
            idx = getattr(data, f"{collection_name}_index")
            
            if idx < len(collection) - 1:
                collection.move(idx, idx + 1)
                setattr(data, f"{collection_name}_index", idx + 1)
            
            return {'FINISHED'}
    
    return GenericAdd, GenericRemove, GenericMoveUp, GenericMoveDown


# Scene-level list operators (Core and AOV passes)
def get_scene_shotput(context):
    """Get shotput data from scene"""
    return context.scene.shotput


# Create Core Pass operators
(
    SHOTPUT_OT_CorePassAdd,
    SHOTPUT_OT_CorePassRemove,
    SHOTPUT_OT_CorePassMoveUp,
    SHOTPUT_OT_CorePassMoveDown
) = create_list_operators('core_passes', 'Core Pass', 'core_pass', get_scene_shotput)


# Create AOV Pass operators
(
    SHOTPUT_OT_AOVPassAdd,
    SHOTPUT_OT_AOVPassRemove,
    SHOTPUT_OT_AOVPassMoveUp,
    SHOTPUT_OT_AOVPassMoveDown
) = create_list_operators('aov_passes', 'AOV Pass', 'aov_pass', get_scene_shotput)


# Node-level list operators (Stored passes)
def get_node_shotput_data(context):
    """Get shotput_data from active node"""
    from ..helpers import get_active_file_output_node
    node = get_active_file_output_node(context)
    if node and hasattr(node, 'shotput_data'):
        return node.shotput_data
    return None


# Create Stored Pass operators
(
    SHOTPUT_OT_StoredPassAdd,
    SHOTPUT_OT_StoredPassRemove,
    SHOTPUT_OT_StoredPassMoveUp,
    SHOTPUT_OT_StoredPassMoveDown
) = create_list_operators('stored_passes', 'Stored Pass', 'stored_pass', get_node_shotput_data)


# All list management operator classes for registration
classes = (
    SHOTPUT_OT_CorePassAdd,
    SHOTPUT_OT_CorePassRemove,
    SHOTPUT_OT_CorePassMoveUp,
    SHOTPUT_OT_CorePassMoveDown,
    SHOTPUT_OT_AOVPassAdd,
    SHOTPUT_OT_AOVPassRemove,
    SHOTPUT_OT_AOVPassMoveUp,
    SHOTPUT_OT_AOVPassMoveDown,
    SHOTPUT_OT_StoredPassAdd,
    SHOTPUT_OT_StoredPassRemove,
    SHOTPUT_OT_StoredPassMoveUp,
    SHOTPUT_OT_StoredPassMoveDown,
)
