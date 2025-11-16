# Quick Start: Implementing the Shotput UI Refactoring

This guide provides the fastest path to implementing the refactored UI structure.

## Prerequisites

- ✅ Review `CODE_ASSESSMENT.md` to understand the issues
- ✅ Review `PROJECT_SUMMARY.md` for overview
- ✅ Backup created at `shotput/ui_original_backup.py`
- ✅ Proof-of-concept code in `shotput/ui/` directory

## Fast Track Implementation (4 Steps)

### Step 1: Verify Proof-of-Concept Works (30 min)

Test that the refactored operators work:

```bash
# Open Blender with Shotput addon
# Open Python Console and test:

import bpy
from shotput.ui.operators.list_management import SHOTPUT_OT_CorePassAdd

# Verify operator exists
print(SHOTPUT_OT_CorePassAdd.bl_idname)  # Should print: shotput.core_pass_add

# Test factory pattern
from shotput.ui.operators.list_management import create_list_operators
print("Factory pattern works!")
```

If this works, proceed. If not, stop and debug.

### Step 2: Extract Remaining Components (2-3 hours)

#### A. Extract Token Menus

Create `shotput/ui/menus/token_menus.py`:

```python
"""Token insertion menus"""
import bpy
from ...utils import custom_icons

class SHOTPUT_MT_TokenMenuRoot(bpy.types.Menu):
    bl_label = "Insert Token"
    bl_idname = "SHOTPUT_MT_token_menu_root"
    
    def draw(self, context):
        layout = self.layout
        prop_path = "scene.shotput.root_folder_token"
        
        # Core tokens
        icon = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon)
        
        core_tokens = [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            ('outputlayer', 'Output Layer'),
            ('passname', 'Pass Name'),
            ('variant', 'Variant'),
            ('version', 'Version'),
        ]
        
        for token, label in core_tokens:
            op = layout.operator("shotput.insert_token", text=label)
            op.token = token
            op.property_path = prop_path
        
        # Copy similar sections from original ui.py for:
        # - Project tokens
        # - Date/time tokens
        # - Blender tokens

# Create similar classes for:
# - SHOTPUT_MT_TokenMenuFile
# - SHOTPUT_MT_TokenMenuNodeRoot  
# - SHOTPUT_MT_TokenMenuNodeFile

classes = (
    SHOTPUT_MT_TokenMenuRoot,
    # ... others
)
```

**Time**: 1 hour (copy existing code, adjust imports)

#### B. Extract Panels

Create `shotput/ui/panels/main_panel.py`:

```python
"""Main Shotput panel"""
import bpy
import os
from ...utils import custom_icons

def get_panel_title():
    from shotput import bl_info, __release_stage__
    base = f"Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}-{__release_stage__}"
    ayon_project = os.getenv("AYON_PROJECT_NAME")
    return f"{base} - {ayon_project}" if ayon_project else base

class TL_PT_Shotput_UI(bpy.types.Panel):
    bl_label = get_panel_title()
    bl_category = "Shotput"
    bl_context = "output"
    bl_order = 2
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    
    def draw(self, context):
        # Copy entire draw() method from original ui.py
        # (keep as-is for now, can split into helpers later)
        pass

classes = (TL_PT_Shotput_UI,)
```

Create `shotput/ui/panels/node_panel.py` similarly for `TL_PT_Shotput_Node_UI`.

**Time**: 1 hour (mostly copy-paste)

#### C. Extract Remaining Menus

Create files for:
- `shotput/ui/menus/preset_menu.py` - SHOTPUT_MT_PresetEnvironmentMenu
- `shotput/ui/menus/compositor_menu.py` - NODE_MT_shotput

**Time**: 30 minutes (copy-paste)

### Step 3: Create Unified ui.py (1 hour)

Replace `shotput/ui.py` with:

```python
"""
Shotput UI module - Refactored modular structure.
Original 1538-line file split into organized components.
"""
import bpy
import os

# Import operators
from .operators import (
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
    SHOTPUT_OT_TogglePathLinking,
    SHOTPUT_OT_InsertToken,
    SHOTPUT_OT_LoadPresetFromEnvironment,
    SHOTPUT_OT_SyncNodePasses,
    SHOTPUT_OT_BuildRenderLayers,
)

# Import UILists
from .lists import (
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    SHOTPUT_UL_StoredPasses,
)

# Import panels
from .panels.main_panel import TL_PT_Shotput_UI
from .panels.node_panel import TL_PT_Shotput_Node_UI

# Import menus
from .menus.token_menus import (
    SHOTPUT_MT_TokenMenuRoot,
    SHOTPUT_MT_TokenMenuFile,
    SHOTPUT_MT_TokenMenuNodeRoot,
    SHOTPUT_MT_TokenMenuNodeFile,
)
from .menus.preset_menu import SHOTPUT_MT_PresetEnvironmentMenu
from .menus.compositor_menu import NODE_MT_shotput

# All classes for registration
classes = (
    # UILists
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    SHOTPUT_UL_StoredPasses,
    # Panels
    TL_PT_Shotput_UI,
    TL_PT_Shotput_Node_UI,
    # Operators
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
    SHOTPUT_OT_TogglePathLinking,
    SHOTPUT_OT_InsertToken,
    SHOTPUT_OT_LoadPresetFromEnvironment,
    SHOTPUT_OT_SyncNodePasses,
    SHOTPUT_OT_BuildRenderLayers,
    # Menus
    SHOTPUT_MT_TokenMenuRoot,
    SHOTPUT_MT_TokenMenuFile,
    SHOTPUT_MT_TokenMenuNodeRoot,
    SHOTPUT_MT_TokenMenuNodeFile,
    SHOTPUT_MT_PresetEnvironmentMenu,
    NODE_MT_shotput,
)

def menu_func_compositor(self, context):
    """Draw function to add Shotput menu to compositor header"""
    if context.space_data and context.space_data.type == 'NODE_EDITOR':
        if context.space_data.tree_type == 'CompositorNodeTree':
            self.layout.menu(NODE_MT_shotput.bl_idname)

def register():
    """Register all UI classes"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add Shotput menu to compositor header
    bpy.types.NODE_HT_header.append(menu_func_compositor)

def unregister():
    """Unregister all UI classes"""
    # Remove Shotput menu from compositor header
    bpy.types.NODE_HT_header.remove(menu_func_compositor)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

### Step 4: Test Everything (2 hours)

#### Minimal Test

```python
# In Blender Python console:
import bpy

# Reload addon
bpy.ops.preferences.addon_disable(module="shotput")
bpy.ops.preferences.addon_enable(module="shotput")

# Test an operator
bpy.ops.shotput.core_pass_add()

# Check UI
# - Open Compositor
# - Check Shotput panel appears
# - Test buttons
```

#### Full Test Checklist

```
Registration:
[ ] Addon loads without errors
[ ] No Python errors in console
[ ] All operators appear in search (F3)

UI Rendering:
[ ] Main panel renders
[ ] Node panel renders  
[ ] Icons display correctly
[ ] UILists work

Operators:
[ ] Add/remove/move core passes
[ ] Add/remove/move AOV passes
[ ] Add/remove/move stored passes
[ ] Path linking toggle works
[ ] Token menus insert tokens
[ ] Preset loading works
[ ] Node sync works
[ ] Build render layers works

Integration:
[ ] Create core passes
[ ] Create AOV passes
[ ] Create data passes
[ ] Update version
[ ] Full workflow test
```

## If Something Breaks

### Immediate Rollback

```bash
cd shotput/
rm ui.py
mv ui_original_backup.py ui.py
# Restart Blender
```

### Partial Rollback

Keep what works, revert problematic parts:

```bash
# Example: Keep operators, revert panels
rm ui/panels/main_panel.py
# Copy original panel code back into ui.py temporarily
```

## Success Criteria

✅ Addon loads without errors
✅ All existing functionality works
✅ No visual changes to UI
✅ No Python errors in console
✅ File structure is cleaner

## Time Estimate

- **Step 1** (Verify): 30 minutes
- **Step 2** (Extract): 2-3 hours
- **Step 3** (Unify): 1 hour
- **Step 4** (Test): 2 hours

**Total**: 5.5 - 6.5 hours

## Pro Tips

1. **Work in phases**: Complete one section, test, move to next
2. **Keep Blender open**: Reload addon after each change
3. **Use console**: Check for errors immediately
4. **Commit often**: Git commit after each working phase
5. **Test incrementally**: Don't wait until end to test

## After Completion

1. Update `bl_info` version (increment patch version)
2. Delete `ui_original_backup.py` after confirming everything works
3. Update README.md to mention new structure
4. Document the changes in git commit message

## Need Help?

Refer to:
- `CODE_ASSESSMENT.md` - Why we're doing this
- `IMPLEMENTATION_GUIDE.md` - Detailed steps
- `PROJECT_SUMMARY.md` - Overview
- `shotput/ui/README.md` - Module documentation
- Original code in `ui_original_backup.py`

---

**Good luck! The refactoring is straightforward and low-risk. Take it step by step.**
