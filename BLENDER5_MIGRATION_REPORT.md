# Blender 5.0 Migration Report for Shotput
**Date:** November 24, 2025  
**Blender Version:** 5.0.0  
**Current Shotput Version:** 1.2.8  

---

## Executive Summary

Blender 5.0 introduces **breaking changes** to the compositor system that fundamentally impact Shotput's architecture. The most critical changes are:

1. **`Scene.node_tree` removed** - Scenes no longer have direct compositor node trees
2. **`Scene.use_nodes` deprecated** - Will be removed in Blender 6.0
3. **Composite node eliminated** - Group Output node is now the scene output mechanism
4. **Native path templates introduced** - Blender now has its own tokenization system

These changes require a **significant refactor** of Shotput, but also present opportunities to enhance compatibility and leverage Blender's new systems.

---

## Branch Strategy

### Recommended Approach

**Two-Branch Development Model:**

```
main (deprecated - will become tag)
├── blender4x (Blender 4.0 - 4.x support)
│   └── Maintain current codebase
│   └── Bug fixes only, no new features
│
└── blender5x (Blender 5.0+ support)
    └── Full refactor for new compositor system
    └── Active feature development
```

**After successful migration:**
- Tag current `main` as `v1.2.8-blender4-final`
- Merge `blender5x` into `main` as new default
- Keep `blender4x` branch for legacy support

**bl_info version strategy:**
- Blender 4.x: Version 1.2.x (current)
- Blender 5.x: Version 2.0.x (new major version)

---

## Critical API Changes Detected

### 1. Compositor Node Tree Access

**Blender 4.x (Current):**
```python
scene = bpy.context.scene
scene.use_nodes = True
tree = scene.node_tree  # CompositorNodeTree
```

**Blender 5.0 (Error):**
```python
# 'Scene' object has no attribute 'node_tree'
# DeprecationWarning: 'Scene.use_nodes' expected to be removed in Blender 6.0
```

**Implication:** All Shotput code accessing `scene.node_tree` will fail immediately.

**Files Affected:**
- `ui.py` - Panel draws, operator executions
- `op/create_core_passes.py` - Node creation
- `op/create_aov_passes.py` - Node creation  
- `op/create_data_passes.py` - Node creation
- `op/versioning.py` - Version updates across nodes
- `op/lazy_hookup.py` - Node connections

### 2. Composite Node Removed

**API Test Results:**
```json
{
  "exists": false,
  "type_available": false,
  "error": "General error: 'Scene' object has no attribute 'node_tree'"
}
```

**Compositor Types Available:**
- `CompositorNodeOutputFile` ✓ (Still exists)
- `CompositorNodeComposite` ✗ (Removed)
- `NodeGroupOutput` ✓ (New replacement)

**Implication:** Shotput's composite node creation logic is completely broken.

### 3. Group Output as Composite Replacement

**New Workflow:**
- Compositor now works with **compositor graphs** (asset-like)
- Group Output node defines scene render output
- **Only the first image input** is used as final render result
- Multiple Group Output nodes can exist, but only the active one is used

**From Documentation:**
> "In the Compositor, this node defines the image result that is sent to the renderer or to image output after rendering."

---

## Blender's Native Path Templates

### Available Variables

**Universal tokens (all paths):**
- `{blend_name}` - Current .blend file name (without extension)
- `{blend_dir}` - Path to .blend file directory
- `{blend_name_lib}` - Library blend name (for linked data)
- `{blend_dir_lib}` - Library blend directory

**Render output only:**
- `{fps}` - Frames per second
- `{resolution_x}` / `{resolution_y}` - Render resolution (with scale)
- `{scene_name}` - Current scene name
- `{camera_name}` - Active render camera name

**Node-specific:**
- `{node_name}` - Name of the node (for File Output nodes)

### Format Specifiers

```python
# Integer padding
"render_{fps:###}.png"     # -> render_030.png

# Float precision  
"render_{fps:.###}.png"    # -> render_29.970.png

# Combined
"render_{fps:###.##}.png"  # -> render_029.97.png
```

### Escape Sequences

- `{{` → `{` (literal brace)
- `}}` → `}` (literal brace)

### Supported Paths

**Currently supported:**
- Scene render output path (`scene.render.filepath`)
- File Output node paths (`base_path`, `file_slots[].path`)

**API Test Confirmed:**
All Blender tokens (`#`, `####`, `<f>`, `<scene>`, `<camera>`, `<layer>`, `<pass>`, `//`) are accepted in `scene.render.filepath`.

---

## Token System Comparison

### Shotput Current Tokens

```python
# Core tokens
{workdir}, {subpath}, {outputlayer}, {passname}, {variant}, {version}

# AYON tokens  
{project}, {projectname}, {task}, {folder}, {user}

# Blender tokens
{blendfile}, {scenename}, {frame}, {camera}

# Date/Time
{date}, {time}
```

### Compatibility Strategy

**Shotput tokens → Blender equivalents:**
- `{blendfile}` → `{blend_name}`
- `{scenename}` → `{scene_name}`
- `{camera}` → `{camera_name}`
- `{frame}` → `#` or `####` (padding)

**Unique Shotput tokens (keep):**
- `{workdir}`, `{subpath}` - Project structure
- `{outputlayer}`, `{passname}`, `{variant}` - Pipeline specific
- `{version}` - Version management
- `{project}`, `{task}`, `{folder}`, `{user}` - AYON integration
- `{date}`, `{time}` - Metadata

**Recommended Approach:**
1. **Parser compatibility layer**: Detect and convert Blender tokens to Shotput tokens during parsing
2. **Hybrid mode**: Allow users to mix Shotput and Blender tokens
3. **Migration tool**: Convert existing presets from old tokens to new tokens

---

## Migration Plan

### Phase 1: API Detection & Compatibility Layer

**Goal:** Make Shotput version-aware

```python
# In __init__.py
BLENDER_VERSION = bpy.app.version

if BLENDER_VERSION >= (5, 0, 0):
    from . import compositor_5x as compositor
else:
    from . import compositor_4x as compositor
```

**Files to create:**
- `compositor_4x.py` - Wrapper for Blender 4.x API (current code)
- `compositor_5x.py` - New compositor API for Blender 5.0

### Phase 2: Compositor 5.0 API Implementation

**New accessor pattern:**

Research needed to find the new way to access compositor trees in Blender 5.0. Possible approaches:

1. **Compositor Graph Assets:**
   ```python
   # Hypothesis: Compositor is now an asset library system
   # Need to investigate bpy.data.node_groups for compositor graphs
   ```

2. **Scene-level compositor reference:**
   ```python
   # Hypothesis: Scene may have a compositor property instead
   # Check: scene.compositor, scene.compositing, etc.
   ```

3. **Workspace-level access:**
   ```python
   # Hypothesis: Compositor may be workspace-specific
   # Check: workspace.compositor, context.workspace
   ```

**Action Item:** Write discovery script to probe Blender 5.0 data structures.

### Phase 3: Group Output Implementation

**Replace composite node creation:**

```python
# OLD (Blender 4.x)
def create_linked_composite(scene):
    tree = scene.node_tree
    comp_node = tree.nodes.new(type='CompositorNodeComposite')
    comp_node.shotput_data.path_linked = True
    # ...

# NEW (Blender 5.x)  
def create_group_output(compositor_graph):
    tree = compositor_graph  # New tree access method
    output_node = tree.nodes.new(type='NodeGroupOutput')
    
    # Define output socket
    tree.interface.new_socket(
        name="Image",
        in_out='OUTPUT',
        socket_type='NodeSocketColor'
    )
    
    # Note: Custom properties won't work the same way
    # Need new storage strategy for Shotput metadata
```

**Challenges:**
- Custom properties (`shotput_data`) may not work on Group Output nodes
- Need alternative storage for path tokens, version info, etc.
- Potentially use node labels or scene properties instead

### Phase 4: File Output Node Verification

**Good news:** `CompositorNodeOutputFile` still exists in Blender 5.0

**Verification needed:**
- Does `base_path` still work the same way?
- Do `file_slots` behave identically?
- Are custom properties (`shotput_data`) still supported?
- Do path templates work in `base_path` and `file_slots[].path`?

**Action:** Update test script to create File Output node with path templates.

### Phase 5: Token Parser Enhancement

**Update `utils/token_parser.py`:**

```python
class TokenParser:
    # Blender native tokens (passthrough or convert)
    BLENDER_NATIVE_TOKENS = {
        'blend_name': '{blendfile}',      # Map to Shotput equivalent
        'blend_dir': None,                 # Passthrough
        'scene_name': '{scenename}',       # Map to Shotput equivalent
        'camera_name': '{camera}',         # Map to Shotput equivalent
        'fps': None,                       # Passthrough
        'resolution_x': None,              # Passthrough
        'resolution_y': None,              # Passthrough
        'node_name': None,                 # Passthrough
    }
    
    def parse_token(self, token_string, **context):
        """
        Enhanced to handle both Shotput and Blender tokens.
        
        Strategy:
        1. Detect Blender token format: {variable_name}
        2. If Blender token, check if we have Shotput equivalent
        3. If yes, resolve using Shotput logic
        4. If no, passthrough to Blender's native resolution
        5. For Shotput-only tokens, resolve as before
        """
        # Implementation...
```

**Hybrid Path Example:**
```python
# User inputs:
root_folder = "{blend_dir}/renders/{project}/{task}"
file_name = "{scene_name}_{passname}_v{version}.{frame:####}"

# Shotput resolves:
# {blend_dir} - Passthrough to Blender
# {project}, {task} - Shotput AYON tokens
# {scene_name} - Map to Shotput {scenename} or passthrough
# {passname}, {version} - Shotput pipeline tokens
# {frame:####} - Blender format specifier (passthrough)

# Final result:
# "//renders/ProjectX/modeling/Scene_Beauty_v003.0001.exr"
```

### Phase 6: UI Updates

**Minimal changes required:**
- Update `bl_info["blender"]` to `(5, 0, 0)`
- Update version to `(2, 0, 0)`
- Panel poll methods may need adjustment for new compositor access
- Add Blender 5.0 badge/indicator in UI
- Token help popup should explain Blender vs Shotput tokens

### Phase 7: Testing & Validation

**Test matrix:**

| Feature | Blender 4.x | Blender 5.0 | Status |
|---------|-------------|-------------|--------|
| Core pass creation | ✓ | ? | Test needed |
| AOV pass creation | ✓ | ? | Test needed |
| Data pass creation | ✓ | ? | Test needed |
| Composite node (B4) / Group Output (B5) | ✓ | ? | Needs refactor |
| Version updates | ✓ | ? | Test needed |
| Path linking | ✓ | ? | Test needed |
| AYON integration | ✓ | ? | Test needed |
| Preset save/load | ✓ | ? | Test needed |
| Token parsing | ✓ | ? | Enhance |
| Build render layers | ✓ | ? | Test needed |

---

## Immediate Action Items

### 1. Create Compositor Access Discovery Script

```python
# test_compositor_access_5x.py
"""
Discover how to access compositor in Blender 5.0
"""

import bpy

def investigate_compositor_access():
    """Try all possible ways to access compositor in Blender 5.0"""
    
    results = {}
    scene = bpy.context.scene
    
    # Test 1: Check data.node_groups for compositor
    print("=== Testing bpy.data.node_groups ===")
    for ng in bpy.data.node_groups:
        print(f"Node Group: {ng.name}, Type: {ng.bl_idname}")
        if 'Compositor' in ng.bl_idname:
            results['node_groups'] = ng
    
    # Test 2: Check scene attributes
    print("\n=== Testing scene attributes ===")
    scene_attrs = [attr for attr in dir(scene) if 'compos' in attr.lower() or 'node' in attr.lower()]
    for attr in scene_attrs:
        try:
            value = getattr(scene, attr)
            print(f"scene.{attr} = {type(value)}")
            results[f'scene_{attr}'] = value
        except:
            pass
    
    # Test 3: Check context attributes
    print("\n=== Testing context attributes ===")
    ctx_attrs = [attr for attr in dir(bpy.context) if 'compos' in attr.lower()]
    for attr in ctx_attrs:
        try:
            value = getattr(bpy.context, attr)
            print(f"context.{attr} = {type(value)}")
            results[f'context_{attr}'] = value
        except:
            pass
    
    # Test 4: Try to find compositing workspace
    print("\n=== Testing workspace ===")
    for ws in bpy.data.workspaces:
        print(f"Workspace: {ws.name}")
        if 'Compositing' in ws.name:
            for attr in dir(ws):
                if 'node' in attr.lower() or 'comp' in attr.lower():
                    try:
                        value = getattr(ws, attr)
                        print(f"  {attr} = {type(value)}")
                    except:
                        pass
    
    return results

if __name__ == "__main__":
    investigate_compositor_access()
```

**Run:** `blender --background --python test_compositor_access_5x.py`

### 2. Update bl_info for Version Detection

```python
# In __init__.py
bl_info = {
    "name": "Shotput",
    "blender": (5, 0, 0),  # Update minimum version
    "version": (2, 0, 0),  # Major version bump
    # ...
}

# Add version check
if bpy.app.version < (5, 0, 0):
    raise Exception(
        "Shotput 2.0+ requires Blender 5.0 or newer. "
        "For Blender 4.x, please use Shotput 1.2.x from the 'blender4x' branch."
    )
```

### 3. Create Migration Guide for Users

Document in `MIGRATION_BLENDER5.md`:
- What changed in Blender 5.0
- How Shotput adapted
- How to migrate existing scenes
- Token compatibility table
- Troubleshooting common issues

---

## Risk Assessment

### High Risk
- ❌ **Compositor access broken** - Complete blocker until resolved
- ❌ **Custom property storage** - May need new metadata strategy
- ❌ **Preset compatibility** - Existing presets may not load

### Medium Risk
- ⚠️ **File Output node changes** - Need verification
- ⚠️ **Token parser conflicts** - Need careful Blender/Shotput token handling
- ⚠️ **AYON integration** - May have breaking changes in 5.0

### Low Risk
- ✓ **UI panels** - Minor adjustments only
- ✓ **Version management** - Logic remains valid
- ✓ **Pass creation logic** - Core concepts unchanged

---

## Opportunities

### 1. Leverage Blender's Path Templates
- Reduce custom token parsing where Blender provides equivalents
- Better integration with Blender's native workflows
- Format specifiers for frame padding, decimal precision

### 2. Compositor Graph Assets
- If compositor becomes asset-based, Shotput presets could be saved as compositor graphs
- Share compositor setups between scenes
- Better version control integration

### 3. Cleaner Architecture
- Forced refactor allows fixing technical debt
- Separate 4.x and 5.x code cleanly
- Modernize property registration patterns

### 4. Enhanced Documentation
- Complete migration guide
- Video tutorials for 5.0 changes
- Better onboarding for new users

---

## Timeline Estimate

**Conservative estimate:** 40-60 hours

| Phase | Effort | Priority |
|-------|--------|----------|
| Compositor access discovery | 4-6 hours | CRITICAL |
| API compatibility layer | 6-8 hours | HIGH |
| Group Output implementation | 8-12 hours | HIGH |
| Token parser enhancement | 6-8 hours | MEDIUM |
| File Output verification | 4-6 hours | MEDIUM |
| UI updates | 4-6 hours | LOW |
| Testing & debugging | 8-12 hours | HIGH |

**Fast-track scenario:** If Blender provides clear migration docs: 24-32 hours

**Worst-case scenario:** If compositor access requires deep changes: 80-100 hours

---

## Recommended Next Steps

1. ✅ **Branch structure created** (blender4x, blender5x)
2. ✅ **Initial API test completed**
3. ✅ **Documentation reviewed**
4. ⏭️ **Run compositor access discovery script** (NEXT)
5. ⏭️ **Create compatibility detection utility**
6. ⏭️ **Implement compositor 5.x wrapper module**
7. ⏭️ **Update File Output node tests**
8. ⏭️ **Refactor composite → group output**
9. ⏭️ **Enhance token parser**
10. ⏭️ **Full integration testing**

---

## Questions for Blender Community

If blocked, ask on Blender developers forums:

1. **Where is the compositor node tree now stored?**
   - Previously `scene.node_tree`, now returns AttributeError
   
2. **How do addons access compositor graphs in 5.0?**
   - Is it through `bpy.data.node_groups`?
   - Is there a scene reference?
   
3. **Can custom properties be added to Group Output nodes?**
   - Shotput stores metadata on nodes
   - Alternative storage strategies?
   
4. **Do File Output nodes support path templates?**
   - Both `base_path` and `file_slots[].path`?
   - Format specifier support?

---

## Conclusion

**The migration is feasible but requires significant effort.** The core Shotput concepts (token-based paths, version management, AYON integration) remain valid, but the implementation must be completely refactored for Blender 5.0's new compositor architecture.

**Recommended strategy:**
- Maintain Blender 4.x support on dedicated branch (bug fixes only)
- Develop Blender 5.0 support as new major version (2.0.0)
- Use this as opportunity to improve architecture and documentation

**Critical blocker:** Understanding how to access and create compositor nodes in Blender 5.0. This must be resolved before any other work can proceed.

**Timeline:** 4-8 weeks for complete migration and testing, depending on API discovery complexity.

---

**Report compiled by:** GitHub Copilot  
**Repository:** Lonerobot/b3d-shotput  
**Branch:** blender5x  
