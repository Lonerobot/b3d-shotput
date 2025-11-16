# Shotput Addon - System Documentation

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Overview

Shotput is a Blender addon for managing file output nodes with token-based path resolution, smart versioning, and intelligent file format handling. It works standalone or integrates seamlessly with AYON pipeline for production environments.

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

- `{workdir}` - Working directory. This is set from the blendfile's save location, or the AYON pipeline context (of present)
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

### 🎨 Smart File Format Override System

Format selection based on pass type and user preferences:

- **Core Passes**: Respect UI format setting (PNG, JPEG, EXR, etc.)
- **AOV Passes**: Respect UI format setting for flexibility
- **Data Passes**: Always forced to OPEN_EXR_MULTILAYER with 32-bit precision

### 📁 Automated Version Management

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

## File Structure

```

addons/shotput/

├── __init__.py              # Addon registration and metadata

├── [preferences.py](http://preferences.py/)           # Addon preferences and settings

├── [properties.py](http://properties.py/)           # Custom property definitions and path linking

├── [ui.py](http://ui.py/)                   # User interface panels, operators, and path controls

├── data/

│   └── passes.json         # Pass definitions and format overrides

├── op/                     # Operators for addon functionality

│   ├── create_core_passes.py  # Enhanced with composite node linking

│   ├── create_aov_passes.py

│   ├── create_data_passes.py

│   ├── [versioning.py](http://versioning.py/)       # Version management with path linking support

│   ├── lazy_hookup.py      # Node connection utilities

│   └── open_output_folder.py

└── utils/                  # Utility modules

    ├── token_parser.py     # Core token resolution with linked path support

    ├── [defaults.py](http://defaults.py/)         # Configuration loading and format logic

    ├── version_utils.py    # Version calculation utilities

    ├── path_utils.py       # Path manipulation helpers

    ├── output_utils.py     # Output node management

    └── [log.py](http://log.py/)             # Logging system

```

## Usage Examples

### Path Linking Examples

```python

# Parent node (Core passes)

core_node.base_path = "/project/renders/seq010/shot020/beauty/v003"


# Child node with path linking enabled

aov_node.path_linked = True

aov_node.linked_node = "Shotput_Core_beauty"

aov_node.root_folder_token = "aov"  # Append path

# Resolved: "/project/renders/seq010/shot020/beauty/v003/aov"


# Composite node automatically linked to core

composite_node.path_linked = True

composite_node.linked_node = "Shotput_Core_beauty"

composite_node.root_folder_token = "composite"

# Resolved: "/project/renders/seq010/shot020/beauty/v003/composite"

```

### Path Token Examples

```python

# Feature film shot structure

"{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}"

# Result: Z:/projects/film/seq010/shot020/Beauty_diffuse_v001/008


# Commercial project structure  

"{project}_{task}_{blendfile}_{passname}_{frame}"

# Result: ClientABC_comp_spot_final_beauty_0001


# Data pass with versioning

"{workdir}/data/{version}/{passname}_{frame}.exr"

# Result: C:/project/data/003/depth_1024.exr

```

### Format Override Behavior

```python

# UI Format: PNG

create_core_passes()    # → PNG files (respects UI)

create_aov_passes()     # → PNG files (respects UI)  

create_data_passes()    # → EXR Multilayer files (forced override)


# UI Format: JPEG

create_core_passes()    # → JPEG files (respects UI)

create_aov_passes()     # → JPEG files (respects UI)

create_data_passes()    # → EXR Multilayer files (forced override)

```

## Configuration (passes.json)

```json

{

  "core_passes": ["Beauty", "Diffuse", "Specular", "Reflection"],

  "aovs": ["AO", "Shadow", "Fresnel", "Roughness"],

  "data_passes": ["z", "mist", "normal", "vector", "crypto_object"],

  "file_format_overrides": {

    "core": "UI",

    "aov": "UI", 

    "data": "OPEN_EXR_MULTILAYER"

  },

  "data_format_settings": {

    "color_depth": "32",

    "exr_codec": "ZIP"

  },

  "path_linking_settings": {

    "enable_automatic_linking": true,

    "composite_auto_link": true,

    "backup_original_tokens": true

  },

  "root_folder_token": "{workdir}/{subpath}/{outputlayer}_{passname}_{variant}/{version}",

  "file_name_token": "{outputlayer}_{passname}_{variant}"

}

```

## API Integration

### Path Linking API

```python

from shotput.properties import ShotputFileOutputProperties


# Enable path linking programmatically

node_props = file_output_node.shotput_data

node_props.path_linked = True

node_props.linked_node = "Shotput_Core_beauty"

node_props.root_folder_token = "subfolder"


# Access linked node properties

linked_node = node_props.node  # Returns actual linked File Output node

if linked_node:

    base_path = linked_node.base_path

```

### TokenParser Class

```python

from utils.token_parser import TokenParser


parser = TokenParser()


# Standard token parsing

resolved_path = parser.resolve_full_output_path(

    folder_pattern="{workdir}/{subpath}",

    filename_pattern="{passname}_{frame}",

    passname="beauty"

)


# Path linking aware parsing

parser = TokenParser(node_properties)

if parser._is_path_linked():

    # Uses linked node's base path + append path

    linked_path = parser._parse_linked_path("{passname}")

else:

    # Uses normal token resolution

    normal_path = parser._parse_normal_path("{workdir}/{passname}")

```

### Version Management

```python

from utils.version_utils import VersionUtils


version_utils = VersionUtils()

next_version = version_utils.get_next_version_for_folder(base_path)

```

### Format Override System

```python

from utils.defaults import get_file_format_for_pass_type


format_result = get_file_format_for_pass_type("data", "PNG")

# Returns: "OPEN_EXR_MULTILAYER" (override applied)


format_result = get_file_format_for_pass_type("core", "PNG")  

# Returns: "PNG" (UI setting respected)

```

## Testing

The addon includes comprehensive test suites:

- `test_comprehensive.py` - Full system integration tests
- `test_format_standalone.py` - Format override logic validation
- `test_tokens_standalone.py` - Token parsing verification
- `test_format_overrides.py` - Blender-integrated format tests

All tests validate:

✅ Configuration loading and validation

✅ Token parsing with edge case handling

✅ File format override logic

✅ Integration scenarios for real-world pipelines

## Pipeline Integration

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
