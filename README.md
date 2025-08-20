# Shotput Addon - System Documentation

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Overview
Shotput is a comprehensive Blender addon for managing file output nodes with advanced token-based path resolution, smart versioning, and intelligent file format handling. The system is designed for professional VFX and animation pipelines where automated, consistent file management is critical.

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
- `{blend_name}` - Current blend file name
- `{scene_name}` - Active scene name

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

### ⚙️ Pass Type Categories

**Core Passes** (Primary beauty renders):
- Beauty, Diffuse, Specular, Reflection
- Uses UI-selected format
- Standard render layer output

**AOV Passes** (Additional render elements):
- AO, Shadow, Fresnel, Roughness
- Uses UI-selected format
- Utility and artistic passes

**Data Passes** (Technical/compositing data):
- Z-depth, Mist, Normal, Vector, Crypto
- Always EXR Multilayer format
- Full precision for compositing accuracy

## File Structure

```
addons/shotput/
├── __init__.py              # Addon registration and metadata
├── preferences.py           # Addon preferences and settings
├── properties.py           # Custom property definitions
├── ui.py                   # User interface panels and operators
├── data/
│   └── passes.json         # Pass definitions and format overrides
├── op/                     # Operators for addon functionality
│   ├── create_core_passes.py
│   ├── create_aov_passes.py
│   ├── create_data_passes.py
│   ├── versioning.py       # Version management operators
│   └── open_output_folder.py
└── utils/                  # Utility modules
    ├── token_parser.py     # Core token resolution engine
    ├── defaults.py         # Configuration loading and format logic
    ├── version_utils.py    # Version calculation utilities
    ├── path_utils.py       # Path manipulation helpers
    ├── output_utils.py     # Output node management
    └── log.py             # Logging system
```

## Usage Examples

### Path Token Examples
```python
# Feature film shot structure
"{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}"
# Result: Z:/projects/film/seq010/shot020/Beauty_diffuse_v001/008

# Commercial project structure  
"{project}_{task}_{blend_name}_{passname}_{frame}"
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
  "root_folder_token": "{workdir}/{subpath}/{renderlayer}_{passname}_{variant}/{version}",
  "file_name_token": "{renderlayer}_{passname}_{variant}"
}
```

## API Integration

### TokenParser Class
```python
from utils.token_parser import TokenParser

parser = TokenParser()
resolved_path = parser.resolve_full_output_path(
    folder_pattern="{workdir}/{subpath}",
    filename_pattern="{passname}_{frame}",
    passname="beauty"
)
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

## Best Practices

1. **Use meaningful token patterns** that reflect your pipeline structure
2. **Test path resolution** before running large render jobs
3. **Leverage format overrides** to ensure data passes maintain precision
4. **Preview paths** using the versioning operators before committing
5. **Maintain consistent** version numbering across your pipeline

---

*Built for professional VFX and animation pipelines requiring robust, automated file management.*
