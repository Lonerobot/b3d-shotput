
import bpy
from .utils.defaults import initialize_default_passes

# List item for passes
class ShotputPassItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Pass Name",
        default=""
    )

# Node-level property group for File Output Nodes  
class ShotputFileOutputProperties(bpy.types.PropertyGroup):
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
    
    # Initialize default passes after a short delay using timer
    bpy.app.timers.register(initialize_default_passes, first_interval=0.1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.shotput
    del bpy.types.CompositorNodeOutputFile.shotput_data