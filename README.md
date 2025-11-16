# Shotput - User Documentation

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Overview

Shotput is a Blender addon for managing file output nodes with token-based path resolution, smart versioning, and intelligent file format handling. It works standalone or integrates seamlessly with AYON pipeline for production environments.

## Workflow

Shotput lives in the Compostor workspace, andhas a main interface, and a quick compositor menu. These are designed for different stages of your render workflow:

### Main UI Panel (Sidebar)

Located in the Compositor workspace sidebar under the "Shotput" tab. This is where you **create and configure** your output nodes:

- Set up pass lists (Core, AOV, Data)
- Configure path tokens and output formats
- Create file output nodes with one click
- Load and save presets

Use this panel when you're first setting up your render outputs or making major changes to your node structure.

### Compositor Menu (Header)

Located in the Compositor workspace header menu. This is for **ongoing management** once nodes are created:

- **Update Version** - Increment version numbers across all Shotput nodes (or just the selected ones)
- **Open Output Folder** - Quickly access your current render output directory
- **Build Render Layers from View** - Operator to Auto-create render layer nodes based on the Viewlayers present in the scene.

**Once your nodes are set up, you won't need to open the main UI panel anymore** - just use the compositor menu for version updates and quick actions.

## Core Features

### 🎬 AYON Pipeline Integration

**NEW in v1.2.1** - Full AYON compatibility with automatic detection and configuration:

- **Automatic Detection**: Shotput detects AYON context from environment variables
- **Locked Path Tokens**: When AYON is active, output paths are controlled by your pipeline configuration
- **Project-Aware UI**: Panel displays active AYON project name
- **Toggle Control**: Each node can enable/disable AYON mode independently
- **Path Linking Disabled**: AYON's structured paths don't need linking (automatically hidden)
- **Token Backup**: Original tokens preserved when switching between AYON and normal modes

AYON mode ensures renders follow your studio's pipeline structure while maintaining all Shotput's organizational features like output layers, variants, and pass management.

### 🏷️ Token Parsing System

The TokenParser class provides 16+ dynamic tokens for flexible path construction:

**Path Tokens:**

- `{workdir}` - Working directory. This is set from the blendfile's save location, or the AYON pipeline context (if present)
- `{subpath}` - Subfolder structure for organization. Useful to provide a sub path of any length or hierarchy for the renders to go.

e.g. you might want `renders/previz` added to the output path

- `{version}` - Automatically managed version numbers. This is calculated based on the folder contents, analysing the path and extracting the version number. Within an AYON context, this is bound to the workfile name, given AYON has tight file versioning already, and each render should be aligned with this.

**Render Tokens:**

Blender's compositor is its superpower - you can combine multiple scenes, render layers, and view layers in endless ways. Rather than being locked to Blender's layer naming, Shotput gives you flexible control:

- `{outputlayer}` - What you're rendering. Think of it as "what goes in this folder?" Examples: a character name, background plate, or "hero_car". This is your main organizational unit.
- `{passname}` - The render pass type (beauty, diffuse, shadow, etc.)
- `{variant}` - Your version flavor (MAIN, alt, test, etc.)

**Project Tokens (AYON Integration):**

- `{project}` - Project name
- `{task}` - Current task designation
- `{user}` - Active user name

**Context Tokens:**

- `{blendfile}` - Current blend file name
- `{scenename}` - Active scene name

### 🎨 File Format Logic

Format selection based on pass type and user preferences:

- **Core Passes**: Respect UI format setting (PNG, JPEG, EXR, etc.)
- **AOV Passes**: Respect UI format setting for flexibility
- **Data Passes**: Always forced to OPEN_EXR_MULTILAYER with 32-bit precision (This can be changed in the Addon preferences)

### 📁 Automatic Version Management

- Next version calculation without creating directories
- Preview path resolution before execution
- Version update operations with user confirmation
- Integration with existing version numbering systems

### 🔗 Path Linking System

Organize complex outputs by linking child nodes to parent folders:

- **Automatic Inheritance**: Child nodes use parent node's base path
- **One-Click Toggle**: Enable/disable with visual feedback
- **Smart Subfolders**: Add custom paths to linked bases (like "aov" or "data")
- **Backup Protection**: Original paths preserved automatically

*Note: Path linking is disabled in AYON mode as pipeline structure is predetermined.*

### ⚙️ Pass Type Categories

**Core Passes** - Your main beauty renders (diffuse, specular, etc.) in your preferred format

**AOV Passes** - Extra render elements (AO, shadow, fresnel) for compositing control

**Data Passes** - Technical data (Z-depth, normals, cryptomatte) always saved as EXR Multilayer for precision

Sometimes it helps to have separate pass types to make it clear what they're used for. This might sound straightforward with pass names, but if you're using multichannel EXRs, this won't be visible until opened.

It can also avoid having numerous channels in a single EXR that may or may not be used in compositing.

With Blender's shader AOVs, the output potential is almost limitless - hence why the AOV category exists purely for visual and filesystem organization.

**Do you need to use the AOV Type?**

Certainly not. There are only small differences in the functionality of the core and AOV nodes, so they can function the same. AOV nodes have access to additional operators - like being able to import the Shader AOVs from the view layer.

## File Structure

```
addons/shotput/
├── __init__.py              # Addon registration and metadata
├── preferences.py           # Addon preferences with AYON settings
├── properties.py            # Node and scene property definitions
├── ui.py                    # User interface panels and operators
├── blender_manifest.toml    # Blender 4.2+ extension manifest
├── assets/                  # Icons and visual resources
├── data/
│   ├── passes.json          # Pass definitions
│   ├── cycles.json          # Cycles render engine passes
│   ├── cycles_plus.json     # Extended Cycles passes
│   └── eevee.json           # Eevee render engine passes
├── op/                      # Operators
│   ├── create_core_passes.py
│   ├── create_aov_passes.py
│   ├── create_data_passes.py
│   ├── versioning.py        # Version management
│   ├── lazy_hookup.py       # Auto-connection utilities
│   ├── scan_shader_aovs.py  # Shader AOV detection
│   └── open_output_folder.py
└── utils/                   # Utility modules
    ├── ayon_utils.py        # AYON pipeline integration
    ├── token_parser.py      # Token resolution engine
    ├── defaults.py          # Configuration and format logic
    ├── version_utils.py     # Version calculation
    ├── path_utils.py        # Path manipulation
    ├── color_utils.py       # Node color management
    ├── custom_icons.py      # Icon loading system
    ├── pass_mapping.py      # Pass type mapping
    └── log.py               # Logging system
```

## Preset Configuration

Presets are JSON files that define pass configurations and organizational settings. Load presets from the main UI to quickly set up your render output structure.

```json
{
  "_info": "Complete Shotput preset with all configurable properties",
  "bl_version": "1.2.1",
  "core_passes": ["Beauty", "Diffuse", "Specular", "Reflection"],
  "aovs": ["AO", "Shadow", "Fresnel", "Roughness"],
  "data_passes": {
    "z": true,
    "mist": false,
    "normal": true,
    "vector": true,
    "position": false,
    "occlusion": false,
    "crypto_object": false,
    "crypto_material": false,
    "crypto_asset": false
  },
  "output_layer": "ViewLayer",
  "variant": "MAIN",
  "core_override": "Core",
  "aov_override": "AOV",
  "root_folder_token": "{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}",
  "file_name_token": "{outputlayer}_{passname}_{variant}",
  "default_file_format": "OPEN_EXR",
  "file_format_overrides": {
    "core": "UI",
    "aov": "UI",
    "data": "OPEN_EXR_MULTILAYER"
  },
  "data_format_settings": {
    "color_depth": "32",
    "exr_codec": "ZIP"
  },
  "create_composite_from_core": false,
  "expand_core_ui": false,
  "expand_aov_ui": false,
  "expand_data_ui": false
}
```

## Pipeline Integration

All the tokenization logic happens when the nodes are updated - while the tokens exist within custom properties on the node, no part of the output path or filename is "tokenized". This means there is nothing incompatible about the file's output, nor is it tied to the addon in that regard. This means it should be 100% compatible with render farms. It also means you could share a file that was set up with this addon with a user that doesn't have it - it would remove the ability to update automatically, but it wouldn't break anything.

Shotput works with:

- **AYON Pipeline**: Native integration with automatic detection and locked token support
- **Standalone Mode**: Full token flexibility for custom pipeline setups
- **Version Control**: Smart version increment without creating directories
- **Render Farms**: Token-based paths work across different machines

## User Interface Features

### 🔧 Path Linking Controls

- **One-click toggle**: Enable/disable path linking with visual state indicators
- **Real-time preview**: See resolved paths instantly in the node UI
- **Linked node selector**: Dropdown menu to choose parent File Output nodes
- **Backup indicator**: Visual confirmation when original paths are preserved
- **Path validation**: Automatic error checking and user feedback

### 📊 Node Pass Management

- **Stored passes section**: Collapsible advanced controls for output management
- **Sync operations**: One-way synchronization from stored passes to node slots
- **Dynamic node labels**: Automatic label updates based on current properties
- **Context-sensitive UI**: Different interfaces for File Output vs Composite nodes

## Best Practices

### Path Management

1. Use meaningful token patterns that match your workflow
2. Preview paths before big render jobs
3. Data passes automatically use EXR Multilayer for precision
4. In AYON mode, tokens are locked to pipeline settings

### AYON Workflow

1. Shotput automatically detects AYON context
2. Toggle AYON mode per-node if needed (enabled by default)
3. Output layer and variant stay editable for organization
4. Path linking and composite creation disabled (not compatible with AYON structure)

### Path Linking Workflow

1. Create core passes first - they serve as parent nodes
2. Enable path linking for related outputs (AOV, data) to keep hierarchy clean
3. Use simple append paths like "aov" or "data" for organization
4. Preview resolved paths before rendering

*Path linking unavailable in AYON mode - pipeline structure is predetermined*

### UI Organization

1. Collapsible panels keep things clean
2. Color-coded icons identify pass types quickly
3. AYON project name shows in panel title when active
4. Read-only tokens in AYON mode prevent accidental changes

---

*Built with love for the Blender community.*
