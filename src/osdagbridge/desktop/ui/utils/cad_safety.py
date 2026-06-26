"""Scoped-guard policy for safely tearing down/rebuilding the single OCC context."""
import gc
import os
from contextlib import contextmanager


def _dbg(msg):
    # Monitoring print, on by default; set OSDAGBRIDGE_CAD_DEBUG=0 to silence.
    if os.environ.get("OSDAGBRIDGE_CAD_DEBUG", "1") != "0":
        print(f"[CAD-SAFETY] {msg}", flush=True)


class CADSafetyGuard:
    # Owns the "safe to mutate the OCC context" policy for one viewer.

    def __init__(self, viewer):
        self._viewer = viewer
        # Interaction handlers consult this to avoid re-entering the context mid-mutation.
        self.in_progress = False

    @contextmanager
    def critical_section(self):
        # Freeze GC + pause overlays for the body; always restore on exit, even if it raises.
        viewer = self._viewer
        gc_was_enabled = gc.isenabled()
        gc.disable()
        self.in_progress = True
        try:
            viewer._pause_overlays()
        except Exception:
            pass
        _dbg(f"critical_section: enter — gc frozen, overlays paused {getattr(viewer, '_overlay_state', {})}")
        try:
            yield
        except Exception as exc:
            _dbg(f"critical_section: body raised {type(exc).__name__}: {exc} — restoring anyway")
            raise
        finally:
            try:
                viewer._resume_overlays()
            except Exception:
                pass
            self.in_progress = False
            # Never gc.collect() here — the gdb backtrace blamed GC of Shiboken objects.
            if gc_was_enabled:
                gc.enable()
            _dbg("critical_section: exit — overlays resumed, gc restored")

    def teardown_model(self):
        # Ordered AIS teardown (call inside critical_section): C++ Remove before dropping Python refs.
        viewer = self._viewer
        ctx = viewer.context

        # Unhilight first (IsHilighted guard — Linux double-frees on Remove-of-freed).
        if getattr(viewer, "current_highlighted_ais_list", None) and ctx:
            for obj in viewer.current_highlighted_ais_list:
                try:
                    if ctx.IsHilighted(obj):
                        ctx.Unhilight(obj, False)
                except Exception:
                    pass
        viewer.current_highlighted_ais_list = []
        viewer.current_highlighted_owner = None
        viewer.current_hovered_model = None

        # Release the C++ side before the Python refs drop; include deck-texture AIS (own list) under the same ordered teardown.
        n_ais = 0
        n_keys = len(viewer.model_ais_objects)
        if ctx is not None:
            deck_ais = getattr(viewer, "deck_texture_ais", None) or []
            for ais_list in list(viewer.model_ais_objects.values()) + [deck_ais]:
                items = ais_list if isinstance(ais_list, (list, tuple)) else [ais_list]
                for ais in items:
                    n_ais += 1
                    try:
                        if ctx.IsDisplayed(ais):
                            ctx.Remove(ais, False)
                    except Exception:
                        pass

        # Now drop the last Python wrapper references.
        viewer.model_ais_objects.clear()
        viewer.model_hover_labels.clear()
        viewer.model_hover_labels_by_ais.clear()
        viewer.ais_to_model = {}
        viewer._node_hover_data = []
        if hasattr(viewer, "deck_texture_ais"):
            viewer.deck_texture_ais = []
        _dbg(f"teardown_model: removed {n_ais} AIS across {n_keys} keys")

    def remove_model_keys(self, keys, display=None):
        # Guarded ordered removal of specific model_ais_objects keys (Remove, not Erase); re-entrant if already in a critical_section.
        if self.in_progress:
            self._remove_keys(keys, display)
        else:
            with self.critical_section():
                self._remove_keys(keys, display)

    def _remove_keys(self, keys, display=None):
        # Ordered teardown for the given keys: C++ Remove before dropping refs.
        viewer = self._viewer
        ctx = viewer.context
        removed = 0
        for key in keys:
            ais_list = viewer.model_ais_objects.pop(key, None)
            if ais_list is None:
                continue
            items = ais_list if isinstance(ais_list, (list, tuple)) else [ais_list]
            for ais in items:
                removed += 1
                # Drop any hover ref pointing at this AIS before releasing it.
                try:
                    viewer.model_hover_labels_by_ais.pop(ais, None)
                except Exception:
                    pass
                try:
                    if ctx is not None and ctx.IsDisplayed(ais):
                        ctx.Remove(ais, False)
                except Exception:
                    pass
        if removed and display is not None:
            try:
                display.Repaint()
            except Exception:
                pass
        _dbg(f"remove_model_keys: removed {removed} AIS for {list(keys)}")

    def clear(self, display=None):
        # Tear the model down and erase the view (unlock / clear).
        with self.critical_section():
            self.teardown_model()
            if display is not None:
                try:
                    display.EraseAll()
                    display.Repaint()
                except Exception:
                    pass
        _dbg("clear: model torn down + view erased")

    def for_app_exit(self, display=None):
        # Ordered teardown at app/tab close: GC-frozen, no resume, navcube made inert.
        viewer = self._viewer
        _dbg("for_app_exit: tearing down (no resume)")
        gc_was_enabled = gc.isenabled()
        gc.disable()
        self.in_progress = True
        try:
            viewer._pause_overlays()
        except Exception:
            pass
        try:
            self.teardown_model()
            if display is not None:
                try:
                    display.EraseAll()
                except Exception:
                    pass
            try:
                viewer._teardown_navcube()
            except Exception:
                pass
        finally:
            if gc_was_enabled:
                gc.enable()
        _dbg("for_app_exit: navcube inert, teardown done")
