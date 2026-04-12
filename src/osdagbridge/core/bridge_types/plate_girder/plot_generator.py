import io
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
        vals.append(round(get_force(e, comp_i), 3))
        node_ids.append(n1)

    last_e = elems[-1]
    n1, n2 = members[last_e]
    x2, y2, z2 = nodes[n2]
    xs.append(x2); ys.append(y2); zs.append(z2)
    vals.append(round(get_force(last_e, comp_j), 3))
    node_ids.append(n2)

    return np.array(xs), np.array(ys), np.array(zs), np.array(vals), node_ids


# =============================================================================
# DRAWING HELPERS (matplotlib 3-D)
# =============================================================================

def _add_grillage_background(ax, nodes, members):
    """Draw all elements as thin dark-grey lines (structural grid)."""
    for ele, (n1, n2) in members.items():
        x1, _, z1 = nodes[n1]
        x2, _, z2 = nodes[n2]
        ax.plot([x1, x2], [z1, z2], [0, 0],
                color="darkgrey", linewidth=0.8, alpha=0.6, zorder=1)


def _add_coordinate_triad(ax, nodes, scale=0.10):
    """Draw X / Y / Z arrows and labels at the minimum-corner of the model."""
    xs = [c[0] for c in nodes.values()]
    ys = [c[1] for c in nodes.values()]
    zs = [c[2] for c in nodes.values()]

    span = max(max(xs) - min(xs), max(zs) - min(zs)) or 5000
    L = span * scale

    ox, oy, oz = min(xs), 0, min(zs)          # triad origin

    colors = {"X": "#FF4136", "Y": "#2ECC40", "Z": "#0074D9"}

    # X arrow (along span)
    ax.quiver(ox, oz, oy, L, 0, 0,
              color=colors["X"], linewidth=2, arrow_length_ratio=0.25, zorder=5)
    ax.text(ox + L * 1.25, oz, oy, "X", color=colors["X"],
            fontsize=9, fontweight="bold", zorder=5)

    # Z arrow (along width) — note ax.plot uses (x=span, y=width, z=force)
    ax.quiver(ox, oz, oy, 0, L, 0,
              color=colors["Z"], linewidth=2, arrow_length_ratio=0.25, zorder=5)
    ax.text(ox, oz + L * 1.25, oy, "Z", color=colors["Z"],
            fontsize=9, fontweight="bold", zorder=5)

    # Y arrow (upward = force direction)
    ax.quiver(ox, oz, oy, 0, 0, L,
              color=colors["Y"], linewidth=2, arrow_length_ratio=0.25, zorder=5)
    ax.text(ox, oz, oy + L * 1.25, "Y", color=colors["Y"],
            fontsize=9, fontweight="bold", zorder=5)


# =============================================================================
# SFD PLOT
# =============================================================================

def build_figure_sfd(ds, force_key, nodes, members):
    """
    Build a 3-D matplotlib figure showing the Shear Force Diagram.

    Parameters
    ----------
    ds         : xarray.Dataset  — analysis results (must have 'forces' DataArray)
    force_key  : str             — one of FORCE_MAP keys, e.g. "Fy"
    nodes      : dict            — {tag: [x, y, z]}
    members    : dict            — {tag: [n1, n2]}

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
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

    shear_color = "#1565C0"
    fill_color  = "#90CAF9"
    base_color  = "#388E3C"

    girder_items  = list(girders.items())
    _scatter_objs = []
    _scatter_data = {}

    for i, (z_val, elems) in enumerate(girder_items):
        girder_name = f"G{i + 1}"

        xs, ys, zs, Vy, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        val_range = max(Vy) - min(Vy)
        if val_range == 0:
            shear_scale = 1.0 if max(Vy) == 0 else 0.25 * abs((max(xs) - min(xs)) / max(Vy))
        else:
            shear_scale = 0.25 * abs((max(xs) - min(xs)) / val_range)

        x_step  = np.repeat(xs, 2)[1:-1]
        Vy_step = np.repeat(Vy[:-1], 2)
        y_step  = Vy_step * shear_scale
        z_step  = np.full_like(x_step, z_base)

        ax.plot_surface(
            np.vstack([x_step, x_step]),
            np.vstack([z_step, z_step]),
            np.vstack([np.zeros_like(y_step), y_step]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        ax.plot(x_step, z_step, y_step, color=shear_color, linewidth=2.0, zorder=4)

        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color=base_color, linewidth=1.5, zorder=3)
        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=18, zorder=4, depthshade=False)

        for xi, vyi in zip(xs, Vy):
            ax.plot([xi, xi], [z_base, z_base], [0, vyi * shear_scale],
                    color=shear_color, linewidth=1.2, alpha=0.7, zorder=3)

        sc = ax.scatter(xs, z_arr, Vy * shear_scale,
                        color=shear_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_ids, xs, Vy)

        ax.text(xs[0], z_base, 0, f" {girder_name}",
                color="black", fontsize=8, fontweight="bold",
                ha="left", va="bottom", zorder=6)

    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=force_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f}"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

    ax.set_xlabel("Span Length", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{force_key} (scaled)", fontsize=10, labelpad=8)
    ax.set_title(f"Shear Force Diagram  —  {force_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("lightgrey")
    ax.yaxis.pane.set_edgecolor("lightgrey")
    ax.zaxis.pane.set_edgecolor("lightgrey")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    return fig


# =============================================================================
# BMD PLOT
# =============================================================================

def build_figure_bmd(ds, force_key, nodes, members):
    """
    Build a 3-D matplotlib figure showing the Bending Moment Diagram.

    Parameters
    ----------
    ds         : xarray.Dataset  — analysis results (must have 'forces' DataArray)
    force_key  : str             — one of FORCE_MAP keys, e.g. "Mz"
    nodes      : dict            — {tag: [x, y, z]}
    members    : dict            — {tag: [n1, n2]}

    Returns
    -------
    fig          : matplotlib.figure.Figure
    summary_data : dict  — {girder_name: {"max": float, "min": float}}
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
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

    moment_color = "#C62828"
    fill_color   = "#EF9A9A"
    base_color   = "#388E3C"

    summary_data  = {}
    _scatter_objs = []
    _scatter_data = {}

    for i, (z_val, elems) in enumerate(girders.items()):
        girder_name = f"G{i + 1}"

        xs, ys, zs, Mz, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        val_range = max(Mz) - min(Mz)
        if val_range == 0:
            moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = -Mz * moment_scale   # negate: positive moment plots downward

        ax.plot_surface(
            np.vstack([xs, xs]),
            np.vstack([z_arr, z_arr]),
            np.vstack([np.zeros_like(y_plot), y_plot]),
            color=fill_color, alpha=0.25, linewidth=0, antialiased=False, zorder=2
        )

        ax.plot(xs, z_arr, y_plot, color=moment_color, linewidth=2.0, zorder=4)

        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color=base_color, linewidth=1.5, zorder=3)
        ax.scatter(xs, z_arr, np.zeros_like(xs),
                   color=base_color, s=18, zorder=4, depthshade=False)

        idx_max = int(np.argmax(Mz))
        idx_min = int(np.argmin(Mz))
        for idx, clr in ((idx_max, "#FF4136"), (idx_min, "#0074D9")):
            ax.plot([xs[idx], xs[idx]], [z_base, z_base], [0, y_plot[idx]],
                    color=clr, linewidth=1.5, zorder=3)
            ax.text(xs[idx], z_base, y_plot[idx],
                    f" {Mz[idx]:.2f}", color=clr, fontsize=7, zorder=6)

        sc = ax.scatter(xs, z_arr, y_plot,
                        color=moment_color, s=30, zorder=5, depthshade=False)
        _scatter_objs.append(sc)
        _scatter_data[id(sc)] = (node_ids, xs, Mz)

        ax.text(xs[0], z_base, 0, f" {girder_name}",
                color="black", fontsize=8, fontweight="bold",
                ha="left", va="bottom", zorder=6)

        summary_data[girder_name] = {"max": float(max(Mz)), "min": float(min(Mz))}

    if _MPLCURSORS and _scatter_objs:
        cursor = mplcursors.cursor(_scatter_objs, hover=True)

        @cursor.connect("add")
        def on_add(sel, _data=_scatter_data, _fk=force_key):
            nids, xs_g, vals_g = _data[id(sel.artist)]
            idx = sel.index
            sel.annotation.set_text(
                f"Node {nids[idx]}\nX: {xs_g[idx]:.2f}\n{_fk}: {vals_g[idx]:.3f}"
            )
            sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

    ax.set_xlabel("Span Length", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{force_key} (scaled)", fontsize=10, labelpad=8)
    ax.set_title(f"Bending Moment Diagram  —  {force_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("lightgrey")
    ax.yaxis.pane.set_edgecolor("lightgrey")
    ax.zaxis.pane.set_edgecolor("lightgrey")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    return fig, summary_data


# =============================================================================
# BMD CONTOUR PLOT
# =============================================================================

def build_figure_bmd_contour(ds, force_key, nodes, members):
    """
    Build a 3-D matplotlib figure showing the BMD with a Jet colour-map
    scaled to the global moment range across all girders.

    Parameters
    ----------
    ds         : xarray.Dataset
    force_key  : str
    nodes      : dict
    members    : dict

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    comp_i_name, comp_j_name = FORCE_MAP[force_key]
    girders = _find_girders(nodes, members)

    # Global moment range for a consistent colour scale
    all_vals = []
    for elems in girders.values():
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

    base_color = "#388E3C"

    for i, (z_val, elems) in enumerate(girders.items()):
        girder_name = f"G{i + 1}"

        xs, ys, zs, Mz, node_ids = _build_polyline(
            elems, members, nodes, comp_i_name, comp_j_name, ds
        )

        z_base = float(np.mean(zs))
        z_arr  = np.full_like(xs, z_base)

        val_range = max(Mz) - min(Mz)
        if val_range == 0:
            moment_scale = 1.0 if max(Mz) == 0 else 0.1 * abs((max(xs) - min(xs)) / max(Mz))
        else:
            moment_scale = 0.1 * abs((max(xs) - min(xs)) / val_range)

        y_plot = Mz * moment_scale

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

        ax.plot([xs[0], xs[-1]], [z_base, z_base], [0, 0],
                color=base_color, linewidth=1.5, linestyle="--", zorder=3)

        for xi, zi, mzi, ypi in zip(xs, z_arr, Mz, y_plot):
            ax.plot([xi, xi], [zi, zi], [0, ypi],
                    color=cmap(norm(mzi)), linewidth=1.0, alpha=0.7, zorder=3)

        ax.text(xs[0], z_base, 0, f" {girder_name}",
                color="black", fontsize=8, fontweight="bold",
                ha="left", va="bottom", zorder=6)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.1, aspect=20)
    cbar.set_label(f"{force_key}", fontsize=10)

    ax.set_xlabel("Span Length", fontsize=10, labelpad=8)
    ax.set_ylabel("Bridge Width", fontsize=10, labelpad=8)
    ax.set_zlabel(f"{force_key} (scaled)", fontsize=10, labelpad=8)
    ax.set_title(f"BMD Contour  —  {force_key}", fontsize=12, fontweight="bold", pad=12)
    ax.view_init(elev=DEFAULT_ELEV, azim=DEFAULT_AZIM)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("lightgrey")
    ax.yaxis.pane.set_edgecolor("lightgrey")
    ax.zaxis.pane.set_edgecolor("lightgrey")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    return fig


def figure_to_bytes(fig, fmt="png", dpi=150):
    """Convenience helper — render a matplotlib figure to raw bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    plt.close(fig)
    return buf.read()
