"""
Sync operator to synchronize stored passes with File Output node slots.
"""
import bpy
from ..helpers import get_active_file_output_node, update_node_label


class SHOTPUT_OT_SyncNodePasses(bpy.types.Operator):
    bl_idname = "shotput.sync_node_passes"
    bl_label = "Sync Node Passes"
    bl_description = "Sync the stored passes list to the actual File Output node slots (non-destructive)"
    
    def execute(self, context):
        node = get_active_file_output_node(context)
        if not node:
            self.report({'ERROR'}, "No File Output node selected")
            return {'CANCELLED'}
        if not hasattr(node, 'shotput_data'):
            self.report({'ERROR'}, "Selected node is not a Shotput File Output node")
            return {'CANCELLED'}
            
        shotput_data = node.shotput_data
        
        # Get current node slot names
        current_slots = []
        for i, file_slot in enumerate(node.file_slots):
            current_slots.append(file_slot.path)
        
        # Get desired pass names from stored_passes
        desired_passes = []
        is_data_pass_node = node.name == "Shotput_Data_Passes"
        
        for pass_item in shotput_data.stored_passes:
            if pass_item.name.strip():  # Only add non-empty names
                pass_name = pass_item.name.strip()
                
                # Handle data pass cryptomatte expansion
                if is_data_pass_node:
                    if pass_name == "Cryptomatte Object":
                        desired_passes.extend(['CryptoObject00', 'CryptoObject01', 'CryptoObject02'])
                    elif pass_name == "Cryptomatte Material":
                        desired_passes.extend(['CryptoMaterial00', 'CryptoMaterial01', 'CryptoMaterial02'])
                    elif pass_name == "Cryptomatte Asset":
                        desired_passes.extend(['CryptoAsset00', 'CryptoAsset01', 'CryptoAsset02'])
                    elif pass_name == "Depth":
                        desired_passes.append("depth")  # Map "Depth" to "depth" for compositing
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
                        desired_passes.append(channel_name)
                else:
                    # Non-data passes, use pass name directly
                    desired_passes.append(pass_name)
        
        if not desired_passes:
            self.report({'WARNING'}, "No passes defined to sync")
            return {'CANCELLED'}

        changes_made = False
        
        # Special handling for EXR multilayer format (data passes)
        if is_data_pass_node and node.format.file_format == 'OPEN_EXR_MULTILAYER':
            # For EXR multilayer, we need to recreate slots like in create_data_passes.py
            print("Shotput: Sync - EXR multilayer detected, using slot recreation approach")
            
            # Clear all existing slots and recreate them
            # This ensures proper input/slot name synchronization for EXR multilayer
            while len(node.file_slots) > 0:
                try:
                    node.inputs.remove(node.inputs[-1])
                except (RuntimeError, IndexError, ValueError):
                    break
            
            # Recreate all slots with desired names
            for desired_name in desired_passes:
                node.file_slots.new(desired_name)
                print(f"Shotput: Recreated slot: '{desired_name}'")
            
            changes_made = True
        else:
            # Standard slot renaming for non-EXR multilayer formats
            # Rename existing slots to match desired names
            for i, desired_name in enumerate(desired_passes):
                if i < len(node.file_slots):
                    current_name = node.file_slots[i].path
                    if current_name != desired_name:
                        node.file_slots[i].path = desired_name
                        changes_made = True
                        print(f"Renamed slot {i}: '{current_name}' -> '{desired_name}'")
                else:
                    # Add new slot for this pass
                    node.file_slots.new(desired_name)
                    changes_made = True
                    print(f"Added new slot: '{desired_name}'")
        
        # Handle removed passes (only if we have fewer desired passes than current slots)
        if len(desired_passes) < len(node.file_slots):
            # We have fewer desired passes than current slots
            # Rebuild file slots to match desired passes (simpler and more reliable)
            
            # Check if any of the slots to be removed have connections
            has_connections = False
            for i in range(len(desired_passes), len(node.file_slots)):
                slot = node.file_slots[i]
                if any(link.to_socket == slot for link in node.id_data.links):
                    has_connections = True
                    print(f"Keeping connected slot {i}: '{slot.path}'")
                    break
            
            # Only rebuild if no connections would be lost
            if not has_connections:
                print(f"Rebuilding file slots to match {len(desired_passes)} desired passes")
                # Clear all slots and rebuild with desired passes
                node.file_slots.clear()
                for pass_name in desired_passes:
                    node.file_slots.new(pass_name)
                changes_made = True
            else:
                print("Keeping extra slots to preserve connections")
        
        if changes_made:
            self.report({'INFO'}, f"Synced {len(desired_passes)} passes to node slots")
        else:
            self.report({'INFO'}, "Node slots already match stored passes")
        
        # Update node label based on current Shotput properties
        update_node_label(node, shotput_data)
            
        return {'FINISHED'}


classes = (
    SHOTPUT_OT_SyncNodePasses,
)
