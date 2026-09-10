"""
Menu data for OsdagBridge GUI.
Provides static data for modules, navigation, and the top-right button row.
"""
from osdagbridge.desktop.data.module_keys import KEY_DISP_PLATE_GIRDER_BRIDGE


class Data:
    # Empty List means "Under Development"
    MODULES = {
        "Home": [""], # Just to suggest that it is not under development
        "Plate Girder Bridge":
        [
            (KEY_DISP_PLATE_GIRDER_BRIDGE, "Composite Plate Girder Bridge", ":/images/modules/plate_girder_bridge.png")
        ],
        "Box Girder Bridge":
        [],
        "Truss Bridge":
        [],
        "Substructure":
        [],
        "Foundation":
        []
    }

    NAVBAR_ICONS = {
        "Home": [":/vectors/nav_icons/home_default.svg", ":/vectors/nav_icons/home_clicked.svg"],
        "Plate Girder Bridge": [":/vectors/nav_icons/flexural_member.svg"],
        "Box Girder Bridge": [":/vectors/nav_icons/beam_column.svg"],
        "Truss Bridge": [":/vectors/nav_icons/truss.svg"],
        "Substructure": [":/vectors/nav_icons/compression_member.svg"],
        "Foundation": [":/vectors/nav_icons/2d_frame.svg"],
    }

    # Recents rows show the module's own artwork where it exists. Without an
    # entry here the row falls back to the navbar glyph's "recents" variant,
    # which for the bridge categories is still a borrowed Osdag member icon.
    RECENTS_ICONS = {
        "Plate Girder Bridge": ":/images/modules/plate_girder_bridge.png",
    }

    FLOATING_NAVBAR = [
        (
            ":/vectors/info_default.svg",
            ":/vectors/info_hover.svg",
            "   Info",
            ["About OsdagBridge", "Ask us a question", "Check for Update"]
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
