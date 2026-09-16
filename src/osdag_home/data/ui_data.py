"""
Menu data for Osdag GUI.
Provides static data for modules, navigation, and recent projects.
"""
from osdagbridge.core.utils.common import KEY_MODULE_PLATE_GIRDER
class Data:
    # Empty List means "Under Development"
    MODULES = {
        "Home": [""], # Just to suggest that it is not under development
        "OsdagBridge": 
        [
            (KEY_MODULE_PLATE_GIRDER, "Plate Girder Bridge", ":/images/modules/osdagbridge_plategirder.png"),
        ]
    }
    
    NAVBAR_ICONS = {
        "Home": [":/vectors/nav_icons/home_default.svg", ":/vectors/nav_icons/home_clicked.svg"],
        "OsdagBridge": [":/vectors/nav_icons/osdagbridge.svg", ":/vectors/nav_icons/osdagbridge_dark.svg"],
    }

    FLOATING_NAVBAR = [
        (
            ":/vectors/info_default.svg",
            ":/vectors/info_hover.svg",
            "   Info",
            ["About Osdag", "Ask us a question", "Check for Update"]
        ),
        (
            ":/vectors/resources_default.svg",
            ":/vectors/resources_hover.svg",
            "Resources",
            ["Design Examples", "Databases (IS 808:2021)", "Databases (IS 4923:2017)", "Databases (IS 1161:2014)", "Custom Database"]
        ),
        (
            ":/vectors/plugin_default.svg",
            ":/vectors/plugin_hover.svg",
            "Plugins",
            None
        ),
        (
            ":/vectors/load_default.svg",
            ":/vectors/load_hover.svg", 
            " Import",
            None
        ),
    ]

