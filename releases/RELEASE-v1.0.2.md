# 🎬 Shotput v1.0.2

> **Professional render output management for Blender 4.4+**

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## 🐛 **Critical Bug Fixes in v1.0.2**

### 🔧 **Fixed: Composite Node Path Construction**
- **Issue**: Composite nodes were generating incomplete render paths (e.g., `ViewLayer_composite_v001`)
- **Solution**: Enhanced `_update_scene_render_path` method to include proper sequence padding and file extensions
- **Result**: Composite nodes now generate complete paths like `ViewLayer_composite_v001.####.png`

### ✨ **Enhanced Path Generation**
- **Sequence Padding**: Added proper sequence numbering (`.####.`) to composite output paths
- **Format Extension Mapping**: Intelligent file extension detection based on UI output format settings
- **Consistency**: Aligned composite node behavior with file output nodes for uniform path generation

### 🎯 **Improved Version Update Operator**
- **Better Error Handling**: Enhanced composite node path validation and error reporting  
- **Format Mapping**: Added comprehensive format-to-extension mapping for all supported formats
- **User Feedback**: Clearer console messages for successful path updates

## 🚀 **All Features from v1.0.1**

### ✨ **Major Features**

- **🎯 Smart File Output Node Creation** - Automatically generates organized compositor nodes for Core, AOV, and Data passes
- **🔄 Intelligent Version Management** - Filesystem-aware version bumping that detects existing renders
- **🎨 Visual Node Organization** - Color-coded nodes with meaningful labels for instant workflow recognition
- **⚡ Lazy Hook-Up System** - Automatic connection of render layer outputs to file outputs via fuzzy matching
- **📋 Preset System** - Save and load complete render setups with JSON presets

### 🛠️ **Production-Ready Tools**

#### **Core Pass Management**
- Create organized file output nodes for beauty, diffuse, specular, and reflection passes
- Flexible format support (PNG, JPEG, EXR, EXR Multilayer)
- Automatic composite node generation for main render output
- Smart channel naming for pipeline compatibility

#### **AOV Pass Handling** 
- Support for arbitrary AOV passes with override naming
- Automatic render layer pass enabling
- Format-specific path generation
- Color-coded node identification

#### **Data Pass Automation**
- Full support for Z-depth, Normal, Motion Vector, Position passes
- Complete Cryptomatte integration (Object, Material, Asset)
- Always uses EXR Multilayer with 32-bit float precision
- Automatic render layer configuration

### 🎛️ **Advanced Configuration**

#### **Token-Based Path System**
Powerful path templating with support for:
- `{workdir}` - Current Blender file directory or AYON work path
- `{subpath}` - Configurable subfolder structure
- `{renderlayer}` - Active render layer name
- `{passname}` - Specific pass identifier
- `{variant}` - Version variant designation  
- `{version}` - Automatic version numbering (v001, v002, etc.)
- `{blend_name}` - Current .blend filename
- `{scene_name}` - Active scene name
- `{frame}` - Current frame number
- `{camera}` - Active camera name
- `{date}` - Current date (DD-MM-YY)
- `{time}` - Current time (HH-MM-SS)

#### **Format Override System**
Fine-grained format control per pass type:
```json
"file_format_overrides": {
  "core": "UI",                    // Use UI selection
  "aov": "UI",                     // Use UI selection  
  "data": "OPEN_EXR_MULTILAYER"    // Force EXR multilayer
}
```

#### **Data Format Precision**
Guaranteed quality for technical passes:
```json
"data_format_settings": {
  "color_depth": "32",    // 32-bit float precision
  "exr_codec": "ZIP"      // ZIP compression
}
```

## 🏗️ **Professional Workflow Features**

### **Version Management** ⭐ *Updated*
- **Smart Version Detection** - Scans filesystem to find next available version
- **Update All Nodes** - Batch update all Shotput nodes to next version
- **Multiple Composite Node Warnings** - Alerts for render conflicts
- **Scene Render Path Sync** - Automatic scene render settings update with proper file extensions

### **Lazy Hook-Up System**
Intelligent automatic connections with fuzzy matching:
- `Image` ↔ `Beauty` - Main beauty pass
- `Depth` ↔ `Z` - Depth information  
- `DiffDir` ↔ `Diffuse` - Diffuse lighting
- `GlossDir` ↔ `Specular` - Specular reflection
- `Normal` ↔ `Normal` - Surface normals
- `Vector` ↔ `Motion Vector` - Motion vectors
- Plus support for Cryptomatte and custom AOVs

## 📦 **Installation**

1. Download `shotput-v1.0.2.zip`
2. In Blender: **Edit** → **Preferences** → **Add-ons** → **Install...**
3. Select the downloaded zip file
4. Enable "Shotput" addon
5. Find the panel in **Compositor** workspace → **Sidebar** → **Shotput** tab

## 🔄 **Upgrade from v1.0.1**

If you're upgrading from v1.0.1:
1. Disable the old addon in Blender preferences
2. Install the new v1.0.2 zip file
3. Re-enable the addon
4. Your existing scenes will automatically benefit from the improved path generation

## 🎯 **Quick Start**

1. **Configure Settings** - Set your render layer, variant, and output format
2. **Add Passes** - Select which core passes, AOVs, and data passes you need
3. **Create Nodes** - Use the create buttons to generate organized output nodes
4. **Version Control** - Use "Update Version" to bump all nodes to next version (now with proper file extensions!)
5. **Save Preset** - Export your setup for reuse across projects

## 🔧 **Technical Specifications**

- **Blender Version**: 4.4.0+ required
- **Category**: THE LINE Studio Tools
- **File Size**: ~139KB
- **Dependencies**: None (pure Python)
- **Platform**: Windows, macOS, Linux

## 🚨 **Known Considerations**

- **EXR Multilayer First Slot**: Automatic workaround for Blender's first slot naming issue
- **Multiple Composite Nodes**: Warning system alerts to prevent render conflicts
- **Version Detection**: Requires existing folder structure for smart version detection
- **Token Resolution**: Some tokens require AYON environment or scene context

## 🎨 **Pipeline Integration**

### **AYON/OpenPype Ready**
- Auto-detects AYON environment variables
- Uses AYON project structure when available
- Fallback to standard Blender workflow when not in AYON

### **Studio Workflow**
- Follows naming conventions for downstream compositing
- Supports render farm integration
- Compatible with asset management systems
- Designed for multi-artist collaboration

## 📚 **Documentation & Support**

- **Website**: [THE LINE STUDIO](https://www.thelinestudio.com/)
- **Support**: Community-driven
- **License**: Open Source
- **Author**: Pete Addington @ THE LINE STUDIO

---

## 🎉 **Ready for Even Better Render Management?**

Download Shotput v1.0.2 and experience the improved composite node path generation. This critical bug fix ensures your render paths are complete and consistent across all node types.

**Happy Rendering!** 🎬✨

---

*Built with ❤️ for the Blender community by THE LINE*
