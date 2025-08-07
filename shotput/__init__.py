"""
#   _____ _  _ ___   _     ___ _  _ ___
#  |_   _| || | __| | |   |_ _| \| | __|
# _______________________________________
#    | | | || |___| |____|___|_|\_|___|
                                                
#    ___ _____ _   _ ___ ___ ___  
#   / __|_   _| | | |   \_ _/ _ \
#   \__ \ | | | |_| | |) | | (_) |
#   |___/ |_|  \___/|___/___\___/
                                                
# Shotput - A Blender addon for managing file output nodes

"""

# Addon metadata - required by Blender
bl_info = {
    "name": "Shotput",
    "description": "Build and repath file output nodes automatically",
    "blender": (4, 4, 0),
    "category": "THELINE",
    "author": "Pete.Addington",
    "version": (0, 0, 2),
    "location": "Compositor Tab > Sidebar",
    "doc_url": "https://www.thelineanimation.com/",
    "wiki_url": "https://www.thelineanimation.com",
    "warning": "",  # Optional: for development versions
    "support": "COMMUNITY",  # OFFICIAL, COMMUNITY, or TESTING
}

# Module level constants
__version__ = ".".join(str(x) for x in bl_info["version"])
__author__ = bl_info["author"]
__package_name__ = __name__.rpartition('.')[0] if '.' in __name__ else __name__

# Standard reload pattern for Blender addon development
if "bpy" in locals():
    import importlib
    # Reload all submodules to ensure changes take effect
    _modules_to_reload = [
        "preferences", 
        "properties", 
        "op", 
        "ui"
    ]
    for module_name in _modules_to_reload:
        if module_name in locals():
            importlib.reload(locals()[module_name])
else:
    import bpy
    from . import preferences
    from . import properties
    from . import op
    from . import ui


def register():
    """Register all classes and initialize the addon"""
    # Register in dependency order
    preferences.register()
    properties.register()
    op.register()
    ui.register()
    
    # Initialize default settings if available
    try:
        from .utils.defaults import initialize_default_passes
        if hasattr(bpy.context, 'scene') and bpy.context.scene:
            initialize_default_passes()
    except (ImportError, AttributeError):
        # Gracefully handle missing utils or no active scene
        pass

    print(f"Shotput v{__version__} registered successfully")


def unregister():
    """Unregister all classes and clean up"""
    # Unregister in reverse order
    ui.unregister() 
    op.unregister() 
    properties.unregister()
    preferences.unregister()
    
    print(f"Shotput v{__version__} unregistered successfully")


# Standard Python module execution pattern
if __name__ == "__main__":
    register()

