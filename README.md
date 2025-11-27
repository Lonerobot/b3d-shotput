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

## 📋 Branch Status

| Branch                             | Blender   | Version     | Status      | Use Case                                 |
| ---------------------------------- | --------- | ----------- | ----------- | ---------------------------------------- |
| [`blender4x`](../../tree/blender4x) | 4.0 - 4.x | 1.3.0       | 🟢 Stable   | Production                               |
| [`blender5x`](../../tree/blender5x) | 5.0+      | 2.0.0-alpha | 🟡 Dev      | Testing                                  |
| `master`                         |           | -           | Depreciated | May merge `blender5x` branch in future |

---

## 🏷️ Latest Release

**Stable (Blender 4.x):** [v1.3.0](../../releases/tag/v1.3.0)

Download the appropriate version for your Blender installation.
