# Central policy for releasing ospgrillage / OpenSeesPy analysis memory for one bridge backend.
import ctypes
import gc
import os
import types


def _dbg(msg):
    # Monitoring print, on by default; set OSDAGBRIDGE_OPS_DEBUG=0 to silence.
    if os.environ.get("OSDAGBRIDGE_OPS_DEBUG", "1") != "0":
        print(f"[OPS-MEMORY] {msg}", flush=True)


def _malloc_trim():
    # Return free glibc heap arenas to the OS. gc.collect() frees objects into the
    # allocator's arena but does NOT hand memory back to the OS — this does.
    # Best-effort: no-op on non-glibc platforms.
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def proc_mem_mb():
    # Current process (RSS, VIRT) in MB from /proc/self/status; (None, None) if unavailable.
    rss = virt = None
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1]) / 1024.0
                elif line.startswith("VmSize:"):
                    virt = int(line.split()[1]) / 1024.0
    except Exception:
        pass
    return rss, virt


class _Mallinfo2(ctypes.Structure):
    # glibc >= 2.33 struct mallinfo2 (all size_t). uordblks = bytes in use, hblkhd = mmap bytes.
    _fields_ = [(n, ctypes.c_size_t) for n in (
        "arena", "ordblks", "smblks", "hblks", "hblkhd", "usmblks",
        "fsmblks", "uordblks", "fordblks", "keepcost",
    )]


def proc_native_mb():
    # glibc allocator (in-use, mmap) in MB via mallinfo2; (None, None) off glibc / on failure.
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.mallinfo2.restype = _Mallinfo2
        mi = libc.mallinfo2()
        return mi.uordblks / 1024.0 / 1024.0, mi.hblkhd / 1024.0 / 1024.0
    except Exception:
        return None, None


def log_memory(tag):
    # Print the current process RSS / VIRT (+ glibc in-use/mmap) with a tag.
    rss, virt = proc_mem_mb()
    in_use, mmap_mb = proc_native_mb()
    if rss is None:
        _dbg(f"{tag}: memory unavailable")
    elif in_use is None:
        _dbg(f"{tag}: RSS {rss:.0f} MB | VIRT {virt:.0f} MB")
    else:
        _dbg(f"{tag}: RSS {rss:.0f} MB | VIRT {virt:.0f} MB | in-use {in_use:.0f} MB | mmap {mmap_mb:.0f} MB")
    return rss, virt


# Previous type-histogram, kept to report per-release deltas (which type is growing).
_prev_histogram = {}


def census_opensees_domain(tag):
    # Census the process-global OpenSees C++ domain. Call this AFTER ops.wipe(): a clean
    # wipe MUST report 0 nodes / 0 elements. Non-zero counts here are a genuine native leak —
    # the domain (and its C++ Node/Element/Pattern objects, invisible to Python's gc) survived
    # wipe(), which is the #1 suspect for the residual per-cycle in-use growth.
    if os.environ.get("OSDAGBRIDGE_OPS_DEBUG", "1") == "0":
        return
    try:
        import openseespy.opensees as ops
    except Exception:
        return
    parts = []
    for label, fn in (("nodes", "getNodeTags"), ("elements", "getEleTags")):
        try:
            tags = getattr(ops, fn)()
            parts.append(f"{label}={len(tags) if tags else 0}")
        except Exception:
            parts.append(f"{label}=?")
    _dbg(f"{tag}: OpenSees domain after wipe — {', '.join(parts)} (expect 0/0; non-zero = native leak)")


# tracemalloc harness: the decisive Python-vs-native test. If the top growers here stay small
# while RSS / in-use climb per cycle, the leak is native C++ (OpenSees/OCC) — not Python.
_tm_snapshot = None


def tracemalloc_mark_start():
    # Snapshot Python allocations at design START. Opt-in via OSDAGBRIDGE_MEM_TRACE=1 (adds overhead).
    if os.environ.get("OSDAGBRIDGE_MEM_TRACE", "0") != "1":
        return
    try:
        import tracemalloc
        if not tracemalloc.is_tracing():
            tracemalloc.start(15)
        global _tm_snapshot
        _tm_snapshot = tracemalloc.take_snapshot()
    except Exception:
        pass


def tracemalloc_report(tag):
    # Compare against the start snapshot and log the top-10 Python allocation growers by file:line.
    if os.environ.get("OSDAGBRIDGE_MEM_TRACE", "0") != "1":
        return
    try:
        import tracemalloc
        global _tm_snapshot
        if _tm_snapshot is None:
            return
        now = tracemalloc.take_snapshot()
        # Total traced Python bytes alive, and the numpy-owned slice of it. numpy>=1.22 routes its
        # array-data allocations through tracemalloc under a dedicated domain, so this is the
        # reliable "retained array DATA" figure the gc histogram (objects only) cannot give.
        total_mb = sum(s.size for s in now.statistics("lineno")) / 1024.0 / 1024.0
        np_mb = None
        try:
            import numpy as np
            dom = getattr(np.lib, "tracemalloc_domain", None)
            if dom is not None:
                np_snap = now.filter_traces([tracemalloc.DomainFilter(True, dom)])
                np_mb = sum(s.size for s in np_snap.statistics("lineno")) / 1024.0 / 1024.0
        except Exception:
            pass
        summary = f"{tag}: tracemalloc total Python-traced {total_mb:.1f} MB"
        if np_mb is not None:
            summary += f" (of which numpy array data {np_mb:.1f} MB)"
        _dbg(summary)
        stats = now.compare_to(_tm_snapshot, "lineno")
        _dbg(f"{tag}: tracemalloc top Python growers vs design-start:")
        for stat in stats[:10]:
            _dbg(f"    {stat}")
        _tm_snapshot = now
    except Exception:
        pass


def log_live_objects(tag):
    # Diagnostic: full gc type-histogram with cross-call deltas + explicit OCC/Qt counts, to name
    # exactly which object type accumulates across designs (the earlier counters proved numpy/
    # xarray/matplotlib are flat, so the residual native memory is held by some other type).
    # Gated on the same flag as _dbg (on by default). Walks the whole heap once per design.
    if os.environ.get("OSDAGBRIDGE_OPS_DEBUG", "1") == "0":
        return
    try:
        hist = {}
        n_occ = 0
        n_qt = 0
        for obj in gc.get_objects():
            t = type(obj)
            tname = t.__name__
            tmod = getattr(t, "__module__", "")
            if not isinstance(tmod, str):
                tmod = ""
            key = f"{tmod}.{tname}" if tmod else tname
            hist[key] = hist.get(key, 0) + 1
            # OCC native-backed wrappers (AIS_Shape / TopoDS_* / BRep* / Handle_*).
            if tmod.startswith("OCC.") or tname.startswith(("AIS_", "TopoDS_", "BRep", "Handle_")):
                n_occ += 1
            elif tname.startswith("Q") and (tmod.startswith("PySide") or tmod.startswith("PyQt")):
                n_qt += 1

        global _prev_histogram
        # Biggest growers vs the previous release call.
        deltas = sorted(
            ((k, hist[k] - _prev_histogram.get(k, 0)) for k in hist),
            key=lambda kv: kv[1], reverse=True,
        )
        top_growers = [f"{k}(+{d})" for k, d in deltas[:8] if d > 0]
        _prev_histogram = hist

        total = sum(hist.values())
        _dbg(f"{tag}: total gc objects={total}, OCC objects={n_occ}, Qt objects={n_qt}")
        if top_growers:
            _dbg(f"{tag}: top growers vs prev = {', '.join(top_growers)}")
    except Exception:
        pass


# Heavy design-result attributes dropped from the bridge backend on release.
_BRIDGE_RESULT_ATTRS = (
    "cad_components",
    "crossbracing_design_results",
    "end_diaphragm_design_results",
    "deck_design_results",
    "_load_effects_cache",
    "_deflections_cache",
    # Envelope force/displacement xarray arrays copied onto the bridge from the grillage
    # model. Not cleared previously, so it kept one design's deduplicated-dataset slice
    # (~20 MB, tracemalloc: xarray duck_array_ops) alive on the post-release floor even
    # though grillage_model itself was replaced. Recomputed every design — safe to drop.
    "result_envelopes",
)

# Raw per-load-case record containers on the ospgrillage Results object.
_RESULT_RECORD_ATTRS = (
    "basic_load_case_record",
    "basic_load_case_record_global_forces",
    "basic_load_case_record_stresses",
    "moving_load_case_record",
    "moving_load_case_record_global_forces",
)


class OpsMemoryGuard:
    # Owns the "release ospgrillage / OpenSeesPy memory" policy for one bridge backend.

    def __init__(self, bridge):
        self._bridge = bridge

    def wipe_domain(self):
        # Wipe the process-global OpenSeesPy C++ domain — the only way to free native memory.
        try:
            import openseespy.opensees as ops
            ops.wipe()
        except Exception:
            pass

    def release(self):
        # Drop all heavy backend data, replace the grillage model, wipe the domain, then collect.
        # Single entry point for unlock, app-close, and the start of every design run.
        # Never touches input_dict / basic_inputs / additional_inputs so UI values survive.
        # Lazy import avoids a circular import with analyser.
        from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel

        b = self._bridge
        b.output_dict = types.MappingProxyType({})
        b.result_data = {}
        b.grillage_geometry = None
        b.deck_layout = None
        for attr in _BRIDGE_RESULT_ATTRS:
            if hasattr(b, attr):
                setattr(b, attr, None)

        # Replace the grillage model with a blank instance so the old xarray Dataset,
        # OpenSeesPy references and cached arrays become unreachable.
        b.grillage_model = BridgeGrillageModel()

        # Dropping Python references does NOT free native memory — ops.wipe() does.
        before_rss, _ = proc_mem_mb()
        self.wipe_domain()
        # Census the C++ domain immediately after wipe: 0/0 = clean, anything else = native leak.
        census_opensees_domain("release")
        gc.collect()
        # Hand the freed arena back to the OS so RSS actually drops.
        _malloc_trim()
        after_rss, after_virt = proc_mem_mb()
        # in-use (glibc mallinfo2) at the post-teardown floor: the decisive true-leak metric.
        in_use, mmap_mb = proc_native_mb()
        if before_rss is not None and after_rss is not None:
            # Positive reclaimed = memory returned to the OS by wipe + gc.
            msg = (
                f"release: heavy backend data dropped + domain wiped — "
                f"RSS {before_rss:.0f} -> {after_rss:.0f} MB "
                f"(reclaimed {before_rss - after_rss:.0f} MB) | VIRT {after_virt:.0f} MB"
            )
            if in_use is not None:
                msg += f" | in-use {in_use:.0f} MB | mmap {mmap_mb:.0f} MB"
            _dbg(msg)
        else:
            _dbg("release: heavy backend data dropped + domain wiped")
        log_live_objects("release: live objects after teardown")
        tracemalloc_report("release")

    def clear_intermediate_results(self):
        # Empty the raw ospgrillage Results records once the deduplicated dataset is cached.
        # No-op unless the deduplicated dataset exists, since the UI reads that cached copy.
        grillage = getattr(self._bridge, "grillage_model", None)
        if getattr(grillage, "_deduplicated_results", None) is None:
            return
        results = getattr(getattr(grillage, "model", None), "results", None)
        if results is None:
            return

        before_rss, _ = proc_mem_mb()
        cleared = 0
        for attr in _RESULT_RECORD_ATTRS:
            container = getattr(results, attr, None)
            if isinstance(container, dict) and container:
                container.clear()
                cleared += 1
            elif isinstance(container, list) and container:
                del container[:]
                cleared += 1
        gc.collect()
        # Hand the freed arena back to the OS so RSS actually drops.
        _malloc_trim()
        after_rss, after_virt = proc_mem_mb()
        if before_rss is not None and after_rss is not None:
            _dbg(
                f"clear_intermediate_results: cleared {cleared} raw record container(s) — "
                f"RSS {before_rss:.0f} -> {after_rss:.0f} MB "
                f"(reclaimed {before_rss - after_rss:.0f} MB) | VIRT {after_virt:.0f} MB"
            )
        else:
            _dbg(f"clear_intermediate_results: cleared {cleared} raw record container(s)")
