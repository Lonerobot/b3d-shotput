# Shotput v1.3.5

> **A tokenised render output addon for Blender 4.5 LTS**

## What's New in v1.3.5

### Bug Fixes

- **Fixed multichannel EXR base_path missing `.exr` extension**: For `OPEN_EXR_MULTILAYER` nodes, Blender does not append the extension automatically — the full path including `.exr` must be present in `base_path`. This was causing render outputs to be written with the frame-padding token (e.g. `####`) as the file extension. All three create operators (`create_core_passes`, `create_aov_passes`, `create_data_passes`) and the Update Version operator now produce the correct `filename.####.exr` pattern.

- **Fixed Update Version overwriting manually-changed node format**: The update operator was forcing each node's format back to the scene-level Shotput setting on every run, reverting any manual format changes the artist made in the compositor. Format is now only set at creation time; Update Version respects the node's current format.

- **Fixed `{passname}` spurious subdirectory on path-linked nodes**: `_update_file_slots` was adding a `pass_type` subdirectory whenever `{passname}` appeared *anywhere* in the root token. The condition is now an exact match (`root_token == '{passname}'`), so compound tokens such as `{outputlayer}_{passname}_{variant}/{version}` no longer produce a duplicate subdirectory.

- **Fixed empty `base_path` causing "no base path set" error on Update Version**: When a linked node's `base_path` was cleared, the update path was hard-aborting with a warning. It now rebuilds the path from the node's `root_folder_token` via a fresh `TokenParser`.

- **Fixed `_is_path_linked()` ignoring AYON mode in `token_parser`**: The AYON precedence check that was already present in `versioning.py` was missing from `TokenParser._is_path_linked()`, allowing path-linking to interfere with AYON token resolution.

---

## Installation

1. Download **Shotput-v1.3.5.zip**
2. In Blender: **Edit → Preferences → Add-ons → Install...**
3. Select the downloaded zip
4. Enable the **Shotput** addon
5. Find controls in: **Compositor → Sidebar → Shotput Tab**

---

*Built for Blender 4.5 LTS by Lonerobot/THE LINE*
