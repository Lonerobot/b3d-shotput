"""
UIList classes for displaying pass collections in the Shotput UI.
"""
import bpy
from ...utils import custom_icons


class SHOTPUT_UL_CorePasses(bpy.types.UIList):
    """UIList for core passes"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Use custom icon if available, otherwise fallback to built-in
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)


class SHOTPUT_UL_AOVPasses(bpy.types.UIList):
    """UIList for AOV passes"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Use custom icon if available, otherwise fallback to built-in
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)


class SHOTPUT_UL_StoredPasses(bpy.types.UIList):
    """UIList for stored passes on File Output nodes"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_params = custom_icons.get_icon_id_or_fallback('renderlayers')
        layout.prop(item, "name", text="", emboss=True, **icon_params)


classes = (
    SHOTPUT_UL_CorePasses,
    SHOTPUT_UL_AOVPasses,
    SHOTPUT_UL_StoredPasses,
)
