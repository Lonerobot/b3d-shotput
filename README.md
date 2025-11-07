# Shotput Addon - System Documentation

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Overview
Shotput is a Blender addon for managing file output nodes with token-based path resolution, smart versioning, and intelligent file format handling. The system is designed for VFX and animation pipelines where automated, consistent file management is critical.

## Core Features

### 🏷️ Token Parsing System
The TokenParser class provides 16+ dynamic tokens for flexible path construction:

**Path Tokens:**
- `{workdir}` - Working directory from scene properties
- `{subpath}` - Subfolder structure for organization
- `{version}` - Automatically managed version numbers

**Render Tokens:**
- `{renderlayer}` - Current render layer name
- `{passname}` - Individual pass name (beauty, diffuse, etc.)
- `{variant}` - Version variant identifier
- `{frame}` - Current frame number with padding

**Project Tokens (AYON Integration):**
- `{project}` - Project name
- `{task}` - Current task designation
- `{user}` - Active user name

**Context Tokens:**
- `{blendfile}` - Current blend file name
- `{scenename}` - Active scene name

### 🎨 Smart File Format Override System
Intelligent format selection based on pass type and user preferences:

- **Core Passes**: Respect UI format setting (PNG, JPEG, EXR, etc.)
- **AOV Passes**: Respect UI format setting for flexibility
- **Data Passes**: Always forced to OPEN_EXR_MULTILAYER with 32-bit precision

### 📁 Automated Version Management
- Next version calculation without creating directories
- Preview path resolution before execution
- Version update operations with user confirmation
- Integration with existing version numbering systems

### 🔗 Path Linking System
Advanced node path synchronization for complex output hierarchies:

- **Automatic Path Inheritance**: Child nodes inherit base paths from parent nodes
- **Backup & Restore**: Original path tokens are preserved when linking is enabled
- **Dynamic Subfolder Creation**: Append custom paths to linked base directories
- **Real-time Path Preview**: See resolved paths instantly in the node UI
- **Toggle Controls**: Enable/disable linking with one-click operators
- **Composite Node Integration**: Automatic path linking for render output nodes

**Path Linking Benefits:**
- Maintains consistent folder structures across related outputs
- Reduces path configuration errors and duplication
- Enables complex hierarchical output organization
- Supports both File Output and Composite node types

### ⚙️ Pass Type Categories

**Core Passes** (Primary beauty renders):
- Beauty, Diffuse, Specular, Reflection
- Uses UI-selected format
- Standard render layer output
- Can serve as parent nodes for path linking

**AOV Passes** (Additional render elements):
- AO, Shadow, Fresnel, Roughness
- Uses UI-selected format
- Utility and artistic passes
- Often linked to core pass folder structures

**Data Passes** (Technical/compositing data):
- Z-depth, Mist, Normal, Vector, Crypto
- Always EXR Multilayer format
- Full precision for compositing accuracy
- Typically organized in separate linked hierarchies

## File Structure

```
addons/shotput/
├── __init__.py              # Addon registration and metadata
├── preferences.py           # Addon preferences and settings
├── properties.py           # Custom property definitions and path linking
├── ui.py                   # User interface panels, operators, and path controls
├── data/
│   └── passes.json         # Pass definitions and format overrides
├── op/                     # Operators for addon functionality
│   ├── create_core_passes.py  # Enhanced with composite node linking
│   ├── create_aov_passes.py
│   ├── create_data_passes.py
│   ├── versioning.py       # Version management with path linking support
│   ├── lazy_hookup.py      # Node connection utilities
│   └── open_output_folder.py
└── utils/                  # Utility modules
    ├── token_parser.py     # Core token resolution with linked path support
    ├── defaults.py         # Configuration loading and format logic
    ├── version_utils.py    # Version calculation utilities
    ├── path_utils.py       # Path manipulation helpers
    ├── output_utils.py     # Output node management
    └── log.py             # Logging system
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
"{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}"
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
  "root_folder_token": "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}",
  "file_name_token": "{renderlayer}_{passname}_{variant}"
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

Shotput is designed to integrate with:
- **AYON Pipeline**: Native token support for project/task/user
- **Version Control**: Automatic version increment without file creation
- **Render Farms**: Token-based paths work across different machines
- **Compositing Software**: EXR multilayer output for seamless integration

## User Interface Features

### 🎨 Enhanced Visual Design
- **Color-coded icons**: Consistent STRIP_COLOR_* icons for visual organization
  - Blue (STRIP_COLOR_05) for Core passes
  - Orange (STRIP_COLOR_02) for AOV passes  
  - Red (STRIP_COLOR_01) for Data passes
- **Collapsible panels**: Clean, organized interface with expandable sections
- **Split layout formatting**: Professional version display in node panels
- **Toggle button grids**: Modern 3x2 grid layout for data pass selection

### 🔧 Path Linking Controls
- **One-click toggle**: Enable/disable path linking with visual state indicators
- **Real-time preview**: See resolved paths instantly in the node UI
- **Linked node selector**: Dropdown menu to choose parent File Output nodes
- **Backup indicator**: Visual confirmation when original paths are preserved
- **Path validation**: Automatic error checking and user feedback

### 📊 Advanced Node Management
- **Stored passes section**: Collapsible advanced controls for output management
- **Sync operations**: One-way synchronization from stored passes to node slots
- **Dynamic node labels**: Automatic label updates based on current properties
- **Context-sensitive UI**: Different interfaces for File Output vs Composite nodes

## Best Practices

### Path Management
1. **Use meaningful token patterns** that reflect your pipeline structure
2. **Test path resolution** before running large render jobs
3. **Leverage format overrides** to ensure data passes maintain precision
4. **Preview paths** using the versioning operators before committing
5. **Maintain consistent** version numbering across your pipeline

### Path Linking Workflow
1. **Create core passes first** as they typically serve as parent nodes
2. **Enable path linking** for related outputs (AOV, composite) to maintain hierarchy
3. **Use descriptive append paths** like "aov", "data", "composite" for organization
4. **Backup original tokens** are automatically preserved when linking is enabled
5. **Test linked paths** using the preview functionality before rendering
6. **Organize complex projects** with multiple linking levels for deep folder structures

### UI Organization
1. **Use collapsible panels** to focus on relevant sections during different workflow stages
2. **Color-coded icons** help quickly identify pass types in complex node trees
3. **Toggle controls** provide quick access to common boolean settings
4. **Advanced sections** can be collapsed to maintain clean interface for basic operations

## Recent Updates (v0.0.3)

### 🎉 Major UI Improvements
- **Enhanced visual consistency** with color-coded icon system across all pass types
- **Professional layout formatting** with improved version display and split layouts
- **Collapsible interface sections** for cleaner, more organized user experience
- **Modern toggle controls** replacing checkbox interfaces for better usability

### 🔗 Path Linking System (NEW)
- **Complete path linking implementation** for hierarchical output organization
- **Automatic backup/restore system** preserving original path configurations
- **Real-time path preview** with linked node base path display
- **Composite node integration** with automatic path linking to core outputs
- **Enhanced token parser** supporting linked path resolution alongside normal parsing

### 🛠️ Technical Enhancements
- **Improved validation system** with comprehensive path token error checking
- **Streamlined codebase** with removal of redundant operators and better architecture
- **Enhanced versioning support** for both linked and non-linked node configurations
- **Better node management** with automatic label updating and sync functionality

---

*Built for professional VFX and animation pipelines requiring robust, automated file management.*
