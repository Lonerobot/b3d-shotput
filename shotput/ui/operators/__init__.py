"""
Shotput UI operators initialization.
"""
from .list_management import (
    SHOTPUT_OT_CorePassAdd,
    SHOTPUT_OT_CorePassRemove,
    SHOTPUT_OT_CorePassMoveUp,
    SHOTPUT_OT_CorePassMoveDown,
    SHOTPUT_OT_AOVPassAdd,
    SHOTPUT_OT_AOVPassRemove,
    SHOTPUT_OT_AOVPassMoveUp,
    SHOTPUT_OT_AOVPassMoveDown,
    SHOTPUT_OT_StoredPassAdd,
    SHOTPUT_OT_StoredPassRemove,
    SHOTPUT_OT_StoredPassMoveUp,
    SHOTPUT_OT_StoredPassMoveDown,
)
from .path_linking import SHOTPUT_OT_TogglePathLinking
from .token_insertion import SHOTPUT_OT_InsertToken
from .preset_loading import SHOTPUT_OT_LoadPresetFromEnvironment
from .sync_passes import SHOTPUT_OT_SyncNodePasses
from .build_layers import SHOTPUT_OT_BuildRenderLayers

__all__ = [
    'SHOTPUT_OT_CorePassAdd',
    'SHOTPUT_OT_CorePassRemove',
    'SHOTPUT_OT_CorePassMoveUp',
    'SHOTPUT_OT_CorePassMoveDown',
    'SHOTPUT_OT_AOVPassAdd',
    'SHOTPUT_OT_AOVPassRemove',
    'SHOTPUT_OT_AOVPassMoveUp',
    'SHOTPUT_OT_AOVPassMoveDown',
    'SHOTPUT_OT_StoredPassAdd',
    'SHOTPUT_OT_StoredPassRemove',
    'SHOTPUT_OT_StoredPassMoveUp',
    'SHOTPUT_OT_StoredPassMoveDown',
    'SHOTPUT_OT_TogglePathLinking',
    'SHOTPUT_OT_InsertToken',
    'SHOTPUT_OT_LoadPresetFromEnvironment',
    'SHOTPUT_OT_SyncNodePasses',
    'SHOTPUT_OT_BuildRenderLayers',
]
