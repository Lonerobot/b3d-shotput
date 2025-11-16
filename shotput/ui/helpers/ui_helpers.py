"""
Helper utilities for UI rendering and common patterns.
Provides cleaner APIs for icon loading and layout management.
"""
import bpy
from ...utils import custom_icons


class UIHelper:
    """Helper class for common UI patterns and icon management"""
    
    @staticmethod
    def get_icon(icon_name):
        """Get icon parameters for UI elements
        
        Args:
            icon_name: Name of the icon to load
            
        Returns:
            Dictionary with icon parameters for unpacking into UI calls
        """
        return custom_icons.get_icon_id_or_fallback(icon_name)
    
    @staticmethod
    def icon_operator(layout, operator_id, icon_name, text="", **kwargs):
        """Create an operator button with icon
        
        Args:
            layout: UI layout to add operator to
            operator_id: Operator bl_idname
            icon_name: Name of icon to use
            text: Button text (optional)
            **kwargs: Additional operator properties
            
        Returns:
            Operator button reference
        """
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        return layout.operator(operator_id, text=text, **icon, **kwargs)
    
    @staticmethod
    def icon_label(layout, text, icon_name, **kwargs):
        """Create a label with icon
        
        Args:
            layout: UI layout to add label to
            text: Label text
            icon_name: Name of icon to use
            **kwargs: Additional layout properties
            
        Returns:
            Label reference
        """
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        return layout.label(text=text, **icon, **kwargs)
    
    @staticmethod
    def icon_menu(layout, menu_id, icon_name, text="", **kwargs):
        """Create a menu with icon
        
        Args:
            layout: UI layout to add menu to
            menu_id: Menu bl_idname
            icon_name: Name of icon to use
            text: Menu text (optional)
            **kwargs: Additional menu properties
            
        Returns:
            Menu reference
        """
        icon = custom_icons.get_icon_id_or_fallback(icon_name)
        return layout.menu(menu_id, text=text, **icon, **kwargs)
