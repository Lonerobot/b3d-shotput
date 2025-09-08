import bpy

def get_file_output_nodes(self, context):
    """Generate enum items for File Output nodes only"""
    items = []
    scene = context.scene
    if scene and scene.node_tree:
        for node in scene.node_tree.nodes:
            if node.type == 'OUTPUT_FILE':
                items.append((
                    node.name, 
                    node.name, 
                    f"File Output Node: {node.name}",
                    'NODE',  # Node icon
                    len(items)  # Unique number for each item
                ))
    
    if not items:
        items.append((
            "NONE", 
            "No File Output Nodes", 
            "No File Output nodes found",
            'ERROR',  # Error icon when no nodes
            0
        ))
    
    return items

class FileOutputNodeProperty(bpy.types.PropertyGroup):
    output_node: bpy.props.EnumProperty(
        name="File Output Node",
        description="Select a File Output node",
        items=get_file_output_nodes
    )
    
    @property
    def node(self):
        """Get the actual file output node from the scene's node tree"""
        scene = bpy.context.scene
        if scene.node_tree:
            node_name = str(self.output_node) if self.output_node else ""
            if node_name and node_name != "NONE":
                node = scene.node_tree.nodes.get(node_name)
                if node and node.type == 'OUTPUT_FILE':
                    return node
        return None

class NODE_PT_file_output_test(bpy.types.Panel):
    bl_label = "File Output Node Test"
    bl_idname = "NODE_PT_file_output_test"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'ShotPut'
    
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Show stored file output nodes
        for item in scene.file_output_nodes:
            layout.prop(item, "output_node", text="File Output Node")
            
            # Display info about the selected node
            try:
                selected_node = item.node
                if selected_node:
                    box = layout.box()
                    box.label(text=f"Node: {selected_node.name}")
                    box.label(text=f"Base path: {selected_node.base_path}")
            except:
                # Handle any property access issues gracefully
                pass

def register():
    bpy.utils.register_class(FileOutputNodeProperty)
    bpy.utils.register_class(NODE_PT_file_output_test)
    bpy.types.Scene.file_output_nodes = bpy.props.CollectionProperty(type=FileOutputNodeProperty)

def unregister():
    del bpy.types.Scene.file_output_nodes
    bpy.utils.unregister_class(NODE_PT_file_output_test)
    bpy.utils.unregister_class(FileOutputNodeProperty)

if __name__ == "__main__":
    register()
    
    # Initialize with one item to demonstrate
    scene = bpy.context.scene
    if not scene.file_output_nodes:
        item = scene.file_output_nodes.add()
        # The enum will automatically populate with available File Output nodes
