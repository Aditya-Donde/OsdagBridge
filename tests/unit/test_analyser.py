import pytest
from unittest.mock import MagicMock, patch, call

from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

from osdagbridge.core.bridge_types.plate_girder.dto import (
    SectionProperties,
    SteelProperties,
    ConcreteProperties,
    MaterialProperties,
    GrillageGeometry,
    DeckLayoutProperties
)

from osdagbridge.core.bridge_components.super_structure.plate_girder.geometry import girder_self_weight_kN_m, STEEL_UNIT_WEIGHT_kN_m3
from osdagbridge.core.bridge_components.super_structure.deck.geometry import slab_dead_load_kN_m2, wearing_course_dead_load_kN_m2, WET_CONCRETE_DENSITY_kN_m3
from osdagbridge.core.bridge_components.super_structure.footpath.geometry import footpath_dead_load_kN_m2
from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import crash_barrier_dead_load_kN_m
from osdagbridge.core.bridge_components.super_structure.railing.geometry import railing_dead_load_kN_m
from osdagbridge.core.bridge_components.super_structure.median.geometry import median_dead_load_kN_m

# Stash the real IRC6 impact-factor function at import time — before any @patch
# decorator can replace it on the class.  Tests that need the real arithmetic
# use this reference instead of IRC6_2017.cl_208_3_impact_factor (which is
# replaced by a MagicMock for the duration of TestLiveLoad).
_real_cl_208_3_impact_factor = IRC6_2017.cl_208_3_impact_factor

@pytest.fixture
def bridge():
    return BridgeGrillageModel()

@pytest.fixture
def sample_geometry():
    return GrillageGeometry(
        L=33.5,
        n_l=7,
        n_t=11,
        edge_dist=1.1,
        ext_to_int_dist=2.2775,
        angle=0
    )

@pytest.fixture
def sample_layout():
    return DeckLayoutProperties(
        carriageway_width=7.0,
        crash_barrier_width=0.45,
        footpath_width=1.50,
        railing_width=0.30,
        median_width=1.0,
        n_footpaths=2
    )

@pytest.fixture
def sample_sections():
    return {
        "longitudinal": SectionProperties(
            A=1.025, J=0.1878, Iz=0.3694, Iy=0.3634, Az=0.4979, Ay=0.309
        ),
        "edge_longitudinal": SectionProperties(
            A=0.934, J=0.1857, Iz=0.3478, Iy=0.213602, Az=0.444795, Ay=0.258704
        ),
        "transverse": SectionProperties(
            A=0.504, J=5.22303e-3, Iz=1.3608e-3, Iy=0.32928, Az=0.42, Ay=0.42
        ),
        "end_transverse": SectionProperties(
            A=0.252, J=2.5012e-3, Iz=0.6804e-3, Iy=0.04116, Az=0.21, Ay=0.21
        ),
    }

@pytest.fixture
def sample_material():
    steel = SteelProperties(
        grade="steel", E=200e9, v=0.3, rho=78500.0,
        Fy=250e6, E0=200e9, b=0.01
    )
    concrete = ConcreteProperties(grade="M30", fck=30.0, fctm=2.5, Ecm=31e9)
    return MaterialProperties(steel_prop=steel, concrete_prop=concrete)

class TestInit:
    def test_all_attributes_are_none(self, bridge):
        attrs = [
            "steel_custom", "edge_longitudinal_section", "longitudinal_section",
            "transverse_section", "end_transverse_section", "longitudinal_props",
            "edge_longitudinal_props", "longitudinal_beam", "edge_longitudinal_beam",
            "transverse_slab", "end_transverse_slab", "L", "n_l", "n_t", "edge_dist",
            "ext_to_int_dist", "angle", "w", "model", "wearing_course_load",
            "self_weight_load_case", "layout", "bridge_geometry", "load_manager"
        ]
        for attr in attrs:
            val = getattr(bridge, attr, "MISSING")
            assert val is None, (
                f"__init__ must set '{attr}' to None, but got {val!r}"
            )

    def test_vehicle_maps_are_empty_dicts(self, bridge):
        assert bridge.vehicle_moving_loads_by_case == {}, (
            f"vehicle_moving_loads_by_case should be empty dict, got {bridge.vehicle_moving_loads_by_case!r}"
        )
        assert bridge.vehicle_type_map == {}, (
            f"vehicle_type_map should be empty dict, got {bridge.vehicle_type_map!r}"
        )

    def test_model_is_none(self, bridge):
        assert bridge.model is None, f"model should be None after __init__, got {bridge.model!r}"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.BridgeGeometry")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.CrossSectionLayout")
class TestSetGeometry:
    def test_geometry_values_stored(self, mock_layout, mock_bridge_geom, bridge, sample_geometry, sample_layout):
        bridge.set_geometry(sample_geometry, sample_layout)
        assert bridge.L == sample_geometry.L, f"L expected {sample_geometry.L}, got {bridge.L}"
        assert bridge.n_l == sample_geometry.n_l, f"n_l expected {sample_geometry.n_l}, got {bridge.n_l}"
        assert bridge.n_t == sample_geometry.n_t, f"n_t expected {sample_geometry.n_t}, got {bridge.n_t}"
        assert bridge.edge_dist == sample_geometry.edge_dist, f"edge_dist expected {sample_geometry.edge_dist}, got {bridge.edge_dist}"
        assert bridge.ext_to_int_dist == sample_geometry.ext_to_int_dist, f"ext_to_int_dist expected {sample_geometry.ext_to_int_dist}, got {bridge.ext_to_int_dist}"
        assert bridge.angle == sample_geometry.angle, f"angle expected {sample_geometry.angle}, got {bridge.angle}"

    def test_cross_section_layout_called_with_correct_kwargs(self, mock_layout, mock_bridge_geom, bridge, sample_geometry, sample_layout):
        bridge.set_geometry(sample_geometry, sample_layout)
        mock_layout.assert_called_once_with(
            carriageway_width=sample_layout.carriageway_width,
            crash_barrier_width=sample_layout.crash_barrier_width,
            footpath_width=sample_layout.footpath_width,
            railing_width=sample_layout.railing_width,
            median_width=sample_layout.median_width,
            n_footpaths=sample_layout.n_footpaths
        )

    def test_bridge_geometry_called_with_span_and_width(self, mock_layout, mock_bridge_geom, bridge, sample_geometry, sample_layout):
        mock_layout.return_value.total_width = 12.0
        bridge.set_geometry(sample_geometry, sample_layout)
        mock_bridge_geom.assert_called_with(span=sample_geometry.L, width=12.0)

    def test_layout_stored_on_instance(self, mock_layout, mock_bridge_geom, bridge, sample_geometry, sample_layout):
        bridge.set_geometry(sample_geometry, sample_layout)
        assert bridge.layout == mock_layout.return_value, "layout not stored on bridge instance after set_geometry()"

    def test_bridge_geometry_stored_on_instance(self, mock_layout, mock_bridge_geom, bridge, sample_geometry, sample_layout):
        bridge.set_geometry(sample_geometry, sample_layout)
        assert bridge.bridge_geometry == mock_bridge_geom.return_value, "bridge_geometry not stored on bridge instance after set_geometry()"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_section")
class TestCreateSections:
    def test_create_section_called_four_times(self, mock_create_section, bridge, sample_sections):
        bridge.create_sections(
            sample_sections["longitudinal"], sample_sections["edge_longitudinal"],
            sample_sections["transverse"], sample_sections["end_transverse"]
        )
        assert mock_create_section.call_count == 4, f"og.create_section should be called 4 times, got {mock_create_section.call_count}"

    def test_longitudinal_props_stored(self, mock_create_section, bridge, sample_sections):
        bridge.create_sections(
            sample_sections["longitudinal"], sample_sections["edge_longitudinal"],
            sample_sections["transverse"], sample_sections["end_transverse"]
        )
        assert bridge.longitudinal_props is sample_sections["longitudinal"], "longitudinal_props not stored correctly after create_sections()"

    def test_edge_longitudinal_props_stored(self, mock_create_section, bridge, sample_sections):
        bridge.create_sections(
            sample_sections["longitudinal"], sample_sections["edge_longitudinal"],
            sample_sections["transverse"], sample_sections["end_transverse"]
        )
        assert bridge.edge_longitudinal_props is sample_sections["edge_longitudinal"], "edge_longitudinal_props not stored correctly after create_sections()"

    def test_transverse_section_has_unit_width_true(self, mock_create_section, bridge, sample_sections):
        bridge.create_sections(
            sample_sections["longitudinal"], sample_sections["edge_longitudinal"],
            sample_sections["transverse"], sample_sections["end_transverse"]
        )
        calls_with_unit_width = [call for call in mock_create_section.call_args_list if call.kwargs.get("unit_width") is True]
        assert len(calls_with_unit_width) == 1, f"Expected exactly 1 section with unit_width=True, got {len(calls_with_unit_width)}"

    def test_all_section_attributes_set_on_instance(self, mock_create_section, bridge, sample_sections):
        bridge.create_sections(
            sample_sections["longitudinal"], sample_sections["edge_longitudinal"],
            sample_sections["transverse"], sample_sections["end_transverse"]
        )
        assert bridge.longitudinal_section is not None, "longitudinal_section should not be None after create_sections()"
        assert bridge.edge_longitudinal_section is not None, "edge_longitudinal_section should not be None after create_sections()"
        assert bridge.transverse_section is not None, "transverse_section should not be None after create_sections()"
        assert bridge.end_transverse_section is not None, "end_transverse_section should not be None after create_sections()"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_material")
class TestCreateMaterial:
    def test_og_create_material_called_once(self, mock_create_material, bridge, sample_material):
        bridge.create_material(sample_material)
        assert mock_create_material.call_count == 1, f"og.create_material should be called once, got {mock_create_material.call_count}"

    def test_material_called_with_steel_keyword(self, mock_create_material, bridge, sample_material):
        bridge.create_material(sample_material)
        # Verify material="steel" was part of kwargs
        found = False
        for call in mock_create_material.call_args_list:
            if call.kwargs.get("material") == "steel":
                found = True
        assert found, "og.create_material was never called with material='steel'"

    def test_correct_properties_passed(self, mock_create_material, bridge, sample_material):
        bridge.create_material(sample_material)
        found = False
        for call in mock_create_material.call_args_list:
            if (
                call.kwargs.get("E") == sample_material.steel_prop.E
                and call.kwargs.get("v") == sample_material.steel_prop.v
                and call.kwargs.get("rho") == sample_material.steel_prop.rho
            ):
                found = True
        assert found, f"og.create_material was not called with expected E={sample_material.steel_prop.E}, v={sample_material.steel_prop.v}, rho={sample_material.steel_prop.rho}"

    def test_steel_custom_stored_on_instance(self, mock_create_material, bridge, sample_material):
        bridge.create_material(sample_material)
        assert bridge.steel_custom == mock_create_material.return_value, f"steel_custom not stored correctly, got {bridge.steel_custom!r}"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_member")
class TestAssignMembers:
    def test_create_member_called_four_times(self, mock_create_member, bridge):
        bridge.longitudinal_section = MagicMock()
        bridge.edge_longitudinal_section = MagicMock()
        bridge.transverse_section = MagicMock()
        bridge.end_transverse_section = MagicMock()
        bridge.steel_custom = MagicMock()
        bridge.assign_members()
        assert mock_create_member.call_count == 4, f"og.create_member should be called 4 times, got {mock_create_member.call_count}"

    def test_longitudinal_beam_stored(self, mock_create_member, bridge):
        bridge.longitudinal_section = MagicMock()
        bridge.edge_longitudinal_section = MagicMock()
        bridge.transverse_section = MagicMock()
        bridge.end_transverse_section = MagicMock()
        bridge.steel_custom = MagicMock()
        bridge.assign_members()
        assert bridge.longitudinal_beam is not None, "longitudinal_beam should not be None after assign_members()"

    def test_edge_longitudinal_beam_stored(self, mock_create_member, bridge):
        bridge.longitudinal_section = MagicMock()
        bridge.edge_longitudinal_section = MagicMock()
        bridge.transverse_section = MagicMock()
        bridge.end_transverse_section = MagicMock()
        bridge.steel_custom = MagicMock()
        bridge.assign_members()
        assert bridge.edge_longitudinal_beam is not None, "edge_longitudinal_beam should not be None after assign_members()"

    def test_transverse_and_end_transverse_stored(self, mock_create_member, bridge):
        bridge.longitudinal_section = MagicMock()
        bridge.edge_longitudinal_section = MagicMock()
        bridge.transverse_section = MagicMock()
        bridge.end_transverse_section = MagicMock()
        bridge.steel_custom = MagicMock()
        bridge.assign_members()
        assert bridge.transverse_slab is not None, "transverse_slab should not be None after assign_members()"
        assert bridge.end_transverse_slab is not None, "end_transverse_slab should not be None after assign_members()"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.LoadPlacementManager")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_grillage")
class TestCreateModel:
    def _setup_bridge(self, bridge, edge_dist):
        bridge.longitudinal_beam = MagicMock()
        bridge.edge_longitudinal_beam = MagicMock()
        bridge.transverse_slab = MagicMock()
        bridge.end_transverse_slab = MagicMock()
        bridge.L = 33.5
        bridge.w = 12.0
        bridge.angle = 0
        bridge.n_l = 7
        bridge.n_t = 11
        bridge.edge_dist = edge_dist
        bridge.ext_to_int_dist = 2.2775
        bridge.bridge_geometry = MagicMock()
        bridge.layout = MagicMock()

    def test_og_create_grillage_called_once(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=1.1)
        bridge.create_model()
        assert mock_create_grillage.call_count == 1, f"og.create_grillage should be called once, got {mock_create_grillage.call_count}"

    def test_grillage_called_with_correct_params(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=1.1)
        bridge.create_model()
        found = False
        for call in mock_create_grillage.call_args_list:
            if (
                call.kwargs.get("long_dim") == bridge.L
                and call.kwargs.get("mesh_type") == "Oblique"
                and call.kwargs.get("num_long_grid") == bridge.n_l
                and call.kwargs.get("num_trans_grid") == bridge.n_t
            ):
                found = True
        assert found, f"og.create_grillage not called with expected long_dim={bridge.L}, mesh_type='Oblique', num_long_grid={bridge.n_l}, num_trans_grid={bridge.n_t}"

    def test_set_member_called_seven_times(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=1.1)
        mock_model = mock_create_grillage.return_value
        bridge.create_model()
        assert mock_model.set_member.call_count == 7, f"set_member should be called 7 times, got {mock_model.set_member.call_count}"

    def test_edge_beam_uses_edge_longitudinal_when_overhang_exists(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=1.1)
        mock_model = mock_create_grillage.return_value
        bridge.create_model()
        mock_model.set_member.assert_any_call(bridge.edge_longitudinal_beam, member="edge_beam")

    def test_edge_beam_uses_longitudinal_when_no_overhang(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=0)
        mock_model = mock_create_grillage.return_value
        bridge.create_model()
        mock_model.set_member.assert_any_call(bridge.longitudinal_beam, member="edge_beam")

    def test_edge_beam_no_overhang_never_uses_edge_longitudinal_beam(self, mock_create_grillage, mock_lpm, bridge):
        """When edge_dist=0 the code must fall into the else branch and use longitudinal_beam,
        NOT edge_longitudinal_beam, for the edge_beam member.  This guards against someone
        removing or inverting the `if self.edge_dist > 0` condition in create_model().
        Uses object-identity comparison so the check is not fooled by string repr."""
        self._setup_bridge(bridge, edge_dist=0)
        mock_model = mock_create_grillage.return_value
        bridge.create_model()
        # Collect the first positional argument from every set_member() call
        all_first_args = [c.args[0] for c in mock_model.set_member.call_args_list]
        assert bridge.edge_longitudinal_beam not in all_first_args, (
            "edge_longitudinal_beam was passed to set_member even though edge_dist=0"
        )

    def test_create_osp_model_called_with_pyfile_false(self, mock_create_grillage, mock_lpm, bridge):
        self._setup_bridge(bridge, edge_dist=1.1)
        mock_model = mock_create_grillage.return_value
        bridge.create_model()
        mock_model.create_osp_model.assert_called_with(pyfile=False)

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_vertex")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.girder_self_weight_kN_m")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.slab_dead_load_kN_m2")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.wearing_course_dead_load_kN_m2")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.footpath_dead_load_kN_m2")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.crash_barrier_dead_load_kN_m")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.railing_dead_load_kN_m")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.median_dead_load_kN_m")
class TestDeadLoads:
    def _ready_bridge(self, bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder):
        bridge.model = MagicMock()
        bridge.load_manager = MagicMock()
        bridge.layout = MagicMock()
        bridge.L = 33.5
        bridge.longitudinal_props = MagicMock()
        bridge.longitudinal_props.A = 1.025
        bridge.model.Mesh_obj.noz = [0.0, 2.0, 4.0, 6.0, 8.0]
        
        point_mock = MagicMock()
        point_mock.x = 0.0
        point_mock.y = 0.0
        point_mock.z = 0.0
        
        geom_patch_mock = MagicMock()
        geom_patch_mock.p1 = point_mock
        geom_patch_mock.p2 = point_mock
        geom_patch_mock.p3 = point_mock
        geom_patch_mock.p4 = point_mock
        
        geom_line_mock = MagicMock()
        geom_line_mock.start = point_mock
        geom_line_mock.end = point_mock
        
        bridge.load_manager.deck_load.return_value = geom_patch_mock
        bridge.load_manager.overlay_load.return_value = geom_patch_mock
        bridge.load_manager.footpath_load.return_value = geom_patch_mock
        bridge.load_manager.crash_barrier_load.return_value = geom_line_mock
        bridge.load_manager.railing_load.return_value = geom_line_mock
        bridge.load_manager.median_line_load.return_value = geom_line_mock
        # Use actual functions to test computed load values dynamically
        mock_girder.side_effect = girder_self_weight_kN_m
        mock_slab.side_effect = slab_dead_load_kN_m2
        mock_wearing.side_effect = wearing_course_dead_load_kN_m2
        mock_footpath.side_effect = footpath_dead_load_kN_m2
        mock_crash.side_effect = crash_barrier_dead_load_kN_m
        mock_railing.side_effect = railing_dead_load_kN_m
        mock_median.side_effect = median_dead_load_kN_m

    def test_self_weight_raises_valueerror_when_model_is_none(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        with pytest.raises(ValueError):
            bridge.create_self_weight_load()

    def test_self_weight_raises_valueerror_when_longitudinal_props_is_none(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        bridge.model = MagicMock()
        bridge.longitudinal_props = None
        with pytest.raises(ValueError):
            bridge.create_self_weight_load()

    def test_self_weight_load_case_stored_on_instance(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.create_self_weight_load()
        assert bridge.self_weight_load_case is not None, "self_weight_load_case should not be None after create_self_weight_load()"

    def test_self_weight_load_case_has_correct_name(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.create_self_weight_load()
        mock_lc.assert_any_call(name="girder self weight")

    def test_deck_raises_valueerror_when_no_model(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        with pytest.raises(ValueError):
            bridge.create_deck_load(slab_thickness_m=0.2)

    def test_deck_raises_valueerror_when_no_thickness(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        with pytest.raises(ValueError):
            bridge.create_deck_load()

    def test_deck_load_case_stored(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.create_deck_load(slab_thickness_m=0.200)
        assert bridge.deck_load_case is not None, "deck_load_case should not be None after create_deck_load()"

    def test_deck_load_case_name(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.create_deck_load(slab_thickness_m=0.200)
        mock_lc.assert_any_call(name="Deck slab load")

    def test_wearing_course_raises_when_no_thickness(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        with pytest.raises(ValueError):
            bridge.create_wearing_course_load()

    def test_wearing_course_stored(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.create_wearing_course_load(thickness_m=0.050)
        assert bridge.wearing_course_load is not None, "wearing_course_load should not be None after create_wearing_course_load()"

    def test_footpath_returns_none_and_warns_when_no_footpath_in_layout(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.return_value = False
        with pytest.warns(UserWarning):
            assert bridge.create_footpath_load() is None, "create_footpath_load() should return None and warn if footpath is not in layout"

    def test_footpath_load_case_stored_when_footpath_present(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.side_effect = lambda x: x in ("footpath_left", "footpath_right")
        bridge.create_footpath_load()
        assert bridge.footpath_load_case is not None, "footpath_load_case should not be None when footpath is in layout"

    def test_crash_barrier_returns_none_and_warns_when_not_in_layout(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.return_value = False
        with pytest.warns(UserWarning):
            assert bridge.create_crash_barrier_load() is None, "create_crash_barrier_load() should return None and warn if crash barrier is not in layout"

    def test_crash_barrier_load_case_stored_when_present(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.side_effect = lambda x: x in ("crash_barrier_left", "crash_barrier_right")
        bridge.create_crash_barrier_load()
        assert bridge.crash_barrier_load_case is not None, "crash_barrier_load_case should not be None when crash barrier is in layout"

    def test_railing_returns_none_and_warns_when_not_in_layout(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.return_value = False
        with pytest.warns(UserWarning):
            assert bridge.create_railing_load() is None, "create_railing_load() should return None and warn if railing is not in layout"

    def test_railing_load_case_stored_when_present(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.side_effect = lambda x: x in ("railing_left", "railing_right")
        bridge.create_railing_load()
        assert bridge.railing_load_case is not None, "railing_load_case should not be None when railing is in layout"

    def test_median_returns_none_and_warns_when_not_in_layout(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.return_value = False
        with pytest.warns(UserWarning):
            assert bridge.create_median_load() is None, "create_median_load() should return None and warn if median is not in layout"

    def test_median_load_case_stored_when_present(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.side_effect = lambda x: x == "median"
        bridge.create_median_load()
        assert bridge.median_load_case is not None, "median_load_case should not be None when median is in layout"

    def test_median_load_case_name(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        bridge.layout.has_component.side_effect = lambda x: x == "median"
        bridge.create_median_load()
        mock_lc.assert_any_call(name="Median load")

    def test_self_weight_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.return_value = "line_load_obj"
        mock_lc.return_value = MagicMock()
        bridge.create_self_weight_load()

        expected_ld = girder_self_weight_kN_m(1.025, STEEL_UNIT_WEIGHT_kN_m3) * 1000.0
        expected_ld_calls = []
        expected_z_positions = bridge.model.Mesh_obj.noz[1:-1]
        for z_pos in expected_z_positions:
            mock_vtx.assert_any_call(x=0, z=z_pos, p=pytest.approx(expected_ld))
            mock_vtx.assert_any_call(x=bridge.L, z=z_pos, p=pytest.approx(expected_ld))
            expected_ld_calls.append(call(
                loadtype="line",
                point1=f"vtx_0_{z_pos}_{expected_ld}",
                point2=f"vtx_{bridge.L}_{z_pos}_{expected_ld}"
            ))
        mock_ld.assert_has_calls(expected_ld_calls, any_order=True)
        expected_call_count = len(bridge.model.Mesh_obj.noz) - 2
        assert mock_lc.return_value.add_load.call_count == expected_call_count, (
            f"Self-weight: add_load should be called {expected_call_count} times (one per interior beam), got {mock_lc.return_value.add_load.call_count}"
        )
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

    def test_self_weight_vertex_count_matches_interior_noz_positions(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        """og.create_load_vertex must be called exactly 2 × (len(noz) - 2) times — once
        for start and once for end of each interior z position.  If the loop in
        create_self_weight_load() changes (e.g. accidentally includes edge positions
        or skips an interior beam), this count will diverge and the test fails."""
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_lc.return_value = MagicMock()
        noz = bridge.model.Mesh_obj.noz  # [0.0, 2.0, 4.0, 6.0, 8.0]
        interior_count = len(noz) - 2  # positions at indices 1..-2 → 3
        bridge.create_self_weight_load()
        # Two vertices per interior z-position (start_beam and end_beam)
        assert mock_vtx.call_count == 2 * interior_count, (
            f"Self-weight loop: expected {2 * interior_count} vertex calls (2 per interior beam), got {mock_vtx.call_count}; "
            f"noz={list(noz)}, interior_count={interior_count}"
        )
        # One og.create_load call per interior z-position (one line load object)
        assert mock_ld.call_count == interior_count, (
            f"Self-weight loop: expected {interior_count} load calls (1 per interior beam), got {mock_ld.call_count}"
        )

    def test_deck_load_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.return_value = "patch_load_obj"
        mock_lc.return_value = MagicMock()
        
        geom_patch_mock = MagicMock()
        geom_patch_mock.p1.x, geom_patch_mock.p1.z = 1.0, 1.1
        geom_patch_mock.p2.x, geom_patch_mock.p2.z = 2.0, 2.1
        geom_patch_mock.p3.x, geom_patch_mock.p3.z = 3.0, 3.1
        geom_patch_mock.p4.x, geom_patch_mock.p4.z = 4.0, 4.1
        bridge.load_manager.deck_load.return_value = geom_patch_mock

        bridge.create_deck_load(slab_thickness_m=0.2)

        expected_ld = slab_dead_load_kN_m2(0.2, WET_CONCRETE_DENSITY_kN_m3) * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=2.0, z=2.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=3.0, z=3.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=4.0, z=4.1, p=pytest.approx(expected_ld))
        mock_ld.assert_called_once_with(
            loadtype="patch", name="deck slab",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}",
            point3=f"vtx_3.0_3.1_{expected_ld}", point4=f"vtx_4.0_4.1_{expected_ld}"
        )
        mock_lc.return_value.add_load.assert_called_once_with("patch_load_obj")
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

    def test_wearing_course_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.return_value = "patch_load_obj"
        mock_lc.return_value = MagicMock()
        
        geom_patch_mock = MagicMock()
        geom_patch_mock.p1.x, geom_patch_mock.p1.z = 1.0, 1.1
        geom_patch_mock.p2.x, geom_patch_mock.p2.z = 2.0, 2.1
        geom_patch_mock.p3.x, geom_patch_mock.p3.z = 3.0, 3.1
        geom_patch_mock.p4.x, geom_patch_mock.p4.z = 4.0, 4.1
        bridge.load_manager.overlay_load.return_value = geom_patch_mock

        bridge.create_wearing_course_load(thickness_m=0.05, partial_safety_factor=1.5)

        expected_ld = wearing_course_dead_load_kN_m2(0.05) * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_ld.assert_called_once_with(
            loadtype="patch", name="overlay",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}",
            point3=f"vtx_3.0_3.1_{expected_ld}", point4=f"vtx_4.0_4.1_{expected_ld}"
        )
        mock_lc.assert_any_call(name="1.5 DW")
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value, load_factor=1.5)

    def test_footpath_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.side_effect = lambda **kwargs: f"patch_load_{kwargs['name']}"
        mock_lc.return_value = MagicMock()
        
        bridge.layout.has_component.side_effect = lambda x: x in ("footpath_left", "footpath_right")
        
        geom_left = MagicMock()
        geom_left.p1.x, geom_left.p1.z = 1.0, 1.1
        geom_left.p2.x, geom_left.p2.z = 2.0, 2.1
        geom_left.p3.x, geom_left.p3.z = 3.0, 3.1
        geom_left.p4.x, geom_left.p4.z = 4.0, 4.1

        geom_right = MagicMock()
        geom_right.p1.x, geom_right.p1.z = 10.0, 10.1
        geom_right.p2.x, geom_right.p2.z = 20.0, 20.1
        geom_right.p3.x, geom_right.p3.z = 30.0, 30.1
        geom_right.p4.x, geom_right.p4.z = 40.0, 40.1

        bridge.load_manager.footpath_load.side_effect = lambda side: geom_left if side == "left" else geom_right

        bridge.create_footpath_load()

        expected_ld = footpath_dead_load_kN_m2() * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=10.0, z=10.1, p=pytest.approx(expected_ld))

        mock_ld.assert_any_call(
            loadtype="patch", name="left footpath",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}",
            point3=f"vtx_3.0_3.1_{expected_ld}", point4=f"vtx_4.0_4.1_{expected_ld}"
        )
        mock_ld.assert_any_call(
            loadtype="patch", name="right footpath",
            point1=f"vtx_10.0_10.1_{expected_ld}", point2=f"vtx_20.0_20.1_{expected_ld}",
            point3=f"vtx_30.0_30.1_{expected_ld}", point4=f"vtx_40.0_40.1_{expected_ld}"
        )
        assert mock_lc.return_value.add_load.call_count == 2, (
            f"Footpath: expected 2 add_load calls (left + right), got {mock_lc.return_value.add_load.call_count}"
        )
        mock_lc.return_value.add_load.assert_any_call("patch_load_left footpath")
        mock_lc.return_value.add_load.assert_any_call("patch_load_right footpath")
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

    def test_crash_barrier_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.side_effect = lambda **kwargs: f"line_load_{kwargs['name']}"
        mock_lc.return_value = MagicMock()
        
        bridge.layout.has_component.side_effect = lambda x: x in ("crash_barrier_left", "crash_barrier_right")
        
        geom_left = MagicMock()
        geom_left.start.x, geom_left.start.z = 1.0, 1.1
        geom_left.end.x, geom_left.end.z = 2.0, 2.1

        geom_right = MagicMock()
        geom_right.start.x, geom_right.start.z = 10.0, 10.1
        geom_right.end.x, geom_right.end.z = 20.0, 20.1

        bridge.load_manager.crash_barrier_load.side_effect = lambda side: geom_left if side == "left" else geom_right

        bridge.create_crash_barrier_load()

        expected_ld = crash_barrier_dead_load_kN_m() * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=10.0, z=10.1, p=pytest.approx(expected_ld))
        
        mock_ld.assert_any_call(
            loadtype="line", name="left crash barrier",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}"
        )
        mock_ld.assert_any_call(
            loadtype="line", name="right crash barrier",
            point1=f"vtx_10.0_10.1_{expected_ld}", point2=f"vtx_20.0_20.1_{expected_ld}"
        )
        assert mock_lc.return_value.add_load.call_count == 2, (
            f"Crash barrier: expected 2 add_load calls (left + right), got {mock_lc.return_value.add_load.call_count}"
        )
        mock_lc.return_value.add_load.assert_any_call("line_load_left crash barrier")
        mock_lc.return_value.add_load.assert_any_call("line_load_right crash barrier")
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

    def test_railing_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.side_effect = lambda **kwargs: f"line_load_{kwargs['name']}"
        mock_lc.return_value = MagicMock()
        
        bridge.layout.has_component.side_effect = lambda x: x in ("railing_left", "railing_right")
        
        geom_left = MagicMock()
        geom_left.start.x, geom_left.start.z = 1.0, 1.1
        geom_left.end.x, geom_left.end.z = 2.0, 2.1

        geom_right = MagicMock()
        geom_right.start.x, geom_right.start.z = 10.0, 10.1
        geom_right.end.x, geom_right.end.z = 20.0, 20.1

        bridge.load_manager.railing_load.side_effect = lambda side: geom_left if side == "left" else geom_right

        bridge.create_railing_load()

        expected_ld = railing_dead_load_kN_m() * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=10.0, z=10.1, p=pytest.approx(expected_ld))
        
        mock_ld.assert_any_call(
            loadtype="line", name="left railing",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}"
        )
        mock_ld.assert_any_call(
            loadtype="line", name="right railing",
            point1=f"vtx_10.0_10.1_{expected_ld}", point2=f"vtx_20.0_20.1_{expected_ld}"
        )
        assert mock_lc.return_value.add_load.call_count == 2, (
            f"Railing: expected 2 add_load calls (left + right), got {mock_lc.return_value.add_load.call_count}"
        )
        mock_lc.return_value.add_load.assert_any_call("line_load_left railing")
        mock_lc.return_value.add_load.assert_any_call("line_load_right railing")
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

    def test_median_creates_correct_vertices_and_loads(self, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder, mock_vtx, mock_ld, mock_lc, bridge):
        self._ready_bridge(bridge, mock_median, mock_railing, mock_crash, mock_footpath, mock_wearing, mock_slab, mock_girder)
        mock_vtx.side_effect = lambda x, z, p: f"vtx_{x}_{z}_{p}"
        mock_ld.return_value = "line_load_obj"
        mock_lc.return_value = MagicMock()
        
        bridge.layout.has_component.side_effect = lambda x: x == "median"
        geom_line_mock = MagicMock()
        geom_line_mock.start.x, geom_line_mock.start.z = 1.0, 1.1
        geom_line_mock.end.x, geom_line_mock.end.z = 2.0, 2.1
        bridge.load_manager.median_line_load.return_value = geom_line_mock

        bridge.create_median_load()

        expected_ld = median_dead_load_kN_m() * 1000.0

        mock_vtx.assert_any_call(x=1.0, z=1.1, p=pytest.approx(expected_ld))
        mock_vtx.assert_any_call(x=2.0, z=2.1, p=pytest.approx(expected_ld))
        mock_ld.assert_called_once_with(
            loadtype="line", name="median",
            point1=f"vtx_1.0_1.1_{expected_ld}", point2=f"vtx_2.0_2.1_{expected_ld}"
        )
        bridge.model.add_load_case.assert_called_once_with(mock_lc.return_value)

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
