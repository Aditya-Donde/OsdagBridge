
import sys
import openseespy.opensees as ops
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QLabel, QComboBox, QCheckBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

import xarray as xr
import numpy as np
import plotly.graph_objects as go

from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}

bridge = BridgeGrillageModel()
bridge.create_model()
bridge.create_self_weight_load()
bridge.create_deck_load()
bridge.create_wearing_course_load()
bridge.create_footpath_load()
bridge.create_crash_barrier_load()
bridge.create_railing_load()
bridge.create_median_load()
bridge.analyze()

results = bridge.model.get_results()

# results = convert_object_to_float(girder_results)


LOADCASES = [
    "girder self weight",
    "Deck slab load",
    "Wearing course self weight",
    "Footpath load",
    "Crash barrier load",
    "Railing load",
    "Median load",
]

ds_all = results


def get_ds(loadcase):
    return ds_all.sel(Loadcase=loadcase)


# ============================================================
# TEMP HTML (single file, overwritten)
'''
TEMP_HTML = (
    Path(__file__).resolve()
    .parent.parent.parent      # (file → dir → parent → parent)
    / "temp_files"
    / "temp_plot.html"
)
TEMP_HTML = str(TEMP_HTML)
'''

# Base directory (same as your logic)
BASE_DIR = (
    Path(__file__).resolve()
    .parent.parent.parent
)

# Ensure temp_files directory exists
TEMP_DIR = BASE_DIR / "temp_files"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Final HTML file path
TEMP_HTML = TEMP_DIR / "temp_plot.html"

# If you really need string
TEMP_HTML = str(TEMP_HTML)

# COMMON IMPORTS (unchanged)


# LOAD NODES & ELEMENT CONNECTIVITY (unchanged)


# --------------------------------------------------
# Extract all nodes from in-memory OpenSees model
# ...................................................
# ============================================================
# BUILD GEOMETRY ONCE (NO FILES, NO EXEC)
# ============================================================

# Node coordinates
nodes = {
    int(n): list(map(float, ops.nodeCoord(n)))
    for n in ops.getNodeTags()
}

# Element connectivity
members = {
    int(e): list(map(int, ops.eleNodes(e)))
    for e in ops.getEleTags()
}


# ============================================================
# SFD (UNCHANGED)
def build_figure_sfd(ds, force_key):
    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]

    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    # GIRDER GROUPING
    Z_TOL = 3  # decimals for grouping (important!)

    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)
    from collections import defaultdict

    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))

        z1 = node_z[n1]
        z2 = node_z[n2]

        # only longitudinal members (same Z at both ends)
        if z1 == z2:
            girders[z1].append(int(ele))

    # BUILD GIRDER POLYLINES
    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []

        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]

            xs.append(x1)
            ys.append(y1)
            zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        # Last end node
        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]

        xs.append(x2)
        ys.append(y2)
        zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)

        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    # ===================== 3D STEPPED SFD =====================

    fig_sfd = go.Figure()

    # girder_spacing = 3.0

    for i, (gid, elems) in enumerate(girders.items()):

        xs, ys, zs, vy, node_ids = build_polyline(elems, comp_i, comp_j)

        Vy = vy.astype(float)

        # use real Z from coordinates file
        z_base = np.mean(zs)  # or zs[0]

        if max(Vy) - min(Vy) == 0:
            shear_scale = 0.1 * abs((max(xs) - min(xs)) / (max(Vy) - 0))

        else:
            shear_scale = 0.1 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))

        # ---------- BASELINE (GROUND) -------------
        fig_sfd.add_trace(go.Scatter3d(
            x=xs,
            y=[0] * len(xs),
            z=zs,  # [z_base] * len(xs),
            mode="lines",
            line=dict(color="green", width=3),
            hoverinfo="skip",
            showlegend=False
        ))

        # ---------- STEPPED SHEAR (MOUNTAINS) ----------
        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)

        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        fig_sfd.add_trace(go.Scatter3d(
            x=x_step,
            y=y_step,
            z=z_step,
            mode="lines",
            line=dict(color="blue", width=6),
            hoverinfo="text",
            text=[
                # f"Girder {gid}"
                f"<br>Node {nid}"
                f"<br>X = {x:.3f}"
                f"<br>{force_key} = {v:.3f}"
                for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])
            ],
            showlegend=False
        ))

        # ---------- VERTICAL WALLS (CLIFFS) ----------

        for xi, vyi in zip(xs, Vy):
            if xi == xs[-1]:
                fig_sfd.add_trace(go.Scatter3d(
                    x=[xi, xi],
                    y=[0, -vyi * shear_scale],
                    z=[z_base, z_base],
                    mode="lines",
                    line=dict(color="blue", width=4),
                    hoverinfo="skip",
                    showlegend=False

                ))
                # skip end nodes
            else:
                fig_sfd.add_trace(go.Scatter3d(
                    x=[xi, xi],
                    y=[0, vyi * shear_scale],
                    z=[z_base, z_base],
                    mode="lines",
                    line=dict(color="blue", width=4),
                    hoverinfo="skip",
                    showlegend=False

                ))
        # fig_bmd = go.Figure()
        # ------------ SUPPORT GEOMETRY -----------
        L = max(xs) - min(xs)
        h = 0.0199 * L  # support height
        w = 0.006 * L  # support half-width
        r = 0.0025 * L  # roller radius
        # ---------- PIN SUPPORT (START NODE) ----------
        x0, z0 = xs[0], zs[0]

        fig_sfd.add_trace(go.Scatter3d(
            x=[x0 - w, x0, x0 + w, x0 - w],
            y=[-h, 0, -h, -h],
            z=[z0, z0, z0, z0],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))
        # ===== PIN SUPPORT BASE (GROUND + HATCH) =====
        n_hatch = 6
        hatch_len = 0.15 * h

        # ground line
        fig_sfd.add_trace(go.Scatter3d(
            x=[x0 - 1.3 * w, x0 + 1.3 * w],
            y=[-h, -h],
            z=[z_base, z_base],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x0 - 1.2 * w, x0 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig_sfd.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[-h, -h - hatch_len],
                z=[z_base, z_base],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))

        # --------ROLLER SUPPORT(END NODE)--------------
        x1, z1 = xs[-1], zs[-1]

        # Triangle
        fig_sfd.add_trace(go.Scatter3d(
            x=[x1 - w, x1, x1 + w, x1 - w],
            y=[-h, 0, -h, -h],
            z=[z1, z1, z1, z1],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))
        Yb = -h  # base of triangle

        # Rollers (two wheels)
        theta = np.linspace(0, 2 * np.pi, 60)

        for dx in [-w / 2, w / 2]:
            fig_sfd.add_trace(go.Scatter3d(
                x=x1 + dx + r * np.cos(theta),
                y=(Yb - r) + r * np.sin(theta),  # tangent to triangle base
                z=[z1] * len(theta),
                mode="lines",
                line=dict(color="green", width=5),
                showlegend=False,
                hoverinfo="skip"
            ))
            # ===== ROLLER SUPPORT BASE (GROUND + HATCH) =====
        # ===== ROLLER SUPPORT BASE (TANGENT TO ROLLERS) =====
        n_hatch = 6
        hatch_len = 0.15 * h

        y_ground = Yb - 2 * r  # tangent to roller bottom

        # ground line
        fig_sfd.add_trace(go.Scatter3d(
            x=[x1 - 1.3 * w, x1 + 1.3 * w],
            y=[y_ground, y_ground],
            z=[z_base, z_base],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x1 - 1.2 * w, x1 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig_sfd.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[y_ground, y_ground - hatch_len],
                z=[z_base, z_base],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))

    fig_sfd.update_layout(
        title="3D Shear Force Diagram",
        scene=dict(

            xaxis=dict(
                showbackground=False, showticklabels=False, title="", showspikes=False
                #

            ),
            yaxis=dict(
                showbackground=False, showticklabels=False, title="", showspikes=False
                #
            ),
            zaxis=dict(
                showbackground=False, showticklabels=False, title="", showspikes=False, autorange="reversed"
                #

            ),

            aspectmode="data",
            camera=dict(
                eye=dict(x=1.6, y=1.2, z=1.6),
                up=dict(x=0, y=1, z=0)
            ),

        ),
        margin=dict(l=0, r=0, t=40, b=0)
    )
    fig_sfd.write_html(TEMP_HTML, include_plotlyjs=True, full_html=True)


# ============================================================
#  BMD


def build_figure_bmd(ds, force_key):
    # LOAD INTERNAL FORCES (NETCDF)
    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    Z_TOL = 3  # decimals for grouping (important!)

    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)
    from collections import defaultdict

    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))

        z1 = node_z[n1]
        z2 = node_z[n2]

        # only longitudinal members (same Z at both ends)
        if z1 == z2:
            girders[z1].append(int(ele))

    # BUILD GIRDER POLYLINES
    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []

        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1)
            ys.append(y1)
            zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)
        print(f"Element list: {elem_list}")
        # Last end node
        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]

        xs.append(x2)
        ys.append(y2)
        zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)

        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    # PLOTLY 3D BMD INTERACTIVE
    fig_bmd = go.Figure()
    '''
    xfull=[]
    mzfull =[]
    for gid, elems in girders.items():
        xs, ys, zs, mz, node_ids = build_polyline(elems, Mz_i, Mz_j)
        xfull.extend(xs)
        mzfull.extend(mz)
    diffxfull = max(xfull)-min(xfull)
    diffmzfull = max(mzfull)-min(mzfull)
    #factormz= abs(diffmzfull/diffxfull)*0.2
    '''
    for gid, elems in girders.items():
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)
        if max(mz) - min(mz) == 0:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - 0))


        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
        y_plot = mz * factormz  # * 0.05  # moment scale
        hover_text = [
            f"Node {nid}<br>X = {x:.3f}<br>{force_key} = {v:.3f}<br>Z = {z:.3f}"
            for nid, x, v, z in zip(node_ids, xs, mz, zs)
        ]

        fig_bmd.add_trace(go.Scatter3d(
            x=xs,
            y=y_plot,
            z=zs,
            mode='lines+markers',
            line=dict(color="red", width=4),
            marker=dict(size=3, color="red"),
            # name=f"Girder {gid}",
            showlegend=False,
            text=hover_text,
            hoverinfo="text"
        ))

        # baseline
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]],  # first and last node X
            y=[0, 0],  # Mz = 0 baseline
            z=[zs[0], zs[0]],  # same girder elevation
            mode='lines',
            line=dict(
                color="green",
                width=3,
                dash='solid'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[np.argmax(mz)], xs[np.argmax(mz)]],
            y=[0, max(mz) * factormz],
            z=[zs[0]] * 2,
            mode="lines",
            line=dict(color="black", width=3),
            legendgroup="max_lines",
            showlegend=False,
            visible=False,  # start OFF
            hoverinfo="skip"
        ))

        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[np.argmin(mz)]] * 2,
            y=[0, min(mz) * factormz],
            z=[zs[0]] * 2,
            mode="lines",
            line=dict(color="black", width=3),
            legendgroup="min_lines",
            showlegend=False,
            visible=False,  # start OFF
            hoverinfo="skip"
        ))

        # ------------ SUPPORT GEOMETRY -----------
        L = max(xs) - min(xs)
        h = 0.0399 * L  # support height
        w = 0.015 * L  # support half-width
        r = 0.005 * L  # roller radius

        # ---------- PIN SUPPORT (START NODE) ----------
        x0, z0 = xs[0], zs[0]

        fig_bmd.add_trace(go.Scatter3d(
            x=[x0 - w, x0, x0 + w, x0 - w],
            y=[-h, 0, -h, -h],
            z=[z0, z0, z0, z0],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))
        n_hatch = 6
        hatch_len = 0.15 * h

        # ground line
        fig_bmd.add_trace(go.Scatter3d(
            x=[x0 - 1.3 * w, x0 + 1.3 * w],
            y=[-h, -h],
            z=[z0, z0],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x0 - 1.2 * w, x0 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig_bmd.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[-h, -h - hatch_len],
                z=[z0, z0],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))
        # --------ROLLER SUPPORT(END NODE)--------------
        x1, z1 = xs[-1], zs[-1]

        # Triangle
        fig_bmd.add_trace(go.Scatter3d(
            x=[x1 - w, x1, x1 + w, x1 - w],
            y=[-h, 0, -h, -h],
            z=[z1, z1, z1, z1],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))
        Yb = -h  # base of triangle

        # Rollers (two wheels)
        theta = np.linspace(0, 2 * np.pi, 60)

        for dx in [-w / 2, w / 2]:
            fig_bmd.add_trace(go.Scatter3d(
                x=x1 + dx + r * np.cos(theta),
                y=(Yb - r) + r * np.sin(theta),  # tangent to triangle base
                z=[z1] * len(theta),
                mode="lines",
                line=dict(color="green", width=5),
                showlegend=False,
                hoverinfo="skip"
            ))
        n_hatch = 6
        hatch_len = 0.15 * h

        y_ground = Yb - 2 * r  # tangent to roller bottom

        # ground line
        fig_bmd.add_trace(go.Scatter3d(
            x=[x1 - 1.3 * w, x1 + 1.3 * w],
            y=[y_ground, y_ground],
            z=[z1, z1],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x1 - 1.2 * w, x1 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig_bmd.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[y_ground, y_ground - hatch_len],
                z=[z1, z1],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))

    # pad = 0.01*(max(xfull) - min(xfull))
    # pad2 = 0.01*(max(mzfull) - min(mzfull))

    max_idx = [i for i, t in enumerate(fig_bmd.data) if t.legendgroup == "max_lines"]
    min_idx = [i for i, t in enumerate(fig_bmd.data) if t.legendgroup == "min_lines"]

    fig_bmd.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.5,
                y=1.15,
                showactive=True,
                active=-1,
                buttons=[
                    # -------- MAX TOGGLE --------
                    dict(
                        label="MAX",
                        method="update",

                        # OFF → ON
                        args=[{
                            "visible": [
                                True if t.legendgroup == "max_lines" else t.visible
                                for t in fig_bmd.data
                            ]
                        }],

                        # ON → OFF
                        args2=[{
                            "visible": [
                                False if t.legendgroup == "max_lines" else t.visible
                                for t in fig_bmd.data
                            ]
                        }]
                    ),

                    # -------- MIN TOGGLE --------
                    dict(
                        label="MIN",
                        method="update",

                        # OFF → ON
                        args=[{
                            "visible": [
                                True if t.legendgroup == "min_lines" else t.visible
                                for t in fig_bmd.data
                            ]
                        }],

                        # ON → OFF
                        args2=[{
                            "visible": [
                                False if t.legendgroup == "min_lines" else t.visible
                                for t in fig_bmd.data
                            ]
                        }]
                    ),
                ]
            )
        ],
        title="Interactive 3D BMD",

        scene=dict(

            camera=dict(
                # eye=dict(x=2.5, y=1, z=10),  #  pull camera along X
                up=dict(x=0, y=0.5, z=0),
                # center=dict(x=0, y=0, z=0),
                # projection=dict(type="orthographic")
            ),
            xaxis=dict(
                title="girder length",
                # range=[min(xfull) - pad, max(xfull) + pad],
                showbackground=False,  # removes YZ plane
                showgrid=False,
                zeroline=False,
                visible=False
            ),
            yaxis=dict(
                # range=[min(mzfull) - 0.25 * (max(mzfull) - min(mzfull)),max(mzfull) + 0.25 * (max(mzfull) - min(mzfull))],
                title="Mz values",
                # range = [min(mzfull)-pad2,max(mzfull)+pad2],
                showbackground=True,  #
                backgroundcolor="rgba(200,200,200,0.15)",
                showgrid=False,
                zeroline=False,
                visible=False  # showaxis line, keep plane
            ),
            zaxis=dict(
                showbackground=False,  # removes XY plane
                showgrid=False,
                zeroline=False,
                visible=False,
                autorange="reversed"
            ),
            aspectmode='data',

        ),

        # legend=dict(title="Girders")
    )

    fig_bmd.write_html(TEMP_HTML, include_plotlyjs=True, full_html=True)


# ============================================================
# BMD CONTOUR
def build_figure_bmd_contour(ds, force_key):
    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    # -------------------------------------------------------------
    # GIRDER GROUPING
    # -------------------------------------------------------------
    Z_TOL = 3  # decimals for grouping (important!)

    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)
    from collections import defaultdict

    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))

        z1 = node_z[n1]
        z2 = node_z[n2]

        # only longitudinal members (same Z at both ends)
        if z1 == z2:
            girders[z1].append(int(ele))

    # -------------------------------------------------------------
    # BUILD GIRDER POLYLINE
    # -------------------------------------------------------------
    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, mz, node_ids = [], [], [], [], []

        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]

            xs.append(x1)
            ys.append(y1)
            zs.append(z1)
            mz.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]

        xs.append(x2)
        ys.append(y2)
        zs.append(z2)
        mz.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)

        return np.array(xs), np.array(ys), np.array(zs), np.array(mz), node_ids

    xfull, mzfull = [], []
    for elems in girders.values():
        xs, ys, zs, mz, _ = build_polyline(elems, comp_i, comp_j)
        xfull.extend(xs)
        mzfull.extend(mz)

    # moment_scale = 0.2 * abs(dx / dmz)   # visual-only scale

    # -------------------------------------------------------------
    # FIGURE
    # -------------------------------------------------------------
    fig = go.Figure()

    for gid, elems in girders.items():
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)
        if max(mz) - min(mz) == 0:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - 0))

        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
        y_plot = mz * moment_scale

        # -------- CONTOUR-STYLE BMD LINE --------
        fig.add_trace(go.Scatter3d(
            x=xs,
            y=y_plot,
            z=zs,
            mode="lines",
            line=dict(
                width=6,
                color=mz,  # color by Mz
                colorscale="Jet",
                cmin=min(mzfull),
                cmax=max(mzfull)
            ),
            showlegend=False,
            hoverinfo="text",
            text=[
                f"Node {nid}<br>X={x:.3f}<br>{force_key}={v:.3f}"
                for nid, x, v in zip(node_ids, xs, mz)
            ]
        ))

        # -------- BASELINE (Mz = 0) --------
        fig.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]],
            y=[0, 0],
            z=[zs[0], zs[0]],
            mode="lines",
            line=dict(color="green", width=3),
            hoverinfo="skip",
            showlegend=False
        ))

        # ---------- DROPLINES FROM BASELINE TO BMD ----------
        for xi, zi, mzi in zip(xs, zs, mz):
            fig.add_trace(go.Scatter3d(
                x=[xi, xi],
                y=[0, mzi * moment_scale],  # baseline → BMD
                z=[zi, zi],
                mode="lines",
                line=dict(
                    width=4,
                    color=[mzi, mzi],  # same color as contour
                    colorscale="Jet",
                    cmin=min(mzfull),
                    cmax=max(mzfull)
                ),
                showlegend=False,
                hoverinfo="skip"
            ))

        # ------------ SUPPORT GEOMETRY -----------
        L = max(xs) - min(xs)
        h = 0.0399 * L  # support height
        w = 0.015 * L  # support half-width
        r = 0.005 * L  # roller radius

        # ---------- PIN SUPPORT (FIRST NODE) ----------
        x0, z0 = xs[0], zs[0]

        fig.add_trace(go.Scatter3d(
            x=[x0 - w, x0, x0 + w, x0 - w],
            y=[-h, 0, -h, -h],
            z=[z0, z0, z0, z0],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))

        # ---------- ROLLER SUPPORT (LAST NODE) ----------
        x1, z1 = xs[-1], zs[-1]

        # Triangle
        fig.add_trace(go.Scatter3d(
            x=[x1 - w, x1, x1 + w, x1 - w],
            y=[-h, 0, -h, -h],
            z=[z1, z1, z1, z1],
            mode="lines",
            line=dict(color="green", width=5),
            showlegend=False,
            hoverinfo="skip"
        ))

        Yb = -h  # base of triangle
        theta = np.linspace(0, 2 * np.pi, 60)

        # Two rollers
        for dxr in [-w / 2, w / 2]:
            fig.add_trace(go.Scatter3d(
                x=x1 + dxr + r * np.cos(theta),
                y=(Yb - r) + r * np.sin(theta),
                z=[z1] * len(theta),
                mode="lines",
                line=dict(color="green", width=5),
                showlegend=False,
                hoverinfo="skip"
            ))
        n_hatch = 6
        hatch_len = 0.15 * h

        # ground line
        fig.add_trace(go.Scatter3d(
            x=[x0 - 1.3 * w, x0 + 1.3 * w],
            y=[-h, -h],
            z=[z0, z0],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x0 - 1.2 * w, x0 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[-h, -h - hatch_len],
                z=[z0, z0],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))

        y_ground = Yb - 2 * r  # tangent to roller bottom

        # ground line
        fig.add_trace(go.Scatter3d(
            x=[x1 - 1.3 * w, x1 + 1.3 * w],
            y=[y_ground, y_ground],
            z=[z1, z1],
            mode="lines",
            line=dict(color="green", width=4),
            showlegend=False,
            hoverinfo="skip"
        ))

        # hatch lines
        xs_hatch = np.linspace(x1 - 1.2 * w, x1 + 1.2 * w, n_hatch)

        for xh in xs_hatch:
            fig.add_trace(go.Scatter3d(
                x=[xh - 0.04 * w, xh + 0.04 * w],
                y=[y_ground, y_ground - hatch_len],
                z=[z1, z1],
                mode="lines",
                line=dict(color="green", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))

    # LAYOUT (POST-PROCESSOR STYLE)

    fig.update_layout(
        title="3D Bending Moment Diagram  Contour View",

        scene=dict(

            camera=dict(
                # eye=dict(x=2.5, y=0.15, z=10),  # 👈 pull camera along X
                up=dict(x=0, y=1, z=0),
                # center=dict(x=0, y=0, z=0),
                # projection=dict(type="orthographic")
            ),
            xaxis=dict(
                title="girder length",
                # range=[min(xfull) - pad, max(xfull) + pad],
                showbackground=False,  # removes YZ plane
                showgrid=False,
                zeroline=False,
                visible=False
            ),
            yaxis=dict(
                # range=[min(mzfull) - 0.25 * (max(mzfull) - min(mzfull)),max(mzfull) + 0.25 * (max(mzfull) - min(mzfull))],
                title="Mz values",
                # range = [min(mzfull)-pad2,max(mzfull)+pad2],
                showbackground=True,  #
                backgroundcolor="rgba(200,200,200,0.15)",
                showgrid=False,
                zeroline=False,
                visible=False  # showaxis line, keep plane
            ),
            zaxis=dict(
                showbackground=False,  # removes XY plane
                showgrid=False,
                zeroline=False,
                visible=False,
                autorange="reversed"
            ),
            aspectmode='data',

        ),
    )

    fig.write_html(TEMP_HTML, include_plotlyjs=True, full_html=True)


# ============================================================
# ====================== QT WIDGET
'''
class PlotWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Girder Plots")

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.sfd = QRadioButton("SFD")
        self.bmd = QRadioButton("BMD")
        self.contour = QRadioButton("BMD Contour")

        self.sfd.setChecked(True)

        group = QButtonGroup(self)
        group.setExclusive(True)
        group.addButton(self.sfd)
        group.addButton(self.bmd)
        group.addButton(self.contour)
        group.buttonClicked.connect(self.update_plot)

        top.addWidget(self.sfd)
        top.addWidget(self.bmd)
        top.addWidget(self.contour)

        self.web = QWebEngineView()

        layout.addLayout(top)
        layout.addWidget(self.web)

        self.update_plot(self.sfd)

    def update_plot(self, btn):
        if btn == self.sfd:
            build_figure_sfd()
        elif btn == self.bmd:
            build_figure_bmd()
        else:
            build_figure_bmd_contour()

        self.web.load(QUrl.fromLocalFile(TEMP_HTML))
'''


# ====================== QT WIDGET
# ============================================================
class PlotWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Girder Results")

        layout = QVBoxLayout(self)

        top = QHBoxLayout()

        # ---------- LOADCASE ----------
        top.addWidget(QLabel("Load case:"))

        self.combo = QComboBox()
        self.combo.addItems(LOADCASES)
        self.combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.combo)

        # ---------- FORCE ----------
        top.addWidget(QLabel("Force:"))

        self.force_combo = QComboBox()
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Fy")
        self.force_combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.force_combo)

        # ---------- CONTOUR ----------
        self.contour = QCheckBox("Contour (Moments only)")
        self.contour.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour)

        top.addStretch()

        self.web = QWebEngineView()

        layout.addLayout(top)
        layout.addWidget(self.web)

        self.update_plot()

    def update_plot(self):
        loadcase = self.combo.currentText()
        force_key = self.force_combo.currentText()

        ds = get_ds(loadcase)

        # -------- FORCE TYPE --------
        is_force = force_key.startswith("F")  # Fx, Fy, Fz
        is_moment = force_key.startswith("M")  # Mx, My, Mz

        # -------- UI LOGIC --------
        if is_force:
            # Forces → SFD, contour disabled
            self.contour.blockSignals(True)
            self.contour.setChecked(False)
            self.contour.setEnabled(False)
            self.contour.blockSignals(False)

            build_figure_sfd(ds, force_key)

        elif is_moment:
            # Moments → BMD (+ optional contour)
            self.contour.setEnabled(True)

            if self.contour.isChecked():
                build_figure_bmd_contour(ds, force_key)
            else:
                build_figure_bmd(ds, force_key)

        else:
            raise ValueError(f"Unsupported force: {force_key}")

        # -------- UPDATE VIEW --------
        self.web.load(QUrl.fromLocalFile(TEMP_HTML))


# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())