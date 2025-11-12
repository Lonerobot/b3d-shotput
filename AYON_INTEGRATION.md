# AYON Pipeline Integration

This document describes the AYON-specific output node functionality added in version 1.2.0.

## Overview

Shotput now integrates seamlessly with the AYON pipeline by automatically detecting AYON environments and applying AYON-specific path conventions. This ensures that rendered outputs conform to AYON's pre-publish validation requirements without manual path configuration.

## Features

### Automatic AYON Detection

Shotput detects AYON context by checking for the presence of these environment variables:
- `AYON_PROJECT_NAME` - The name of the active AYON project
- `AYON_WORKDIR` - The working directory for the current AYON task

When both variables are present, Shotput automatically switches to AYON mode.

### AYON-Specific Token Patterns

When AYON is detected, Shotput uses simplified token patterns that integrate with AYON's versioning system:

#### File Output Nodes
- **Root Folder Token**: `{workdir}/{subpath}/{blendfile}` (default)
  - Uses AYON's workdir instead of manual paths
  - Removes version token since AYON handles versioning through the workfile
  
- **File Name Token**: `{outputlayer}_{passname}_{variant}` (default)
  - Simple naming pattern without version suffix

#### Composite Nodes
- **Root Folder Token**: `{workdir}/{subpath}/{blendfile}` (default)
  - Same as file output nodes, or can use linked node path
  
- **File Name Token**: `/tmp/tmp` (default)
  - AYON composite nodes default to workdir/tmp/tmp/ as per AYON conventions

### Per-Node Override Control

Each node has a `use_ayon_output_style` boolean property that allows you to:
- **Enabled (default)**: Use AYON tokens when AYON is detected
- **Disabled**: Use standard Shotput tokens even in AYON context

This gives you granular control over which nodes follow AYON conventions.

## Configuration

### Preferences

Navigate to Edit → Preferences → Add-ons → Shotput to configure AYON settings:

1. **AYON Pipeline Settings** section shows:
   - Active AYON project indicator (when AYON is detected)
   - AYON Root Folder Token (for file output nodes)
   - AYON File Name Token (for file output nodes)
   - AYON Composite Root Token (for composite nodes)
   - AYON Composite File Token (for composite nodes)

2. Customize these tokens to match your studio's AYON pipeline structure

### Default Token Patterns

The default AYON token patterns are designed to work with standard AYON setups:

```python
# File Output Nodes
root: {workdir}/{subpath}/{blendfile}
file: {outputlayer}_{passname}_{variant}

# Composite Nodes
root: {workdir}/{subpath}/{blendfile}
file: /tmp/tmp
```

### Available Tokens

All standard Shotput tokens work in AYON mode, including AYON-specific ones:
- `{workdir}` - AYON working directory
- `{subpath}` - Render output subdirectory
- `{blendfile}` - Current blend file name
- `{outputlayer}` - Output layer name
- `{passname}` - Pass name (beauty, diffuse, etc.)
- `{variant}` - Variant identifier
- `{project}` / `{projectname}` - AYON project
- `{task}` - AYON task name
- `{user}` - Current user name
- `{folder}` - AYON folder path

Note: The `{version}` token is typically omitted in AYON mode as AYON manages versioning through workfiles.

## Usage

### Creating Nodes in AYON Context

1. Open Blender in an AYON-managed project
2. The Shotput UI header will show "AYON Enabled" when detected
3. Create nodes normally using the Shotput operators:
   - Create Core Passes
   - Create AOV Passes
   - Create Data Passes
   - Create Linked Composite

The nodes will automatically use AYON token patterns.

### Example Output Paths

With AYON environment:
```
AYON_PROJECT_NAME=MyProject
AYON_WORKDIR=/mnt/projects/MyProject/shots/sh010/work/comp/v003
```

File Output Node path:
```
Base: /mnt/projects/MyProject/shots/sh010/work/comp/v003/renders/blender/MyScene
File: ViewLayer_beauty_Main.####.exr
```

Composite Node path:
```
Base: /mnt/projects/MyProject/shots/sh010/work/comp/v003/renders/blender/MyScene
File: /tmp/tmp
```

### Disabling AYON for Specific Nodes

If you need a node to use standard Shotput paths even in AYON context:

1. Select the node
2. In the node properties (N panel)
3. Expand the Shotput section
4. Disable "Use AYON Output Style"
5. The node will now use standard Shotput token patterns

## Technical Details

### Implementation

The AYON integration consists of:

1. **Preferences (`preferences.py`)**
   - New AYON token properties
   - UI section for AYON configuration

2. **Node Properties (`properties.py`)**
   - `use_ayon_output_style` boolean per node

3. **AYON Utilities (`utils/ayon_utils.py`)**
   - `is_ayon_context()` - Detects AYON environment
   - `should_use_ayon_tokens()` - Determines if AYON tokens should be used
   - `get_ayon_tokens()` - Retrieves token patterns from preferences
   - `apply_ayon_tokens_to_node()` - Applies AYON tokens to node properties

4. **Operator Integration**
   - All node creation operators call `apply_ayon_tokens_to_node()` after setting standard properties
   - AYON tokens override standard tokens when applicable

### Compatibility

- **Blender**: 4.4.0+
- **AYON**: All versions that set `AYON_PROJECT_NAME` and `AYON_WORKDIR`
- **Backward Compatibility**: Existing nodes and non-AYON workflows are unaffected

### Token Resolution Order

When creating a node:
1. Copy scene/UI properties to node (standard tokens)
2. If AYON detected AND node has `use_ayon_output_style=True`:
   - Override `root_folder_token` with AYON root token
   - Override `file_name_token` with AYON file token
3. Token parser resolves final paths

## Best Practices

1. **Set AYON tokens once in preferences** - All new nodes will use them automatically
2. **Use standard naming conventions** - The default tokens work for most AYON setups
3. **Keep version management in AYON** - Don't add `{version}` to AYON tokens
4. **Test with real AYON environment** - Path validation happens during publish
5. **Document custom tokens** - If you modify AYON tokens, document them for your team

## Troubleshooting

### AYON Not Detected

Check that environment variables are set:
```bash
echo $AYON_PROJECT_NAME
echo $AYON_WORKDIR
```

### Wrong Paths Generated

1. Check AYON token patterns in preferences
2. Verify environment variables contain expected values
3. Check node's "Use AYON Output Style" is enabled
4. Review token resolution in console output

### Mixed AYON/Standard Nodes

This is supported! Nodes with "Use AYON Output Style" enabled use AYON tokens, others use standard Shotput tokens. Useful for mixing AYON-managed renders with local test renders.

## Future Enhancements

Potential improvements for future versions:
- AYON publish validation within Blender
- Automatic task/shot context detection
- AYON version synchronization
- Integration with AYON workfile system
- AYON-specific node templates

## Support

For issues or questions:
- Check the main README.md for general Shotput documentation
- Review .copilot-instructions.md for development guidelines
- File issues on the GitHub repository
