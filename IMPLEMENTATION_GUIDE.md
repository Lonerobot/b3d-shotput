# Shotput UI Refactoring - Implementation Guide

## Executive Summary

This guide provides a step-by-step plan to refactor the Shotput UI module from a single 1538-line file into a well-organized, maintainable structure. The refactoring has been designed to be **non-destructive**, **incremental**, and **fully backward compatible**.

## What Has Been Prepared

### 1. Complete Code Assessment ✅
See `CODE_ASSESSMENT.md` for detailed analysis of:
- Current issues and code duplication patterns
- Specific line counts and metrics
- Risk assessment
- Proposed solutions

### 2. Proof-of-Concept Refactorings ✅
The following components have been created as working examples:

```
shotput/ui/
├── operators/
│   ├── list_management.py      # Generic factory pattern (90 lines saved)
│   ├── path_linking.py         # Extracted operator
│   ├── token_insertion.py      # Extracted operator
│   ├── preset_loading.py       # Extracted operator
│   ├── sync_passes.py          # Extracted operator
│   └── build_layers.py         # Extracted operator
├── helpers/
│   ├── ui_helpers.py           # NEW - UIHelper utility class
│   └── node_helpers.py         # Extracted helper functions
├── lists/
│   └── ui_lists.py             # All UIList classes
```

These demonstrate the refactoring patterns and can serve as templates for the remaining work.

## Implementation Strategy

### Phase 1: Complete Menu Extraction (2-3 hours)

#### Step 1.1: Extract Token Menus
Create `shotput/ui/menus/token_menus.py`:

```python
"""
Token insertion menus for Shotput path fields.
Uses base class pattern to reduce duplication.
"""
import bpy
from ...utils import custom_icons


class BaseTokenMenu(bpy.types.Menu):
    """Base class for token menus - reduces duplication"""
    property_path = ""  # Override in subclass
    bl_label = "Insert Token"
    
    def draw(self, context):
        layout = self.layout
        
        # Core tokens section
        icon = custom_icons.get_icon_id_or_fallback('file_folder')
        layout.label(text="Core Tokens", **icon)
        
        for token, label in self.get_core_tokens():
            op = layout.operator("shotput.insert_token", text=label)
            op.token = token
            op.property_path = self.property_path
        
        # Additional sections...
    
    def get_core_tokens(self):
        """Override to provide token list"""
        return []


class SHOTPUT_MT_TokenMenuRoot(BaseTokenMenu):
    bl_idname = "SHOTPUT_MT_token_menu_root"
    property_path = "scene.shotput.root_folder_token"
    
    def get_core_tokens(self):
        return [
            ('workdir', 'Working Directory'),
            ('subpath', 'Subpath'),
            # ... etc
        ]

# Similar for other 3 token menu variants
```

**Benefit**: Reduces ~290 lines to ~120 lines (60% reduction)

#### Step 1.2: Extract Preset and Compositor Menus
Create `shotput/ui/menus/preset_menu.py` and `shotput/ui/menus/compositor_menu.py`

### Phase 2: Extract Panel Components (3-4 hours)

#### Step 2.1: Create Panel Helper Functions
Create `shotput/ui/panels/panel_helpers.py`:

```python
"""
Helper functions for drawing panel sections.
Breaks up large draw() methods into manageable pieces.
"""
from ..helpers import UIHelper


def draw_header_section(layout, context, shotput):
    """Draw the welcome/header box"""
    box = layout.box()
    col = box.column(align=True)
    
    # AYON detection and icon
    if os.getenv("AYON_PROJECT_NAME"):
        UIHelper.icon_label(col, "Shotput - Tokenised Render Output System", 'ayon')
    else:
        UIHelper.icon_label(col, "Shotput - Tokenised Render Output System", 'renderlayers')
    
    col.separator(factor=0.5)
    col.scale_y = 0.8
    col.label(text="Create and update automatic versions for renders")


def draw_properties_section(layout, context, shotput):
    """Draw the scene properties box"""
    box = layout.box()
    UIHelper.icon_label(box, "Output Node Properties", 'scene_data')
    box.prop(shotput, "output_layer", text="Output Layer")
    box.prop(shotput, "variant", text="Variant")


def draw_passes_section(layout, context, shotput):
    """Draw the pass creation box"""
    # ... etc


def draw_presets_section(layout, context, shotput):
    """Draw the preset management box"""
    # ... etc
```

#### Step 2.2: Extract Main Panel
Create `shotput/ui/panels/main_panel.py`:

```python
"""
Main Shotput panel in compositor sidebar.
"""
import bpy
import os
from . import panel_helpers


def get_panel_title():
    """Generate panel title with AYON status if available"""
    from ... import bl_info, __release_stage__
    base_title = f"Shotput v{bl_info['version'][0]}.{bl_info['version'][1]}.{bl_info['version'][2]}-{__release_stage__}"
    
    ayon_project = os.getenv("AYON_PROJECT_NAME")
    if ayon_project:
        return f"{base_title} - {ayon_project}"
    
    return base_title


class TL_PT_Shotput_UI(bpy.types.Panel):
    bl_label = get_panel_title()
    bl_category = "Shotput"
    bl_context = "output"
    bl_order = 2
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
        
    def draw(self, context):
        layout = self.layout
        shotput = context.scene.shotput
        
        # Use helper functions for each section
        panel_helpers.draw_header_section(layout, context, shotput)
        panel_helpers.draw_properties_section(layout, context, shotput)
        panel_helpers.draw_passes_section(layout, context, shotput)
        panel_helpers.draw_presets_section(layout, context, shotput)
```

**Benefit**: Main panel draw() method: 250 lines → 8 lines

#### Step 2.3: Extract Node Panel
Similar approach for `TL_PT_Shotput_Node_UI` in `shotput/ui/panels/node_panel.py`

### Phase 3: Create New Unified ui.py (1 hour)

Replace the original `shotput/ui.py` with a clean module that imports and registers all components:

```python
"""
Shotput UI module - Main entry point for UI components.
Simplified module structure with components organized by type.
"""
import bpy
import os

from . import bl_info, __release_stage__

# Import all UI components
from .operators import (
    SHOTPUT_OT_CorePassAdd,
    SHOTPUT_OT_CorePassRemove,
    # ... all operators
)
from .lists import (
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    SHOTPUT_UL_StoredPasses,
)
from .panels import (
    TL_PT_Shotput_UI,
    TL_PT_Shotput_Node_UI,
)
from .menus import (
    SHOTPUT_MT_TokenMenuRoot,
    # ... all menus
)


# Unified classes tuple for registration
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
    # ... all operators
    # Menus
    SHOTPUT_MT_TokenMenuRoot,
    # ... all menus
)


def menu_func_compositor(self, context):
    """Draw function to add Shotput menu to compositor header"""
    if context.space_data and context.space_data.type == 'NODE_EDITOR':
        if context.space_data.tree_type == 'CompositorNodeTree':
            from .menus import NODE_MT_shotput
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

**Result**: New ui.py is ~100 lines (vs 1538 lines original)

### Phase 4: Testing & Validation (2-3 hours)

#### Test Checklist

```markdown
## Registration Tests
- [ ] Addon loads without errors
- [ ] All operators appear in search (F3)
- [ ] No Python errors in console

## UI Tests
- [ ] Main panel renders correctly
- [ ] Node panel renders correctly
- [ ] All icons load correctly
- [ ] UILists display properly

## Operator Tests
- [ ] Core pass add/remove/move
- [ ] AOV pass add/remove/move
- [ ] Stored pass add/remove/move
- [ ] Path linking toggle
- [ ] Token insertion (all menus)
- [ ] Preset loading
- [ ] Node sync
- [ ] Build render layers

## Integration Tests
- [ ] Create core passes
- [ ] Create AOV passes
- [ ] Create data passes
- [ ] Update version
- [ ] Open output folder
- [ ] AYON mode works (if available)

## Compatibility Tests
- [ ] Works in Blender 3.6
- [ ] Works in Blender 4.x
- [ ] No deprecated API usage warnings
```

## Rollback Plan

If issues arise:

1. **Immediate Rollback**:
   ```bash
   cd shotput/
   rm -rf ui/
   mv ui_original_backup.py ui.py
   ```

2. **Partial Rollback**:
   Keep refactored components that work, revert problematic ones

3. **Incremental Adoption**:
   - Phase 1: Just use list_management.py factory pattern
   - Phase 2: Add helper classes
   - Phase 3: Full refactoring

## Expected Results

### Before Refactoring
- 1 file: `ui.py` (1538 lines)
- Code duplication: ~650 lines (42%)
- Maintenance difficulty: High
- Test coverage: Difficult

### After Refactoring  
- 20+ files, average ~100 lines each
- Code duplication: ~100 lines (6%)
- Maintenance difficulty: Low
- Test coverage: Easy to add

### Quantitative Improvements
- **Lines of duplicated code**: 650 → 100 (-85%)
- **Largest file size**: 1538 → 350 lines (-77%)
- **Average file size**: N/A → 100 lines
- **Files in ui module**: 1 → 20+

### Qualitative Improvements
- ✅ Single Responsibility Principle followed
- ✅ Easy to locate specific functionality
- ✅ Reduced cognitive load
- ✅ Better git diff/blame granularity
- ✅ Easier for new contributors
- ✅ Enables unit testing

## Timeline

| Phase | Duration | Risk |
|-------|----------|------|
| Menu Extraction | 2-3 hours | Low |
| Panel Extraction | 3-4 hours | Low |
| New ui.py | 1 hour | Low |
| Testing | 2-3 hours | Medium |
| **Total** | **8-11 hours** | **Low** |

## Notes

1. **Incremental Approach**: Can be done in stages, testing after each phase
2. **No Logic Changes**: All refactoring is structural only
3. **Backward Compatible**: No API changes, all operator IDs remain same
4. **Documentation**: Update README.md to mention new structure
5. **Version Bump**: Increment patch version in bl_info after completion

## Reference Implementation

The proof-of-concept files created in `shotput/ui/` demonstrate:
- Generic operator factory pattern
- Helper utility classes
- Clean import structure
- Proper class organization

These can be used as templates for completing the remaining work.

## Conclusion

This refactoring represents a significant quality improvement to the Shotput codebase. It:
- Eliminates 85% of code duplication
- Improves maintainability dramatically
- Maintains 100% backward compatibility
- Follows Blender addon best practices
- Sets up the codebase for future growth

The work is straightforward, low-risk, and provides immediate benefits.

---

**Prepared by**: Lonerobot Custom Agent  
**Date**: 2025-11-16  
**For**: Shotput Blender Add-on Optimization Project
