import io
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MaxNLocator
import numpy as np
import openseespy.opensees as ops
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from mpl_toolkits.mplot3d import proj3d
from matplotlib.text import Annotation
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


def _value_plot_scale(eng_scale):
    """Clamp engineering scale factor used for diagram geometry (0 = flat diagram)."""
    try:
        return max(0.0, float(eng_scale))
    except (TypeError, ValueError):
        return 1.0


def _set_value_axis_tick_formatter(ax, eng_scale, value_sign: float = 1.0, use_abs: bool = False):
    """
    Format value-axis ticks as real engineering units while data coords stay scaled.

    Matplotlib tick locations are in *scaled* coordinates; real value is:
      real_value = value_sign * (scaled_value / scale)
    """
    scale = _value_plot_scale(eng_scale)
    if scale < 1e-12:
        ax.zaxis.set_major_formatter(FuncFormatter(lambda val, pos: "0"))
        return

    s = float(scale)
    sign = float(value_sign)

    def fmt(val, pos, sv=s, sgn=sign, abs_flag=use_abs):
        real_v = sgn * (val / sv)
        if abs_flag:
            real_v = abs(real_v)
        return f"{real_v:g}"

    ax.zaxis.set_major_formatter(FuncFormatter(fmt))


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

def _add_grillage_background(
    ax,
    nodes,
    members,
    x_tol=3,
    z_tol=3,
    show_transverse=False,
    include_edge_longitudinals=True,
    include_end_transverse=True,
    show_inner_nodes=True,
):
        """
        Draw the structural grid by grouping nodes rather than tracing element tags.
        """
        from collections import defaultdict

        by_z = defaultdict(list)   # z_key → [x, ...]
        by_x = defaultdict(list)   # x_key → [z, ...]

        for coord in nodes.values():
            rx = round(coord[0], x_tol)
            rz = round(coord[2], z_tol)
            by_z[rz].append(coord[0])
            by_x[rx].append(coord[2])

        # ==========================================
        # 1. THE LINES (Transparent Green & Grey)
        # ==========================================
        # Original structural green (#388E3C) but 70% transparent (alpha=0.3)
        long_kw  = dict(color="#388E3C", linewidth=1.0, alpha=0.3, zorder=1)
        
        # Soft grey for the transverse cross-beams (alpha=0.4)
        trans_kw = dict(color="slategrey", linewidth=1.2, alpha=0.4, zorder=1)

        # longitudinal lines (along span)
        z_keys = sorted(by_z.keys())
        edge_z_min = z_keys[0] if z_keys else None
        edge_z_max = z_keys[-1] if z_keys else None
        for z_val, x_vals in by_z.items():
            if not include_edge_longitudinals and z_val in (edge_z_min, edge_z_max):
                continue
            x_sorted = sorted(set(x_vals))
            if len(x_sorted) > 1:
                ax.plot(x_sorted, [z_val] * len(x_sorted), [0] * len(x_sorted), **long_kw)

        if by_x:  # Quick safety check to ensure we have data
            min_x = min(by_x.keys())
            max_x = max(by_x.keys())

            for x_val, z_vals in by_x.items():
                # Check if this specific line is at the absolute start or end of the bridge
                is_end_line = (x_val == min_x or x_val == max_x)

                # Draw it if the Master Switch is ON, OR if it's an end line AND allowed
                if show_transverse or (include_end_transverse and is_end_line):
                    z_sorted = sorted(set(z_vals))
                    if len(z_sorted) > 1:
                        ax.plot([x_val] * len(z_sorted), z_sorted, [0] * len(z_sorted), **trans_kw)
        # ==========================================
        # 3. THE DOTS (Sniper Fix for Z-Fighting)
        # ==========================================
        if show_inner_nodes:
            inner_xs, inner_zs, inner_ys = [], [], []
            if by_x:
                min_x = min(by_x.keys())
                max_x = max(by_x.keys())
                # Only collect dots that are NOT at the absolute ends of the bridge
                for coord in nodes.values():
                    if coord[0] != min_x and coord[0] != max_x:
                        inner_xs.append(coord[0])
                        inner_zs.append(coord[2])
                        inner_ys.append(0) # Base elevation
                ax.scatter(inner_xs, inner_zs, inner_ys, color="#388E3C", alpha=0.4, s=5, zorder=2, depthshade=False)

class Arrow3D(Annotation):
    def __init__(self, start, end, *args, **kwargs):
        super().__init__("", xy=(0, 0), xytext=(0, 0), *args, **kwargs)
        self._start = start
        self._end = end

    def draw(self, renderer):
        x1, y1, z1 = self._start
        x2, y2, z2 = self._end
        
        x1p, y1p, _ = proj3d.proj_transform(x1, y1, z1, self.axes.get_proj())
        x2p, y2p, _ = proj3d.proj_transform(x2, y2, z2, self.axes.get_proj())
        
        self.xy = (x2p, y2p)
        self.set_position((x1p, y1p))
        super().draw(renderer)

def _draw_camera_arrow(ax, start, end, color, lw=2.2, gid=None):
    """Draw a clean camera-facing arrow that dynamically updates in 3D."""
    arrow = Arrow3D(
        start, end,
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=lw,
            mutation_scale=15,
            shrinkA=0,
            shrinkB=0
        ),
        annotation_clip=False
    )
    if gid:
        arrow.set_gid(gid)
    ax.add_artist(arrow)





def _add_coordinate_triad(ax, nodes, scale=0.12, eng_scale: float = 1.0):
    """Draw X/Y/Z axes with 3‑D arrowheads.

    ``eng_scale`` is the engineering‑scale factor applied to the *value* axis
    (Matplotlib **Z**, which we treat as Y).  The original implementation drew
    the Z‑arrow using raw data units, so when the value axis was scaled the
    arrow grew/shrank together with the plotted data.  By dividing the Z‑arrow
    length by ``eng_scale`` we keep the visual size of the triad constant
    regardless of how the value axis is scaled.
    """
    xs = [c[0] for c in nodes.values()]
    zs = [c[2] for c in nodes.values()]
    
    ox, oy, oz = min(xs), 0, min(zs)
    colors = {"X": "#E65100", "Z": "#0D47A1"}
    tag = "coord_triad"

    ax.scatter([ox], [oz], [oy], color="green", s=40, zorder=6, gid=tag)

    # 1. Capture exact current limits to lock the visual screen space
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    zlim = ax.get_zlim()
    
    xr = abs(xlim[1] - xlim[0])
    yr = abs(ylim[1] - ylim[0])
    zr = abs(zlim[1] - zlim[0])

    # Provide safe fallbacks if the graph is completely empty
    if xr < 1e-3: xr = 25.0
    if yr < 1e-3: yr = 10.0
    if zr < 1e-3: zr = 10.0

    # 2. Fixed Screen Proportions (Stems are 12%, widths are 2.5% of visual space)
    Lx, Lz = xr * scale, zr * scale
    hl_x, hl_z = Lx * 0.30, Lz * 0.30
    w_frac = 0.025

    # --- X-Axis (Span) ---
    # Use only the X-range (span length) so the triad stays the same size
    # regardless of how the value axis (Z) is scaled by eng_scale.
    axis_len = xr * 0.10
    start = (ox, oz, oy)
    end   = (ox + axis_len, oz, oy)
    _draw_camera_arrow(ax, start, end, colors["X"], lw=2.2, gid=tag)
    ax.text(
        end[0] + xr * 0.02, end[1], end[2],
        "X",
        color=colors["X"], fontsize=10, fontweight="bold",
        zorder=7, gid=tag
    )

    # --- Z-Axis (Transverse width, mapped to Matplotlib Y) ---
    # The Z-arrow length must be independent of the engineering scale.
    # ``axis_len`` is expressed in data units; the value axis is scaled by
    # ``eng_scale``.  Dividing by ``eng_scale`` yields a constant visual length.
    z_axis_len = axis_len
    end = (ox, oz + z_axis_len, oy)
    _draw_camera_arrow(ax, start, end, colors["Z"], lw=2.2, gid=tag)
    ax.text(
        end[0], end[1] + yr * 0.03, end[2],
        "Z",
        color=colors["Z"], fontsize=10, fontweight="bold",
        zorder=7, gid=tag
    )

    # 3. CRITICAL FIX: Lock limits so drawing the triad doesn't stretch empty charts!
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_zlim(zlim)
    
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
    ax.scatter(pin_x, pin_z, np.zeros_like(pin_x), marker='^', s=70,
               color='#7CB342', edgecolors='black', linewidths=1.5,
               zorder=1000, depthshade=False, gid="supports")

    # Roller supports (Right side) -> Yellow Circle
    ax.scatter(rol_x, rol_z, np.zeros_like(rol_x), marker='o', s=70,
               color='#FBC02D', edgecolors='black', linewidths=1.5,
               zorder=1000, depthshade=False, gid="supports")



# =============================================================================
# NODE NUMBER LABELS HELPER
# =============================================================================

def _add_node_number_labels(ax, nodes, visible: bool = False):
    """
    Draw the integer node ID as a small text label at each node position.
    All labels are tagged with gid="node_number" so MplPlotWidget can
    show/hide them in bulk without rebuilding the figure.

    Parameters
    ----------
    ax      : mpl_toolkits.mplot3d.axes3d.Axes3D
    nodes   : dict  — {node_id: [x, y, z]}
    visible : bool  — initial visibility (default False, toggled by toolbar)
    """
    for nid, coord in nodes.items():
        x, z, y = coord[0], coord[2], 0.0
        t = ax.text(
            x, z, y,
            f" {nid}",
            fontsize=7,
            color="#1565C0",
            fontweight="normal",
            ha="left",
            va="bottom",
            zorder=8,
            gid="node_number",
        )
        t.set_visible(visible)

# =============================================================================
# ELEMENT NUMBER LABELS HELPER
# =============================================================================

def _add_element_number_labels(ax, nodes, members, visible: bool = False):
    """
    Draw the integer element tag as a small text label at the midpoint of each
    element (average of its two end-node positions, at y=0).

    All labels are tagged with gid="element_number" so MplPlotWidget can
    show/hide them in bulk without rebuilding the figure.

    DATA SOURCE
    -----------
    nodes   : dict  — {node_id: [x, y, z]}  (from results_data._build_nodes_members)
    members : dict  — {element_id: [n1, n2]} (from results_data._build_nodes_members)

    Parameters
    ----------
    ax      : mpl_toolkits.mplot3d.axes3d.Axes3D
    nodes   : dict  — {node_id: [x, y, z]}
    members : dict  — {element_id: [n1, n2]}
    visible : bool  — initial visibility (default False, toggled by toolbar)
    """
    for eid, (n1, n2) in members.items():
        c1 = nodes.get(n1)
        c2 = nodes.get(n2)
        if c1 is None or c2 is None:
            continue
        mx = (c1[0] + c2[0]) / 2.0
        mz = (c1[2] + c2[2]) / 2.0  # physical Z plotted on Matplotlib Y-axis
        t = ax.text(
            mx, mz, 0.0,
            f" E{eid}",
            fontsize=6,
            color="#BF360C",          # deep orange — distinct from node blue
            fontweight="normal",
            ha="center",
            va="top",
            zorder=7,
            gid="element_number",
        )
        t.set_visible(visible)


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

    _add_grillage_background(ax, nodes, members, show_transverse=True, include_end_transverse=True)
    _add_coordinate_triad(ax, nodes)
    

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
                    color="black", fontsize=13, fontweight="normal",
                    ha="right", va="center", zorder=6, gid="girder_labels")

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
    _add_supports(ax, nodes, members, edge_dist=edge_dist)
    _add_node_number_labels(ax, nodes)
    _add_element_number_labels(ax, nodes, members)  # hidden by default; toggled by toolbar
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
    # fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    return fig


# =============================================================================
# SFD PLOT
# =============================================================================

def build_figure_sfd(ds, force_key, nodes, members, edge_dist=0.0, eng_scale=1.0):
    """
    Build a 3-D matplotlib figure showing the Shear Force Diagram.
    """
    v_scale = _value_plot_scale(eng_scale)
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    disp_key = FORCE_DISPLAY.get(force_key, force_key)
    girders = _find_girders(nodes, members)

    # Use muted gray/slate for standard non-active node values
    standard_gray = "#455A64"

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    
    x_min, x_max = min(all_xs), max(all_xs)
    z_min, z_max = min(all_zs), max(all_zs)
    
    x_pad = (x_max - x_min) * 0.05 if (x_max - x_min) != 0 else 1.0
    z_pad = (z_max - z_min) * 0.05 if (z_max - z_min) != 0 else 1.0
    
    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(z_min - z_pad, z_max + z_pad)
    ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    _add_grillage_background(
        ax, nodes, members,
        show_transverse=False,
        include_edge_longitudinals=False,
        include_end_transverse=False,
        show_inner_nodes=False,
    )
    
    shear_color = "#1565C0"
    fill_color  = "#90CAF9"
    base_color  = "#388E3C"

    girder_items  = list(girders.items())
    n_girders     = len(girder_items)
    _scatter_objs = []
    _scatter_data = {}

    summary_data = {}
    # Track global scaled value range for z-limits so 0 stays a visible baseline
    # and the 3D "grid" can expand/shrink with v_scale.
    global_vmin = 0.0
    global_vmax = 0.0

    for i, (z_val, elems) in enumerate(girder_items):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        xs, ys, zs, Vy, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        Vy = Vy.copy()
        Vy[-1] = -Vy[-1]
        Vy_geom = Vy * v_scale
        if (not is_edge_beam) and Vy_geom.size:
            global_vmin = min(global_vmin, float(np.min(Vy_geom)))
            global_vmax = max(global_vmax, float(np.max(Vy_geom)))

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        if is_edge_beam:
            continue

        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=5, zorder=4, depthshade=False, alpha=0.4)

        dynamic_zorder = 100 - i  
        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=13, ha="right", va="center",
                zorder=dynamic_zorder, gid="girder_labels")

        x_step  = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy_geom[:-1], 2)
        y_step  = Vy_step
        z_step  = np.full_like(x_step, z_base)

        ax.plot_surface(
            np.vstack([x_step, x_step]),
            np.vstack([z_step, z_step]),
            np.vstack([np.zeros_like(y_step), y_step]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        ax.plot(x_step, z_step, y_step, color=shear_color, linewidth=2.0, zorder=4)

        for xi, vyi_geom in zip(xs, Vy_geom):
            ax.plot([xi, xi], [z_base, z_base], [0, vyi_geom],
                    color=shear_color, linewidth=1.2, alpha=0.7, zorder=3)

        sc = ax.scatter(xs, z_arr, Vy_geom,
                        color=shear_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_ids, xs, Vy)

        if len(Vy) > 0:
            idx_max = int(np.argmax(Vy))
            idx_min = int(np.argmin(Vy))

            summary_data[girder_name] = {
                "max": float(Vy[idx_max]),
                "min": float(Vy[idx_min])
            }

            # ==========================================
            # CLEANED Extreme Value Logic (Nodes and Text)
            # ==========================================
            
            # Use Prominent BLACK (like BMD) for extreme node highlights and text
            extreme_align_color = "black"

            # Max Node Highlight and Text (Highest Positive)
            ax.plot([xs[idx_max]], [z_base], [Vy_geom[idx_max]],
                    marker="o", markersize=9, color=extreme_align_color, markeredgecolor="white", markeredgewidth=1.5, 
                    linestyle="None", zorder=10, gid="max_line")
            
            # CLEAN: Removed "Max:" prefix.
            ax.text(xs[idx_max], z_base, Vy_geom[idx_max], f" {Vy[idx_max]:.3f} kN",
                    color=extreme_align_color, fontsize=7, fontweight="bold", ha="left", va="bottom", zorder=11,
                    gid="max_line", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"))

            # Min Node Highlight and Text (Lowest Negative)
            ax.plot([xs[idx_min]], [z_base], [Vy_geom[idx_min]],
                    marker="o", markersize=9, color=extreme_align_color, markeredgecolor="white", markeredgewidth=1.5, 
                    linestyle="None", zorder=10, gid="min_line")
            
            # CLEAN: Removed "Min:" prefix.
            ax.text(xs[idx_min], z_base, Vy_geom[idx_min], f" {Vy[idx_min]:.3f} kN",
                    color=extreme_align_color, fontsize=7, fontweight="bold", ha="right", va="top", zorder=11,
                    gid="min_line", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"))

            # "All" Values Staggered Labels (Muted Gray)
            for j in range(len(xs)):
                if abs(Vy[j]) > 1e-4: 
                    if j == idx_max or j == idx_min:
                        continue
                        
                    v_align = "bottom" if j % 2 == 0 else "top"
                    h_align = "left" if i % 2 == 0 else "right" 

                    ax.text(xs[j], z_base, Vy_geom[j], 
                            f" {Vy[j]:.3f} kN", 
                            color=standard_gray, fontsize=7, ha=h_align, va=v_align, zorder=6, 
                            gid="all_vals", bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7, edgecolor="none"))

    # ==========================================
    # Hover Annotations (With Garbage-Collection Fix)
    # ==========================================
    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        
        # 🚨 THE FIX: Attach cursor and timers to the figure so Python's 
        # Garbage Collector doesn't delete them the moment the function ends!
        fig._custom_cursor = cursor
        fig._hover_timers = {}

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} kN"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9, edgecolor="#BBBBBB")

            # 1. Stop any existing timer for this specific hover box to prevent glitching
            sel_id = id(sel)
            if sel_id in fig._hover_timers:
                fig._hover_timers[sel_id].stop()

            # 2. Create the new 6.5-second timer
            timer = fig.canvas.new_timer(interval=3000) 
            timer.single_shot = True
            fig._hover_timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    # Safely hide the text box visually instead of fighting mplcursors internal arrays
                    sel.annotation.set_visible(False)
                    fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    fig._hover_timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    _add_supports(ax, nodes, members, edge_dist=edge_dist)
    _add_node_number_labels(ax, nodes)
    _add_element_number_labels(ax, nodes, members)  # hidden by default; toggled by toolbar
    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_key} (kN)", fontsize=10, labelpad=8)
    _set_value_axis_tick_formatter(ax, v_scale)
    # Keep baseline at 0 and let z-limits expand/shrink with v_scale.
    zmin = min(0.0, global_vmin)
    zmax = max(0.0, global_vmax)
    z_span = max(1e-9, zmax - zmin)
    pad = max(1e-6, 0.05 * z_span)
    ax.set_zlim(zmin - pad, zmax + pad)
    # IMPORTANT: rescale the 3D grid height so the diagram does not get stuck
    # inside the same cube for different v_scale values.
    ax.set_box_aspect([x_range, z_range, (x_range * 0.30) * max(v_scale, 1e-6)])
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
    ax.set_title(f"Shear Force Diagram  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    fig._eng_scale = v_scale
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
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

    _add_coordinate_triad(ax, nodes, eng_scale=v_scale)
    ax.set_axis_off()

    return fig, summary_data

# =============================================================================
# BMD PLOT
# =============================================================================

def build_figure_bmd(ds, force_key, nodes, members, edge_dist=0.0, eng_scale=1.0):
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
    v_scale = _value_plot_scale(eng_scale)
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

    _add_grillage_background(
        ax, nodes, members,
        show_transverse=False,
        include_edge_longitudinals=False,
        include_end_transverse=False,
        show_inner_nodes=False,
    )

    moment_color = "#C62828"
    fill_color   = "#EF9A9A"
    base_color   = "#388E3C"

    girder_items_bmd = list(girders.items())
    n_girders_bmd    = len(girder_items_bmd)
    summary_data  = {}
    _scatter_objs = []
    _scatter_data = {}

    # Track global scaled z-range for baseline at 0 and cube resizing.
    global_vmin = 0.0
    global_vmax = 0.0
    for i, (z_val, elems) in enumerate(girder_items_bmd):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders_bmd - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        xs, ys, zs, Mz, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # baseline (solid) - grey for edge beams, green for structural
        # ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
        #         color="slategrey" if is_edge_beam else base_color,
        #         linewidth=1.0, alpha=0.3, zorder=3)

        # edge beams: baseline only, no markers / label / force diagram
        if is_edge_beam:
            continue

        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=5, zorder=4, depthshade=False, alpha=0.4)

        # girder label
        # 1. Reverse the stack: G1 (i=0) gets zorder 100, G2 gets 99, etc.
        dynamic_zorder = 100 - i  
        

        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=13, ha="right", va="center",
                zorder=dynamic_zorder, gid="girder_labels")

        # val_range = max(Mz) - min(Mz)
        # if val_range == 0:
        #     moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        # else:
        #     moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = -Mz * v_scale   # negate: positive moment plots downward
        if y_plot.size:
            global_vmin = min(global_vmin, float(np.min(y_plot)))
            global_vmax = max(global_vmax, float(np.max(y_plot)))

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
                f" {Mz[idx_max]:.2f}", color="#333333", fontsize=8, fontweight="bold", zorder=6, gid="max_line",
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.0))

        # Min line (Dashed, Tagged for toggling)
        idx_min = int(np.argmin(Mz))
        ax.plot([xs[idx_min], xs[idx_min]], [z_base, z_base], [0, y_plot[idx_min]],
                color="#0074D9", linewidth=1.5, linestyle="--", zorder=3, gid="min_line")
        ax.text(xs[idx_min], z_base, y_plot[idx_min],
                f" {Mz[idx_min]:.2f}", color="#333333", fontsize=8, fontweight="bold", zorder=6, gid="min_line",
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.0))

        # 'All' values annotations (Slightly lighter grey, Tagged for toggling)
        for xi, yi, mzi in zip(xs, y_plot, Mz):
            ax.text(xi, z_base, yi, f" {mzi:.2f}", color="#555555", fontsize=7, zorder=5, gid="all_vals")

        # Slicing [1:-1] strips away the first and last dots so the supports stay clean!
        sc = ax.scatter(xs[1:-1], z_arr[1:-1], y_plot[1:-1],
                        color=moment_color, s=30, zorder=5, depthshade=False)
        
        _scatter_objs.append(sc)
        
        # CRITICAL: You must slice the hover data too, or the tooltip will show the wrong node!
        _scatter_data[id(sc)] = (node_ids[1:-1], xs[1:-1], Mz[1:-1])

        summary_data[girder_name] = {"max": float(max(Mz)), "min": float(min(Mz))}

    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        cursor._timers = {}  # THE FIX: A safe dictionary to store active timers

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            
            # 1. Dynamically assign the correct engineering unit
            if _fk.startswith("M") or _fk.startswith("T"):
                unit = "kNm"  # Moment and Torsion
            elif _fk.startswith("D"):
                unit = "mm"   # Deflection/Displacement
            else:
                unit = "kN"   # Shear and Axial Forces (F, V)

            # 2. Apply the dynamic unit to the text
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} {unit}"
            )
            
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

            fig = sel.annotation.figure
            timer = fig.canvas.new_timer(interval=3000)
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
    _add_supports(ax, nodes, members, edge_dist=edge_dist)
    _add_node_number_labels(ax, nodes)
    _add_element_number_labels(ax, nodes, members)  # hidden by default; toggled by toolbar
    ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{disp_key} (kNm)", fontsize=10, labelpad=8)
    # z-coordinate is y_plot = -Mz * v_scale, so real Mz = -(z / scale)
    _set_value_axis_tick_formatter(ax, v_scale, value_sign=-1.0, use_abs=True)

    zmin = min(0.0, global_vmin)
    zmax = max(0.0, global_vmax)
    z_span = max(1e-9, zmax - zmin)
    pad = max(1e-6, 0.05 * z_span)
    ax.set_zlim(zmin - pad, zmax + pad)
    ax.set_box_aspect([x_range, z_range, (x_range * 0.30) * max(v_scale, 1e-6)])
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
    ax.set_title(f"Bending Moment Diagram  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    fig._eng_scale = v_scale
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
    _add_coordinate_triad(ax, nodes, eng_scale=v_scale)
    ax.set_axis_off()
    return fig, summary_data


# =============================================================================
# BMD CONTOUR PLOT
# =============================================================================

# def build_figure_bmd_contour(ds, force_key, nodes, members, edge_dist=0.0):
    # """
    # Build a 3-D matplotlib figure showing the BMD with a Jet colour-map
    # scaled to the global moment range across all girders.

    # Parameters
    # ----------
    # ds         : xarray.Dataset
    # force_key  : str
    # nodes      : dict
    # members    : dict
    # edge_dist  : float  — overhang distance; when > 0 the outermost two
    #                       girders are edge beams and are skipped in the
    #                       force diagram (their lines remain visible via
    #                       the grillage background).

    # Returns
    # -------
    # fig : matplotlib.figure.Figure
    # """
    # comp_i_name, comp_j_name = FORCE_MAP[force_key]
    # disp_key = FORCE_DISPLAY.get(force_key, force_key)
    # girders = _find_girders(nodes, members)

    # girder_items_cnt = list(girders.items())
    # n_girders_cnt    = len(girder_items_cnt)

    # Global moment range - exclude edge beams from colour scale
    # all_vals = []
    # for i, (_, elems) in enumerate(girder_items_cnt):
    #     if edge_dist > 0 and (i == 0 or i == n_girders_cnt - 1):
    #         continue
    #     _, _, _, mz, _ = _build_polyline(elems, members, nodes, comp_i_name, comp_j_name, ds)
    #     all_vals.extend(mz.tolist())
    # vmin, vmax = min(all_vals), max(all_vals)
    # if vmin == vmax:
    #     vmin -= 1.0; vmax += 1.0

    # norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    # cmap = plt.colormaps["jet"]

    # fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    # ax  = fig.add_subplot(111, projection="3d", facecolor="white")

    # all_xs = [coord[0] for coord in nodes.values()]
    # all_zs = [coord[2] for coord in nodes.values()]
    # x_range = max(all_xs) - min(all_xs) or 1.0
    # z_range = max(all_zs) - min(all_zs) or 1.0
    # ax.set_xlim(min(all_xs), max(all_xs))
    # ax.set_ylim(min(all_zs), max(all_zs))
    # ax.set_box_aspect([x_range, z_range, x_range * 0.30])

    # _add_grillage_background(
    #     ax, nodes, members,
    #     include_edge_longitudinals=False,
    #     include_end_transverse=False,
    #     show_inner_nodes=False,
    # )
    # _add_coordinate_triad(ax, nodes, eng_scale=1.0)
    # _add_supports(ax, nodes, members, edge_dist=edge_dist)

    # base_color = "#388E3C"

    # for i, (z_val, elems) in enumerate(girder_items_cnt):
    #     is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders_cnt - 1)
    #     girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

    #     xs, ys, zs, Mz, node_ids = _build_polyline(
    #         elems, members, nodes, comp_i_name, comp_j_name, ds
    #     )

    #     z_base = float(np.mean(zs))
    #     z_arr  = np.full_like(xs, z_base)

        # baseline - grey for edge beams, green for structural
        # ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
        #         color="slategrey" if is_edge_beam else base_color,
        #         linewidth=1.5, linestyle="--", zorder=3)

        # edge beams: baseline only, no label or force diagram
        # if is_edge_beam:
        #     continue

        # girder label
        # ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
        #         color="black", fontsize=13, fontweight="normal",
        #         ha="right", va="center", zorder=6, gid="girder_labels")

        # val_range = max(Mz) - min(Mz)
        # if val_range == 0:
        #     moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        # else:
        #     moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        # y_plot = Mz 

        # face_colors = cmap(norm(np.vstack([Mz, Mz])))
        # ax.plot_surface(
        #     np.vstack([xs, xs]),
        #     np.vstack([z_arr, z_arr]),
        #     np.vstack([np.zeros_like(y_plot), y_plot]),
        #     facecolors=face_colors, alpha=0.35, linewidth=0,
        #     antialiased=False, zorder=2
        # )

        # pts  = np.column_stack([xs, z_arr, y_plot])          # (N, 3)
        # segs = np.stack([pts[:-1], pts[1:]], axis=1)          # (N-1, 2, 3)
        # seg_colors = cmap(norm((Mz[:-1] + Mz[1:]) / 2))
        # lc = Line3DCollection(segs, colors=seg_colors, linewidths=3, zorder=4)
        # ax.add_collection3d(lc)

        # coloured drop lines at each node
        # for xi, zi, mzi, ypi in zip(xs, z_arr, Mz, y_plot):
        #     ax.plot([xi, xi], [zi, zi], [0, ypi],
        #             color=cmap(norm(mzi)), linewidth=1.0, alpha=0.7, zorder=3)

    # sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    # sm.set_array([])
    # cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.1, aspect=20)
    # cbar.set_label(f"{disp_key}", fontsize=10)

    # ax.set_xlabel("Span Length (m)", fontsize=10, labelpad=8)
    # ax.set_ylabel("Bridge Width (m)", fontsize=10, labelpad=8)
    # ax.set_zlabel(f"{disp_key} (kNm)", fontsize=10, labelpad=8)
    # ax.set_title(f"BMD Contour  —  {disp_key}", fontsize=12, fontweight="bold", pad=12)
    # ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    # ax.xaxis.pane.fill = False
    # ax.yaxis.pane.fill = False
        # ax.zaxis.pane.fill = False
        # # Professional, high-contrast bounding box borders
        # ax.xaxis.pane.set_edgecolor("#555555")
        # ax.yaxis.pane.set_edgecolor("#555555")
        # ax.zaxis.pane.set_edgecolor("#555555")
        # ax.xaxis.pane.set_linewidth(1.5)
        # ax.yaxis.pane.set_linewidth(1.5)
        # ax.zaxis.pane.set_linewidth(1.5)
        # ax.xaxis.pane.set_alpha(1.0)
        # ax.yaxis.pane.set_alpha(1.0)
        # ax.zaxis.pane.set_alpha(1.0)
        # ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    # Force the 3D plot to use the maximum available canvas space
    # Dedicate 18% of the right side purely to the massive axis labels.
    # This naturally shoves the 3D bridge perfectly into the center of the screen!
    # fig.subplots_adjust(left=0.05, right=0.88, bottom=0.05, top=0.90)
    # return fig


# =============================================================================
# DEFLECTION PLOT
# =============================================================================

def build_figure_deflection(ds, disp_key, nodes, members, edge_dist=0.0, eng_scale=1.0):
    """
    Build a 3-D matplotlib figure showing the Deflection Diagram.
    """
    v_scale = _value_plot_scale(eng_scale)
    comp_name  = DISP_MAP[disp_key]
    disp_label = DISP_DISPLAY.get(disp_key, disp_key)
    girders    = _find_girders(nodes, members)

    fig = plt.figure(figsize=(14, 6), dpi=110, facecolor="white")
    ax  = fig.add_subplot(111, projection="3d", facecolor="white")

    all_xs = [coord[0] for coord in nodes.values()]
    all_zs = [coord[2] for coord in nodes.values()]
    x_range = max(all_xs) - min(all_xs) or 1.0
    z_range = max(all_zs) - min(all_zs) or 1.0
    
    # Rigid 3D bounding box (matches our UI zoom fix)
    ax.set_box_aspect(aspect=(2.5, 1.2, 1.0))

    _add_grillage_background(
        ax, nodes, members,
        show_transverse=False,
        include_edge_longitudinals=False,
        include_end_transverse=False,
        show_inner_nodes=False,
    )

    defl_color = "#6A1B9A"   # deep purple
    base_color = "#388E3C"   # green baseline

    # =========================================================
    # PHASE 1: FOOLPROOF DATA EXTRACTION (ospgrillage Mapping)
    # =========================================================
    disp_dict = {}
    actual_comp = None
    
    # 1A. Map UI input (Dx, Dy) to the correct static displacement key (x, y)
    # This prevents us from accidentally grabbing the 'velocity' components!
    _DISP_COMPONENT_MAP = {
        "dx": "x", "dy": "y", "dz": "z",
        "Dx": "x", "Dy": "y", "Dz": "z"
    }
    target_ds_key = _DISP_COMPONENT_MAP.get(comp_name, comp_name)
    
    try:
        available_comps = [str(c) for c in ds["displacements"].coords["Component"].values]
        
        for c in available_comps:
            if str(c).lower() == target_ds_key.lower():
                actual_comp = c
                break
                
    except Exception as e:
        print(f"[DEBUG] Error reading components: {e}")

    # 1B. Extract node values into the dictionary
    if actual_comp is not None:
        try:
            for node_id in ds["displacements"].coords["Node"].values:
                val = float(ds["displacements"].sel(Node=node_id, Component=actual_comp).values)
                
                # Apply the engineering sign flip for vertical sag (Y or Z axis)
                if actual_comp.lower() in ["y", "z"]:
                    val = -val 
                    
                disp_dict[str(int(node_id))] = val * 1000.0  # Convert to mm
                
        except Exception as e:
            print(f"🚨 [CRITICAL ERROR] Extraction crashed: {e}")
    else:
        print(f"[DEBUG] 🚨 CRITICAL: Target '{target_ds_key}' not found in dataset!")

    # =========================================================
    # PHASE 2: PLOTTING THE DIAGRAM
    # =========================================================
    girder_items = list(girders.items())
    n_girders    = len(girder_items)
    _scatter_objs = []
    _scatter_data = {}
    summary_data = {}
    # Track global scaled z-range for baseline at 0 and cube resizing.
    global_vmin = 0.0
    global_vmax = 0.0

    for i, (z_val, elems) in enumerate(girder_items):
        is_edge_beam = edge_dist > 0 and (i == 0 or i == n_girders - 1)
        girder_name  = f"G{i}" if edge_dist > 0 else f"G{i + 1}"

        node_list = [members[e][0] for e in elems] + [members[elems[-1]][1]]
        xs = np.array([nodes[n][0] for n in node_list])
        zs = np.array([nodes[n][2] for n in node_list])

        # Fetch from our safe dictionary (defaults to 0.0 if missing)
        vals  = np.array([disp_dict.get(str(int(n)), 0.0) for n in node_list])
        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        # Draw Baseline
        # ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
        #         color="slategrey" if is_edge_beam else base_color,
        #         linewidth=1.0, alpha=0.3, zorder=3)

        if is_edge_beam:
            continue

        # Draw Girder Label
        # 1. Reverse the stack: G1 (i=0) gets zorder 100, G2 gets 99, etc.
        dynamic_zorder = 100 - i  
        

        ax.text(xs[0] - (x_range * 0.02), z_base, 0, f"{girder_name}",
                color="black", fontsize=13, ha="right", va="center",
                zorder=dynamic_zorder, gid="girder_labels")

        y_plot = vals * v_scale
        if y_plot.size:
            global_vmin = min(global_vmin, float(np.min(y_plot)))
            global_vmax = max(global_vmax, float(np.max(y_plot)))

        # Draw thick deflection line (NO plot_surface fill!)
        ax.plot(xs, z_arr, y_plot, color=defl_color, linewidth=2.5, zorder=4)

        # Draw Nodes (Pure Black)
        sc = ax.scatter(xs[1:-1], z_arr[1:-1], y_plot[1:-1], color="black", s=30, zorder=5, depthshade=False)
        
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_list[1:-1], xs[1:-1], vals[1:-1])
        if not is_edge_beam and len(vals) > 0:
            summary_data[girder_name] = {
                "max": float(np.max(vals)), # Uplift / Least sag
                "min": float(np.min(vals))  # Maximum downward deflection
            }

        # Annotate maximum deflection
        if len(vals) > 0 and np.max(np.abs(vals)) > 0:
            idx_max = int(np.argmin(vals))  # Finds the most negative value (Maximum Sag)
            idx_min = int(np.argmax(vals))

            for j in range(len(xs)):
                if abs(vals[j]) > 1e-4: 
                    
                    # 🚨 THE CRITICAL FIX: Skip the nodes that already get Bold Max/Min labels!
                    if j == idx_max or j == idx_min:
                        continue
                        
                    # 2. Staggering logic (Keeps regular nodes from touching each other)
                    v_align = "bottom" if j % 2 == 0 else "top"
                    h_align = "left" if i % 2 == 0 else "right" 

                    ax.text(xs[j], z_base, y_plot[j], 
                            f" {vals[j]:.3f} mm", 
                            color="#455A64", 
                            fontsize=7, 
                            ha=h_align, 
                            va=v_align, 
                            zorder=6, 
                            gid="all_vals",
                            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", alpha=0.7, edgecolor="none"))
                    
            # 1. Add gid="max_line" to the dotted line
            ax.plot([xs[idx_max], xs[idx_max]], [z_base, z_base], [0, y_plot[idx_max]],
                    color=defl_color, linewidth=1.5, linestyle="--", zorder=3, gid="max_line")
            
            # 2. Add gid="max_line" to the text label
            ax.text(xs[idx_max], z_base, y_plot[idx_max],
                    f" {vals[idx_max]:.3f} mm", color="#4A4A4A", fontsize=7, fontweight="bold", zorder=6, gid="max_line")
            # 3. Add gid="min_line" to the dotted line
            ax.plot([xs[idx_min], xs[idx_min]], [z_base, z_base], [0, y_plot[idx_min]],
                    color=defl_color, linewidth=1.5, linestyle="--", zorder=3, gid="min_line")
            ax.text(xs[idx_min], z_base, y_plot[idx_min],
                    f" {vals[idx_min]:.3f} mm", color="#4A4A4A", fontsize=7, fontweight="bold", zorder=6, gid="min_line")
        
        

    # =========================================================
    # PHASE 3: FINISHING TOUCHES (Hover, Supports, Axes)
    # =========================================================
    # ==========================================
    # Hover Annotations (With Garbage-Collection Fix)
    # ==========================================
    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)
        
        # 🚨 THE FIX: Attach cursor and timers to the figure so Python's 
        # Garbage Collector doesn't delete them the moment the function ends!
        fig._custom_cursor = cursor
        fig._hover_timers = {}

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=disp_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f} mm"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9, edgecolor="#BBBBBB")

            # 1. Stop any existing timer for this specific hover box to prevent glitching
            sel_id = id(sel)
            if sel_id in fig._hover_timers:
                fig._hover_timers[sel_id].stop()

            # 2. Create the new 3-second timer
            timer = fig.canvas.new_timer(interval=3000) 
            timer.single_shot = True
            fig._hover_timers[sel_id] = timer 
            
            def auto_hide():
                try:
                    # Safely hide the text box visually instead of fighting mplcursors internal arrays
                    sel.annotation.set_visible(False)
                    fig.canvas.draw_idle()
                except Exception:
                    pass
                finally:
                    fig._hover_timers.pop(sel_id, None)
                    
            timer.add_callback(auto_hide)
            timer.start()

    # CRITICAL: Draw supports absolute last so they sit on top of the black nodes
    _add_supports(ax, nodes, members, edge_dist=edge_dist)
    _add_node_number_labels(ax, nodes)
    _add_element_number_labels(ax, nodes, members)  # hidden by default; toggled by toolbar

    # Robust axes and labels
    ax.set_xlabel("Span Length (m)", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_ylabel("Bridge Width (m)", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_zlabel(f"{disp_label} (mm)", fontsize=10, fontweight="bold", labelpad=8)
    
    from matplotlib.ticker import MaxNLocator
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True, steps=[1, 2, 4, 5, 10]))
    ax.zaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 2.5, 5, 10]))
    _set_value_axis_tick_formatter(ax, v_scale)
    zmin = min(0.0, global_vmin)
    zmax = max(0.0, global_vmax)
    z_span = max(1e-9, zmax - zmin)
    pad = max(1e-6, 0.05 * z_span)
    ax.set_zlim(zmin - pad, zmax + pad)
    ax.set_box_aspect(aspect=(2.5, 1.2, max(v_scale, 1e-6)))
    fig._eng_scale = v_scale

    ax.set_title(f"Deflection Diagram  —  {disp_label}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    
    # Pane styling
    for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        pane.fill = False
        pane.set_edgecolor("#555555")
        pane.set_linewidth(1.5)
        pane.set_alpha(1.0)
        
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    _add_coordinate_triad(ax, nodes, eng_scale=v_scale)
    ax.set_axis_off()
    return fig, summary_data


def figure_to_bytes(fig, fmt="png", dpi=150):
    """Convenience helper — render a matplotlib figure to raw bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches=None, facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return buf.read()
