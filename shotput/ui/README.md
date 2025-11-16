# Shotput UI Module - Refactored Structure

This directory contains the refactored UI components for the Shotput Blender add-on. The code has been reorganized from a single 1538-line file into a modular, maintainable structure.

## Directory Structure

```
ui/
├── operators/          # All operator classes
│   ├── __init__.py
│   ├── list_management.py      # Generic list operator factory
│   ├── path_linking.py         # Path linking toggle
│   ├── token_insertion.py      # Token insertion operator
│   ├── preset_loading.py       # Preset loading from environment
│   ├── sync_passes.py          # Node pass synchronization
│   └── build_layers.py         # Render layer building
│
├── helpers/           # Utility classes and functions
│   ├── __init__.py
│   ├── ui_helpers.py          # UIHelper class for cleaner icon API
│   └── node_helpers.py        # Node utility functions
│
├── lists/             # UIList classes for pass collections
│   ├── __init__.py
│   └── ui_lists.py            # Core, AOV, and Stored pass lists
│
├── panels/            # Panel classes (TODO)
│   ├── __init__.py
│   ├── main_panel.py          # Main Shotput panel
│   ├── node_panel.py          # Node-specific panel
│   └── panel_helpers.py       # Panel drawing helpers
│
├── menus/             # Menu classes (TODO)
│   ├── __init__.py
│   ├── token_menus.py         # Token insertion menus
│   ├── preset_menu.py         # Preset menu
│   └── compositor_menu.py     # Compositor header menu
│
└── __init__.py        # Main module entry point (TODO - create unified)
```

## Key Improvements

### 1. Generic List Operator Factory
**File**: `operators/list_management.py`

Instead of 12 nearly identical operators (240 lines), uses a factory function to generate operators dynamically (150 lines).

```python
# Creates 4 operators (Add, Remove, MoveUp, MoveDown) for a collection
(Add, Remove, Up, Down) = create_list_operators(
    collection_name='core_passes',
    display_name='Core Pass',
    id_prefix='core_pass',
    get_data_func=get_scene_shotput
)
```

**Benefit**: 90 lines saved, single source of truth for list management logic.

### 2. UIHelper Utility Class
**File**: `helpers/ui_helpers.py`

Provides cleaner API for common UI patterns:

```python
# Before (verbose)
icon = custom_icons.get_icon_id_or_fallback('renderlayers')
layout.operator("shotput.create_core", **icon)

# After (clean)
UIHelper.icon_operator(layout, "shotput.create_core", 'renderlayers')
```

**Benefit**: Reduces verbosity, improves readability across 85+ icon usage sites.

### 3. Extracted Helper Functions
**File**: `helpers/node_helpers.py`

Common node operations extracted to reusable functions:
- `get_active_file_output_node(context)` - Get active File Output node safely
- `update_node_label(node, shotput_data)` - Update node label based on properties

**Benefit**: Reduces code duplication, easier to test and maintain.

## Implementation Status

### ✅ Completed (Proof-of-Concept)
- Generic list operator factory
- UIHelper utility class
- Node helper functions
- All operators extracted to separate files
- UIList classes extracted
- Directory structure created

### ⏸️ Ready for Implementation
- Token menus (base class pattern documented)
- Panel extraction (helper pattern documented)
- Unified __init__.py (template ready)

See `../IMPLEMENTATION_GUIDE.md` for detailed implementation steps.

## Usage Example

When refactoring is complete, the main `ui.py` will look like:

```python
"""Shotput UI module - Clean entry point"""
import bpy

# Import all components
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
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    # ... all classes
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Additional setup...

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

## Design Principles

1. **Single Responsibility**: Each file has one clear purpose
2. **DRY (Don't Repeat Yourself)**: Code duplication minimized
3. **Separation of Concerns**: Operators, panels, menus separated
4. **Backward Compatibility**: No API changes, all IDs unchanged
5. **Blender Best Practices**: Follows addon development standards

## Testing

After completing the refactoring:

1. **Registration Test**: Addon loads without errors
2. **Operator Test**: All operators work as before
3. **UI Test**: Panels render correctly
4. **Icon Test**: All icons load properly
5. **Integration Test**: Full workflow testing

See testing checklist in `../IMPLEMENTATION_GUIDE.md`.

## Rollback

If issues arise:

```bash
# From shotput directory
rm -rf ui/
mv ui_original_backup.py ui.py
```

The original `ui.py` is preserved as `ui_original_backup.py`.

## Contributing

When adding new UI components:

1. **Operators**: Add to appropriate file in `operators/`
2. **Panels**: Add to appropriate file in `panels/`
3. **Menus**: Add to appropriate file in `menus/`
4. **Helpers**: Add to `helpers/` if reusable across files
5. **UILists**: Add to `lists/ui_lists.py`

Keep files under 300 lines. Split if larger.

## References

- `../CODE_ASSESSMENT.md` - Detailed analysis of issues
- `../IMPLEMENTATION_GUIDE.md` - Step-by-step implementation plan
- `../PROJECT_SUMMARY.md` - Executive overview
- `../.copilot-instructions.md` - Shotput coding standards

---

**Status**: Proof-of-concept complete, ready for full implementation  
**Estimated Implementation Time**: 8-11 hours  
**Risk Level**: LOW (structural changes only, no logic modifications)
