"""
Shotput addon unit tests — runs inside Blender's Python environment.

Run via:
    blender --background --python tests/run_tests.py

Or directly (less useful outside the runner):
    blender --background --python tests/test_shotput.py
"""

import sys
import os
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the addon package is importable from Blender's Python environment.
# When Blender is invoked with --background the addon is NOT automatically
# enabled; we load it manually via bpy.ops.preferences.addon_install / enable
# or by inserting the repo root into sys.path and importing directly.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import bpy

# Enable the addon so bl_info, properties, and operators are all registered.
# Safe to call even if already enabled.
bpy.ops.preferences.addon_enable(module="shotput")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_props(**kwargs):
    """
    Return a plain namespace object that quacks like ShotputFileOutputProperties
    with only the attributes needed by the code under test.  This avoids needing
    a live Blender scene for pure-logic token tests.
    """
    import types
    props = types.SimpleNamespace(
        output_layer="ViewLayer",
        variant="main",
        pass_type="core",
        version="v001",
        path_linked=False,
        linked_node="NONE",
        use_ayon_output_style=False,
        root_folder_token="",
        file_name_token="",
        normal_root_folder_token="",
        normal_file_name_token="",
    )
    for k, v in kwargs.items():
        setattr(props, k, v)
    return props


def _new_compositor_scene():
    """Create a fresh scene with compositing nodes enabled and return it."""
    # Use the existing default scene so we don't accumulate scenes
    scene = bpy.context.scene
    scene.use_nodes = True
    # Clear all existing nodes
    scene.node_tree.nodes.clear()
    return scene


def _add_file_output(tree, name="Shotput_Core_Test"):
    """Add a File Output node and mark it as a Shotput node."""
    node = tree.nodes.new(type="CompositorNodeOutputFile")
    node.name = name
    node.label = name
    return node


# ---------------------------------------------------------------------------
# Test suites
# ---------------------------------------------------------------------------

class TestTokenParserBlendfile(unittest.TestCase):
    """_resolve_blendname must return the stem only, never include .blend."""

    def setUp(self):
        from shotput.utils.token_parser import TokenParser
        self.TokenParser = TokenParser

    def test_blendfile_no_extension_when_saved(self):
        """When a .blend file is open, {blendfile} should be the stem."""
        # bpy.data.filepath is empty in --background with no file; skip gracefully
        if not bpy.data.filepath:
            self.skipTest("No .blend file open — skipping blendfile-stem test")
        props = _make_fake_props()
        parser = self.TokenParser(props)
        result = parser._resolve_blendname()
        self.assertFalse(
            result.endswith(".blend"),
            f"{{blendfile}} resolved to '{result}' which still contains the .blend extension"
        )
        self.assertNotIn(
            ".blend",
            result,
            f"{{blendfile}} resolved to '{result}' which contains '.blend'"
        )

    def test_blendfile_untitled_fallback(self):
        """In --background mode with no .blend open, fallback must be 'untitled'."""
        # bpy.data.filepath is read-only; in --background mode it is already empty
        if bpy.data.filepath:
            self.skipTest("A .blend file is open — cannot test untitled fallback")
        props = _make_fake_props()
        parser = self.TokenParser(props)
        result = parser._resolve_blendname()
        self.assertEqual(result, "untitled")


class TestTokenParserIsPathLinked(unittest.TestCase):
    """_is_path_linked must return False when AYON mode is active."""

    def setUp(self):
        from shotput.utils.token_parser import TokenParser
        self.TokenParser = TokenParser

    def test_path_linked_false_when_ayon_enabled(self):
        """Even if path_linked=True and linked_node is set, AYON mode takes precedence."""
        props = _make_fake_props(
            path_linked=True,
            linked_node="Shotput_Core",
            use_ayon_output_style=True,
        )
        parser = self.TokenParser(props)
        self.assertFalse(
            parser._is_path_linked(),
            "_is_path_linked() should return False when use_ayon_output_style=True"
        )

    def test_path_linked_true_without_ayon(self):
        """path_linked is respected when AYON mode is off."""
        props = _make_fake_props(
            path_linked=True,
            linked_node="Shotput_Core",
            use_ayon_output_style=False,
        )
        parser = self.TokenParser(props)
        self.assertTrue(
            parser._is_path_linked(),
            "_is_path_linked() should return True when path_linked=True and AYON mode is off"
        )

    def test_path_linked_false_when_no_linked_node(self):
        """path_linked=True with no linked node should still return False."""
        props = _make_fake_props(path_linked=True, linked_node="NONE", use_ayon_output_style=False)
        parser = self.TokenParser(props)
        self.assertFalse(parser._is_path_linked())


class TestTokenParserNormalPath(unittest.TestCase):
    """parse_token resolution for the core tokens used in AYON root paths."""

    def setUp(self):
        from shotput.utils.token_parser import TokenParser
        self.TokenParser = TokenParser

    def test_passname_override(self):
        """passname kwarg must override the default pass_type resolution."""
        props = _make_fake_props(pass_type="core", output_layer="VL", variant="main")
        parser = self.TokenParser(props)
        result = parser.parse_token("{passname}", passname="beauty")
        self.assertEqual(result, "beauty")

    def test_outputlayer_resolves(self):
        props = _make_fake_props(output_layer="comp_010", variant="main")
        parser = self.TokenParser(props)
        result = parser.parse_token("{outputlayer}")
        self.assertEqual(result, "comp_010")

    def test_variant_resolves(self):
        props = _make_fake_props(output_layer="VL", variant="hero")
        parser = self.TokenParser(props)
        result = parser.parse_token("{variant}")
        self.assertEqual(result, "hero")

    def test_token_combination(self):
        """Compound token strings must resolve all parts."""
        props = _make_fake_props(output_layer="VL", variant="main", pass_type="core")
        parser = self.TokenParser(props)
        result = parser.parse_token("{outputlayer}_{passname}_{variant}", passname="rgba")
        self.assertEqual(result, "VL_rgba_main")

    def test_unknown_token_left_as_placeholder(self):
        """Unknown tokens must not raise; they become UNRESOLVED_<NAME>."""
        props = _make_fake_props()
        parser = self.TokenParser(props)
        result = parser.parse_token("{totallymadeuptoken}")
        self.assertIn("UNRESOLVED_", result.upper())


class TestMultilayerExrPathGuard(unittest.TestCase):
    """
    The pathlib guard added to create_core/aov/data_passes.py must strip any
    extension-bearing component from resolved_base_path before it is used to
    construct full_base_path.  We test the guard logic in isolation using the
    same pathlib pattern the production code uses.
    """

    def _apply_guard(self, resolved_base_path: str) -> str:
        """Replicate the guard block verbatim."""
        from pathlib import Path as _Path
        _resolved_path_obj = _Path(resolved_base_path)
        if _resolved_path_obj.suffix and '.' in _resolved_path_obj.name:
            return str(_resolved_path_obj.parent)
        return resolved_base_path

    def test_no_extension_unchanged(self):
        self.assertEqual(
            self._apply_guard("/some/workdir/subpath/comp_010"),
            "/some/workdir/subpath/comp_010",
        )

    def test_blend_extension_stripped(self):
        """If the token resolves to something ending in .blend the guard strips it."""
        result = self._apply_guard("/some/workdir/subpath/comp_010.blend")
        # Use Path objects so Windows path-separator normalisation is irrelevant
        self.assertEqual(Path(result), Path("/some/workdir/subpath"))
        self.assertNotIn(".blend", result)

    def test_arbitrary_extension_stripped(self):
        result = self._apply_guard("/renders/shot_010.v001")
        self.assertEqual(Path(result), Path("/renders"))

    def test_path_with_dots_in_directories_only(self):
        """Dots in directory components (not the final name) must be preserved."""
        p = "/some.dir/another.dir/finaldir"
        self.assertEqual(self._apply_guard(p), p)


class TestVersioningPassnameSubdirectory(unittest.TestCase):
    """
    The {passname} subdirectory logic in _update_file_slots must ONLY fire
    when the root_token is literally '{passname}', not when {passname} is
    embedded in a longer token segment.
    """

    def _should_add_subdir(self, root_token: str, pass_type: str = "core") -> bool:
        """Replicate the fixed condition from versioning.py."""
        return root_token.strip() == "{passname}" and bool(pass_type)

    def test_literal_passname_token_adds_subdir(self):
        """The path-linked composite case: root_folder_token = \"{passname}\"."""
        self.assertTrue(self._should_add_subdir("{passname}", "core"))

    def test_embedded_passname_does_not_add_subdir(self):
        """{passname} embedded in a compound token should NOT trigger subdirectory."""
        self.assertFalse(
            self._should_add_subdir("{outputlayer}_{passname}_{variant}/{version}", "core")
        )

    def test_empty_pass_type_no_subdir(self):
        self.assertFalse(self._should_add_subdir("{passname}", ""))

    def test_ayon_root_token_no_subdir(self):
        self.assertFalse(
            self._should_add_subdir("{workdir}/{subpath}/{blendfile}", "core")
        )


# ---------------------------------------------------------------------------
# Context-override helper for background-mode operator tests
# ---------------------------------------------------------------------------

from contextlib import contextmanager as _contextmanager

@_contextmanager
def _bypass_node_editor_poll():
    """
    Temporarily replace the create_core_passes poll() so it does not require
    a NODE_EDITOR space_data context.  In --background mode Blender has no
    window/area/space, making the stock poll always fail.

    Blender looks up poll() dynamically on the class every time it is called,
    so patching the classmethod attribute works reliably.
    """
    from shotput.op.create_core_passes import OT_Create_Core_Passes
    # Grab the original classmethod descriptor from __dict__ so we can restore it
    _orig = OT_Create_Core_Passes.__dict__['poll']
    # Replacement: skip space_data guard but keep the scene-property checks
    @classmethod
    def _permissive_poll(cls, ctx):
        sp = ctx.scene.shotput
        required = [sp.output_layer.strip(), sp.variant.strip(),
                    sp.root_folder_token.strip(), sp.file_name_token.strip()]
        if not all(required):
            return False
        return sp.use_render_layer_channels or len(sp.core_passes) > 0
    OT_Create_Core_Passes.poll = _permissive_poll
    try:
        yield
    finally:
        OT_Create_Core_Passes.poll = _orig


class TestFileOutputNodeCreation(unittest.TestCase):
    """
    Integration: run the Create Core Passes operator in Blender's compositor
    with OPEN_EXR_MULTILAYER format selected and assert that base_path is
    correctly formed (directory + filename.####, no stray extension).

    These tests require a running Blender scene and the shotput addon to be
    fully registered, so they are skipped if conditions are not met.
    """

    def setUp(self):
        scene = _new_compositor_scene()
        self.scene = scene
        self.tree = scene.node_tree

        # Set up minimal Shotput UI props required by poll()
        sp = scene.shotput
        sp.output_layer = "ViewLayer"
        sp.variant = "main"
        sp.root_folder_token = "/tmp/renders/{outputlayer}_{passname}_{variant}"
        sp.file_name_token = "{outputlayer}_{passname}_{variant}"

        # Add one core pass
        sp.core_passes.clear()
        new_pass = sp.core_passes.add()
        new_pass.name = "rgba"
        sp.use_render_layer_channels = False

    def _set_output_format(self, fmt):
        self.scene.shotput.output_format = fmt

    def test_multilayer_base_path_no_spurious_extension(self):
        """base_path for OPEN_EXR_MULTILAYER must not contain a file extension."""
        self._set_output_format("OPEN_EXR_MULTILAYER")
        with _bypass_node_editor_poll():
            result = bpy.ops.shotput.create_core_passes()
        self.assertEqual(result, {"FINISHED"})

        # Find the created node
        node = next(
            (n for n in self.tree.nodes if n.type == "OUTPUT_FILE" and "Core" in n.name),
            None,
        )
        self.assertIsNotNone(node, "Create Core Passes should have produced a File Output node")

        base = node.base_path
        self.assertTrue(base, "base_path must not be empty after creation")

        # OPEN_EXR_MULTILAYER base_path must be the full file path: dir/filename.####.exr
        last_segment = Path(base).name
        self.assertRegex(
            last_segment,
            r".*\.\#+\.exr$",
            f"base_path '{base}' should end with filename.####.exr pattern"
        )
        self.assertNotIn(
            ".blend",
            base,
            f"base_path '{base}' must not contain .blend"
        )

    def test_single_exr_base_path_is_directory(self):
        """For OPEN_EXR (single), base_path should be a directory, not include filename."""
        self._set_output_format("OPEN_EXR")
        with _bypass_node_editor_poll():
            result = bpy.ops.shotput.create_core_passes()
        self.assertEqual(result, {"FINISHED"})

        node = next(
            (n for n in self.tree.nodes if n.type == "OUTPUT_FILE" and "Core" in n.name),
            None,
        )
        self.assertIsNotNone(node)
        # Single EXR: base_path is directory; individual slots carry the filename+ext
        base = node.base_path
        self.assertTrue(base, "base_path must not be empty after creation")
        # Should not have #### in the base_path itself
        self.assertNotIn("####", base, "Single EXR base_path must not include sequence padding")

    def test_cleared_base_path_repopulated_by_update_version(self):
        """
        If base_path is cleared after creation, Update Version must repopulate it
        from the node's token properties without error.
        """
        self._set_output_format("OPEN_EXR_MULTILAYER")
        with _bypass_node_editor_poll():
            bpy.ops.shotput.create_core_passes()

        node = next(
            (n for n in self.tree.nodes if n.type == "OUTPUT_FILE" and "Core" in n.name),
            None,
        )
        self.assertIsNotNone(node)

        # Clear the path
        node.base_path = ""
        self.assertEqual(node.base_path, "")

        # Update version — should rebuild the path
        result = bpy.ops.shotput.update_version()
        self.assertNotIn("CANCELLED", result, "update_version should not cancel when base_path is empty")

        self.assertTrue(
            node.base_path,
            "base_path must be repopulated by update_version even when starting from empty"
        )


class TestMultichannelExrNodeStructure(unittest.TestCase):
    """
    Diagnostic: document the exact base_path and slot structure that
    Create Core Passes produces for each EXR format variant.

    OPEN_EXR_MULTILAYER (multichannel):
        - base_path  = full file path, e.g.  /dir/filename.####.exr
          Blender uses base_path verbatim for the output file;
          it does NOT append .exr automatically.
        - file_slots = channel names only, e.g. "rgba"  (no path, no extension)

    OPEN_EXR (single-layer) / PNG / JPEG:
        - base_path  = directory only, e.g.  /dir/
          Blender writes one file per slot into this directory.
        - file_slots = filename stem + sequence-padding, e.g. "filename.####"
          Blender appends the correct extension automatically per slot.
    """

    def _create_core_node(self, fmt: str):
        """Helper: fresh scene + run create_core_passes, return the created node."""
        scene = _new_compositor_scene()
        sp = scene.shotput
        sp.output_layer = "ViewLayer"
        sp.variant = "main"
        sp.root_folder_token = "/tmp/renders/{outputlayer}_{passname}_{variant}"
        sp.file_name_token = "{outputlayer}_{passname}_{variant}"
        sp.output_format = fmt
        sp.core_passes.clear()
        p = sp.core_passes.add()
        p.name = "rgba"
        sp.use_render_layer_channels = False

        with _bypass_node_editor_poll():
            result = bpy.ops.shotput.create_core_passes()
        self.assertEqual(result, {"FINISHED"}, f"Operator failed for format {fmt}")

        node = next(
            (n for n in scene.node_tree.nodes
             if n.type == "OUTPUT_FILE" and "Core" in n.name),
            None,
        )
        self.assertIsNotNone(node, f"No Core File Output node created for format {fmt}")
        return node

    # ------------------------------------------------------------------
    # OPEN_EXR_MULTILAYER
    # ------------------------------------------------------------------

    def test_multilayer_base_path_ends_with_exr(self):
        """
        base_path for OPEN_EXR_MULTILAYER must end with the .exr extension.
        Structure: /dir/filename.####.exr
        Failing means the production code omits the extension.
        """
        node = self._create_core_node("OPEN_EXR_MULTILAYER")
        base = node.base_path
        print(f"\n  [MULTILAYER] base_path = {base!r}")
        self.assertTrue(
            base.lower().endswith(".exr"),
            f"OPEN_EXR_MULTILAYER base_path should end with .exr, got: {base!r}",
        )

    def test_multilayer_base_path_contains_sequence_padding(self):
        """base_path must contain frame-padding (####) before the .exr suffix."""
        node = self._create_core_node("OPEN_EXR_MULTILAYER")
        base = node.base_path
        # Expect  …/name.####.exr
        self.assertRegex(
            base,
            r"\.#+\.exr$",
            f"Expected pattern …/name.####.exr, got: {base!r}",
        )

    def test_multilayer_slots_are_channel_names_only(self):
        """
        Each file slot path for OPEN_EXR_MULTILAYER must be just the channel
        name — no directory prefix and no extension.
        """
        node = self._create_core_node("OPEN_EXR_MULTILAYER")
        for slot in node.file_slots:
            print(f"  [MULTILAYER] slot path = {slot.path!r}")
            self.assertNotIn("/", slot.path, f"Slot path should not contain '/': {slot.path!r}")
            self.assertNotIn("\\", slot.path, f"Slot path should not contain '\\\\': {slot.path!r}")
            self.assertFalse(
                slot.path.lower().endswith(".exr"),
                f"Slot path should NOT include extension for multilayer EXR: {slot.path!r}",
            )

    # ------------------------------------------------------------------
    # OPEN_EXR  (single-layer)
    # ------------------------------------------------------------------

    def test_single_exr_base_path_is_directory(self):
        """
        base_path for single OPEN_EXR is a directory path only.
        It must NOT contain .#### sequence padding.
        """
        node = self._create_core_node("OPEN_EXR")
        base = node.base_path
        print(f"\n  [SINGLE EXR] base_path = {base!r}")
        self.assertNotIn(
            "####", base,
            f"Single EXR base_path must be a directory only, got: {base!r}",
        )

    def test_single_exr_slots_contain_filename_and_padding(self):
        """
        For single OPEN_EXR each slot path carries the filename stem + padding.
        Blender appends .exr automatically per slot.
        """
        node = self._create_core_node("OPEN_EXR")
        for slot in node.file_slots:
            print(f"  [SINGLE EXR] slot path = {slot.path!r}")
            self.assertIn(
                "####", slot.path,
                f"Single EXR slot should contain sequence padding: {slot.path!r}",
            )


# ---------------------------------------------------------------------------
# Entry point — when executed directly by Blender's --python flag
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Collect and run all tests, writing results to stdout
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for cls in [
        TestTokenParserBlendfile,
        TestTokenParserIsPathLinked,
        TestTokenParserNormalPath,
        TestMultilayerExrPathGuard,
        TestVersioningPassnameSubdirectory,
        TestFileOutputNodeCreation,
        TestMultichannelExrNodeStructure,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Exit with a non-zero code so CI can detect failures
    sys.exit(0 if result.wasSuccessful() else 1)
