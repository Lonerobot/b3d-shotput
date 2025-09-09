
import bpy
from .utils.defaults import initialize_default_passes

def get_file_output_nodes(self, context):
    """Generate enum items for File Output nodes only, excluding the current node"""
    items = []
    scene = context.scene
    
    # Try to determine the current node to exclude it
    current_node_name = None
    if hasattr(context, 'active_node') and context.active_node:
        current_node_name = context.active_node.name
    
    if scene and scene.node_tree:
        for node in scene.node_tree.nodes:
            if node.type == 'OUTPUT_FILE':
                # Skip the current node to prevent self-linking
                if current_node_name and node.name == current_node_name:
                    continue
                    
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
            "No Other File Output Nodes", 
            "No other File Output nodes available for linking",
            'ERROR',  # Error icon when no nodes
            0
        ))
    
    return items

# List item for passes
class ShotputPassItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Pass Name",
        default=""
    )

# Node-level property group for File Output Nodes  
class ShotputFileOutputProperties(bpy.types.PropertyGroup):
    shotput_version: bpy.props.StringProperty(
        name="Shotput Version",
        default="",
        description="Version of Shotput that created this node"
    )
    version: bpy.props.StringProperty(
        name="Version",
        default="v001",
        description="Current version number for this node"
    )
    render_layer: bpy.props.StringProperty(
        name="Render Layer"
    )
    pass_name: bpy.props.StringProperty(
        name="Pass Name"
    )
    variant: bpy.props.StringProperty(
        name="Variant"
    )
    root_folder_token: bpy.props.StringProperty(
        name="Root Folder Token"
    )
    file_name_token: bpy.props.StringProperty(
        name="File Name Token"
    )
    stored_passes: bpy.props.CollectionProperty(type=ShotputPassItem)
    stored_passes_index: bpy.props.IntProperty(
        name="Stored Passes Index", 
        default=0
    )
    
    # UI expansion state for stored passes section
    expand_stored_ui: bpy.props.BoolProperty(
        name="Stored Passes UI",
        description="Show/hide stored passes section in node UI",
        default=False
    )
    
    # Path linking properties
    path_linked: bpy.props.BoolProperty(
        name="Path Linked",
        description="Link this node's path to another File Output node",
        default=False
    )
    root_folder_token_backup: bpy.props.StringProperty(
        name="Root Folder Token Backup",
        description="Backup of the original root folder token before path linking",
        default=""
    )
    linked_node: bpy.props.EnumProperty(
        name="Linked Node",
        description="Select a File Output node to link paths with",
        items=get_file_output_nodes
    )
    
    @property
    def node(self):
        """Get the actual linked file output node from the scene's node tree"""
        scene = bpy.context.scene
        if scene.node_tree:
            node_name = str(self.linked_node) if self.linked_node else ""
            if node_name and node_name != "NONE":
                node = scene.node_tree.nodes.get(node_name)
                if node and node.type == 'OUTPUT_FILE':
                    return node
        return None


# Scene-level property group for Shotput settings
class ShotputSceneProperties(bpy.types.PropertyGroup):
    render_layer: bpy.props.StringProperty(
        name="Render Layer",
        default="RenderLayer"
    )
    pass_name: bpy.props.StringProperty(
        name="Pass Name"
    )
    variant: bpy.props.StringProperty(
        name="Variant",
        default="Main"
    )
    root_folder_token: bpy.props.StringProperty(
        name="Root Folder Token",
        default="{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}"
    )
    file_name_token: bpy.props.StringProperty(
        name="File Name Token",
        default="{renderlayer}_{passname}_{variant}"
    )
    output_format: bpy.props.EnumProperty(
        name="Output Format",
        description="File format for rendered output",
        items=[
            ('PNG', "PNG", "Portable Network Graphics format"),
            ('JPEG', "JPEG", "Joint Photographic Experts Group format"),
            ('OPEN_EXR', "OpenEXR", "OpenEXR single-layer format"),
            ('OPEN_EXR_MULTILAYER', "OpenEXR Multilayer", "OpenEXR multi-layer format")
        ],
        default='OPEN_EXR'
    )
    core_override: bpy.props.StringProperty(
        name="Core Name Override",
        description="Override name for core passes group",
        default="Core"
    )
    aov_override: bpy.props.StringProperty(
        name="AOV Name Override", 
        description="Override name for AOV passes group",
        default="AOV"
    )
    core_passes: bpy.props.CollectionProperty(type=ShotputPassItem)
    core_passes_index: bpy.props.IntProperty(
        name="Core Passes Index", 
        default=0
    )
    aov_passes: bpy.props.CollectionProperty(type=ShotputPassItem)
    aov_passes_index: bpy.props.IntProperty(
        name="AOV Passes Index", 
        default=0
    )
    
    # Data pass boolean properties
    z: bpy.props.BoolProperty(
        name="Z",
        description="Enable Z depth pass",
        default=False
    )
    mist: bpy.props.BoolProperty(
        name="Mist",
        description="Enable Mist pass",
        default=False
    )
    normal: bpy.props.BoolProperty(
        name="Normal",
        description="Enable Normal pass",
        default=False
    )
    vector: bpy.props.BoolProperty(
        name="Vector",
        description="Enable Motion Vector pass",
        default=False
    )
    position: bpy.props.BoolProperty(
        name="Position",
        description="Enable Position pass",
        default=False
    )
    occlusion: bpy.props.BoolProperty(
        name="Occlusion",
        description="Enable Ambient Occlusion pass",
        default=False
    )
    crypto_object: bpy.props.BoolProperty(
        name="Crypto Object",
        description="Enable Cryptomatte Object pass",
        default=False
    )
    crypto_material: bpy.props.BoolProperty(
        name="Crypto Material",
        description="Enable Cryptomatte Material pass",
        default=False
    )
    crypto_asset: bpy.props.BoolProperty(
        name="Crypto Asset",
        description="Enable Cryptomatte Asset pass",
        default=False
    )
    
    # Composite output creation option
    create_composite_from_core: bpy.props.BoolProperty(
        name="Create Composite Output From Core",
        description="Create a composite output node when creating core passes",
        default=False
    )
    
    # Lazy hook-up option
    lazy_hook_up: bpy.props.BoolProperty(
        name="Lazy Hook-up",
        description="Automatically connect File Output nodes to render layer outputs when created",
        default=False
    )
    
    # UI expansion states for main panel
    expand_core_ui: bpy.props.BoolProperty(
        name="Core Passes UI",
        description="Show/hide core passes section in main UI",
        default=False
    )
    
    expand_aov_ui: bpy.props.BoolProperty(
        name="AOV Passes UI", 
        description="Show/hide AOV passes section in main UI",
        default=False
    )
    
    expand_data_ui: bpy.props.BoolProperty(
        name="Data Passes UI",
        description="Show/hide data passes section in main UI", 
        default=False
    )

classes = (
    ShotputPassItem,
    ShotputFileOutputProperties,
    ShotputSceneProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.shotput = bpy.props.PointerProperty(type=ShotputSceneProperties)
    bpy.types.CompositorNodeOutputFile.shotput_data = bpy.props.PointerProperty(type=ShotputFileOutputProperties)
    bpy.types.CompositorNodeComposite.shotput_data = bpy.props.PointerProperty(type=ShotputFileOutputProperties)
    
    # Initialize default passes immediately if possible, otherwise use timer
    try:
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            initialize_default_passes()
        else:
            # Use timer if no scene context available yet
            bpy.app.timers.register(initialize_default_passes, first_interval=0.1)
    except Exception:
        # Fallback to timer initialization
        bpy.app.timers.register(initialize_default_passes, first_interval=0.1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.shotput
    del bpy.types.CompositorNodeOutputFile.shotput_data
    del bpy.types.CompositorNodeComposite.shotput_data