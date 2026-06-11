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
class TestDeadLoadCombination:
    def test_raises_valueerror_when_no_model(self, mock_lc, bridge):
        bridge.model = None
        with pytest.raises(ValueError):
            bridge.create_dead_load_combination()

    def test_returns_none_and_warns_when_no_sub_cases_set(self, mock_lc, bridge):
        bridge.model = MagicMock()
        with pytest.warns(UserWarning):
            assert bridge.create_dead_load_combination() is None, "create_dead_load_combination() should return None and warn if no sub-cases are set"

    def test_combines_all_non_none_sub_cases(self, mock_lc, bridge):
        bridge.model = MagicMock()
        bridge.self_weight_load_case = MagicMock()
        bridge.self_weight_load_case.load_groups = [{"load": MagicMock()}]
        bridge.deck_load_case = MagicMock()
        bridge.deck_load_case.load_groups = [{"load": MagicMock()}]
        bridge.footpath_load_case = None
        bridge.crash_barrier_load_case = None
        bridge.railing_load_case = None
        bridge.median_load_case = None
        
        result = bridge.create_dead_load_combination()
        assert result is not None, "create_dead_load_combination() should return a value when sub-cases exist"
        assert bridge.dead_load_combination is not None, "dead_load_combination attribute should be set after create_dead_load_combination()"

    def test_dl_combination_load_count_matches_sub_cases(self, mock_lc, bridge):
        """The number of loads added to DL_combined must equal the total number of
        load_groups entries across all non-None sub-cases.  If create_dead_load_combination()
        accidentally skips a sub-case or double-counts one, this count diverges."""
        bridge.model = MagicMock()

        # Build three sub-cases with known load counts (2 + 1 + 3 = 6 total)
        def _make_lc(n_loads):
            lc = MagicMock()
            lc.load_groups = [{"load": MagicMock()} for _ in range(n_loads)]
            return lc

        bridge.self_weight_load_case = _make_lc(2)
        bridge.deck_load_case = _make_lc(1)
        bridge.crash_barrier_load_case = _make_lc(3)
        bridge.footpath_load_case = None
        bridge.railing_load_case = None
        bridge.median_load_case = None

        expected_total = sum(
            len(lc.load_groups)
            for lc in [bridge.self_weight_load_case, bridge.deck_load_case, bridge.crash_barrier_load_case]
            if lc is not None
        )

        # Capture what DL_combined.add_load is called with
        mock_combined_lc = MagicMock()
        mock_lc.return_value = mock_combined_lc

        bridge.create_dead_load_combination()
        assert mock_combined_lc.add_load.call_count == expected_total, (
            f"Expected {expected_total} loads in DL_combined, "
            f"got {mock_combined_lc.add_load.call_count}"
        )

    def test_load_factor_passed_to_model(self, mock_lc, bridge):
        bridge.model = MagicMock()
        bridge.self_weight_load_case = MagicMock()
        bridge.self_weight_load_case.load_groups = [{"load": MagicMock()}]
        bridge.create_dead_load_combination(partial_safety_factor=1.35)
        bridge.model.add_load_case.assert_called_with(bridge.dead_load_combination, load_factor=1.35)

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.cl_209_3_3_transverse_wind_load")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
class TestWindLoad:
    def setup_method(self, method):
        self.bridge = BridgeGrillageModel()
        self.bridge.model = MagicMock()
        self.bridge.L = 33.5
        self.bridge.w = 12.0
        self.bridge.edge_dist = 1.1
        self.bridge.bridge_geometry = MagicMock()
        self.bridge.load_manager = MagicMock()
        self.bridge.model.Mesh_obj.noz = [0.0, 1.1, 10.9, 12.0]
        self.bridge.model.Mesh_obj.nox = [0.0, 16.75, 33.5]
        self.bridge.model.Mesh_obj.node_spec = {
            1: {"coordinate": [0.0, 0.0, 1.1]},
            2: {"coordinate": [33.5, 0.0, 10.9]}
        }


    def test_raises_valueerror_when_model_is_none(self, mock_lc, mock_ld, mock_wind):
        self.bridge.model = None
        with pytest.raises(ValueError):
            self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0)

    def test_returns_dict_with_four_keys(self, mock_lc, mock_ld, mock_wind):
        mock_wind.return_value = {"Pz": 500.0, "G": 2.0, "FT": 100000.0}
        result = self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0)
        assert isinstance(result, dict), f"create_wind_load should return a dict, got {type(result).__name__}"
        assert set(result.keys()) == {"WL_T", "WL_L", "WL_V", "WL"}, (
            f"Wind load dict should have keys {{WL_T, WL_L, WL_V, WL}}, got {set(result.keys())}"
        )

    def test_wind_transverse_load_case_stored(self, mock_lc, mock_ld, mock_wind):
        mock_wind.return_value = {"Pz": 500.0, "G": 2.0, "FT": 100000.0}
        self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0)
        assert self.bridge.wind_transverse_load_case is not None, "wind_transverse_load_case should not be None after create_wind_load()"

    def test_wind_longitudinal_load_case_stored(self, mock_lc, mock_ld, mock_wind):
        mock_wind.return_value = {"Pz": 500.0, "G": 2.0, "FT": 100000.0}
        self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0)
        assert self.bridge.wind_longitudinal_load_case is not None, "wind_longitudinal_load_case should not be None after create_wind_load()"

    def test_wind_combined_registered_with_partial_safety_factor(self, mock_lc, mock_ld, mock_wind):
        mock_wind.return_value = {"Pz": 500.0, "G": 2.0, "FT": 100000.0}
        self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0, partial_safety_factor=1.5)
        found = False
        for call_args in self.bridge.model.add_load_case.call_args_list:
            if call_args.kwargs.get("load_factor") == 1.5:
                found = True
                break
        assert found, "add_load_case not called with load_factor=1.5"

    def test_wind_load_calculates_correct_forces_and_nodal_loads(self, mock_lc, mock_ld, mock_wind):
        mock_wind.return_value = {"Pz": 500.0, "G": 2.0, "FT": 100000.0}
        
        # Calculate expected values mathematically from the mock inputs:
        FT = 100000.0
        span = self.bridge.L
        width = self.bridge.w
        Pz = 500.0
        G = 2.0
        CL = 0.75
        
        nox = self.bridge.model.Mesh_obj.nox
        noz = self.bridge.model.Mesh_obj.noz
        
        # Node 1 coordinate is [0.0, 0.0, 1.1]
        # trib_x for x=0.0 in [0.0, 16.75, 33.5] is (16.75 - 0.0) / 2 = 8.375
        trib_x = (nox[1] - nox[0]) / 2
        # trib_z for z=1.1 in [0.0, 1.1, 10.9, 12.0] is (1.1 - 0.0) / 2 + (10.9 - 1.1) / 2 = 5.45
        trib_z = ((noz[1] - noz[0]) / 2) + ((noz[2] - noz[1]) / 2)
        trib_area = trib_x * trib_z
        
        FT_per_m = FT / span
        FL_per_m2 = (0.25 * FT) / (span * width)
        FV_per_m2 = Pz * G * CL
        
        expected_fz = FT_per_m * trib_x
        expected_fx = FL_per_m2 * trib_area
        expected_fy = -FV_per_m2 * trib_area

        mock_deck = MagicMock()
        mock_deck.p1.x, mock_deck.p1.z = 0.0, 0.0
        mock_deck.p2.x, mock_deck.p2.z = 33.5, 0.0
        mock_deck.p3.x, mock_deck.p3.z = 33.5, 12.0
        mock_deck.p4.x, mock_deck.p4.z = 0.0, 12.0
        self.bridge.load_manager.deck_load.return_value = mock_deck

        mock_lc.side_effect = lambda name: MagicMock(name=name, load_groups=[])

        self.bridge.create_wind_load(c_spacing=2.2775, d_depth=1.5, crash_barrier_height=1.0)
        
        transverse_forces = []
        longitudinal_forces = []
        uplift_forces = []

        for call_args in mock_ld.call_args_list:
            kwargs = call_args.kwargs
            if kwargs.get("loadtype") == "nodal":
                if kwargs.get("Fz", 0) > 0 and kwargs.get("Fx", 0) == 0:
                    transverse_forces.append(kwargs.get("Fz"))
                if kwargs.get("Fx", 0) > 0 and kwargs.get("Fz", 0) == 0:
                    longitudinal_forces.append(kwargs.get("Fx"))
                if kwargs.get("Fy", 0) < 0:
                    uplift_forces.append(kwargs.get("Fy"))

        assert len(transverse_forces) > 0, "Transverse nodal load was not created"
        assert len(longitudinal_forces) > 0, "Longitudinal nodal load was not created"
        assert len(uplift_forces) > 0, "Uplift nodal load was not created"

        # Check exact calculated magnitude values and unit mappings
        assert transverse_forces[0] == pytest.approx(expected_fz, rel=1e-3), (
            f"Wind transverse force expected ~{expected_fz} N, got {transverse_forces[0]}"
        )
        assert longitudinal_forces[0] == pytest.approx(expected_fx, rel=1e-3), (
            f"Wind longitudinal force expected ~{expected_fx} N, got {longitudinal_forces[0]}"
        )
        assert uplift_forces[0] == pytest.approx(expected_fy, rel=1e-3), (
            f"Wind uplift force expected ~{expected_fy} N, got {uplift_forces[0]}"
        )



@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_model")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.cl_208_3_impact_factor")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.table_6A")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.table_6")
class TestLiveLoad:
    def setup_method(self, method):
        self.bridge = BridgeGrillageModel()
        self.bridge.model = MagicMock()
        self.bridge.layout = MagicMock()
        self.bridge.L = 33.5
        
    def test_vehicle_lane_coordinates_returns_list(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}, {"Class70R": 1}]}
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        result = self.bridge.vehicle_lane_coordinates()
        assert isinstance(result, list), f"vehicle_lane_coordinates should return a list, got {type(result).__name__}"
        assert len(result) > 0, "vehicle_lane_coordinates returned an empty list — expected at least one combination"

    def test_case_num_increments_from_one(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}, {"Class70R": 1}]}
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        result = self.bridge.vehicle_lane_coordinates()
        assert result[0]["case_num"] == 1, f"First case_num should be 1, got {result[0]['case_num']}"
        assert result[1]["case_num"] == 2, f"Second case_num should be 2, got {result[1]['case_num']}"

    def test_classA_assigned_one_lane_per_vehicle(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}]}
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        result = self.bridge.vehicle_lane_coordinates()
        for item in result:
            for v_name, coords in item.get("combinations", {}).items():
                if v_name.startswith("ClassA"):
                    assert len(coords) == 2, (
                        f"ClassA vehicle '{v_name}' should occupy 2 lane positions, got {len(coords)}"
                    )

    def test_class70R_z_coord_is_midpoint_of_two_lanes(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        n_lanes = 2
        mock_t6.return_value = n_lanes
        mock_t6a.return_value = {"vehicle_combinations": [{"Class70R": 1}]}
        carriageway_mock = MagicMock()
        carriageway_mock.z_start = 0.0
        carriageway_mock.width = 7.0
        self.bridge.layout.get_component.return_value = carriageway_mock
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        result = self.bridge.vehicle_lane_coordinates()
        case = result[0]
        z_coord = None
        for k, v in case.get("combinations", {}).items():
            if k.startswith("Class70R"):
                z_coord = v[0][1]
        lane_width = carriageway_mock.width / n_lanes
        z0 = carriageway_mock.z_start + 0.5 * lane_width
        z1 = carriageway_mock.z_start + 1.5 * lane_width
        expected_z = (z0 + z1) / 2
        assert z_coord == expected_z, (
            f"Class70R z-coordinate should be midpoint of lanes = {expected_z}, got {z_coord}"
        )

    def test_vehicle_length_class70r_returns_exact_length(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        result = BridgeGrillageModel._vehicle_length("Class70R")
        assert isinstance(result, float), f"vehicle_length('Class70R') should return float, got {type(result).__name__}"
        expected_length = max(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()['x'])
        assert result == pytest.approx(expected_length, rel=1e-3), f"Class70R length expected ~{expected_length} m, got {result}"

    def test_vehicle_length_classA_returns_exact_length(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        result = BridgeGrillageModel._vehicle_length("ClassA")
        assert isinstance(result, float), f"vehicle_length('ClassA') should return float, got {type(result).__name__}"
        expected_length = max(IRC6_2017.cl_204_1_ClassA_vehicle()['x'])
        assert result == pytest.approx(expected_length, rel=1e-3), f"ClassA length expected ~{expected_length} m, got {result}"

    def test_split_carriageway_with_median_produces_lane_coords_from_both_sides(
        self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm
    ):
        """Split carriageway (carriageway_left + carriageway_right) must collect lanes from both sides."""
        # No single carriageway — only left and right
        self.bridge.layout.has_component.side_effect = lambda x: x in ("carriageway_left", "carriageway_right")

        # left carriageway: 3.5m wide, z_start=0.0 → 1 lane at z=1.75
        cw_left = MagicMock()
        cw_left.width = 3.5
        cw_left.z_start = 0.0

        # right carriageway: 3.5m wide, z_start=5.0 → 1 lane at z=6.75
        cw_right = MagicMock()
        cw_right.width = 3.5
        cw_right.z_start = 5.0

        self.bridge.layout.get_component.side_effect = lambda name: cw_left if name == "carriageway_left" else cw_right

        # IRC6_2017.table_6(3.5) = 1, table_6A(7.0) = ClassA:2 or Class70R:1
        # Cannot assign IRC6_2017.table_6 as side_effect because the class-level @patch
        # already replaces that symbol — calling it would recurse into the mock itself.
        mock_t6.return_value = 1
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}, {"Class70R": 1}]}

        result = self.bridge.vehicle_lane_coordinates()

        # Collect every z coordinate across all cases and combinations
        all_z = []
        for case in result:
            for coords in case["combinations"].values():
                for _, z in coords:
                    all_z.append(z)

        # lane_width = 3.5 / 1 lane = 3.5
        # Left  lane: z = 0.0 + 0.5 * 3.5 = 1.75
        # Right lane: z = 5.0 + 0.5 * 3.5 = 6.75
        left_z_expected  = 0.0 + 0.5 * (3.5 / 1)
        right_z_expected = 5.0 + 0.5 * (3.5 / 1)

        assert any(abs(z - left_z_expected) < 1e-6 for z in all_z), \
            f"Left carriageway lane z={left_z_expected} not found in {all_z}"
        assert any(abs(z - right_z_expected) < 1e-6 for z in all_z), \
            f"Right carriageway lane z={right_z_expected} not found in {all_z}"

    def test_vehicle_length_unknown_returns_25(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        result = BridgeGrillageModel._vehicle_length("SomethingUnknown")
        assert result == 25.0, f"Unknown vehicle type should default to 25.0 m, got {result}"

    def test_dla_applied_as_load_factor(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 1}]}
        mock_impact.return_value = 0.1
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        self.bridge.add_vehicle_load_cases_from_combinations()
        self.bridge.model.add_load_case.assert_called_with(mock_lc.return_value, load_factor=1.1)

    def test_dla_uses_real_impact_factor_from_irc6(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        """DLA passed to add_load_case must equal 1.0 + IRC6_2017.cl_208_3_impact_factor(L)
        computed with the real (unpatched) formula.  If anyone changes the formula or
        omits the +1.0 offset in analyser.py, this test fails.

        The class-level @patch replaces IRC6_2017.cl_208_3_impact_factor before this
        method runs, so IRC6_2017.cl_208_3_impact_factor inside the method body would
        already be a MagicMock (causing infinite recursion if used as side_effect).
        _real_cl_208_3_impact_factor is captured at module import time — before any
        patch — and is therefore the genuine, unpatched function.
        """
        # expected_dla computed with the REAL function, captured before any patching
        expected_dla = 1.0 + _real_cl_208_3_impact_factor(33.5)

        # Delegate the patched symbol back to the real function so analyser.py
        # executes the actual IRC:6-2017 Cl.208.3 arithmetic
        mock_impact.side_effect = _real_cl_208_3_impact_factor

        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 1}]}
        carriageway_mock = MagicMock()
        carriageway_mock.width = 7.0
        carriageway_mock.z_start = 0.0
        self.bridge.layout.get_component.return_value = carriageway_mock
        mock_lc.return_value = MagicMock()

        self.bridge.add_vehicle_load_cases_from_combinations()

        self.bridge.model.add_load_case.assert_called_with(
            mock_lc.return_value, load_factor=pytest.approx(expected_dla, rel=0.005)
        )

    def test_vehicle_moving_loads_by_case_populated(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 1}]}
        mock_impact.return_value = 0.1
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        self.bridge.add_vehicle_load_cases_from_combinations()
        assert self.bridge.vehicle_moving_loads_by_case != {}, "vehicle_moving_loads_by_case should be populated after add_vehicle_load_cases_from_combinations()"

    def test_vehicle_type_map_populated(self, mock_t6, mock_t6a, mock_impact, mock_lc, mock_lm):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 1}]}
        mock_impact.return_value = 0.1
        self.bridge.layout.get_lane_transverse_coordinates.return_value = [1.75, 5.25]
        self.bridge.add_vehicle_load_cases_from_combinations()
        assert self.bridge.vehicle_type_map != {}, "vehicle_type_map should be populated after add_vehicle_load_cases_from_combinations()"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_point")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_moving_path")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_moving_load")
class TestMovingLoad:
    def test_raises_valueerror_when_vehicle_loads_empty(self, mock_ml, mock_mp, mock_pt):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        bridge.vehicle_moving_loads_by_case = {}
        with pytest.raises(ValueError):
            bridge.create_moving_vehicle_load_cases()

    def test_one_moving_case_per_combination(self, mock_ml, mock_mp, mock_pt):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        mock_vehicle_1 = MagicMock()
        mock_vehicle_2 = MagicMock()
        bridge.vehicle_moving_loads_by_case = {1: [mock_vehicle_1], 2: [mock_vehicle_2]}
        bridge.vehicle_type_map = {id(mock_vehicle_1): "ClassA", id(mock_vehicle_2): "ClassA"}
        bridge.L = 33.5
        bridge.create_moving_vehicle_load_cases()
        assert len(bridge.moving_load_cases_list) == 2, (
            f"Expected 2 moving load cases (one per combination), got {len(bridge.moving_load_cases_list)}"
        )

    def test_path_start_is_negative_vehicle_length(self, mock_ml, mock_mp, mock_pt):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        mock_vehicle_1 = MagicMock()
        bridge.vehicle_moving_loads_by_case = {1: [mock_vehicle_1]}
        bridge.vehicle_type_map = {id(mock_vehicle_1): "ClassA"}
        bridge.L = 33.5
        bridge.create_moving_vehicle_load_cases()
        neg_x_found = False
        for call in mock_pt.call_args_list:
            if call.kwargs.get("x") is not None and call.kwargs["x"] < 0:
                neg_x_found = True
                break
            elif call.args and call.args[0] < 0:
                neg_x_found = True
                break
        assert neg_x_found, "Moving path should start at negative x (= −vehicle_length), but no negative x coord found in create_point calls"

    def test_moving_load_cases_list_stored(self, mock_ml, mock_mp, mock_pt):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        mock_vehicle_1 = MagicMock()
        bridge.vehicle_moving_loads_by_case = {1: [mock_vehicle_1]}
        bridge.vehicle_type_map = {id(mock_vehicle_1): "ClassA"}
        bridge.L = 33.5
        bridge.create_moving_vehicle_load_cases()
        assert bridge.moving_load_cases_list is not None, "moving_load_cases_list should not be None after create_moving_vehicle_load_cases()"
        assert len(bridge.moving_load_cases_list) > 0, "moving_load_cases_list should contain at least one entry"

class TestAnalyze:
    def test_raises_valueerror_when_model_is_none(self):
        bridge = BridgeGrillageModel()
        bridge.model = None
        with pytest.raises(ValueError):
            bridge.analyze()

    def test_model_analyze_called_once(self):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        bridge.analyze()
        assert bridge.model.analyze.call_count == 1, f"model.analyze() should be called once, got {bridge.model.analyze.call_count}"

    def test_returns_results_from_model_get_results(self):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        bridge.model.get_results.return_value = "fake_results"
        result = bridge.analyze()
        assert result == "fake_results", f"analyze() should return model.get_results(), got {result!r}"

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.PlateGirderAnalysisResults")
class TestResultHandler:
    def setup_method(self, method):
        self.bridge = BridgeGrillageModel()
        self.bridge.model = MagicMock()
        self.bridge.model.analyze.return_value = None
        self.bridge.model.get_results.return_value = MagicMock(name="fake_dataset")
        self.bridge.edge_dist = 1.1

    def test_result_handler_created_once(self, mock_handler):
        results = self.bridge.analyze()
        mock_handler(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)
        assert mock_handler.call_count == 1, f"PlateGirderAnalysisResults should be instantiated once, got {mock_handler.call_count}"

    def test_correct_dataset_passed(self, mock_handler):
        results = self.bridge.analyze()
        mock_handler(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)
        mock_handler.assert_called_with(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)

    def test_correct_bridge_instance_passed(self, mock_handler):
        results = self.bridge.analyze()
        mock_handler(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)
        mock_handler.assert_called_with(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)

    def test_correct_edge_dist_passed(self, mock_handler):
        self.bridge.edge_dist = 1.1
        results = self.bridge.analyze()
        mock_handler(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)
        mock_handler.assert_called_with(dataset=results, bridge=self.bridge, edge_dist=self.bridge.edge_dist)

    def test_run_interactive_viewer_called_once(self, mock_handler):
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        mock_instance.run_interactive_viewer()
        assert mock_instance.run_interactive_viewer.call_count == 1, (
            f"run_interactive_viewer should be called once, got {mock_instance.run_interactive_viewer.call_count}"
        )

    def test_viewer_called_with_no_arguments(self, mock_handler):
        mock_instance = MagicMock()
        mock_handler.return_value = mock_instance
        mock_instance.run_interactive_viewer()
        mock_instance.run_interactive_viewer.assert_called_with()

    def test_raises_if_model_not_built(self, mock_handler):
        self.bridge.model = None
        with pytest.raises(ValueError):
            self.bridge.analyze()

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.plt", create=True)
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.opsv", create=True)
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.opsplt", create=True)
class TestPlotModel:
    def test_raises_valueerror_when_model_is_none(self, mock_opsplt, mock_opsv, mock_plt):
        bridge = BridgeGrillageModel()
        bridge.model = None
        with pytest.raises(ValueError):
            bridge.plot_model()

    def test_calls_plotting_functions(self, mock_opsplt, mock_opsv, mock_plt):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        mock_fig = MagicMock()
        mock_plt.gcf.return_value = mock_fig
        
        bridge.plot_model()
        
        mock_opsplt.plot_model.assert_called_once_with(show_nodes="yes", show_nodetags="yes")
        mock_opsv.plot_model.assert_called_once_with(az_el=(-90, 0), element_labels=0)
        mock_plt.gcf.assert_called_once()
        mock_fig.set_size_inches.assert_called_once_with(8, 8)
        mock_plt.show.assert_called_once()

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.plot_force")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.plot_defo")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.plt", create=True)
class TestPlot:
    def test_raises_valueerror_when_model_is_none(self, mock_plt, mock_defo, mock_force):
        bridge = BridgeGrillageModel()
        bridge.model = None
        with pytest.raises(ValueError):
            bridge.plot()

    def test_executes_plot_workflow(self, mock_plt, mock_defo, mock_force):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        
        # Setup model mock returns
        bridge.model.get_element.side_effect = lambda member, options: [101]
        
        # Mock the results dataset
        mock_results = MagicMock()
        mock_max_disp = MagicMock()
        mock_max_disp.values = 0.005
        mock_results.displacements.sel.return_value = [mock_max_disp]
        
        mock_static_results = MagicMock()
        mock_max_force = MagicMock()
        mock_max_force.values = 12000.0
        mock_static_results.forces.sel.return_value = [mock_max_force]

        # Deterministic call sequence: first call returns mock_results, second returns mock_static_results
        bridge.model.get_results.side_effect = [mock_results, mock_static_results]
        
        bridge.plot()
        
        # Verify calls
        mock_defo.assert_called_once_with(
            bridge.model, mock_results, member="exterior_main_beam_1", option="nodes", loadcase='girder self weight'
        )
        mock_force.assert_called_once_with(
            bridge.model, mock_results, member="exterior_main_beam_1", component="Mz", loadcase='Deck slab load'
        )
        mock_plt.show.assert_any_call()

    def test_plot_extracts_correct_load_case_names(self, mock_plt, mock_defo, mock_force):
        """Ensure that hardcoded load case names in plot() remain consistent with analyser."""
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        bridge.model.get_element.side_effect = lambda member, options: [101]

        mock_results = MagicMock()
        mock_max_disp = MagicMock()
        mock_max_disp.values = 0.001
        mock_results.displacements.sel.return_value = [mock_max_disp]

        mock_static_results = MagicMock()
        mock_max_force = MagicMock()
        mock_max_force.values = 5000.0
        mock_static_results.forces.sel.return_value = [mock_max_force]

        bridge.model.get_results.side_effect = [mock_results, mock_static_results]
        bridge.plot()

        # get_results() called twice: once with no args, once with load_case=[]
        assert bridge.model.get_results.call_count == 2, (
            f"plot() should call model.get_results() twice (general + load-case-specific), got {bridge.model.get_results.call_count}"
        )
        first_call_kwargs = bridge.model.get_results.call_args_list[1]
        # Second call must include 'Deck slab load' as the load case
        assert first_call_kwargs == call(load_case=['Deck slab load']), (
            f"Second get_results() call should use load_case=['Deck slab load'], got {first_call_kwargs}"
        )

@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
class TestCreateGoverningLLLoadCase:
    def test_raises_valueerror_when_model_is_none(self, mock_lc):
        bridge = BridgeGrillageModel()
        bridge.model = None
        dataset = MagicMock()
        with pytest.raises(ValueError):
            bridge.create_governing_ll_load_case(dataset)

    def test_warns_when_no_static_load_cases(self, mock_lc):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        dataset = MagicMock()
        dataset.coords = {"Loadcase": MagicMock(values=[])}
        with pytest.warns(UserWarning, match="No vehicle static load cases found"):
            res = bridge.create_governing_ll_load_case(dataset)
            assert res == dataset, "When no static load cases, create_governing_ll_load_case should return the original dataset"
            assert bridge.ll_load_case is None, "ll_load_case should remain None when no static load cases found"

    def test_governing_ll_load_case_creation_flow(self, mock_lc):
        bridge = BridgeGrillageModel()
        bridge.model = MagicMock()
        
        # Setup dataset
        dataset = MagicMock()
        dataset.coords = {"Loadcase": MagicMock(values=["case 1", "case 2"])}
        
        # Forces selection mocks: case 1 has max |Mz_i| = 50000, case 2 has 20000
        forces_mock = MagicMock()
        forces_mock.__abs__.return_value.max.side_effect = [50000.0, 20000.0]
        dataset.__getitem__.return_value.sel.return_value = forces_mock

        # Setup target load case matching case 1
        mock_lc_case_1 = MagicMock()
        mock_lc_case_1.name = "case 1"
        mock_lc_case_1.load_groups = [{"load": "load_obj_1"}]
        bridge.vehicle_load_cases_list = [mock_lc_case_1]

        # Mock create_load_case return value for ULS load case
        mock_uls_lc = MagicMock()
        mock_lc.return_value = mock_uls_lc

        # Mock self.model.get_results return value for post-analysis
        post_ds = MagicMock()
        post_ds.coords = {"Loadcase": MagicMock(values=["case 1", "case 2", "1.5 LL"])}
        bridge.model.get_results.return_value = post_ds

        res = bridge.create_governing_ll_load_case(dataset, partial_safety_factor=1.5)

        # Assert correct governing case ULS created
        mock_lc.assert_called_with(name="1.5 LL")
        mock_uls_lc.add_load.assert_called_once_with("load_obj_1")
        bridge.model.add_load_case.assert_called_once_with(mock_uls_lc, load_factor=1.5)
        assert bridge.ll_load_case == mock_uls_lc, f"ll_load_case should be the ULS load case object, got {bridge.ll_load_case!r}"
        assert bridge.governing_ll_name == "case 1", f"governing_ll_name should be 'case 1', got {bridge.governing_ll_name!r}"
        assert bridge.model.analyze.call_count == 1, (
            f"model.analyze() should be called once after adding LL, got {bridge.model.analyze.call_count}"
        )


@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_case")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.og.create_load_model")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.table_6A")
@patch("osdagbridge.core.bridge_types.plate_girder.analyser.IRC6_2017.table_6")
class TestCreateVehicleLoadCases:
    """
    Tests for BridgeGrillageModel.create_vehicle_load_cases().

    Verifies orchestration logic:
    - raises ValueError when model is not set
    - creates exactly one load case per vehicle combination
    - places vehicles at z-coordinates derived from IRC table_6 lane spacing
    - adds each load case to model exactly once
    - stores all load cases in self.vehicle_load_cases_list
    """

    def setup_method(self, method):
        self.bridge = BridgeGrillageModel()
        self.bridge.model = MagicMock()
        self.bridge.L = 33.5
        self.bridge.layout = MagicMock()

    def _setup_single_carriageway(self, mock_t6, mock_t6a, n_lanes, cw_width, z_start=0.0):
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        cw = MagicMock()
        cw.width = cw_width
        cw.z_start = z_start
        self.bridge.layout.get_component.return_value = cw
        mock_t6.return_value = n_lanes
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": n_lanes}]}

    def test_raises_valueerror_when_model_is_none(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        self.bridge.model = None
        with pytest.raises(ValueError, match="Model is not available"):
            self.bridge.create_vehicle_load_cases()

    def test_creates_one_load_case_per_combination(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """One IRC combination → one og.create_load_case call."""
        self._setup_single_carriageway(mock_t6, mock_t6a, n_lanes=2, cw_width=7.0)
        mock_lc.return_value = MagicMock()

        self.bridge.create_vehicle_load_cases()

        assert mock_lc.call_count == 1, f"Expected 1 og.create_load_case call for 1 combination, got {mock_lc.call_count}"

    def test_load_case_name_reflects_combination(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """Load case name must follow format 'Case{n} {k}x{vehicle_type}'."""
        n_lanes = 2
        self._setup_single_carriageway(mock_t6, mock_t6a, n_lanes=n_lanes, cw_width=7.0)
        mock_lc.return_value = MagicMock()

        self.bridge.create_vehicle_load_cases()

        name_used = mock_lc.call_args_list[0].kwargs["name"]
        expected_name = f"Case1 {n_lanes}xClassA"
        assert name_used == expected_name, f"Load case name should be {expected_name!r}, got {name_used!r}"

    def test_vehicle_placed_at_correct_z_coordinate(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """Each vehicle must be placed at z = z_start + (i+0.5) * lane_width from IRC table_6."""
        n_lanes = 2
        cw_width = 7.0
        z_start = 0.0
        self._setup_single_carriageway(mock_t6, mock_t6a, n_lanes=n_lanes, cw_width=cw_width, z_start=z_start)

        mock_vehicle = MagicMock()
        mock_lm.return_value.create.return_value = mock_vehicle
        mock_lc.return_value = MagicMock()

        self.bridge.create_vehicle_load_cases()

        # Check that set_global_coord was called with the expected z values
        set_coord_calls = mock_vehicle.set_global_coord.call_args_list
        lane_width = cw_width / n_lanes
        expected_z_coords = [z_start + (i + 0.5) * lane_width for i in range(n_lanes)]

        actual_z_coords = [c.args[0].z for c in set_coord_calls]
        assert sorted(actual_z_coords) == pytest.approx(sorted(expected_z_coords)), (
            f"Vehicle placed at incorrect Z-coordinates. Expected: {expected_z_coords}, Got: {actual_z_coords}"
        )

    def test_vehicle_x_coord_is_zero(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """Vehicles always start at x=0 (longitudinal start of bridge)."""
        self._setup_single_carriageway(mock_t6, mock_t6a, n_lanes=1, cw_width=3.5, z_start=0.0)
        mock_vehicle = MagicMock()
        mock_lm.return_value.create.return_value = mock_vehicle
        mock_lc.return_value = MagicMock()

        self.bridge.create_vehicle_load_cases()

        for c in mock_vehicle.set_global_coord.call_args_list:
            assert c.args[0].x == pytest.approx(0.0), f"Vehicle x-coordinate should be 0.0, got {c.args[0].x}"

    def test_each_load_case_added_to_model(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """Each created load case must be added to self.model exactly once."""
        mock_t6.return_value = 2
        # Two combinations → two calls to add_load_case
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}, {"Class70R": 1}]}
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        cw = MagicMock()
        cw.width = 7.0
        cw.z_start = 0.0
        self.bridge.layout.get_component.return_value = cw
        mock_lc.side_effect = lambda name: MagicMock(name=name)

        self.bridge.create_vehicle_load_cases()

        assert self.bridge.model.add_load_case.call_count == 2, (
            f"Expected 2 add_load_case calls for 2 combinations, got {self.bridge.model.add_load_case.call_count}"
        )

    def test_vehicle_load_cases_list_stored_on_instance(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """All created load cases must be stored in self.vehicle_load_cases_list."""
        mock_t6.return_value = 2
        mock_t6a.return_value = {"vehicle_combinations": [{"ClassA": 2}, {"Class70R": 1}]}
        self.bridge.layout.has_component.side_effect = lambda x: x == "carriageway"
        cw = MagicMock()
        cw.width = 7.0
        cw.z_start = 0.0
        self.bridge.layout.get_component.return_value = cw
        mock_lc.side_effect = lambda name: MagicMock(name=name)

        result = self.bridge.create_vehicle_load_cases()

        assert hasattr(self.bridge, "vehicle_load_cases_list"), "vehicle_load_cases_list attribute missing after create_vehicle_load_cases()"
        assert len(self.bridge.vehicle_load_cases_list) == 2, (
            f"vehicle_load_cases_list should have 2 entries, got {len(self.bridge.vehicle_load_cases_list)}"
        )
        assert self.bridge.vehicle_load_cases_list == result, "vehicle_load_cases_list should equal the return value of create_vehicle_load_cases()"

    def test_create_load_model_called_with_uppercase_vehicle_type(self, mock_t6, mock_t6a, mock_lm, mock_lc):
        """og.create_load_model must be called with a model_type that is all-uppercase.
        Uses a .upper() self-check so the assertion is not tied to a specific vehicle
        name: if analyser.py drops .upper(), the received value will differ from its
        own .upper() and the test fails regardless of vehicle type.
        """
        self._setup_single_carriageway(mock_t6, mock_t6a, n_lanes=1, cw_width=3.5, z_start=0.0)
        mock_lc.return_value = MagicMock()

        self.bridge.create_vehicle_load_cases()

        assert mock_lm.call_count >= 1, "og.create_load_model was never called"
        for c in mock_lm.call_args_list:
            model_type = c.kwargs.get("model_type") or (c.args[0] if c.args else "")
            assert model_type == model_type.upper(), (
                f"model_type '{model_type}' was not uppercased — .upper() may have been removed from analyser.py"
            )