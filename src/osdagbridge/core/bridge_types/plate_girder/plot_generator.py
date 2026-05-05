import io
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter
import numpy as np
import openseespy.opensees as ops
from mpl_toolkits.mplot3d.art3d import Line3DCollection

try:
    import mplcursors
    _MPLCURSORS = True
except ImportError:
    _MPLCURSORS = False

# Force component map
FORCE_MAP = {
    "Fx": ("Vx_i", "Vx_j"),
    "Fy": ("Vy_i", "Vy_j"),
    "Fz": ("Vz_i", "Vz_j"),
    "Mx": ("Mx_i", "Mx_j"),
    "My": ("My_i", "My_j"),
    "Mz": ("Mz_i", "Mz_j"),
}

# Human-readable labels shown in plot titles / axis labels
# Human-readable labels shown in plot titles / axis labels
FORCE_DISPLAY = {
    "Fx": "V$_x$", "Fy": "V$_y$", "Fz": "V$_z$",
    "Mx": "M$_x$", "My": "M$_y$", "Mz": "M$_z$",
}

# Displacement component map  key → component name in ds["displacements"]
DISP_MAP = {
    "Dx": "dx",
    "Dy": "dy",
    "Dz": "dz",
}

DISP_DISPLAY = {
    "Dx": "D$_x$", "Dy": "D$_y$", "Dz": "D$_z$",
}

# View settings (elevation/azimuth for a near-front-elevation look)
DEFAULT_ELEV = 10
DEFAULT_AZIM = -90


# =============================================================================
# LOW-LEVEL HELPERS
# =============================================================================

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


def _find_girders(nodes, members, z_tol=3):
    """
    Return an OrderedDict  { z_value: [elem_tag, ...] }
    containing only longitudinal elements (both end-nodes share the same z).
    Elements within each girder are sorted by their i-node x-coordinate.
    """
    node_z = {n: round(coord[2], z_tol) for n, coord in nodes.items()}

    girders = defaultdict(list)
    for ele, (n1, n2) in members.items():
        if node_z[n1] == node_z[n2]:
            girders[node_z[n1]].append(ele)

    # sort elements within each girder by x of i-node
    for z_val in girders:
        girders[z_val].sort(key=lambda e: nodes[members[e][0]][0])

    return dict(sorted(girders.items()))


def _build_polyline(elems, members, nodes, force_i, force_j, ds):
    """
    Build arrays (xs, ys, zs, vals, node_ids) for one girder.
    vals[k] is the force at node k: for the i-node of each element and
    the j-node of the last element.
    """
    def get_force(elem, comp):
        return float(ds["forces"].sel(Element=elem, Component=comp).values)

    def find_component(name):
        for c in ds["Component"].values:
            if c.lower() == name.lower():
                return c
        return None

    comp_i = find_component(force_i)
    comp_j = find_component(force_j)

    xs, ys, zs, vals, node_ids = [], [], [], [], []
    for e in elems:
        n1, n2 = members[e]
        x1, y1, z1 = nodes[n1]
        xs.append(x1); ys.append(y1); zs.append(z1)
        vals.append(round(get_force(e, comp_i) / 1000, 3))   # N → kN
        node_ids.append(n1)

    last_e = elems[-1]
    n1, n2 = members[last_e]
    x2, y2, z2 = nodes[n2]
    xs.append(x2); ys.append(y2); zs.append(z2)
    vals.append(round(get_force(last_e, comp_j) / 1000, 3))   # N → kN
    node_ids.append(n2)

    return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids


# =============================================================================
# DRAWING HELPERS (matplotlib 3-D)
# =============================================================================

def _add_grillage_background(ax, nodes, members, x_tol=3, z_tol=3):
    """
    Draw the structural grid by grouping nodes rather than tracing element tags.

    • Longitudinal lines  — nodes sharing the same z-position connected in x-order.
    • Transverse lines    — nodes sharing the same x-position connected in z-order.

    This guarantees that transverse connections are visible regardless of how
    ospgrillage numbers its elements or the current camera angle.
    """
    from collections import defaultdict

    # round keys to avoid floating-point scatter
    by_z = defaultdict(list)   # z_key → [x, ...]
    by_x = defaultdict(list)   # x_key → [z, ...]

    for coord in nodes.values():
        rx = round(coord[0], x_tol)
        rz = round(coord[2], z_tol)
        by_z[rz].append(coord[0])
        by_x[rx].append(coord[2])

    long_kw  = dict(color="darkgrey", linewidth=0.8, alpha=0.5, zorder=1)
    trans_kw = dict(color="slategrey", linewidth=1.8, alpha=0.8, zorder=1)

    # longitudinal lines (along span)
    for z_val, x_vals in by_z.items():
        x_sorted = sorted(set(x_vals))
        if len(x_sorted) > 1:
            ax.plot(x_sorted, [z_val] * len(x_sorted), [0] * len(x_sorted), **long_kw)

    # transverse lines (across width)
    for x_val, z_vals in by_x.items():
        z_sorted = sorted(set(z_vals))
        if len(z_sorted) > 1:
            ax.plot([x_val] * len(z_sorted), z_sorted, [0] * len(z_sorted), **trans_kw)


def _add_coordinate_triad(ax, nodes, scale=0.12):
    """Draw X / Y / Z arrows and labels with professional, distortion-free CAD aesthetics."""
    xs = [c[0] for c in nodes.values()]
    ys = [c[1] for c in nodes.values()]
    zs = [c[2] for c in nodes.values()]

    span = max(max(xs) - min(xs), max(zs) - min(zs)) or 5000
    L = span * scale

    ox, oy, oz = min(xs), 0, min(zs)

    # Deeper, high-contrast CAD colors
    # Professional Non-Clashing Palette: Deep Orange (X), Purple (Y), Teal (Z)
    colors = {"X": "#E65100", "Y": "#0097A7", "Z": "#6A1B9A"}
    tag = "coord_triad" 

    # Add a bold origin anchor dot
    ax.scatter([ox], [oz], [oy], color="#333333", s=40, zorder=6, gid=tag)

    # X-Axis (Span)
    ax.plot([ox, ox + L], [oz, oz], [oy, oy], color=colors["X"], linewidth=2.5, zorder=5, gid=tag)
    ax.scatter([ox + L], [oz], [oy], color=colors["X"], marker='>', s=50, zorder=6, gid=tag, depthshade=False)
    ax.text(ox + L * 1.25, oz, oy, "X", color=colors["X"], fontsize=10, fontweight="bold", zorder=6, gid=tag)

    # Z-Axis (Transverse width)
    ax.plot([ox, ox], [oz, oz + L], [oy, oy], color=colors["Z"], linewidth=2.5, zorder=5, gid=tag)
    ax.scatter([ox], [oz + L], [oy], color=colors["Z"], marker='^', s=50, zorder=6, gid=tag, depthshade=False)
    ax.text(ox, oz + L * 1.25, oy, "Z", color=colors["Z"], fontsize=10, fontweight="bold", zorder=6, gid=tag)

    # Y-Axis (Vertical)
    Ly = L * 3.0 
    ax.plot([ox, ox], [oz, oz], [oy, oy + Ly], color=colors["Y"], linewidth=2.5, zorder=5, gid=tag)
    ax.scatter([ox], [oz], [oy + Ly], color=colors["Y"], marker='^', s=50, zorder=6, gid=tag, depthshade=False)
    ax.text(ox, oz, oy + Ly * 1.15, "Y", color=colors["Y"], fontsize=10, fontweight="bold", zorder=6, gid=tag)
    
def _add_supports(ax, nodes, members, edge_dist=0.0):
    """Draw pin (diamond) and roller (circle) supports at the ends of girders."""
    girders = _find_girders(nodes, members)
    girder_items = list(girders.items())
    n_girders = len(girder_items)

    pin_x, pin_z = [], []
    rol_x, rol_z = [], []

    for i, (z_val, elems) in enumerate(girder_items):
        if not elems: continue
        
        # Skip placing supports on edge beams if an overhang exists!
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        if is_edge_beam:
            continue

        n_left = members[elems[0]][0]
        n_right = members[elems[-1]][1]

        pin_x.append(nodes[n_left][0])
        pin_z.append(nodes[n_left][2])

        rol_x.append(nodes[n_right][0])
        rol_z.append(nodes[n_right][2])

    # Pinned supports (Left side) -> Green Diamond
    ax.scatter(pin_x, pin_z, np.zeros_like(pin_x), marker='D', s=70,
               color='#7CB342', edgecolors='black', linewidths=1.5,
               zorder=6, depthshade=False, gid="supports")

    # Roller supports (Right side) -> Yellow Circle
    ax.scatter(rol_x, rol_z, np.zeros_like(rol_x), marker='o', s=70,
               color='#FBC02D', edgecolors='black', linewidths=1.5,
               zorder=6, depthshade=False, gid="supports")


# =============================================================================
# GRILLAGE PLOT
# =============================================================================

def build_figure_grillage(nodes, members, edge_dist=0.0):
    """
    Build a 3-D matplotlib figure showing only the bridge grillage mesh.

    Parameters
    ----------
    nodes   : dict  — {tag: [x, y, z]}
    members : dict  — {tag: [n1, n2]}

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax  = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    ax.set_xlim(min(all_xs), max(all_xs))
    ax.set_ylim(min(all_zs), max(all_zs))
    ax.set_zlim(-x_range * 0.05, x_range * 0.15)
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(ax, nodes, members)
    _add_coordinate_triad(ax, nodes)
    _add_supports(ax, nodes, members, edge_dist=edge_dist)

    girders = _find_girders(nodes, members)
    girder_items = list(girders.items())
    n_girders = len(girder_items)
    base_color = "#388E3C"

    for i, (z_val, elems) in enumerate(girder_items):
        if not elems: continue
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        n_first = members[elems[0]][0]
        n_last  = members[elems[-1]][1]

        x_start = nodes[n_first][0]
        x_end   = nodes[n_last][0]
        z_base  = nodes[n_first][2]

        # Draw the solid longitudinal line (Grey for edge, Green for inner)
        ax.plot([x_start, x_end], [z_base, z_base], [0, 0],
                color="slategrey" if is_edge_beam else base_color,
                linewidth=1.5, zorder=3)

        # Add the Girder labels (G1, G2, etc.) to the inner beams
        if not is_edge_beam:
            ax.text(x_start - (x_range * 0.02), z_base, 0, f"{girder_name}",
                    color="black", fontsize=11, fontweight="normal",
                    ha="right", va="center", zorder=6,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              alpha=0.8, edgecolor="none"))

    # Extract node IDs and coordinates properly for tracking
    node_ids = list(nodes.keys())
    xs = [nodes[n][0] for n in node_ids]
    ys = [nodes[n][2] for n in node_ids] # The physical Z-coordinate is plotted on the Y-axis here
    
    # Capture the scatter object
    sc = ax.scatter(xs, ys, [0] * len(xs),
                    color="#388E3C", s=14, zorder=4, depthshade=False)

    # Attach the hover cursor specifically for the Grillage view
    # Attach the hover cursor directly to the single Grillage scatter object 'sc'
    if _MPLCURSORS:
        cursor = mplcursors.cursor(sc, hover=True)
        cursor._timers = {}  # A safe dictionary to store active timers

        @cursor.connect("add")
        def on_add(sel):
            # Extract data directly from the lists we built earlier in the function
            idx = sel.index
            nid = node_ids[idx]
            nx = xs[idx]
            nz = ys[idx]  # Remember, physical Z is plotted on the Y-axis here
            
            sel.annotation.set_text(
                f"Node {nid}\nX: {nx:.2f} m\nZ: {nz:.2f} m"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            # ================= TIMER LOGIC =================
            fig = sel.annotation.figure
            timer = fig.canvas.new_timer(interval=6500) 
            timer.single_shot = True
            
            # Store the timer safely in our dictionary using the selection's unique ID
            sel_id = id(sel)
            cursor._timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    if sel in cursor.selections:
                        cursor.remove_selection(sel)
                        fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    # Clean up the dictionary reference to free memory
                    cursor._timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel("", fontsize=10, labelpad=8)
    ax.set_title("Bridge Grillage", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("lightgrey")
    ax.yaxis.pane.set_edgecolor("lightgrey")
    ax.zaxis.pane.set_edgecolor("lightgrey")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig


# =============================================================================
# SFD PLOT
# =============================================================================

def build_figure_sfd(ds, force_key, nodes, members, edge_dist=0.0):
    """
    Build a 3-D matplotlib figure showing the Shear Force Diagram.

    Parameters
    ----------
    ds         : xarray.Dataset  — analysis results (must have 'forces' DataArray)
    force_key  : str             — one of FORCE_MAP keys, e.g. "Fy"
    nodes      : dict            — {tag: [x, y, z]}
    members    : dict            — {tag: [n1, n2]}
    edge_dist  : float           — overhang distance; when > 0 the outermost two
                                   girders are edge beams and are skipped in the
                                   force diagram (their lines remain visible via
                                   the grillage background).

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    disp_key = FORCE_DISPLAY.get(force_key, force_key)
    girders = _find_girders(nodes, members)

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    ax.set_xlim(min(all_xs), max(all_xs))
    ax.set_ylim(min(all_zs), max(all_zs))
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(ax, nodes, members)
    _add_coordinate_triad(ax, nodes)
    _add_supports(ax, nodes, members, edge_dist=edge_dist)

    shear_color = "#1565C0"
    fill_color  = "#90CAF9"
    base_color  = "#388E3C"

    girder_items  = list(girders.items())
    n_girders     = len(girder_items)
    _scatter_objs = []
    _scatter_data = {}

    for i, (z_val, elems) in enumerate(girder_items):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        xs, ys, zs, Vy, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        # The j-end force from OpenSees uses the opposite sign convention.
        # Negate the last value so the rightmost node shows the correct shear.
        Vy = Vy.copy()
        Vy[-1] = -Vy[-1]

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # baseline (solid) - grey for edge beams, green for structural
        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color="slategrey" if is_edge_beam else base_color,
                linewidth=1.5, zorder=3)

        # edge beams: baseline only, no markers / label / force diagram
        if is_edge_beam:
            continue

        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=18, zorder=4, depthshade=False)

        # girder label
        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=11, fontweight="normal",
                ha="right", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.8, edgecolor="none"))

        # val_range = max(Vy) - min(Vy)
        # if val_range == 0:
        #     shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        # else:
        #     shear_scale = 0.25 * abs((max(xs) - min(xs)) / val_range)

        x_step  = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step  = Vy_step 
        z_step  = np.full_like(x_step, z_base)

        ax.plot_surface(
            np.vstack([x_step, x_step]),
            np.vstack([z_step, z_step]),
            np.vstack([np.zeros_like(y_step), y_step]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        # shear step line
        ax.plot(x_step, z_step, y_step, color=shear_color, linewidth=2.0, zorder=4)

        # vertical cliff lines
        for xi, vyi in zip(xs, Vy):
            ax.plot([xi, xi], [z_base, z_base], [0, vyi],
                    color=shear_color, linewidth=1.2, alpha=0.7, zorder=3)
        for xi, vyi in zip(xs, Vy):
            ax.text(xi, z_base, vyi, f" {vyi:.2f}", color="#666666", fontsize=6, zorder=5, gid="all_vals")

        sc = ax.scatter(xs, z_arr, Vy,
                        color=shear_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_ids, xs, Vy)

    # hover annotations
    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        cursor._timers = {}  # THE FIX: A safe dictionary to store active timers

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} kN"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            fig = sel.annotation.figure
            timer = fig.canvas.new_timer(interval=6500) 
            timer.single_shot = True
            
            # Store the timer safely in our dictionary using the selection's unique ID
            sel_id = id(sel)
            cursor._timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    if sel in cursor.selections:
                        cursor.remove_selection(sel)
                        fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    # Clean up the dictionary reference to free memory
                    cursor._timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_key} (kN)", fontsize=10, labelpad=8)
    ax.set_title(f"Shear Force Diagram  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    # Professional, high-contrast bounding box borders
    ax.xaxis.pane.set_edgecolor("#555555")
    ax.yaxis.pane.set_edgecolor("#555555")
    ax.zaxis.pane.set_edgecolor("#555555")
    ax.xaxis.pane.set_linewidth(1.5)
    ax.yaxis.pane.set_linewidth(1.5)
    ax.zaxis.pane.set_linewidth(1.5)
    ax.xaxis.pane.set_alpha(1.0)
    ax.yaxis.pane.set_alpha(1.0)
    ax.zaxis.pane.set_alpha(1.0)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig


# =============================================================================
# BMD PLOT
# =============================================================================

def build_figure_bmd(ds, force_key, nodes, members, edge_dist=0.0):
    """
    Build a 3-D matplotlib figure showing the Bending Moment Diagram.

    Parameters
    ----------
    ds         : xarray.Dataset  — analysis results (must have 'forces' DataArray)
    force_key  : str             — one of FORCE_MAP keys, e.g. "Mz"
    nodes      : dict            — {tag: [x, y, z]}
    members    : dict            — {tag: [n1, n2]}
    edge_dist  : float           — overhang distance; when > 0 the outermost two
                                   girders are edge beams and are skipped in the
                                   force diagram (their lines remain visible via
                                   the grillage background).

    Returns
    -------
    fig          : matplotlib.figure.Figure
    summary_data : dict  — {girder_name: {"max": float, "min": float}}
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    disp_key = FORCE_DISPLAY.get(force_key, force_key)
    girders = _find_girders(nodes, members)

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    ax.set_xlim(min(all_xs), max(all_xs))
    ax.set_ylim(min(all_zs), max(all_zs))
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(ax, nodes, members)
    _add_coordinate_triad(ax, nodes)
    _add_supports(ax, nodes, members, edge_dist=edge_dist)

    moment_color = "#C62828"
    fill_color   = "#EF9A9A"
    base_color   = "#388E3C"

    girder_items_bmd = list(girders.items())
    n_girders_bmd    = len(girder_items_bmd)
    summary_data  = {}
    _scatter_objs = []
    _scatter_data = {}

    for i, (z_val, elems) in enumerate(girder_items_bmd):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders_bmd - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        xs, ys, zs, Mz, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # baseline (solid) - grey for edge beams, green for structural
        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color="slategrey" if is_edge_beam else base_color,
                linewidth=1.5, zorder=3)

        # edge beams: baseline only, no markers / label / force diagram
        if is_edge_beam:
            continue

        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=18, zorder=4, depthshade=False)

        # girder label
        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=11, fontweight="normal",
                ha="right", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.8, edgecolor="none"))

        # val_range = max(Mz) - min(Mz)
        # if val_range == 0:
        #     moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        # else:
        #     moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = -Mz   # negate: positive moment plots downward

        ax.plot_surface(
            np.vstack([xs, xs]),
            np.vstack([z_arr, z_arr]),
            np.vstack([np.zeros_like(y_plot), y_plot]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        ax.plot(xs, z_arr, y_plot, color=moment_color, linewidth=2.0, zorder=4)

        # Max line (Dashed, Tagged for toggling)
        idx_max = int(np.argmax(Mz))
        ax.plot([xs[idx_max], xs[idx_max]], [z_base, z_base], [0, y_plot[idx_max]],
                color="#FF4136", linewidth=1.5, linestyle="--", zorder=3, gid="max_line")
        # Bold Dark Grey Text
        ax.text(xs[idx_max], z_base, y_plot[idx_max],
                f" {-Mz[idx_max]:.2f}", color="#333333", fontsize=8, fontweight="bold", zorder=6, gid="max_line")

        # Min line (Dashed, Tagged for toggling)
        idx_min = int(np.argmin(Mz))
        ax.plot([xs[idx_min], xs[idx_min]], [z_base, z_base], [0, y_plot[idx_min]],
                color="#0074D9", linewidth=1.5, linestyle="--", zorder=3, gid="min_line")
        ax.text(xs[idx_min], z_base, y_plot[idx_min],
                f" {-Mz[idx_min]:.2f}", color="#333333", fontsize=8, fontweight="bold", zorder=6, gid="min_line")

        # 'All' values annotations (Slightly lighter grey, Tagged for toggling)
        for xi, yi, mzi in zip(xs, y_plot, Mz):
            ax.text(xi, z_base, yi, f" {-mzi:.2f}", color="#555555", fontsize=7, zorder=5, gid="all_vals")

        sc = ax.scatter(xs, z_arr, y_plot,
                        color=moment_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_ids, xs, Mz)

        summary_data[girder_name] = {"max": float(max(Mz)), "min": float(min(Mz))}

    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        cursor._timers = {}  # THE FIX: A safe dictionary to store active timers

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} kN"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            fig = sel.annotation.figure
            timer = fig.canvas.new_timer(interval=6500) 
            timer.single_shot = True
            
            # Store the timer safely in our dictionary using the selection's unique ID
            sel_id = id(sel)
            cursor._timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    if sel in cursor.selections:
                        cursor.remove_selection(sel)
                        fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    # Clean up the dictionary reference to free memory
                    cursor._timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_key} (kNm)", fontsize=10, labelpad=8)
    ax.zaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{abs(val):g}"))
    ax.set_title(f"Bending Moment Diagram  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    # Professional, high-contrast bounding box borders
    ax.xaxis.pane.set_edgecolor("#555555")
    ax.yaxis.pane.set_edgecolor("#555555")
    ax.zaxis.pane.set_edgecolor("#555555")
    ax.xaxis.pane.set_linewidth(1.5)
    ax.yaxis.pane.set_linewidth(1.5)
    ax.zaxis.pane.set_linewidth(1.5)
    ax.xaxis.pane.set_alpha(1.0)
    ax.yaxis.pane.set_alpha(1.0)
    ax.zaxis.pane.set_alpha(1.0)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig, summary_data


# =============================================================================
# BMD CONTOUR PLOT
# =============================================================================

def build_figure_bmd_contour(ds, force_key, nodes, members, edge_dist=0.0):
    """
    Build a 3-D matplotlib figure showing the BMD with a Jet colour-map
    scaled to the global moment range across all girders.

    Parameters
    ----------
    ds         : xarray.Dataset
    force_key  : str
    nodes      : dict
    members    : dict
    edge_dist  : float  — overhang distance; when > 0 the outermost two
                          girders are edge beams and are skipped in the
                          force diagram (their lines remain visible via
                          the grillage background).

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    disp_key = FORCE_DISPLAY.get(force_key, force_key)
    girders = _find_girders(nodes, members)

    girder_items_cnt = list(girders.items())
    n_girders_cnt    = len(girder_items_cnt)

    # Global moment range - exclude edge beams from colour scale
    all_vals = []
    for i, (_, elems) in enumerate(girder_items_cnt):
        if edge_dist > 0 and (i == 0 or i == n_girders_cnt - 1):
            continue
        _, _, _, mz, _ = _build_polyline(elems, members, nodes, comp_i_name, comp_j_name, ds)
        all_vals.extend(mz.tolist())
    vmin, vmax = min(all_vals), max(all_vals)
    if vmin == vmax:
        vmin -= 1.0; vmax += 1.0

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = plt.colormaps["jet"]

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax  = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    ax.set_xlim(min(all_xs), max(all_xs))
    ax.set_ylim(min(all_zs), max(all_zs))
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(ax, nodes, members)
    _add_coordinate_triad(ax, nodes)
    _add_supports(ax, nodes, members, edge_dist=edge_dist)

    base_color = "#388E3C"

    for i, (z_val, elems) in enumerate(girder_items_cnt):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders_cnt - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        xs, ys, zs, Mz, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # baseline - grey for edge beams, green for structural
        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color="slategrey" if is_edge_beam else base_color,
                linewidth=1.5, linestyle="--", zorder=3)

        # edge beams: baseline only, no label or force diagram
        if is_edge_beam:
            continue

        # girder label
        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=11, fontweight="normal",
                ha="right", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.8, edgecolor="none"))

        # val_range = max(Mz) - min(Mz)
        # if val_range == 0:
        #     moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        # else:
        #     moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = Mz 

        face_colors = cmap(norm(np.vstack([Mz, Mz])))
        ax.plot_surface(
            np.vstack([xs, xs]),
            np.vstack([z_arr, z_arr]),
            np.vstack([np.zeros_like(y_plot), y_plot]),
            facecolors=face_colors, alpha=0.35, linewidth=0,
            antialiased=False, zorder=2
        )

        pts  = np.column_stack([xs, z_arr, y_plot])          # (N, 3)
        segs = np.stack([pts[:-1], pts[1:]], axis=1)          # (N-1, 2, 3)
        seg_colors = cmap(norm((Mz[:-1] + Mz[1:]) / 2))
        lc = Line3DCollection(segs, colors=seg_colors, linewidths=3, zorder=4)
        ax.add_collection3d(lc)

        # coloured drop lines at each node
        for xi, zi, mzi, ypi in zip(xs, z_arr, Mz, y_plot):
            ax.plot([xi, xi], [zi, zi], [0, ypi],
                    color=cmap(norm(mzi)), linewidth=1.0, alpha=0.7, zorder=3)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.1, aspect=20)
    cbar.set_label(f"{disp_key}", fontsize=10)

    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_key} (kNm)", fontsize=10, labelpad=8)
    ax.set_title(f"BMD Contour  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    # Professional, high-contrast bounding box borders
    ax.xaxis.pane.set_edgecolor("#555555")
    ax.yaxis.pane.set_edgecolor("#555555")
    ax.zaxis.pane.set_edgecolor("#555555")
    ax.xaxis.pane.set_linewidth(1.5)
    ax.yaxis.pane.set_linewidth(1.5)
    ax.zaxis.pane.set_linewidth(1.5)
    ax.xaxis.pane.set_alpha(1.0)
    ax.yaxis.pane.set_alpha(1.0)
    ax.zaxis.pane.set_alpha(1.0)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig


# =============================================================================
# DEFLECTION PLOT
# =============================================================================

def build_figure_deflection(ds, disp_key, nodes, members, edge_dist=0.0):
    """
    Build a 3-D matplotlib figure showing the Deflection Diagram.

    Parameters
    ----------
    ds         : xarray.Dataset  — analysis results for one load case
                                   (must have 'displacements' DataArray keyed
                                    by Node and Component)
    disp_key   : str             — one of DISP_MAP keys: "Dx", "Dy", "Dz"
    nodes      : dict            — {tag: [x, y, z]}
    members    : dict            — {tag: [n1, n2]}
    edge_dist  : float           — overhang distance; outermost girders are
                                   shown as baselines only (no diagram).

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    comp_name  = DISP_MAP[disp_key]
    disp_label = DISP_DISPLAY.get(disp_key, disp_key)
    girders    = _find_girders(nodes, members)

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax  = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    ax.set_xlim(min(all_xs), max(all_xs))
    ax.set_ylim(min(all_zs), max(all_zs))
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(ax, nodes, members)
    _add_coordinate_triad(ax, nodes)
    _add_supports(ax, nodes, members, edge_dist=edge_dist)

    defl_color = "#6A1B9A"   # deep purple
    fill_color = "#CE93D8"   # light purple
    base_color = "#388E3C"

    # Resolve the actual component string in the dataset (case-insensitive)
    actual_comp = None
    try:
        for c in ds["displacements"].coords["Component"].values:
            if c.lower() == comp_name.lower():
                actual_comp = c
                break
    except Exception:
        pass

    girder_items = list(girders.items())
    n_girders    = len(girder_items)
    _scatter_objs = []
    _scatter_data = {}

    for i, (z_val, elems) in enumerate(girder_items):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        # Node list in span order (mirrors _build_polyline ordering)
        node_list = [members[e][0] for e in elems] + [members[elems[-1]][1]]
        xs = np.array([nodes[n][0] for n in node_list])
        zs = np.array([nodes[n][2] for n in node_list])

        # Fetch nodal displacement (m → mm); fall back to 0 on missing data
        def _get(n, _comp=actual_comp):
            if _comp is None:
                return 0.0
            try:
                return float(
                    ds["displacements"].sel(Node=n, Component=_comp).values
                ) * 1000.0
            except Exception:
                return 0.0

        vals  = np.array([_get(n) for n in node_list])
        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # baseline
        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color="slategrey" if is_edge_beam else base_color,
                linewidth=1.5, zorder=3)

        if is_edge_beam:
            continue

        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=18, zorder=4, depthshade=False)

        # girder label
        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=11, fontweight="normal",
                ha="right", va="center", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          alpha=0.8, edgecolor="none"))

        # val_range = max(vals) - min(vals)
        # if val_range == 0:
        #     defl_scale = (
        #         1.0 if np.max(np.abs(vals)) == 0
        #         else 0.1 * abs((max(xs) - min(xs)) / np.max(np.abs(vals)))
        #     )
        # else:
        #     defl_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = vals 

        ax.plot_surface(
            np.vstack([xs, xs]),
            np.vstack([z_arr, z_arr]),
            np.vstack([np.zeros_like(y_plot), y_plot]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        ax.plot(xs, z_arr, y_plot, color=defl_color, linewidth=2.0, zorder=4)

        # annotate the node with maximum absolute deflection
        idx_max = int(np.argmax(np.abs(vals)))
        ax.plot([xs[idx_max], xs[idx_max]], [z_base, z_base], [0, y_plot[idx_max]],
                color=defl_color, linewidth=1.5, linestyle="--", zorder=3, gid="max_line")
        ax.text(xs[idx_max], z_base, y_plot[idx_max],
                f" {vals[idx_max]:.3f} mm", color="#4A4A4A", fontsize=7, fontweight="bold", zorder=6, gid="max_line")

        # 'All' values annotations (Tagged for toggling)
        for xi, yi, val in zip(xs, y_plot, vals):
            ax.text(xi, z_base, yi, f" {val:.3f}", color="#666666", fontsize=6, zorder=5, gid="all_vals")

        sc = ax.scatter(xs, z_arr, y_plot,
                        color=defl_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_list, xs, vals)

    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        cursor._timers = {}  # THE FIX: A safe dictionary to store active timers

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} kN"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            fig = sel.annotation.figure
            timer = fig.canvas.new_timer(interval=6500) 
            timer.single_shot = True
            
            # Store the timer safely in our dictionary using the selection's unique ID
            sel_id = id(sel)
            cursor._timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    if sel in cursor.selections:
                        cursor.remove_selection(sel)
                        fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    # Clean up the dictionary reference to free memory
                    cursor._timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_label} (mm)", fontsize=10, labelpad=8)
    ax.set_title(f"Deflection Diagram  —  {disp_label}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    # Professional, high-contrast bounding box borders
    ax.xaxis.pane.set_edgecolor("#555555")
    ax.yaxis.pane.set_edgecolor("#555555")
    ax.zaxis.pane.set_edgecolor("#555555")
    ax.xaxis.pane.set_linewidth(1.5)
    ax.yaxis.pane.set_linewidth(1.5)
    ax.zaxis.pane.set_linewidth(1.5)
    ax.xaxis.pane.set_alpha(1.0)
    ax.yaxis.pane.set_alpha(1.0)
    ax.zaxis.pane.set_alpha(1.0)
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig


def figure_to_bytes(fig, fmt="png", dpi=150):
    """Convenience helper — render a matplotlib figure to raw bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches=None, facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return buf.read()
