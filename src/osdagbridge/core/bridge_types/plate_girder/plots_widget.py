import numpy as np
import plotly.graph_objects as go

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
        tickangle=0,  
        visible=True, showspikes=False
    ),
    zaxis=dict(
        title=dict(text="<b>Bridge Width</b>", font=dict(size=12, color="black")),
        showbackground=False, showgrid=True, gridcolor="rgba(100, 100, 100, 0.15)",
        zeroline=False, showline=True, linecolor="black", linewidth=2,
        ticks="outside", tickfont=dict(size=11, color="black"),
        tickangle=0,  
        autorange="reversed", visible=True, showspikes=False
    ),
    yaxis=dict(
        showbackground=False, showgrid=False, zeroline=False,
        visible=False, showspikes=False
    ),
    aspectmode='data',
)

# ============================================================
# BACKGROUND & AXES GENERATORS
# ============================================================
def add_grillage_background(fig, nodes_dict, members_dict):
    Z_TOL = 3
    X_TOL = 3

    z_vals, x_vals = set(), set()
    for coord in nodes_dict.values():
        x_vals.add(round(coord[0], X_TOL))
        z_vals.add(round(coord[2], Z_TOL))

    if not z_vals: return
    z_sorted = sorted(list(z_vals))
    x_sorted = sorted(list(x_vals))

    min_z, max_z = z_sorted[0], z_sorted[-1]
    min_x, max_x = x_sorted[0], x_sorted[-1]

    transverse_x, transverse_y, transverse_z = [], [], []
    edges_x, edges_y, edges_z = [], [], []
    longitudinal = {z: {"x":[], "y":[], "z":[]} for z in z_sorted}

    for ele_tag, conn in members_dict.items():
        if len(conn) != 2: continue
        n1, n2 = conn
        x1, y1, z1 = nodes_dict[n1]
        x2, y2, z2 = nodes_dict[n2]

        rz1, rz2 = round(z1, Z_TOL), round(z2, Z_TOL)
        rx1, rx2 = round(x1, X_TOL), round(x2, X_TOL)

        if rz1 == rz2:
            # Longitudinal lines
            longitudinal[rz1]["x"].extend([x1, x2, None])
            longitudinal[rz1]["y"].extend([y1, y2, None])
            longitudinal[rz1]["z"].extend([z1, z2, None])
        else:
            # Transverse lines (Split into Slabs and End Edges)
            if rx1 == rx2 and (rx1 == min_x or rx1 == max_x):
                edges_x.extend([x1, x2, None])
                edges_y.extend([y1, y2, None])
                edges_z.extend([z1, z2, None])
            else:
                transverse_x.extend([x1, x2, None])
                transverse_y.extend([y1, y2, None])
                transverse_z.extend([z1, z2, None])

    # 1. Plot Transverse Slabs (Darker Bronze/Brown)
    if transverse_x:
        fig.add_trace(go.Scatter3d(
            x=transverse_x, y=transverse_y, z=transverse_z, mode='lines',
            line=dict(color='rgba(160, 80, 0, 0.9)', width=2), 
            hoverinfo='skip', name="Transverse Slabs", legendgroup="Transverse Slabs"
        ))

    # 2. Plot End Edges (Red)
    if edges_x:
        fig.add_trace(go.Scatter3d(
            x=edges_x, y=edges_y, z=edges_z, mode='lines',
            line=dict(color='rgba(255, 0, 0, 0.6)', width=3), 
            hoverinfo='skip', name="End Edges", legendgroup="End Edges"
        ))

    # 3. Plot Longitudinal Backgrounds (Controls the Master Legend!)
    num_girders = len(z_sorted)
    inner_legend_added = False

    for i, z_val in enumerate(z_sorted, start=1):
        if i == 1:
            group = "Edge Beam 1"
            display_name = "Edge Beam 1"
            show_leg = True
        elif i == num_girders:
            group = "Edge Beam 2"
            display_name = "Edge Beam 2"
            show_leg = True
        else:
            group = "Inner Girders"
            display_name = "Inner Girders"
            if not inner_legend_added:
                show_leg = True
                inner_legend_added = True
            else:
                show_leg = False
                
        data = longitudinal[z_val]
        if data["x"]:
            fig.add_trace(go.Scatter3d(
                x=data["x"], y=data["y"], z=data["z"], mode='lines',
                line=dict(color='black', width=3), # Solid Black
                hoverinfo='skip', name=display_name, legendgroup=group, showlegend=show_leg 
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
def build_figure_sfd(results_handler, loadcase, force_key, user_scale=1.0):
    ds = results_handler.ds

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        # Queries the raw dataset for the specific loadcase
        return float(ds["forces"].sel(Loadcase=loadcase, Element=elem, Component=comp).values)

    # --- SINGLE SOURCE OF TRUTH: BFS GRAPH ---
    nodes, members, _ = results_handler.build_grillage_connectivity()
    girder_map, _ = results_handler.build_girders(verbose=False)
    # -----------------------------------------

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

    # Plot directly from the BFS dictionary
    for girder_name, g_data in girder_map.items():
        elems = g_data["elements"]
        
        # Link to the master background toggles
        if girder_name == "EB1":
            legend_group = "Edge Beam 1"
        elif girder_name == "EB2":
            legend_group = "Edge Beam 2"
        else:
            legend_group = "Inner Girders"

        xs, ys, zs, vy, node_ids = build_polyline(elems, comp_i, comp_j)
        Vy = vy.astype(float)
        z_base = np.mean(zs)

        if max(Vy) - min(Vy) == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / (max(Vy) - min(Vy)))
        shear_scale *= user_scale

        x_step = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step = Vy_step * shear_scale
        z_step = [z_base] * len(y_step)

        # -------------------------------------------------------------
        # PER-GIRDER PLOTTING
        # -------------------------------------------------------------

        # 1. 3D Surface
        fig_sfd.add_trace(go.Surface(
            x=[x_step, x_step], y=[np.zeros(len(y_step)), y_step], z=[z_step, z_step],
            surfacecolor=[[1]*len(y_step), [1]*len(y_step)], colorscale=[[0, 'blue'], [1, 'blue']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            legendgroup=legend_group, showlegend=False
        ))

        # 2. Main Shear Line 
        hover_strings = [f"<br>Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}"
                         for x, v, nid in zip(x_step, Vy_step, np.repeat(node_ids, 2)[1:-1])]
        fig_sfd.add_trace(go.Scatter3d(
            x=x_step, y=y_step, z=z_step, mode="lines",
            line=dict(color="blue", width=6), hoverinfo="text", text=hover_strings,
            name=girder_name, legendgroup=legend_group, showlegend=False
        ))

        # 3. Green Base Line
        fig_sfd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip", 
            legendgroup=legend_group, showlegend=False
        ))

        # 4. Vertical Drops (Cliffs)
        cliff_x, cliff_y, cliff_z = [], [], []
        for xi, vyi in zip(xs, Vy):
            cliff_x.extend([xi, xi, None])
            cliff_z.extend([z_base, z_base, None])
            cliff_y.extend([0, -vyi * shear_scale if xi == xs[-1] else vyi * shear_scale, None])
            
        fig_sfd.add_trace(go.Scatter3d(
            x=cliff_x, y=cliff_y, z=cliff_z, mode="lines", 
            line=dict(color="blue", width=4), hoverinfo="skip", 
            legendgroup=legend_group, showlegend=False
        ))

        # 5. Text Label
        fig_sfd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"),
            hoverinfo="skip", legendgroup=legend_group, showlegend=False
        ))

    fig_sfd.update_layout(
        legend=dict(title="<b>Members</b>", itemsizing="constant"),
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
def build_figure_bmd(results_handler, loadcase, force_key, user_scale=1.0):
    ds = results_handler.ds

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Loadcase=loadcase, Element=elem, Component=comp).values)

    # --- SINGLE SOURCE OF TRUTH: BFS GRAPH ---
    nodes, members, _ = results_handler.build_grillage_connectivity()
    girder_map, _ = results_handler.build_girders(verbose=False)
    # -----------------------------------------

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

    master_max_x, master_max_y, master_max_z = [], [], []
    master_min_x, master_min_y, master_min_z = [], [], []
    summary_data = {}

    for girder_name, g_data in girder_map.items():
        elems = g_data["elements"]
        
        if girder_name == "EB1":
            legend_group = "Edge Beam 1"
        elif girder_name == "EB2":
            legend_group = "Edge Beam 2"
        else:
            legend_group = "Inner Girders"

        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            factormz = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            factormz = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
        factormz *= user_scale

        y_plot = mz * factormz

        # -------------------------------------------------------------
        # PER-GIRDER PLOTTING
        # -------------------------------------------------------------

        # 1. 3D Surface 
        fig_bmd.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[[1]*len(xs), [1]*len(xs)], colorscale=[[0, 'red'], [1, 'red']],
            opacity=0.2, showscale=False, hoverinfo="skip",
            legendgroup=legend_group, showlegend=False
        ))

        # 2. Main BMD Line 
        hover_text = [f"Node {nid}<br>X = {x:.2f}<br>{force_key} = {v:.2f}<br>Z = {z:.2f}" for nid, x, v, z in zip(node_ids, xs, mz, zs)]
        fig_bmd.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode='lines', line=dict(color="red", width=4),
            name=girder_name, legendgroup=legend_group, showlegend=False,
            text=hover_text, hoverinfo="text"
        ))

        # 3. Green Base Line
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode='lines',
            line=dict(color="green", width=3, dash='solid'), hoverinfo='skip',
            legendgroup=legend_group, showlegend=False
        ))

        # 4. Text Label
        fig_bmd.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"), 
            hoverinfo="skip", legendgroup=legend_group, showlegend=False
        ))
        # -------------------------------------------------------------

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

    # Add the single Max/Min traces for the buttons
    fig_bmd.add_trace(go.Scatter3d(
        x=master_max_x, y=master_max_y, z=master_max_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="max_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))
    fig_bmd.add_trace(go.Scatter3d(
        x=master_min_x, y=master_min_y, z=master_min_z, mode="lines", line=dict(color="black", width=3),
        legendgroup="min_lines", showlegend=False, visible=False, hoverinfo="skip"
    ))

    fig_bmd.update_layout(
        legend=dict(title="<b>Members</b>", itemsizing="constant"),
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
def build_figure_bmd_contour(results_handler, loadcase, force_key, user_scale=1.0):
    ds = results_handler.ds

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    comp_i = find_component(comp_i_name)
    comp_j = find_component(comp_j_name)

    def get_force(elem, comp):
        return float(ds["forces"].sel(Loadcase=loadcase, Element=elem, Component=comp).values)

    # --- SINGLE SOURCE OF TRUTH: BFS GRAPH ---
    nodes, members, _ = results_handler.build_grillage_connectivity()
    girder_map, _ = results_handler.build_girders(verbose=False)
    # -----------------------------------------

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

    # Pre-calculate global min/max for the Jet colorscale
    xfull, mzfull = [], []
    for g_data in girder_map.values():
        xs, ys, zs, mz, _ = build_polyline(g_data["elements"], comp_i, comp_j)
        xfull.extend(xs)
        mzfull.extend(mz)

    fig = go.Figure()
    add_grillage_background(fig, nodes, members)
    add_coordinate_triad(fig, nodes)

    for girder_name, g_data in girder_map.items():
        elems = g_data["elements"]
        
        if girder_name == "EB1":
            legend_group = "Edge Beam 1"
        elif girder_name == "EB2":
            legend_group = "Edge Beam 2"
        else:
            legend_group = "Inner Girders"

        xs, ys, zs, mz, node_ids = build_polyline(elems, comp_i, comp_j)

        if max(mz) - min(mz) == 0:
            moment_scale = 1.0 if max(mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / (max(mz) - min(mz)))
        moment_scale *= user_scale

        y_plot = mz * moment_scale

        # -------------------------------------------------------------
        # PER-GIRDER PLOTTING
        # -------------------------------------------------------------

        # 1. Surface 
        fig.add_trace(go.Surface(
            x=[xs, xs], y=[np.zeros(len(xs)), y_plot], z=[zs, zs],
            surfacecolor=[mz, mz], colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull),
            opacity=0.4, showscale=False, hoverinfo="skip",
            legendgroup=legend_group, showlegend=False
        ))

        # 2. Main Line
        fig.add_trace(go.Scatter3d(
            x=xs, y=y_plot, z=zs, mode="lines+markers",
            line=dict(width=6, color=mz, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
            marker=dict(size=12, opacity=0),
            name=girder_name, legendgroup=legend_group, showlegend=False,
            text=[f"Node {nid}<br>X={x:.2f}<br>{force_key}={v:.2f}" for nid, x, v in zip(node_ids, xs, mz)],
            hoverinfo="text"
        ))

        # 3. Label
        fig.add_trace(go.Scatter3d(
            x=[xs[0]], y=[0], z=[zs[0]], mode="text", text=[girder_name],
            textposition="middle left", textfont=dict(size=11, color="black"),
            hoverinfo="skip", legendgroup=legend_group, showlegend=False
        ))

        # 4. Green Base Line
        fig.add_trace(go.Scatter3d(
            x=[xs[0], xs[-1]], y=[0, 0], z=[zs[0], zs[0]], mode="lines",
            line=dict(color="green", width=3), hoverinfo="skip",
            legendgroup=legend_group, showlegend=False
        ))

        # 5. Drop Lines (Cliffs)
        drop_x, drop_y, drop_z, drop_color, drop_text = [], [], [], [], []
        for xi, zi, mzi, nid in zip(xs, zs, mz, node_ids):
            drop_x.extend([xi, xi, None])
            drop_y.extend([0, mzi * moment_scale, None])
            drop_z.extend([zi, zi, None])
            drop_color.extend([mzi, mzi, mzi])
            htext = f"Node {nid}<br>X={xi:.2f}<br>{force_key}={mzi:.2f}"
            drop_text.extend([htext, htext, None])

        fig.add_trace(go.Scatter3d(
            x=drop_x, y=drop_y, z=drop_z, mode="lines+markers",
            line=dict(width=4, color=drop_color, colorscale="Jet", cmin=min(mzfull), cmax=max(mzfull)),
            marker=dict(size=12, opacity=0), showlegend=False, text=drop_text, hoverinfo="text",
            legendgroup=legend_group
        ))

    fig.update_layout(
        legend=dict(title="<b>Members</b>", itemsizing="constant"), 
        uirevision="constant_view",
        hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", font_size=12, font_color="#F8F9FA", bordercolor="#0EA5E9", namelength=-1),
        scene=SHARED_SCENE,
        paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig.to_json()