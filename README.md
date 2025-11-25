# Shotput - Tokenized Render Output for Blender

![Blender](https://img.shields.io/badge/blender-%23F5792A.svg?style=for-the-badge&logo=blender&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

**Token-based render output management for Blender compositor workflows.**

---

## ⚠️ Important: Blender Version Branches

Shotput development has split to support both Blender 4.x and the new Blender 5.0 API.

### 📦 Blender 4.x (Stable - Production Ready)

**Branch:** [`blender4x`](../../tree/blender4x)  
**Version:** 1.3.0-rc  
**Status:** 🟢 Maintenance (Bug fixes only)

```bash
git checkout blender4x
```

**Supported Blender Versions:** 4.0, 4.1, 4.2, 4.3, 4.4+

This branch is stable and production-ready. Use this for:
- Production rendering work
- Studios using Blender 4.x
- AYON pipeline integration on Blender 4.x

[→ See Blender 4.x Documentation](../../tree/blender4x)

---

### 🚧 Blender 5.x (Development - Alpha)

**Branch:** [`blender5x`](../../tree/blender5x)  
**Version:** 2.0.0-alpha  
**Status:** 🟡 Active Development

```bash
git checkout blender5x
```

**Supported Blender Versions:** 5.0+

This branch is under active development for Blender 5.0's new compositor API. Major changes:
- Complete compositor API migration (`scene.node_tree` → `scene.compositing_node_group`)
- File Output node refactoring (`base_path` → `directory`)
- Group Output replaces Composite node
- Enhanced Blender native token support

**Not ready for production use.**

[→ See Blender 5.x Migration Report](./BLENDER5_MIGRATION_REPORT.md)

---

## 📚 Documentation

Full documentation is available in each branch:

- **User Guide:** [addons/README.md](./addons/README.md)
- **API Reference:** [docs/api-reference.md](./docs/api-reference.md)
- **Installation:** [docs/installation-setup.md](./docs/installation-setup.md)
- **Preset System:** [docs/preset-system.md](./docs/preset-system.md)

---

## 🎯 Quick Start

1. **Choose your branch** based on your Blender version
2. Download the addon zip from [Releases](../../releases)
3. Install via Blender Preferences → Add-ons → Install
4. Find Shotput in the Compositor workspace sidebar

---

## 🔗 Links

- **Repository:** [github.com/Lonerobot/b3d-shotput](https://github.com/Lonerobot/b3d-shotput)
- **Issues:** [Report bugs or request features](../../issues)
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md)
- **Studio:** [The Line Animation](https://www.thelineanimation.com)

---

## 📋 Branch Status

| Branch | Blender | Version | Status | Use Case |
|--------|---------|---------|--------|----------|
| [`blender4x`](../../tree/blender4x) | 4.0 - 4.x | 1.3.0-rc | 🟢 Stable | Production |
| [`blender5x`](../../tree/blender5x) | 5.0+ | 2.0.0-alpha | 🟡 Dev | Testing |
| `master` | - | - | 📍 Release | Release tags |

---

## 🛠️ Development

**Contributing to Blender 4.x (Bug fixes):**
```bash
git checkout blender4x
# Make your changes
git commit -m "Fix: description"
```

**Contributing to Blender 5.x (New features):**
```bash
git checkout blender5x
# Make your changes
git commit -m "Feature: description"
```

---

## 📜 License

Licensed under the MIT License. See LICENSE file for details.

**Built with ❤️ for the Blender community.**

---

## 🏷️ Latest Release

**Stable (Blender 4.x):** [v1.3.0-rc](../../releases/tag/v1.3.0-rc)

Download the appropriate version for your Blender installation.
