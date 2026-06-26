"""
Custom 3D CAD Viewer with stable hover highlighting for models and ViewCube.
"""
import math
from PySide6.QtCore import QEvent, QPoint, QRect, QSize, QTimer, Qt
from PySide6.QtGui  import QColor, QFont, QPainter, QPen, QPolygon
from PySide6.QtWidgets import QApplication, QRubberBand, QToolTip, QWidget

from OCC.Display import backend
backend.load_backend("pyside6")

from OCC.Display.qtDisplay import qtViewer3d
from navcube import NavCubeOverlay, NavCubeStyle
from navcube.connectors.occ import OCCNavCubeSync

from osdagbridge.desktop.ui.utils.cad_safety import CADSafetyGuard


# =============================================================================
# OCC-FREE AXIS TRIAD OVERLAY  (drawing is pure QPainter; camera sync via poll)
# =============================================================================

class AxisTriadOverlay(QWidget):
    """
    QPainter-drawn XYZ axis gizmo that stays in sync with the OCC camera.

    COLOURS (user spec)
    --------------------
    X  rgb(217,  26,  26)  red
    Y  rgb(  0,  89,   0)  dark green
    Z  rgb( 26,  26, 217)  blue

    SYNCHRONISATION
    ---------------
    A QTimer fires every _POLL_MS milliseconds and reads three float-tuples
    from V3d_View.Eye / .At / .Up.  From those three vectors the camera's
    Right and Up basis directions are computed in pure Python math, then each
    world axis (X, Y, Z) is projected onto the 2-D screen plane.

    Because the timer reads the SAME V3d_View that OCCNavCubeSync drives, the
    triad is automatically in sync with the NavCube — view snaps, free rotation,
    auto-rotate and any other camera driver all update the triad without any
    extra wiring.

    MATH (verified for front view)
    ------------------------------
    forward  = normalize(At  - Eye)          # camera look direction
    up       = normalize(Up)                 # camera up (from V3d_View)
    right    = normalize(up  × forward)      # camera screen-right

    For a world axis V:
      screen_x = dot(V, right)              → horizontal offset from centre
      screen_y = dot(V, up)                 → vertical   offset (Qt Y-down corrected below)

    Verified front view (Eye on +Y, At at origin, Up = Z):
      forward  = (0,-1, 0),  up = (0,0,1),  right = (1,0,0)
      world X  → screen_x=1, screen_y=0  → points RIGHT   ✓
      world Y  → screen_x=0, screen_y=0  → into screen (dot) ✓
      world Z  → screen_x=0, screen_y=1  → points UP     ✓
    """

    _POLL_MS   = 50     # refresh rate (ms)  ≈ 20 fps, negligible CPU
    _SIZE      = 80     # widget side (logical px)
    _ARM_LEN   = 26     # shaft length (logical px)
    _HEAD_BASE = 7      # arrowhead half-base (logical px)
    _LINE_W    = 2      # shaft line width
    _FONT_SZ   = 9      # axis label point size
    _MARGIN    = 14     # gap from viewer bottom-right corner

    _COL_X = QColor(217,  26,  26)
    _COL_Y = QColor(  0,  89,   0)
    _COL_Z = QColor( 26,  26, 217)

    def __init__(self, viewer_widget, parent=None):
        super().__init__(parent or viewer_widget)
        self._viewer = viewer_widget

        # Host the axis triad as a frameless, translucent top-level overlay
        # window — the SAME way the NavCube avoids a backing box.  A translucent
        # *child* widget over the OpenGL canvas can't composite on Linux, which
        # is why a backing rect (the "box") was previously required.
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.NoDropShadowWindowHint
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground,     True)
        self.setAttribute(Qt.WA_ShowWithoutActivating,     True)
        self.setAttribute(Qt.WA_NoSystemBackground,        True)
        self.setAutoFillBackground(False)

        # Default screen projections — identity (front view, Z-up OCC convention):
        #   X → right,  Y → into screen (near zero),  Z → up
        self._Xx, self._Xy = 1.0, 0.0
        self._Yx, self._Yy = 0.0, 0.0
        self._Zx, self._Zy = 0.0, 1.0

        # Poll timer — started in start(), stopped in stop()
        self._timer = QTimer(self)
        self._timer.setInterval(self._POLL_MS)
        self._timer.timeout.connect(self._sync_from_view)
        self._started = False

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #

    def start(self):
        """Show the widget and begin polling the OCC view orientation."""
        self._started = True
        self._timer.start()
        self.show()
        self.raise_()

    def stop(self):
        """Hide the widget and stop the poll timer."""
        self._started = False
        self._timer.stop()
        self.hide()

    # ------------------------------------------------------------------ #
    #  Camera sync (pure math — no OCC rendering calls)                  #
    # ------------------------------------------------------------------ #

    def _sync_from_view(self):
        """
        Read Eye/At/Up from V3d_View and recompute the 2-D screen projections
        for the X, Y, Z world axes.  No OCC rendering API is touched.
        """
        try:
            view = getattr(self._viewer, "view", None)
            if view is None:
                return

            # 1. Read camera geometry (3 float-tuple reads)
            eye    = view.Eye()   # camera position   (world coords)
            at     = view.At()    # look-at point     (world coords)
            up_raw = view.Up()    # camera up vector  (world coords)

            # 2. Camera forward = normalize(At - Eye)
            fx = float(at[0]) - float(eye[0])
            fy = float(at[1]) - float(eye[1])
            fz = float(at[2]) - float(eye[2])
            fn = math.sqrt(fx*fx + fy*fy + fz*fz) or 1.0
            fx /= fn;  fy /= fn;  fz /= fn

            # 3. Camera up = normalize(Up)
            ux = float(up_raw[0]);  uy = float(up_raw[1]);  uz = float(up_raw[2])
            un = math.sqrt(ux*ux + uy*uy + uz*uz) or 1.0
            ux /= un;  uy /= un;  uz /= un

            # 4. Camera right = normalize(forward × up)
            #    forward × up gives the screen-right direction:
            #    verified: front view (fwd=(0,1,0), up=(0,0,1)) → right=(1,0,0) ✓
            rx = fy*uz - fz*uy
            ry = fz*ux - fx*uz
            rz = fx*uy - fy*ux
            rn = math.sqrt(rx*rx + ry*ry + rz*rz) or 1.0
            rx /= rn;  ry /= rn;  rz /= rn

            # 5. Project each world axis onto screen plane:
            #    screen_x = dot(world_axis, right)
            #    screen_y = dot(world_axis, up)   [used as cy - _Xy*L, so up → smaller Qt-y]
            self._Xx = rx;   self._Xy = ux   # world X = [1,0,0]
            self._Yx = ry;   self._Yy = uy   # world Y = [0,1,0]
            self._Zx = rz;   self._Zy = uz   # world Z = [0,0,1]

            self.update()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Drawing (100 % QPainter)                                          #
    # ------------------------------------------------------------------ #

    def paintEvent(self, event):          # noqa: N802
        p = QPainter(self)

        # Transparent background — only the axis arrows are drawn.
        p.setRenderHint(QPainter.Antialiasing, True)

        cx = cy = self._SIZE // 2
        L  = self._ARM_LEN

        # 2-D tip positions.  Qt Y is positive downward → negate the up component:
        #   tx = cx + screen_x * L
        #   ty = cy - screen_y * L   (up in world → ty < cy → visually above centre)
        # Label → projection mapping:
        #   Display "X"  ← OCC world X  (span,  screen-right)
        #   Display "Y"  ← OCC world Z  (height, screen-up)   ← user wants Y=up
        #   Display "Z"  ← OCC world Y  (depth,  into screen) ← user wants Z=depth
        tips = [
            ("X", self._COL_X,
             cx + round(self._Xx * L),  cy - round(self._Xy * L)),
            ("Y", self._COL_Y,
             cx + round(self._Zx * L),  cy - round(self._Zy * L)),
            ("Z", self._COL_Z,
             cx + round(self._Yx * L),  cy - round(self._Yy * L)),
        ]

        # Back-to-front: axis tips farthest from centre are "behind"
        tips.sort(key=lambda t: -((t[2] - cx) ** 2 + (t[3] - cy) ** 2))

        for label, col, tx, ty in tips:
            self._draw_arrow(p, cx, cy, tx, ty, col, label)

        p.end()

    def _draw_arrow(self, p, ox, oy, tx, ty, col, label):
        """Shaft + filled arrowhead triangle + axis letter."""
        dx, dy = tx - ox, ty - oy
        ln     = math.sqrt(dx * dx + dy * dy) or 1.0
        hs     = self._HEAD_BASE

        # Shaft
        p.setPen(QPen(col, self._LINE_W, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(ox, oy, tx, ty)

        # Arrowhead (filled triangle)
        px = -dy / ln;  py = dx / ln          # unit perpendicular
        bx = tx - round(dx / ln * hs * 1.6)  # base of head
        by = ty - round(dy / ln * hs * 1.6)
        poly = QPolygon([
            QPoint(tx, ty),
            QPoint(round(bx + px * hs * 0.7), round(by + py * hs * 0.7)),
            QPoint(round(bx - px * hs * 0.7), round(by - py * hs * 0.7)),
        ])
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawPolygon(poly)

        # Axis letter (just beyond the arrowhead)
        p.setPen(QPen(col))
        p.setFont(QFont("Arial", self._FONT_SZ, QFont.Bold))
        lx = tx + round(dx / ln * 9)
        ly = ty + round(dy / ln * 9)
        p.drawText(lx - 5, ly + 5, label)

class CustomViewer3d(qtViewer3d):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.context = None
        self.view = None

        self.model_ais_objects = {}
        self.model_hover_labels = {}
        self.ais_to_model = {}
        self.model_hover_labels_by_ais = {}
        self._node_hover_data = []
        self._node_pick_px = 14

        self.current_hovered_model = None
        self.current_hovered_label = None
        self.current_highlighted_ais_list = []
        self.current_highlighted_owner = None

        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(40)
        self.hover_timer.timeout.connect(self.show_tooltip)
        self.hover_position = None

        # Host the overlay as a sibling widget instead of a child of the
        # OCC/OpenGL canvas. This avoids corrupted transparent repaints on Linux.
        overlay_parent = parent if parent is not None else self
        self.navcube = NavCubeOverlay(overlay_parent)
        self.navcube.hide()
        self._overlay_anchor = overlay_parent
        self._navcube_sync: OCCNavCubeSync | None = None  # created once view is ready
        if self._overlay_anchor is not None and self._overlay_anchor is not self:
            self._overlay_anchor.installEventFilter(self)
        self.destroyed.connect(self._teardown_navcube)

        # ---------------- Navigation state ----------------
        self.active_nav_mode = None      # NavMode.ROTATE / PAN / ZOOM_WINDOW
        self.is_dragging_nav = False
        self.last_mouse_pos = None
        self._auto_rotate_timer: QTimer | None = None   # turntable timer

        # Owns the safe context teardown/rebuild policy (see cad_safety.CADSafetyGuard).
        self.safety = CADSafetyGuard(self)
        self._overlay_state = {}

        # Axis triad overlay — parented as a sibling of the OCC canvas so
        # Qt can composit it over the OpenGL surface on all platforms.
        self._axis_triad = AxisTriadOverlay(self, parent=overlay_parent)
        self._axis_triad.hide()

        # ---------------- Zoom-window rubber band ----------------
        self._zoom_win_start: QPoint | None = None
        self._zoom_win_active: bool = False
        self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_navcube()
        self._position_navcube()
        self._position_axis_triad()

    def _resize_navcube(self):
        """Scale the NavCube to a consistent 8% of the viewport in physical pixels.

        style.size is a 96-dpi-equivalent reference pixel value.  _update_dpi
        converts it via:  target_phys = ref_size * physical_dpi / 96.

        To keep the cube at exactly vp_physical * 0.08 physical pixels on every
        screen (regardless of OS zoom level or monitor DPI) we set:
            ref_size = vp_physical * 0.08 * 96 / physical_dpi

        Then _update_dpi computes:
            target_phys = ref_size * physical_dpi / 96 = vp_physical * 0.08  ✓
            new_size    = target_phys / dpr            = vp_logical  * 0.08  ✓

        Padding uses the same 96/physical_dpi factor so it stays proportional.
        """
        if not hasattr(self, "navcube") or not self.navcube:
            return
        vp_logical = min(self.width(), self.height())
        if vp_logical < 10:
            return

        nc = self.navcube
        app = QApplication.instance()
        screen = nc.screen() if nc.isVisible() else None
        if screen is None and app:
            screen = app.primaryScreen()
        dpr = max(1.0, screen.devicePixelRatio()) if screen is not None else 1.0

        physical_dpi = max(72.0, min(screen.physicalDotsPerInch(), 400.0)) if screen else 96.0
        vp_physical = vp_logical * dpr
        ref_size = max(40, min(round(vp_physical * 0.08 * 96.0 / physical_dpi), 90))
        ref_padding = round(10 * 96.0 / physical_dpi)
        ref_scale = round(25.0 * ref_size / 100.0, 2)

        if (nc._style.size == ref_size and nc._style.padding == ref_padding
                and abs(nc._style.scale - ref_scale) < 0.05):
            return
        nc._style.size = ref_size
        nc._style.padding = ref_padding
        nc._style.scale = ref_scale
        nc._update_dpi()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._position_navcube()
        self._position_axis_triad()

    def showEvent(self, event):
        super().showEvent(event)
        self._resize_navcube()
        self._position_navcube()
        self._position_axis_triad()
        if (
            hasattr(self, "navcube") and self.navcube
            and getattr(self, "_navcube_sync", None) is not None
        ):
            QTimer.singleShot(0, self._deferred_show_navcube)
        if hasattr(self, "_axis_triad") and self._axis_triad:
            at = self._axis_triad
            if getattr(at, "_started", False):
                QTimer.singleShot(0, lambda: (at.show(), at.raise_()))

    def _deferred_show_navcube(self):
        self._resize_navcube()
        self._position_navcube()
        self.navcube.show()
        self.navcube.raise_()

    def hideEvent(self, event):
        if hasattr(self, "navcube") and self.navcube:
            self.navcube.hide()
        if hasattr(self, "_axis_triad") and self._axis_triad:
            self._axis_triad.hide()
        super().hideEvent(event)

    def _position_navcube(self):
        if not hasattr(self, "navcube") or not self.navcube:
            return

        host = self.navcube.parentWidget()
        if host is None:
            return

        padding = 10
        local_pos = QPoint(
            max(0, self.width() - self.navcube.width() - padding),
            padding,
        )

        if host is self:
            target_pos = local_pos
        elif self.navcube.isWindow():
            target_pos = self.mapToGlobal(local_pos)
        else:
            global_pos = self.mapToGlobal(local_pos)
            target_pos = host.mapFromGlobal(global_pos)

        self.navcube.move(target_pos)
        if self.navcube.isVisible():
            self.navcube.raise_()

    def _position_axis_triad(self):
        """Place the axis triad in the bottom-right corner of the viewer,
        translated to its parent widget's coordinate system (same logic as
        _position_navcube so it works for any host layout)."""
        if not hasattr(self, "_axis_triad") or not self._axis_triad:
            return
        sz = self._axis_triad._SIZE
        mg = self._axis_triad._MARGIN
        local_pos = QPoint(
            max(0, self.width()  - sz - mg),
            max(0, self.height() - sz - mg),
        )
        host = self._axis_triad.parentWidget()
        if host is None or host is self:
            target_pos = local_pos
        elif self._axis_triad.isWindow():
            target_pos = self.mapToGlobal(local_pos)
        else:
            target_pos = host.mapFromGlobal(self.mapToGlobal(local_pos))
        self._axis_triad.setGeometry(target_pos.x(), target_pos.y(), sz, sz)
        if self._axis_triad.isVisible():
            self._axis_triad.raise_()

    def apply_triad_delta(self, dx: float, dy: float):
        """No-op — kept for compatibility. Triad now syncs via poll timer."""
        pass

    def eventFilter(self, watched, event):
        if watched is getattr(self, "_overlay_anchor", None):
            if event.type() in (
                QEvent.Move,
                QEvent.Resize,
                QEvent.Show,
                QEvent.WindowStateChange,
            ):
                self._position_navcube()
                self._position_axis_triad()
                if hasattr(self, "navcube") and self.navcube and self.navcube.isVisible():
                    self.navcube.raise_()
                if hasattr(self, "_axis_triad") and self._axis_triad and self._axis_triad.isVisible():
                    self._axis_triad.raise_()
        return super().eventFilter(watched, event)

    def set_node_hover_data(self, nodes: list | None) -> None:
        self._node_hover_data = nodes or []

    def _project_to_screen(self, x: float, y: float, z: float):
        """Project a 3D world point to screen pixel coordinates.

        OCC's V3d_View.Convert(X3d, Y3d, Z3d) returns (Xp, Yp) where Yp is
        measured from the **bottom** of the window (OpenGL convention).
        Qt mouse events use Y from the **top**, so we return the OCC value as-is
        and compare against the Y-flipped cursor coordinate in _pick_node_label.
        """
        if not self.view:
            return None
        # Primary: V3d_View.Convert – maps world 3D → window pixel (Y from bottom)
        try:
            res = self.view.Convert(x, y, z)
            if isinstance(res, (tuple, list)) and len(res) >= 2:
                sx, sy = float(res[0]), float(res[1])
                if abs(sx) > 0.0 or abs(sy) > 0.0:
                    return sx, sy
        except Exception:
            pass
        # Fallback: V3d_View.Project – returns normalised device coords
        try:
            res = self.view.Project(x, y, z)
            if isinstance(res, (tuple, list)) and len(res) >= 2:
                vw = float(self.width()) * self.devicePixelRatioF()
                vh = float(self.height()) * self.devicePixelRatioF()
                sx = (float(res[0]) + 1.0) * 0.5 * vw
                sy = (float(res[1]) + 1.0) * 0.5 * vh
                return sx, sy
        except Exception:
            pass
        return None

    def _pick_node_label(self, phys_x: float, phys_y: float,
                         log_x: float, log_y: float) -> str | None:
        """Find the closest grillage node using screen-space projection.

        OCC's Convert() returns Y from the bottom, so we compare against
        (h_phys - phys_y) which mirrors Qt's top-origin cursor Y into OCC's
        bottom-origin space. We try both physical and logical pixel variants.
        """
        if not self._node_hover_data:
            return None

        threshold_sq = self._node_pick_px * self._node_pick_px
        best_label = None
        best_d2 = threshold_sq

        h_phys = float(self.height()) * self.devicePixelRatioF()
        h_log  = float(self.height())

        # OCC Convert Y is from bottom → use (h - y) to flip Qt's top-origin Y
        candidates = [
            (phys_x, h_phys - phys_y),   # physical pixels, OCC Y convention ✓
            (log_x,  h_log  - log_y),    # logical pixels,  OCC Y convention
            (phys_x, phys_y),             # physical, Qt convention (fallback)
            (log_x,  log_y),              # logical,  Qt convention (fallback)
        ]

        for node in self._node_hover_data:
            try:
                sx_sy = self._project_to_screen(node["x"], node["y"], node["z"])
                if not sx_sy:
                    continue
                sx, sy = sx_sy
                for cx, cy in candidates:
                    d2 = (sx - cx) ** 2 + (sy - cy) ** 2
                    if d2 < best_d2:
                        best_d2 = d2
                        best_label = node["label"]
            except Exception:
                continue

        return best_label

    # ------------------------------------------------------------------
    # Mouse Move Event
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        # Do not touch the AIS context while it is being torn down / rebuilt.
        if self.safety.in_progress:
            return

        # ---------------- NAVIGATION MOVE ----------------
        if self.is_dragging_nav and self.active_nav_mode:
            if self.active_nav_mode == NavMode.PAN:
                pr = self.devicePixelRatioF()
                x      = int(event.position().x() * pr)
                y      = int(event.position().y() * pr)
                last_x = int(self.last_mouse_pos.x() * pr)
                last_y = int(self.last_mouse_pos.y() * pr)
                self.view.Pan(x - last_x, -(y - last_y))

            elif self.active_nav_mode == NavMode.ZOOM_WINDOW:
                if self._zoom_win_active and self._zoom_win_start is not None:
                    self._rubber_band.setGeometry(
                        QRect(self._zoom_win_start, event.position().toPoint()).normalized()
                    )

            self.last_mouse_pos = event.position()
            event.accept()
            return

        # Skip hover/raycasting when a mouse button is pressed (OCC drag active)
        if event.buttons() != Qt.NoButton:
            super().mouseMoveEvent(event)
            return


        if not self.context or not self.view:
            super().mouseMoveEvent(event)
            return

        try:
            pr    = self.devicePixelRatioF()
            x_log = float(event.position().x())
            y_log = float(event.position().y())
            x     = int(x_log * pr)
            y     = int(y_log * pr)

            self.context.MoveTo(x, y, self.view, True)

            hovered_model = None
            hovered_label = None

            if self.context.HasDetected():
                detected = None
                detected_list = []

                if hasattr(self.context, "InitDetected"):
                    try:
                        self.context.InitDetected()
                        while self.context.MoreDetected():
                            detected_list.append(self.context.DetectedInteractive())
                            self.context.NextDetected()
                    except Exception:
                        detected_list = []

                if not detected_list:
                    detected_list = [self.context.DetectedInteractive()]

                is_node_hit = False
                for cand in detected_list:
                    if cand in self.model_hover_labels_by_ais:
                        detected = cand
                        hovered_label = self.model_hover_labels_by_ais.get(cand)
                        is_node_hit = True
                        break

                if detected is None and detected_list:
                    detected = detected_list[0]

                # Standard model highlighting
                ptr = self.get_occ_ptr(detected)
                hovered_model = self.ais_to_model.get(ptr)

                objects_to_highlight = []

                if not is_node_hit:
                    if hovered_model in ("Bolt", "Nut"):
                        objects_to_highlight.extend(self.model_ais_objects.get("Bolt", []))
                        objects_to_highlight.extend(self.model_ais_objects.get("Nut", []))
                    elif detected:
                        objects_to_highlight.append(detected)

                if set(objects_to_highlight) != set(self.current_highlighted_ais_list):
                    for obj in self.current_highlighted_ais_list:
                        try:
                            self.context.Unhilight(obj, False)
                        except Exception:
                            pass

                    self.current_highlighted_ais_list = objects_to_highlight

                    for obj in self.current_highlighted_ais_list:
                        try:
                            self.context.HilightWithColor(
                                obj, self.context.HighlightStyle(), False
                            )
                        except Exception:
                            pass

                    self.view.Redraw()

                if hovered_label is None and detected in self.model_hover_labels_by_ais:
                    hovered_label = self.model_hover_labels_by_ais.get(detected)

            else:
                # Nothing detected → cleanup
                if self.current_highlighted_ais_list:
                    for obj in self.current_highlighted_ais_list:
                        try:
                            self.context.Unhilight(obj, False)
                        except Exception:
                            pass
                    self.current_highlighted_ais_list = []
                    self.view.Redraw()

            # Screen-space node hover fallback
            fallback_label = self._pick_node_label(x, y, x_log, y_log)
            if fallback_label:
                hovered_label = fallback_label
                hovered_model = None
                if self.current_highlighted_ais_list:
                    for obj in self.current_highlighted_ais_list:
                        try:
                            self.context.Unhilight(obj, False)
                        except Exception:
                            pass
                    self.current_highlighted_ais_list = []
                    self.view.Redraw()
                if self.hover_position and hovered_label != self.current_hovered_label:
                    self.current_hovered_label = hovered_label
                    self.hover_timer.stop()
                    QToolTip.showText(self.hover_position, hovered_label, self)

            self.hover_position = event.globalPosition().toPoint()
            if (hovered_model != self.current_hovered_model or
                    hovered_label != self.current_hovered_label):
                self.current_hovered_model = hovered_model
                self.current_hovered_label = hovered_label
                if self.current_hovered_model or self.current_hovered_label:
                    self.hover_timer.start(100)
                else:
                    QToolTip.hideText()
            elif hovered_model is None and hovered_label is None:
                QToolTip.hideText()

        except Exception as e:
            print(f"mouseMoveEvent error: {e}")
            QToolTip.hideText()

        super().mouseMoveEvent(event)

    # ------------------------------------------------------------------
    # Tooltip
    # ------------------------------------------------------------------
    def show_tooltip(self):
        if self.safety.in_progress:
            return
        if not self.hover_position:
            return

        if self.current_hovered_label:
            QToolTip.showText(self.hover_position, self.current_hovered_label, self)
            return

        if (
            self.current_hovered_model
            and self.current_hovered_model in self.model_hover_labels
        ):
            QToolTip.showText(
                self.hover_position,
                self.model_hover_labels[self.current_hovered_model],
                self,
            )

    # ------------------------------------------------------------------
    # Leave Event
    # ------------------------------------------------------------------
    def leaveEvent(self, event):
        self.hover_timer.stop()
        self.current_hovered_model = None
        self.current_hovered_label = None

        if self.safety.in_progress:
            return

        if self.current_highlighted_ais_list:
            for obj in self.current_highlighted_ais_list:
                try:
                    self.context.Unhilight(obj, False)
                except Exception:
                    pass
            self.current_highlighted_ais_list = []
            if self.view:
                self.view.Redraw()

        QToolTip.hideText()
        super().leaveEvent(event)

    def cleanup_for_new_model(self):
        # Compat shim: one-shot teardown; rebuilders should use safety.critical_section() directly.
        with self.safety.critical_section():
            self.safety.teardown_model()

    def _pause_overlays(self):
        # Stop overlay/hover timers and record prior state for _resume_overlays (called by the guard).
        state = {}

        at = getattr(self, "_axis_triad", None)
        state["axis"] = bool(at and getattr(at, "_started", False))
        if at is not None:
            try:
                at._timer.stop()
            except Exception:
                pass

        nc = getattr(self, "navcube", None)
        state["navcube"] = bool(nc and nc.isVisible())
        if nc is not None:
            try:
                nc._tmr.stop()
            except Exception:
                pass

        state["auto_rotate"] = self._auto_rotate_timer is not None
        self._stop_auto_rotate()

        try:
            self.hover_timer.stop()
        except Exception:
            pass

        self._overlay_state = state

    def _resume_overlays(self):
        # Restart only the timers that were running when paused (guard clears in_progress).
        state = getattr(self, "_overlay_state", {}) or {}

        at = getattr(self, "_axis_triad", None)
        if at is not None and state.get("axis"):
            try:
                at._timer.start()
            except Exception:
                pass

        nc = getattr(self, "navcube", None)
        if nc is not None and state.get("navcube"):
            try:
                nc._tmr.start()
            except Exception:
                pass

        if state.get("auto_rotate"):
            try:
                self._start_auto_rotate()
            except Exception:
                pass

    def rebuild_ais_lookup_map(self):
        """Rebuilds the fast O(1) hash map mapping C++ pointer addresses to model names."""
        self.ais_to_model = {}
        for model_name, ais_list in self.model_ais_objects.items():
            for ais in ais_list:
                ptr = self.get_occ_ptr(ais)
                self.ais_to_model[ptr] = model_name
    def get_occ_ptr(self, obj):
        """Recursively resolves the raw C++ pointer address from a SWIG/pythonOCC object."""
        import re
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
    # NaviCube teardown
    # ------------------------------------------------------------------
    def _teardown_navcube(self):
        """
        Called via self.destroyed signal when this viewer's C++ object is
        being deleted.  Tears down the OCC sync helper then makes all overlays
        inert so no further Qt/OCC calls happen.
        """
        try:
            sync = getattr(self, "_navcube_sync", None)
            if sync is not None:
                sync.teardown()
                self._navcube_sync = None
        except Exception:
            pass
        try:
            nc = getattr(self, "navcube", None)
            if nc is not None:
                nc._tmr.stop()
                nc.hide()
        except Exception:
            pass
        # Stop the axis triad (it has no OCC refs but we hide it cleanly)
        try:
            if hasattr(self, "_axis_triad") and self._axis_triad:
                self._axis_triad.stop()
        except Exception:
            pass
        self._stop_auto_rotate()

    # ------------------------------------------------------------------
    # View Cube Display
    # ------------------------------------------------------------------
    def display_view_cube(self, start_triad=False):
        """Displays the NaviCube overlay and (optionally) starts the axis triad.

        start_triad is True only when an actual CAD model has been created — the
        axis triad must not appear on the empty viewer at init time.
        """
        if not (hasattr(self, "navcube") and self.navcube and self.view):
            return

        style = NavCubeStyle(
            # size=65: 96-dpi-reference pixels.  _resize_navcube overrides this
            # to exactly 9 % of the viewport, but 65 keeps the fallback small on
            # screens whose physicalDotsPerInch > 96.
            size=65,
            theme="light",
            face_color=(242, 244, 247),
            edge_color=(218, 224, 232),
            corner_color=(228, 232, 238),
            text_color=(45, 55, 72),
            border_color=(30, 30, 30),
            border_secondary_color=(80, 80, 80),
            border_width_main=1.6,
            border_width_secondary=0.9,
            hover_color=(145, 176, 20, 235),
            hover_text_color=(255, 255, 255),
            dot_color=(60, 60, 60, 180),
            shadow_color=(20, 20, 20, 45),
            shadow_offset_x=2.0,
            shadow_offset_y=2.5,
            face_color_dark=(52, 62, 76),
            edge_color_dark=(42, 52, 65),
            corner_color_dark=(47, 57, 70),
            text_color_dark=(210, 220, 232),
            border_color_dark=(200, 200, 200),
            border_secondary_color_dark=(130, 130, 130),
            hover_color_dark=(145, 176, 20, 235),
            show_gizmo=False,
            inactive_opacity=0.70,
            animation_ms=300,
            light_direction=(-0.5, -1.0, -1.5),
        )
        self.navcube.set_style(style)
        self._resize_navcube()

        if self._navcube_sync is None:
            self._navcube_sync = OCCNavCubeSync(self.view, self.navcube)

        QTimer.singleShot(0, self._show_navcube_when_ready)

        # Show axis triad (pure Qt — no OCC init needed) only once a CAD model
        # actually exists; never on the empty viewer at init time.
        if start_triad and hasattr(self, "_axis_triad") and self._axis_triad:
            self._position_axis_triad()
            self._axis_triad._started = True   # flag so showEvent can re-show it
            self._axis_triad.start()

    def _show_navcube_when_ready(self):
        self._resize_navcube()
        self._position_navcube()
        self._position_axis_triad()
        if hasattr(self.navcube, "mark_ready"):
            self.navcube.mark_ready()
        self.navcube.update()
        QTimer.singleShot(100, self._deferred_show_navcube)
        QTimer.singleShot(50, self._position_navcube)

    # ------------------------------------------------------------------
    # Mouse Press
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if not self.context or not self.view:
            super().mousePressEvent(event)
            return

        if self._navcube_sync is not None:
            self._navcube_sync.set_interaction_active(True)

        pr = self.devicePixelRatioF()
        x  = int(event.position().x() * pr)
        y  = int(event.position().y() * pr)

        self.context.MoveTo(x, y, self.view, True)

        # ---------------- NAVIGATION START ----------------
        # Rotate is timer-driven (auto-spin); only PAN and ZOOM_WINDOW use mouse drag.
        if (
            event.button() == Qt.LeftButton
            and self.active_nav_mode in (NavMode.PAN, NavMode.ZOOM_WINDOW)
            and self._can_start_navigation()
        ):
            self.is_dragging_nav = True
            self.last_mouse_pos = event.position()

            if self.active_nav_mode == NavMode.ZOOM_WINDOW:
                self._zoom_win_start = event.position().toPoint()
                self._zoom_win_active = True
                self._rubber_band.setGeometry(QRect(self._zoom_win_start, QSize()))
                self._rubber_band.show()
            elif self.active_nav_mode == NavMode.PAN:
                self.setCursor(Qt.ClosedHandCursor)

            event.accept()
            return

        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # Mouse Release
    # ------------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        if self._navcube_sync is not None:
            self._navcube_sync.set_interaction_active(False)

        if self.is_dragging_nav and event.button() == Qt.LeftButton:
            # Zoom Window: execute the fit on release
            if (
                self.active_nav_mode == NavMode.ZOOM_WINDOW
                and self._zoom_win_active
                and self._zoom_win_start is not None
            ):
                self._rubber_band.hide()
                self._zoom_win_active = False
                end  = event.position().toPoint()
                rect = QRect(self._zoom_win_start, end).normalized()
                self._zoom_win_start = None
                if rect.width() > 4 and rect.height() > 4:
                    self._execute_zoom_window(rect)

            if self.active_nav_mode == NavMode.PAN:
                self.setCursor(Qt.OpenHandCursor)

            self.is_dragging_nav = False
            self.last_mouse_pos = None
            event.accept()
            return

        if self.active_nav_mode == NavMode.PAN:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.unsetCursor()
        QApplication.restoreOverrideCursor()
        self.releaseMouse()
        super().mouseReleaseEvent(event)

    def _execute_zoom_window(self, rect: QRect) -> None:
        """Zoom the OCC view into the screen-space rectangle *rect* (logical px).

        Coordinate convention
        ---------------------
        All OCC V3d_View pixel methods in this codebase (``MoveTo``,
        ``StartRotation``, ``Rotation``, ``Pan``) receive **physical** pixel
        coordinates with **Y measured from the top** — the same convention Qt
        uses.  ``WindowFit`` follows the same convention; no Y-flip is needed.

        Strategy: try pythonocc's high-level ``ZoomArea`` first (it calls
        ``WindowFit`` internally), then fall back to raw ``WindowFit`` /
        ``WindowFitAll``.
        """
        if not self.view:
            return

        pr = self.devicePixelRatioF()
        x1 = int(rect.left()   * pr)
        y1 = int(rect.top()    * pr)
        x2 = int(rect.right()  * pr)
        y2 = int(rect.bottom() * pr)

        # 1. pythonocc display wrapper (highest-level, always present after InitDriver)
        disp = getattr(self, "_display", None)
        if disp is not None:
            try:
                disp.ZoomArea(x1, y1, x2, y2)
                return
            except Exception:
                pass

        # 2. V3d_View.WindowFit (pythonocc-core >= 7.4)
        try:
            self.view.WindowFit(x1, y1, x2, y2)
            self.view.Redraw()
            return
        except Exception:
            pass

        # 3. Alternate name used in some OCCT builds
        try:
            self.view.WindowFitAll(x1, y1, x2, y2)
            self.view.Redraw()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Navigation mode + turntable auto-rotation
    # ------------------------------------------------------------------
    _AUTO_ROTATE_SPEED_PX: int = 3   # virtual horizontal drag per frame (px)
    _AUTO_ROTATE_FPS:      int = 60  # frames per second

    # qtViewer3d pushes application override cursors that stack up and mask
    # setCursor(); neutralise its setter so this widget fully owns the cursor.
    @property
    def cursor(self):
        return self._current_cursor

    @cursor.setter
    def cursor(self, value):
        self._current_cursor = value

    def set_navigation_mode(self, mode) -> None:
        """Set the active nav mode, starting / stopping auto-rotate as needed."""
        prev = self.active_nav_mode
        self.active_nav_mode = mode

        if prev == NavMode.ROTATE and mode != NavMode.ROTATE:
            self._stop_auto_rotate()
        if mode == NavMode.ROTATE:
            self._start_auto_rotate()

        # Cursor feedback, same as the plots: open hand for pan, arrow otherwise.
        if mode == NavMode.PAN:
            while QApplication.overrideCursor() is not None:  # clear stale overrides
                QApplication.restoreOverrideCursor()
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _start_auto_rotate(self) -> None:
        """Begin continuous horizontal (turntable) rotation at ~60 fps."""
        self._stop_auto_rotate()
        if not self.view:
            return

        cx = self.width()  // 2
        cy = self.height() // 2
        disp = getattr(self, "_display", None)
        try:
            if disp is not None:
                disp.StartRotation(cx, cy)
            else:
                self.view.StartRotation(cx, cy)
        except Exception:
            pass

        self._auto_rotate_timer = QTimer(self)
        self._auto_rotate_timer.setInterval(1000 // self._AUTO_ROTATE_FPS)
        self._auto_rotate_timer.timeout.connect(self._auto_rotate_step)
        self._auto_rotate_timer.start()

    def _stop_auto_rotate(self) -> None:
        """Kill the turntable timer if running."""
        if self._auto_rotate_timer is not None:
            self._auto_rotate_timer.stop()
            self._auto_rotate_timer = None

    def _auto_rotate_step(self) -> None:
        """Apply one frame of horizontal rotation.

        Re-initialises the OCC trackball pivot at the viewport centre every
        frame, then applies a fixed virtual horizontal drag of
        ``_AUTO_ROTATE_SPEED_PX`` pixels — giving a constant angular delta per
        tick regardless of accumulated position.
        Also drives the axis triad by the same pixel delta (pure math, no OCC).
        """
        if not self.view:
            return

        cx   = self.width()  // 2
        cy   = self.height() // 2
        step = self._AUTO_ROTATE_SPEED_PX
        disp = getattr(self, "_display", None)
        try:
            if disp is not None:
                disp.StartRotation(cx, cy)
                disp.Rotation(cx + step, cy)   # Rotation() includes Redraw internally
            else:
                self.view.StartRotation(cx, cy)
                self.view.Rotation(cx + step, cy)
                self.view.Redraw()
        except Exception:
            pass

    def _can_start_navigation(self) -> bool:
        """Return True if a navigation drag may begin at the current cursor position."""
        if self.active_nav_mode in (NavMode.PAN, NavMode.ZOOM_WINDOW):
            return True
        return self.context.HasDetected()


class NavMode:
    ROTATE      = "ROTATE"
    PAN         = "PAN"
    ZOOM_WINDOW = "ZOOM_WINDOW"
