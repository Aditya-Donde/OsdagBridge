from osdagbridge.core.bridge_components.super_structure.girder import properties


def test_get_beam_profile_reads_from_resource_db():
    profile = properties.get_beam_profile("WB 500")

    assert profile is not None
    assert profile.depth_mm == 500.0
    assert profile.flange_width_mm == 250.0
    assert profile.web_thickness_mm == 9.9


def test_get_rolled_section_returns_outline_dict():
    outline = properties.get_rolled_section("WB 500")

    assert outline == {
        "designation": "WB 500",
        "depth_mm": 500.0,
        "top_flange_width_mm": 250.0,
        "bottom_flange_width_mm": 250.0,
        "web_thickness_mm": 9.9,
        "top_flange_thickness_mm": 14.7,
        "bottom_flange_thickness_mm": 14.7,
    }


def test_unknown_section_returns_none():
    assert properties.get_beam_profile("NON_EXISTENT") is None
    assert properties.get_rolled_section("NON_EXISTENT") is None
