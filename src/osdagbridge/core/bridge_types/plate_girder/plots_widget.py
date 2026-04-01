import numpy as np
import plotly.graph_objects as go
import openseespy.opensees as ops

FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}

# ============================================================
# UNIFIED SCENE & CAMERA CONFIGURATION
# ============================================================
# Used by all 3 plots so the camera never jumps when switching dropdowns
SHARED_SCENE = dict(
    camera=dict(
        up=dict(x=0, y=1, z=0),
        center=dict(x=0, y=0, z=0),
        eye=dict(x=0, y=0.1, z=2.5) # Perfect front elevation
    ),
    xaxis=dict(
        title=dict(text="<b>Span Length</b>", font=dict(size=12, color="black")),
        showbackground=False, showgrid=True, gridcolor="rgba(100, 100, 100, 0.15)",
        zeroline=False, showline=True, linecolor="black", linewidth=2,
        ticks="outside", tickfont=dict(size=11, color="black"),
        visible=True, showspikes=False
    ),
    zaxis=dict(
        title=dict(text="<b>Bridge Width</b>", font=dict(size=12, color="black")),
        showbackground=False, showgrid=True, gridcolor="rgba(100, 100, 100, 0.15)",
        zeroline=False, showline=True, linecolor="black", linewidth=2,
        ticks="outside", tickfont=dict(size=11, color="black"),
        autorange="reversed", visible=True, showspikes=False
    ),
    yaxis=dict(
        showbackground=False, showgrid=False, zeroline=False,
        visible=False, showspikes=False
    ),
    aspectmode='data',
)


def build_nodes_members():
    """Build nodes and members dicts from the active openseespy model."""
    nodes = {
        int(n): list(map(float, ops.nodeCoord(n)))
        for n in ops.getNodeTags()
    }
    members = {
        int(e): list(map(int, ops.eleNodes(e)))
        for e in ops.getEleTags()
    }
    return nodes, members


def add_grillage_background(fig, nodes_dict, members_dict):
    x_grill, y_grill, z_grill = [], [], []
    for ele_tag, (n1, n2) in members_dict.items():
        x1, _, z1 = nodes_dict[n1]
        x2, _, z2 = nodes_dict[n2]
        x_grill.extend([x1, x2, None])
        y_grill.extend([0, 0, None])
        z_grill.extend([z1, z2, None])

    fig.add_trace(go.Scatter3d(
        x=x_grill, y=y_grill, z=z_grill, mode='lines',
        line=dict(color='darkgrey', width=2), opacity=0.9,
        hoverinfo='skip', showlegend=False
    ))

def add_coordinate_triad(fig, nodes, scale=0.10):
    xs = [coord[0] for coord in nodes.values()]
    ys = [coord[1] for coord in nodes.values()]
    zs = [coord[2] for coord in nodes.values()]

    span_x = max(xs) - min(xs)
    span_z = max(zs) - min(zs)
    span = max(span_x, span_z)
    if span == 0: span = 5000

    L = span * scale
    ox, oy, oz = min(xs), min(ys), min(zs)

    cad_colors = {'X': '#FF4136', 'Y': '#2ECC40', 'Z': '#0074D9'}

    def draw_axis(axis_name, end_pt, vec, color):
        fig.add_trace(go.Scatter3d(
            x=[ox, end_pt[0]], y=[oy, end_pt[1]], z=[oz, end_pt[2]],
            mode='lines', line=dict(color=color, width=5), hoverinfo='skip', showlegend=False
        ))
        fig.add_trace(go.Cone(
            x=[end_pt[0]], y=[end_pt[1]], z=[end_pt[2]], u=[vec[0]], v=[vec[1]], w=[vec[2]],
            sizemode="absolute", sizeref=L*0.2, anchor="tail", showscale=False, hoverinfo='skip',
            colorscale=[[0, color], [1, color]]
        ))

    draw_axis('X', [ox + L, oy, oz], [L, 0, 0], cad_colors['X'])
    draw_axis('Y', [ox, oy + L, oz], [0, L, 0], cad_colors['Y'])
    draw_axis('Z', [ox, oy, oz + L], [0, 0, L], cad_colors['Z'])

    fig.add_trace(go.Scatter3d(
        x=[ox + L*1.2, ox, ox], y=[oy, oy + L*1.2, oy], z=[oz, oz, oz + L*1.2],
        mode='text', text=['<b>X</b>', '<b>Y</b>', '<b>Z</b>'],
        textfont=dict(color=[cad_colors['X'], cad_colors['Y'], cad_colors['Z']], size=13, family="Arial Black, sans-serif"),
        hoverinfo='skip', showlegend=False
    ))

# ============================================================
# SFD
# ============================================================
def build_figure_sfd(ds, force_key, nodes, members):
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

    Z_TOL = 3
    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    from collections import defaultdict
    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    fig_sfd = go.Figure()
    add_grillage_background(fig_sfd, nodes, members)
    add_coordinate_triad(fig_sfd, nodes)

    master_base_x, master_base_y, master_base_z = [], [], []
    master_shear_x, master_shear_y, master_shear_z = [], [], []
    master_hover_text = []
    master_cliff_x, master_cliff_y, master_cliff_z = [], [], []
    master_label_x, master_label_y, master_label_z, master_label_text = [], [], [], []

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (z_val, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, vy, node_ids = build_polyline(elems, comp_i, comp_j)
        Vy = vy.astype(float)
        z_base = np.mean(zs)

        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[[1]*len(y_step), [1]*len(y_step)], colorscale=[[0, 'blue'], [1, 'blue']],
            opacity=0.2, showscale=False, hoverinfo="skip"
        ))

        master_base_x.extend(list(xs) + [None])
        master_base_y.extend([0] * len(xs) + [None])
        master_base_z.extend(list(zs) + [None])

        master_shear_x.extend(list(x_step) + [None])
        master_shear_y.extend(list(y_step) + [None])
        master_shear_z.extend(list(z_step) + [None])

        hover_strings = [f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
                         for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])]
        master_hover_text.extend(hover_strings + [None])

        for xi, vyi in zip(xs, Vy):
            master_cliff_x.extend([xi, xi, None])
            master_cliff_z.extend([z_base, z_base, None])
            master_cliff_y.extend([0, -vyi * shear_scale if xi == xs[-1] else vyi * shear_scale, None])

        master_label_x.append(xs[0])
        master_label_y.append(0)
        master_label_z.append(zs[0])
        master_label_text.append(girder_name)

    fig_sfd.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode="lines",
        line=dict(color="green", width=3), hoverinfo="skip", showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_shear_x, y=master_shear_y, z=master_shear_z, mode="lines",
        line=dict(color="blue", width=6), hoverinfo="text", text=master_hover_text, showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_cliff_x, y=master_cliff_y, z=master_cliff_z, mode="lines",
        line=dict(color="blue", width=4), hoverinfo="skip", showlegend=False
    ))
    fig_sfd.add_trace(go.Scatter3d(
        x=master_label_x, y=master_label_y, z=master_label_z, mode="text",
        text=master_label_text, textposition="middle left", textfont=dict(size=11, color="black"),
        showlegend=False, hoverinfo="skip"
    ))

    fig_sfd.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="#E6F2FF", font_size=12, font_color="#2C3E50", bordercolor="#BBD6EE", namelength=-1),
        scene=SHARED_SCENE,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="white", plot_bgcolor="white"
    )
    return fig_sfd.to_json()


# ============================================================
# BMD
# ============================================================
def build_figure_bmd(ds, force_key, nodes, members):
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

    Z_TOL = 3
    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    from collections import defaultdict
    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, vals, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            vals.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        vals.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids

    fig_bmd = go.Figure()
    add_grillage_background(fig_bmd, nodes, members)
    add_coordinate_triad(fig_bmd, nodes)

    master_line_x, master_line_y, master_line_z = [], [], []
    master_base_x, master_base_y, master_base_z = [], [], []
    master_max_x, master_max_y, master_max_z = [], [], []
    master_min_x, master_min_y, master_min_z = [], [], []
    master_hover_text, master_label_x, master_label_y, master_label_z, master_label_text = [], [], [], [], []

    summary_data = {}

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (gid, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            factormz = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * factormz

        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1]*len(xs), [1]*len(xs)], colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip"
        ))

        master_line_x.extend(list(xs) + [None])
        master_line_y.extend(list(y_plot) + [None])
        master_line_z.extend(list(zs) + [None])

        hover_text = [f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}" for nid, x, v, z in zip(node_ids, xs, mz, zs)]
        master_hover_text.extend(hover_text + [None])

        master_base_x.extend([xs[0], xs[-1], None])
        master_base_y.extend([0, 0, None])
        master_base_z.extend([zs[0], zs[0], None])

        master_label_x.append(xs[0])
        master_label_y.append(0)
        master_label_z.append(zs[0])
        master_label_text.append(girder_name)

        idx_max, max_val = np.argmax(mz), max(mz)
        master_max_x.extend([xs[idx_max], xs[idx_max], None])
        master_max_y.extend([0, max_val * factormz, None])
        master_max_z.extend([zs[0], zs[0], None])

        idx_min, min_val = np.argmin(mz), min(mz)
        master_min_x.extend([xs[idx_min], xs[idx_min], None])
        master_min_y.extend([0, min_val * factormz, None])
        master_min_z.extend([zs[0], zs[0], None])

        summary_data[girder_name] = {"max": max_val, "min": min_val}

    # =========================================================
    # HUD GENERATOR
    # =========================================================
    hud_text = "<b>Extreme Values (N mm)</b><br>"
    hud_text += "-" * 44 + "<br>"

    h_girder = "Girder".ljust(6).replace(" ", "&nbsp;")
    h_max = "Max".rjust(14).replace(" ", "&nbsp;")
    h_min = "Min".rjust(14).replace(" ", "&nbsp;")

    hud_text += f"<b>{h_girder}</b> | <span style='color: #FF4136;'><b>{h_max}</b></span> | <span style='color: #0074D9;'><b>{h_min}</b></span><br>"
    hud_text += "-" * 44 + "<br>"

    for girder, vals in summary_data.items():
        g_str = girder.ljust(6).replace(" ", "&nbsp;")
        max_str = f"{vals['max']:.2f}".rjust(14).replace(" ", "&nbsp;")
        min_str = f"{vals['min']:.2f}".rjust(14).replace(" ", "&nbsp;")
        hud_text += f"<b>{g_str}</b> | {max_str} | {min_str}<br>"

    fig_bmd.add_trace(go.Scatter3d(
        x=master_line_x, y=master_line_y, z=master_line_z, mode='lines', line=dict(color="red", width=4),
        showlegend=False, text=master_hover_text, hoverinfo="text"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode='lines',
        line=dict(color="green", width=3, dash='solid'), showlegend=False, hoverinfo='skip'
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_label_x, y=master_label_y, z=master_label_z, mode="text", text=master_label_text,
        textposition="middle left", textfont=dict(size=11, color="black"), showlegend=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_max_x, y=master_max_y, z=master_max_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="max_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_min_x, y=master_min_y, z=master_min_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="min_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))

    fig_bmd.update_layout(
        uirevision="constant_view",
        annotations=[
            dict(
                x=0.02, y=0.98, xref="paper", yref="paper", text=hud_text, showarrow=False,
                bgcolor="rgba(33, 37, 43, 0.85)", bordercolor="rgba(255, 255, 255, 0.2)",
                borderwidth=1, borderpad=12,
                font=dict(family="Consolas, 'Courier New', monospace", size=12, color="white"),
                align="left", visible=False
            )
        ],
        hoverlabel=dict(bgcolor="#FFE4E1", font_size=12, font_color="#2C3E50", bordercolor="#CBD5E1", namelength=-1),
        updatemenus=[
            dict(
                type="buttons", direction="right", x=0.5, y=1.15, showactive=True, active=-1,
                buttons=[
                    dict(label="MAX", method="update", args=[{"visible": [True if t.legendgroup == "max_lines" else t.visible for t in fig_bmd.data]}], args2=[{"visible": [False if t.legendgroup == "max_lines" else t.visible for t in fig_bmd.data]}]),
                    dict(label="MIN", method="update", args=[{"visible": [True if t.legendgroup == "min_lines" else t.visible for t in fig_bmd.data]}], args2=[{"visible": [False if t.legendgroup == "min_lines" else t.visible for t in fig_bmd.data]}]),
                    dict(label="SUMMARY", method="relayout", args=[{"annotations[0].visible": True}], args2=[{"annotations[0].visible": False}]),
                ]
            )
        ],
        scene=SHARED_SCENE,
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig_bmd.to_json(), summary_data


# ============================================================
# BMD CONTOUR
# ============================================================
def build_figure_bmd_contour(ds, force_key, nodes, members):
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

    Z_TOL = 3
    node_z = {}
    for n in ops.getNodeTags():
        z = float(ops.nodeCoord(n)[2])
        node_z[int(n)] = round(z, Z_TOL)

    from collections import defaultdict
    girders = defaultdict(list)

    for ele in ops.getEleTags():
        n1, n2 = map(int, ops.eleNodes(ele))
        z1, z2 = node_z[n1], node_z[n2]
        if z1 == z2:
            girders[z1].append(int(ele))

    def build_polyline(elem_list, comp_i, comp_j):
        xs, ys, zs, mz, node_ids = [], [], [], [], []
        for e in elem_list:
            n1, n2 = members[e]
            x1, y1, z1 = nodes[n1]
            xs.append(x1); ys.append(y1); zs.append(z1)
            mz.append(round(get_force(e, comp_i), 3))
            node_ids.append(n1)

        last_e = elem_list[-1]
        n1, n2 = members[last_e]
        x2, y2, z2 = nodes[n2]
        xs.append(x2); ys.append(y2); zs.append(z2)
        mz.append(round(get_force(last_e, comp_j), 3))
        node_ids.append(n2)
        return np.array(xs), np.array(ys), np.array(zs), np.array(mz), node_ids

    xfull, mzfull = [], []
    for elems in girders.values():
        xs, ys, zs, mz, _ = build_polyline(elems, comp_i, comp_j)
        xfull.extend(xs)
        mzfull.extend(mz)

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    master_drop_x, master_drop_y, master_drop_z, master_drop_color, master_drop_text = [], [], [], [], []
    master_base_x, master_base_y, master_base_z = [], [], []

    sorted_girders = sorted(girders.items(), key=lambda item: item[0])
    for i, (gid, elems) in enumerate(sorted_girders):
        girder_name = f"G{i+1}"
        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            moment_scale = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))

        y_plot = mz * moment_scale

        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull),
            opacity=0.4, showscale=False, hoverinfo="skip"
        ))

        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
            marker=dict(size=12, opacity=0),
            showlegend=False, text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}" for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text"
        ))

        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[f"<b>{girder_name}</b>"],
            textposition="middle left", textfont=dict(size=14, color="black"),
            showlegend=False, hoverinfo="skip"
        ))

        master_base_x.extend([xs[0], xs[-1], None])
        master_base_y.extend([0, 0, None])
        master_base_z.extend([zs[0], zs[0], None])

        for xi, zi, mzi, nid in zip(xs, zs, mz, node_ids):
            master_drop_x.extend([xi, xi, None])
            master_drop_y.extend([0, mzi * moment_scale, None])
            master_drop_z.extend([zi, zi, None])
            master_drop_color.extend([mzi, mzi, mzi])
            htext = f"Node {nid}<br>X={xi:.2f}<br>{force_key}={mzi:.2f}"
            master_drop_text.extend([htext, htext, None])

    fig.add_trace(go.Scatter3d(
        x=master_base_x, y=master_base_y, z=master_base_z, mode="lines",
        line=dict(color="green", width=3), hoverinfo="skip", showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=master_drop_x, y=master_drop_y, z=master_drop_z, mode="lines+markers",
        line=dict(width=4, color=master_drop_color, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
        marker=dict(size=12, opacity=0), showlegend=False, text=master_drop_text, hoverinfo="text"
    ))

    fig.update_layout(
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", font_size=12, font_color="#F8F9FA", bordercolor="#0EA5E9", namelength=-1),
        scene=SHARED_SCENE,
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig.to_json()
