import bpy

from ..utils.log import LoggerFactory
logger = LoggerFactory.logger_obj()

class OT_Scan_Shader_AOVs(bpy.types.Operator):
    bl_idname = "shotput.scan_shader_aovs"
    bl_label = "Scan for Shader AOVs"
    bl_description = "Scan the current scene for shader AOV outputs and add any missing ones to the AOV list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        logger.info("Scan Shader AOVs operator clicked")
        print("Shotput: Scanning for shader AOVs")
        
        # Get scene properties
        scene = context.scene
        if not hasattr(scene, 'shotput'):
            self.report({'ERROR'}, "Shotput properties not found on scene")
            return {'CANCELLED'}
        
        shotput_props = scene.shotput
        
        # Collect existing AOV pass names (case-insensitive)
        existing_aov_names = {aov_pass.name.lower() for aov_pass in shotput_props.aov_passes}
        print(f"Shotput: Found {len(existing_aov_names)} existing AOV passes: {list(existing_aov_names)}")
        
        # Scan all materials for AOV output nodes
        shader_aovs = set()
        materials_scanned = 0
        aov_nodes_found = 0
        
        for material in bpy.data.materials:
            if not material.use_nodes or not material.node_tree:
                continue
                
            materials_scanned += 1
            
            # Look for AOV Output nodes in the material
            for node in material.node_tree.nodes:
                if node.type == 'OUTPUT_AOV':
                    aov_nodes_found += 1
                    aov_name = node.name
                    
                    # Clean up the AOV name (remove common prefixes/suffixes)
                    cleaned_name = self._clean_aov_name(aov_name)
                    
                    if cleaned_name:
                        shader_aovs.add(cleaned_name)
                        print(f"Shotput: Found AOV output '{aov_name}' -> '{cleaned_name}' in material '{material.name}'")
        
        print(f"Shotput: Scanned {materials_scanned} materials, found {aov_nodes_found} AOV output nodes")
        print(f"Shotput: Unique shader AOVs found: {list(shader_aovs)}")
        
        # Check for AOVs in view layer (Cycles AOV passes)
        view_layer_aovs = set()
        view_layer = context.view_layer
        
        if hasattr(view_layer, 'aovs'):
            for aov in view_layer.aovs:
                if aov.name:
                    cleaned_name = self._clean_aov_name(aov.name)
                    if cleaned_name:
                        view_layer_aovs.add(cleaned_name)
                        print(f"Shotput: Found view layer AOV: '{aov.name}' -> '{cleaned_name}'")
        
        # Combine shader AOVs and view layer AOVs
        all_aovs = shader_aovs | view_layer_aovs
        
        if not all_aovs:
            self.report({'INFO'}, "No shader AOVs found in the scene")
            return {'FINISHED'}
        
        # Find AOVs that are not already in the list
        new_aovs = []
        for aov_name in sorted(all_aovs):  # Sort for consistent ordering
            if aov_name.lower() not in existing_aov_names:
                new_aovs.append(aov_name)
        
        if not new_aovs:
            self.report({'INFO'}, f"All {len(all_aovs)} shader AOVs are already in the AOV list")
            return {'FINISHED'}
        
        # Add new AOVs to the list
        added_count = 0
        for aov_name in new_aovs:
            new_pass = shotput_props.aov_passes.add()
            new_pass.name = aov_name
            added_count += 1
            print(f"Shotput: Added AOV pass: '{aov_name}'")
        
        # Update the index to the last added item
        if added_count > 0:
            shotput_props.aov_passes_index = len(shotput_props.aov_passes) - 1
        
        logger.info(f"Added {added_count} new AOV passes from scene scan")
        
        self.report({'INFO'}, f"Added {added_count} new AOV passes: {', '.join(new_aovs)}")
        
        return {'FINISHED'}
    
    def _clean_aov_name(self, raw_name):
        """Clean up AOV names by removing common prefixes and making them suitable for passes."""
        if not raw_name:
            return ""
        
        # Remove common prefixes that Blender might add
        prefixes_to_remove = [
            "AOV Output",
            "AOV_Output", 
            "AOV.",
            "AOV_",
            "Output_",
            "output_",
        ]
        
        cleaned = raw_name.strip()
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove common suffixes
        suffixes_to_remove = [
            "_AOV",
            "_aov", 
            ".AOV",
            ".aov",
            "_Output",
            "_output",
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
                break
        
        # Replace spaces and special characters with underscores
        cleaned = cleaned.replace(" ", "_")
        cleaned = cleaned.replace("-", "_")
        cleaned = cleaned.replace(".", "_")
        
        # Remove multiple consecutive underscores
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")
        
        # Remove leading/trailing underscores
        cleaned = cleaned.strip("_")
        
        # Convert to a reasonable case (keep the original case mostly)
        # but ensure it starts with a letter or underscore
        if cleaned and not (cleaned[0].isalpha() or cleaned[0] == '_'):
            cleaned = f"AOV_{cleaned}"
        
        return cleaned if cleaned else ""
