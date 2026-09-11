"""
Hover for the 3D CAD's bridge components — the owning module.
==============================================================

Everything about hovering a *bridge component* in the 3D CAD lives here: the
registered labels, the hit-test, the hover highlight, the tooltip timing, and the
label text itself.  ``CustomViewer3d`` forwards its Qt mouse events to
:class:`HoverController`; ``cad_3d.py`` registers components through it;
``cad_safety.py`` clears it on teardown.

Deliberately not owned here
---------------------------
The analysis-mesh overlays: node markers, node numbers, element numbers and the
grillage.  Node markers keep their screen-space picking in ``custom_3dviewer``
exactly as written — the controller gives it a turn through the ``node_hover_label``
hook and takes its answer as-is, so node hover behaves exactly as before.  Node
numbers, element numbers and the grillage have no hover at all; they are 3D text and
lines drawn into the scene and toggled from the toolbar.

Two label channels
------------------
``labels_by_key``  one string per registered component key — the default, for a
                   component whose shapes are interchangeable.
``labels_by_ptr``  one string per individual shape, which takes precedence.  This is
                   how one registration key can still show different text per member,
                   so a girder pair's braces can report their own designed section
                   while the visibility checkbox keeps working off the single key.

Both AIS-keyed maps use the raw C++ pointer address rather than the Python object:
pythonocc can hand back a different Python wrapper for the same C++ object, so object
identity is not reliable across a MoveTo round-trip.
"""

import re

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QToolTip

# The section type and dimension keys below are the same ones cross_bracing/builder.py
# reads to draw the geometry, resolved through the same <base>.<pair> scheme — which is
# what stops the tooltip and the drawn shape disagreeing.  The designation, spacing and
# steel grade keys are extra: the builder has no use for them, but the label does.
from osdagbridge.core.utils.common import (
    KEY_GIRDER,
    KEY_MP_CB_TYPE,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_CB_DIAGONAL_LEG_H, KEY_MP_CB_DIAGONAL_LEG_W, KEY_MP_CB_DIAGONAL_THICKNESS,
    KEY_MP_CB_TOP_CHORD_LEG_H, KEY_MP_CB_TOP_CHORD_LEG_W, KEY_MP_CB_TOP_CHORD_THICKNESS,
    KEY_MP_CB_BOTTOM_CHORD_LEG_H, KEY_MP_CB_BOTTOM_CHORD_LEG_W, KEY_MP_CB_BOTTOM_CHORD_THICKNESS,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BRACING_SECTION,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_ED_DIAGONAL_LEG_H, KEY_MP_ED_DIAGONAL_LEG_W, KEY_MP_ED_DIAGONAL_THICKNESS,
    KEY_MP_ED_TOP_CHORD_LEG_H, KEY_MP_ED_TOP_CHORD_LEG_W, KEY_MP_ED_TOP_CHORD_THICKNESS,
    KEY_MP_ED_BOTTOM_CHORD_LEG_H, KEY_MP_ED_BOTTOM_CHORD_LEG_W, KEY_MP_ED_BOTTOM_CHORD_THICKNESS,
)
from osdagbridge.core.bridge_components.super_structure.cross_bracing.builder import (
    ROLE_DIAGONAL, ROLE_TOP_CHORD, ROLE_BOTTOM_CHORD, ROLE_NAMES,
    COMPONENT_CROSS_BRACING,
)

__all__ = ["HoverController", "build_component_labels", "build_bracing_hover_shapes"]


# =============================================================================
# THE CONTROLLER
# =============================================================================

class HoverController:
    """Owns hover for the bridge components in the 3D CAD viewer.

    Parameters
    ----------
    viewer : CustomViewer3d
        Used for its ``context``, ``view``, safety guard, and the node hover hook.
        Held as a plain reference; the controller's lifetime matches the viewer's.
    """

    # Delay between the cursor settling and the tooltip appearing (ms).
    TOOLTIP_DELAY_MS = 100

    def __init__(self, viewer):
        self.viewer = viewer

        # Registered model objects and their labels.
        self.model_ais_objects = {}      # key -> [AIS]
        self.labels_by_key = {}          # key -> label text
        self.labels_by_ptr = {}          # ptr -> label text (wins over labels_by_key)
        self.ais_to_model = {}           # ptr -> key

        # Shapes that carry their own label but must not be hilighted — the invisible
        # node pick spheres, where a highlight would flash a blob over the marker.
        # Membership is explicit rather than inferred from "has a label", because
        # cross bracings also carry per-shape labels and must still highlight.
        self.no_highlight_ptrs = set()

        # What the cursor is currently over.
        self.current_hovered_model = None
        self.current_hovered_label = None
        self.current_highlighted_ais_list = []

        self.hover_position = None
        self.hover_timer = QTimer(viewer)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._show_tooltip)

    # ------------------------------------------------------------------
    # Registration — called while the model is being built
    # ------------------------------------------------------------------
    def register(self, key, ais_list, label, per_ais_labels=None):
        """Register a component's AIS objects and the text they hover with.

        ``per_ais_labels``, when given, is a list parallel to ``ais_list`` holding one
        label per shape.  Those take precedence over ``label``, which remains the
        fallback for any shape the list does not cover.
        """
        self.model_ais_objects[key] = ais_list
        self.labels_by_key[key] = label

        if per_ais_labels:
            for ais, text in zip(ais_list, per_ais_labels):
                if text is not None:
                    self.labels_by_ptr[self.get_occ_ptr(ais)] = text

    def register_ais_label(self, ais, label, highlight=True):
        """Give one AIS its own label, outside any component key.

        Pass ``highlight=False`` for a shape that should never be hilighted on hover —
        the transparent node pick spheres use this.
        """
        ptr = self.get_occ_ptr(ais)
        self.labels_by_ptr[ptr] = label
        if not highlight:
            self.no_highlight_ptrs.add(ptr)

    def drop_ais(self, ais):
        """Forget one AIS, before the C++ object behind it is released."""
        ptr = self.get_occ_ptr(ais)
        self.labels_by_ptr.pop(ptr, None)
        self.no_highlight_ptrs.discard(ptr)

    def clear(self):
        """Drop all hover state.  Called from the safety guard's teardown."""
        self.hover_timer.stop()
        self.model_ais_objects.clear()
        self.labels_by_key.clear()
        self.labels_by_ptr.clear()
        self.no_highlight_ptrs.clear()
        self.ais_to_model = {}
        self.current_hovered_model = None
        self.current_hovered_label = None
        self.current_highlighted_ais_list = []

    def rebuild_lookup(self):
        """Rebuild the O(1) map from C++ pointer address to component key."""
        self.ais_to_model = {}
        for key, ais_list in self.model_ais_objects.items():
            for ais in ais_list:
                self.ais_to_model[self.get_occ_ptr(ais)] = key

    @staticmethod
    def get_occ_ptr(obj):
        """Resolve the raw C++ pointer address behind a SWIG/pythonocc object."""
        current = obj
        for _ in range(5):  # Limit depth to prevent infinite loops
            if not hasattr(current, "this"):
                break

            # Try converting the SWIG pointer directly to an integer
            try:
                return int(current.this)
            except TypeError:
                pass

            # Try parsing the C++ hex address string representation of the SWIG pointer
            try:
                s = str(current.this)
                # s is formatted like "_000001859d3f34b0_p_Handle_AIS_Shape"
                match = re.match(r"^_[0-9a-fA-F]+", s)
                if match:
                    return int(match.group(0)[1:], 16)
            except Exception:
                pass

            # Go one level deeper (e.g., Handle_AIS_Shape -> AIS_Shape)
            next_obj = getattr(current, "this")
            if next_obj is current:
                break
            current = next_obj

        return hash(obj)

    # ------------------------------------------------------------------
    # Pick geometry
    # ------------------------------------------------------------------
    def pick_scale(self):
        """Factor converting Qt cursor coordinates into the space ``MoveTo`` expects.

        It is 1.0 — there is no conversion.  ``AIS_InteractiveContext.MoveTo`` takes
        **logical** coordinates, the ones Qt already reports, on every platform.
        Upstream pythonocc passes ``pt.x()`` through unscaled
        (qtDisplay.mouseMoveEvent) and is correct.

        This viewer used to multiply by ``devicePixelRatioF()``.  That is 1.0 on an
        ordinary display, so it did nothing and went unnoticed, but 2.0 on a Retina
        screen and 1.25-1.5 under Windows display scaling.  Every pick then landed at
        a multiple of the cursor position, and anything past ``viewport_width / dpr``
        fell outside the window, where OCC detects nothing — leaving hover and click
        working only in the top-left ``1/dpr`` of the viewport, a 75% dead area at 2x.
        Measured on a 937 px-wide viewport: picks succeeded up to qt_x = 468
        (occ_x = 936) and failed from qt_x = 470 (occ_x = 939) on.

        ``view.Window().Size()`` is not a usable source for this factor: it reports
        the backing-store size, 2x logical on Retina, so deriving the scale from it
        reproduces exactly this bug.
        """
        return 1.0

    # ------------------------------------------------------------------
    # Events — called by the viewer's Qt handlers
    # ------------------------------------------------------------------
    def handle_move(self, event):
        """Hit-test under the cursor, update the highlight, schedule the tooltip."""
        viewer = self.viewer
        context, view = viewer.context, viewer.view
        if not context or not view:
            return

        try:
            pr    = self.pick_scale()
            x_log = float(event.position().x())
            y_log = float(event.position().y())
            x     = int(x_log * pr)
            y     = int(y_log * pr)

            context.MoveTo(x, y, view, True)

            hovered_model = None
            hovered_label = None

            if context.HasDetected():
                detected, skip_highlight = self._detect()
                ptr = self.get_occ_ptr(detected)
                hovered_label = self.labels_by_ptr.get(ptr)
                hovered_model = self.ais_to_model.get(ptr)

                objects_to_highlight = []
                if not skip_highlight:
                    if hovered_model in ("Bolt", "Nut"):
                        objects_to_highlight.extend(self.model_ais_objects.get("Bolt", []))
                        objects_to_highlight.extend(self.model_ais_objects.get("Nut", []))
                    elif detected:
                        objects_to_highlight.append(detected)

                self._set_highlight(objects_to_highlight)
            else:
                self._set_highlight([])

            # Node markers keep their own screen-space picking in the viewer.  Give it
            # a turn and take its answer as-is, including its precedence over a solid.
            node_label = viewer.node_hover_label(x, y, x_log, y_log)
            if node_label:
                hovered_label = node_label
                hovered_model = None
                self._set_highlight([])
                if self.hover_position and hovered_label != self.current_hovered_label:
                    self.current_hovered_label = hovered_label
                    self.hover_timer.stop()
                    QToolTip.showText(self.hover_position, hovered_label, viewer)

            self.hover_position = event.globalPosition().toPoint()

            if (hovered_model != self.current_hovered_model
                    or hovered_label != self.current_hovered_label):
                self.current_hovered_model = hovered_model
                self.current_hovered_label = hovered_label
                if hovered_model or hovered_label:
                    self.hover_timer.start(self.TOOLTIP_DELAY_MS)
                else:
                    QToolTip.hideText()
            elif hovered_model is None and hovered_label is None:
                QToolTip.hideText()

        except Exception as exc:
            print(f"hover handle_move error: {exc}")
            QToolTip.hideText()

    def handle_leave(self):
        """Cursor left the viewport — drop the tooltip and any highlight."""
        self.hover_timer.stop()
        self.current_hovered_model = None
        self.current_hovered_label = None

        if self.viewer.safety.in_progress:
            return

        self._set_highlight([])
        QToolTip.hideText()

    def pause(self):
        """Stop the pending tooltip (overlay pause / model teardown)."""
        try:
            self.hover_timer.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _detect(self):
        """Return ``(detected, skip_highlight)`` for what is under the cursor.

        Take the entity ``DetectedInteractive`` reports first — it orders them nearest
        the camera first, so that is what is visibly under the cursor.

        Do *not* scan the list for a shape carrying its own label and prefer that one.
        The node pick spheres are transparent balls of radius 120 on the topmost
        Z-layer, so they sit over much of the deck; preferring them swallows the hover
        of every component behind them.

        ``skip_highlight`` comes from the explicit no_highlight_ptrs set, not from
        "has its own label" — cross bracings carry per-shape labels too and must still
        light up on hover.
        """
        context = self.viewer.context
        detected_list = []

        if hasattr(context, "InitDetected"):
            try:
                context.InitDetected()
                while context.MoreDetected():
                    detected_list.append(context.DetectedInteractive())
                    context.NextDetected()
            except Exception:
                detected_list = []

        if not detected_list:
            detected_list = [context.DetectedInteractive()]

        if not detected_list:
            return None, False

        detected = detected_list[0]
        return detected, self.get_occ_ptr(detected) in self.no_highlight_ptrs

    def _set_highlight(self, objects):
        """Hilight exactly ``objects``, leaving the view untouched if unchanged."""
        if set(objects) == set(self.current_highlighted_ais_list):
            return

        context = self.viewer.context
        for obj in self.current_highlighted_ais_list:
            try:
                context.Unhilight(obj, False)
            except Exception:
                pass

        self.current_highlighted_ais_list = objects

        for obj in objects:
            try:
                context.HilightWithColor(obj, context.HighlightStyle(), False)
            except Exception:
                pass

        if self.viewer.view:
            self.viewer.view.Redraw()

    def _show_tooltip(self):
        """QTimer callback: show the text for whatever the cursor settled on."""
        if self.viewer.safety.in_progress or not self.hover_position:
            return

        text = self.current_hovered_label
        if text is None and self.current_hovered_model is not None:
            text = self.labels_by_key.get(self.current_hovered_model)

        if text:
            QToolTip.showText(self.hover_position, text, self.viewer)


# =============================================================================
# LABEL TEXT — the 17 bridge components
# =============================================================================

def build_component_labels(params):
    """Tooltip text for every bridge component, keyed by its registration key.

    ``params`` is the ``BridgeParametersDTO`` for the rendered bridge.  The keys match
    the ones ``cad_3d._render_model_body`` registers under, and the ones the
    ``component_map`` in ``update_component_visibility`` maps checkboxes to.

    Known limitations, all unchanged by moving the text here:

    * The values come from the DTO's flat scalar fields, which hold one representative
      girder and one representative girder pair — so every girder shows identical text,
      and so does every cross bracing.
    * The cross-bracing section is a hardcoded literal on the DTO, which is what issue
      #247 reports.  Fixing it means reading ``params.output_dict`` per member.
    * Five components carry no data at all: the three supports and the two W-beams.
    * Shear Stud has text but is registered ``selectable=False``, so it cannot be
      hovered at all.
    """
    return {
        "Girder Web":
            f"Girder Web\nDepth: {params.girder_section_d:.2f} mm"
            f"\nWeb Thickness: {params.girder_section_tw:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Girder Top Flange":
            f"Top Flange\nWidth: {params.girder_section_bf:.2f} mm"
            f"\nThickness: {params.girder_section_tf:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Girder Bottom Flange":
            f"Bottom Flange\nWidth: {params.girder_section_bf_b:.2f} mm"
            f"\nThickness: {params.girder_section_tf_b:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Intermediate Stiffener":
            f"Intermediate Stiffener"
            f"\nSpacing: {params.intermediate_stiffener_spacing:.2f} mm"
            f"\nThickness: {params.intermediate_stiffener_thickness:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Bearing Stiffener":
            f"Bearing Stiffener\nPairs: {params.num_end_stiffener_pairs}"
            f"\nThickness: {params.end_stiffener_thickness:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Longitudinal Stiffener":
            f"Longitudinal Stiffener\nCount: {params.num_longitudinal_stiffeners}"
            f"\nThickness: {params.longitudinal_stiffener_thickness:.2f} mm"
            f"\nSteel Grade: {params.steel_grade}",

        "Shear Stud":
            f"Shear Stud\nBase Dia: {params.shear_stud_params.base_diameter:.2f} mm"
            f"\nHeight: {params.shear_stud_params.base_height + params.shear_stud_params.top_height:.2f} mm"
            f"\nPitch: {params.shear_stud_params.pitch:.2f} mm"
            f"\nPer Section: {params.shear_stud_params.num_per_section}",

        "Support Vertical":     "Support - Vertical",
        "Support Transverse":   "Support - Transverse",
        "Support Longitudinal": "Support - Longitudinal",

        "Cross Bracing":
            f"Cross Bracing\nType: {params.bracing_type}-Bracing"
            f"\nSpacing: {params.cross_bracing_spacing:.2f} mm"
            f"\nSection: {params.diagonal_section_type}"
            f"\nLeg H: {params.diagonal_section_dims.leg_h:.2f} mm"
            f"\nLeg W: {params.diagonal_section_dims.leg_w:.2f} mm",

        "Deck":
            f"Deck Slab\nThickness: {params.deck_thickness:.2f} mm"
            f"\nCarriageway Width: {params.carriageway_width:.2f} mm"
            f"\nConcrete Grade: {params.concrete_grade}"
            f"\nFootpath: {params.footpath_config}",

        "Crash Barrier W-Beam": "W-Beam",
        "Median W-Beam":        "Median W-Beam",

        "Crash Barrier":
            f"Crash Barrier\nType: {params.barrier_type}"
            f"\nSubtype: {params.crash_barrier_subtype}",

        "Median":
            f"Median Barrier\nType: {params.median_type}",

        "Railing":
            f"Railing\nType: {params.railing_type.upper()}"
            f"\nRails: {params.rail_count}"
            f"\nWidth: {params.railing_width:.2f} mm",
    }


# =============================================================================
# CROSS BRACING AND END DIAPHRAGM — per girder pair, per member
# =============================================================================
# These read output_dict rather than the DTO.  The DTO has one scalar slot per field
# and so cannot hold G1G2=CHANNEL and G2G3=ANGLE at the same time — which is why the
# label above reports a fixed ANGLE 100x50 whatever the user entered (issue #247).
# output_dict holds every pair's designed values, keyed by girder pair.


def _present(value):
    """True unless the value is genuinely absent.

    Only None and "" count as missing — False and 0 are real answers, so a legitimate
    zero thickness is not mistaken for "no value".
    """
    return value is not None and value != ""


def _resolve(output_dict, base_key, pair_id):
    """Look up one value for one girder pair.

    The same value can be stored under three different key shapes depending on which
    stage wrote it:

      1. ``<base>.<pair>``            — written by the design phase
      2. ``<base>.<pair>.<member id>``— written by the input form
      3. ``<base>``                   — a few legacy flat values

    Tried most specific first.  Taking the first member is correct: extend_cb_dynamic_keys()
    in defaults.py writes every member of a pair identically, so M1..Mn always agree.
    """
    if pair_id:
        exact = f"{base_key}.{pair_id}"
        value = output_dict.get(exact)
        if _present(value):
            return value

        prefix = exact + "."
        for key in sorted(k for k in output_dict if k.startswith(prefix)):
            if _present(output_dict[key]):
                return output_dict[key]

    value = output_dict.get(base_key)
    return value if _present(value) else None


def _fmt_mm(value):
    """Format a millimetre dimension, or None if it cannot be read as a number.

    Returning None lets the caller drop the line entirely rather than print "None mm".
    """
    try:
        return f"{float(value):.2f} mm"
    except (TypeError, ValueError):
        return None


def _pair_label(pair_id):
    """'G1G2' -> 'G1 to G2', for display."""
    head, _, tail = pair_id.partition("G")[2].partition("G")
    return f"G{head} to G{tail}" if head and tail else pair_id


# Per role: (section type key, designation key, leg_h, leg_w, thickness).
# The type and dimension entries must stay in step with the lookups in
# cross_bracing/builder.py, so the label and the drawn shape describe the same section.
_CB_ROLE_KEYS = {
    ROLE_DIAGONAL: (
        KEY_MP_CB_BRACING_SECTION_TYPE, KEY_MP_CB_BRACING_SECTION_DESIGNATION,
        KEY_MP_CB_DIAGONAL_LEG_H, KEY_MP_CB_DIAGONAL_LEG_W, KEY_MP_CB_DIAGONAL_THICKNESS,
    ),
    ROLE_TOP_CHORD: (
        KEY_MP_CB_TOP_CHORD_SECTION_TYPE, KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
        KEY_MP_CB_TOP_CHORD_LEG_H, KEY_MP_CB_TOP_CHORD_LEG_W, KEY_MP_CB_TOP_CHORD_THICKNESS,
    ),
    ROLE_BOTTOM_CHORD: (
        KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
        KEY_MP_CB_BOTTOM_CHORD_LEG_H, KEY_MP_CB_BOTTOM_CHORD_LEG_W, KEY_MP_CB_BOTTOM_CHORD_THICKNESS,
    ),
}

_ED_ROLE_KEYS = {
    ROLE_DIAGONAL: (
        KEY_MP_ED_BRACING_SECTION, KEY_MP_ED_BRACING_SECTION_DESIGNATION,
        KEY_MP_ED_DIAGONAL_LEG_H, KEY_MP_ED_DIAGONAL_LEG_W, KEY_MP_ED_DIAGONAL_THICKNESS,
    ),
    ROLE_TOP_CHORD: (
        KEY_MP_ED_TOP_CHORD_SECTION_TYPE, KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
        KEY_MP_ED_TOP_CHORD_LEG_H, KEY_MP_ED_TOP_CHORD_LEG_W, KEY_MP_ED_TOP_CHORD_THICKNESS,
    ),
    ROLE_BOTTOM_CHORD: (
        KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
        KEY_MP_ED_BOTTOM_CHORD_LEG_H, KEY_MP_ED_BOTTOM_CHORD_LEG_W, KEY_MP_ED_BOTTOM_CHORD_THICKNESS,
    ),
}


def _section_line(output_dict, pair_id, type_key, desig_key):
    """'CHANNEL (JC 100)', falling back to whichever half is available."""
    sec_type = _resolve(output_dict, type_key, pair_id)
    desig    = _resolve(output_dict, desig_key, pair_id)

    sec_type = str(sec_type).strip().upper() if _present(sec_type) else ""
    desig    = str(desig).strip()            if _present(desig)    else ""

    if sec_type and desig:
        return f"{sec_type} ({desig})"
    return sec_type or desig or "not designed"


def _bracing_member_label(output_dict, component, pair_id, role):
    """Build the tooltip for one (component, girder pair, member role).

    Lines whose value is missing are left out rather than printed empty, so a
    partially designed bridge still gives a readable tooltip.
    """
    is_cross_bracing = component == COMPONENT_CROSS_BRACING
    role_keys = _CB_ROLE_KEYS if is_cross_bracing else _ED_ROLE_KEYS

    lines = [f"{component} - {ROLE_NAMES.get(role, role)}",
             f"Location: {_pair_label(pair_id)}"]

    if role in role_keys:
        type_key, desig_key, h_key, w_key, t_key = role_keys[role]
        lines.append(f"Section: {_section_line(output_dict, pair_id, type_key, desig_key)}")

        leg_h = _fmt_mm(_resolve(output_dict, h_key, pair_id))
        leg_w = _fmt_mm(_resolve(output_dict, w_key, pair_id))
        if leg_h and leg_w:
            lines.append(f"Leg H x W: {leg_h} x {leg_w}")
        thickness = _fmt_mm(_resolve(output_dict, t_key, pair_id))
        if thickness:
            lines.append(f"Thickness: {thickness}")

    if is_cross_bracing:
        brace_type = _resolve(output_dict, KEY_MP_CB_TYPE, pair_id)
        if _present(brace_type):
            lines.append(f"Bracing Type: {str(brace_type).strip()}")

        # KEY_MP_CB_SPACING is stored in metres (see extend_cb_dynamic_keys).
        try:
            spacing_mm = float(_resolve(output_dict, KEY_MP_CB_SPACING, pair_id)) * 1e3
            lines.append(f"Spacing: {spacing_mm:.2f} mm")
        except (TypeError, ValueError):
            pass
    else:
        for key, caption in ((KEY_MP_ED_TYPE, "Diaphragm Type"),
                             (KEY_MP_ED_BRACING_TYPE, "Bracing Type")):
            value = _resolve(output_dict, key, pair_id)
            if _present(value):
                lines.append(f"{caption}: {str(value).strip()}")

    steel_grade = output_dict.get(KEY_GIRDER)
    if _present(steel_grade):
        lines.append(f"Steel Grade: {str(steel_grade).strip()}")

    return "\n".join(lines)


def build_bracing_hover_shapes(output_dict, bracing_groups, fallback_shapes=None):
    """Flatten the bracing groups into shapes paired with their tooltip text.

    The CAD layer hands both lists straight to ``HoverController.register`` and does no
    label work of its own.

    Parameters
    ----------
    output_dict : dict or None
        The design snapshot, from ``BridgeParametersDTO.output_dict``.
    bracing_groups : dict or None
        ``(component, pair_id, role) -> [shapes]``, from build_cross_bracings().
    fallback_shapes : list, optional
        The flat, ungrouped bracing list.  Used when there are no groups, or no design
        snapshot to label them with, so the shapes are still displayed.

    Returns
    -------
    (list, list | None)
        Shapes, and a parallel list of labels — one per shape, in the same order, so
        shape *i* gets label *i*.  The label list is ``None`` when there is nothing to
        label with, telling the caller to fall back to the generic per-key label.
    """
    if not bracing_groups:
        return list(fallback_shapes or []), None

    labels_by_group = (
        {gk: _bracing_member_label(output_dict, *gk) for gk in bracing_groups}
        if output_dict else {}
    )

    shapes, labels = [], []
    for group_key, group_shapes in bracing_groups.items():
        shapes.extend(group_shapes)
        labels.extend([labels_by_group.get(group_key)] * len(group_shapes))

    if not shapes:
        return list(fallback_shapes or []), None

    return shapes, (labels if labels_by_group else None)
