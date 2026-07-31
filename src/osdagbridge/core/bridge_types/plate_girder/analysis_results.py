"""
PlateGirderAnalysisResults
---------------------------
Core processing engine for bridge analysis results and structural
load auditing within the OsdagBridge framework.

ARCHITECTURE & DATA FLOW
-------------------------
1.  Result Capture  : Reads raw force/moment/reaction datasets from
                      OpenSeespy via osmgrillage, keyed by load-case
                      name and element ID.
2.  Girder BFS      : Uses Breadth-First Search on the grillage
                      adjacency graph to reconstruct continuous
                      longitudinal girders (EB1, G1 … Gn, EB2) from
                      individual frame elements.
3.  Load Extraction : Reads applied loads directly from ospgrillage
                      Load objects (Line / Patch / Point) and compares
                      with analysis results for audit compliance.
4.  IRC:6 Vehicles  : Calls IRC6_2017.cl_204_1_Class70R_vehicle_wheel()
                      and IRC6_2017.cl_204_1_ClassA_vehicle() to obtain
                      local axle x-positions and wheel z-offsets, then
                      computes global wheel coordinates as:
                          global_x = vehicle.x + local_axle_x
                          global_z = vehicle.z + local_wheel_z
                      Each axle load is split equally into 2 wheel loads (L/R).

CLASS STRUCTURE
---------------
PlateGirderAnalysisResults(dataset, bridge, edge_dist)

  ── Initialisation ──
  __init__                    Store dataset, bridge ref, edge_dist

  ── Grillage Connectivity ──
  build_grillage_connectivity Build node/element/adjacency maps
  build_girders               BFS girder reconstruction
  filter_girders              Remove edge beams when edge_dist > 0

  ── Result Access ──
  get_available_loadcases     List all load-case names in dataset
  classify_loadcases          Group into dead / vehicle_static / vehicle_moving
  get_beam_element_results    Raw force/moment for given elements + LC
  print_load_availability     Print classified LC summary

  ── Public Print Methods (Interactive Menu) ──
  print_moving_load_trace     Option 3 – moving load trace per girder
  print_envelopes             Option 4 – max/min envelopes across LCs
  print_critical_max_state    Option 5 – critical position for a component
  print_girder_reactions      Option 6 – Ra/Rb per girder per LC
  print_load_extraction       Option 7 – dead + moving load audit report

  ── Private DataFrame Builders ──
  _get_girder_sw_df           Girder self-weight tabulation
  _get_dead_lc_df             Dead load case (Line/Patch/Point)
  _get_vehicle_df             IRC:6 vehicle wheel layout with global coords
  _get_moving_trace_df        Moving trace data per girder / component
  _get_envelopes_df           Envelope summary (max/min Vy, Mz) per LC
  _get_critical_state_df      Critical governing position
  _get_reactions_df           Support reactions (Ra, Rb) per girder

  ── Private Print Wrappers ──
  _print_girder_sw_extraction     Print girder self-weight table
  _print_single_dead_lc_extraction Print one dead load case
  _print_single_vehicle_extraction Print one vehicle layout

  ── Helpers ──
  _get_active_pts             Extract non-None points from a load object
  _bound(da, db)              Governing max/min across i-node and j-node DataArrays

  ── Programmatic API ──
  query(category, **kwargs)   Unified read-only interface (see below)
  verify_sections             Print section property verification log

  ── Interactive Entry Point ──
  run_interactive_viewer      7-option terminal menu

INTERACTIVE MENU (run_interactive_viewer)
------------------------------------------
  1. Show girder paths (BFS)
  2. Show analysis result (forces/moments per girder & load case)
  3. Show moving load trace (force vs vehicle position)
  4. Show max/min envelopes (all moving load cases)
  5. Show critical maximum state (governing LC + element)
  6. Show girder reactions (Ra, Rb)
  7. Load extraction (dead loads + IRC:6 vehicle wheel layout)
  0. Exit (triggers section verification log)

PROGRAMMATIC QUERY API  –  results.query(category, **kwargs)
--------------------------------------------------------------
category='girder_paths'
    Returns girder name → {start, end, path, elements, length}
    kwargs: none

category='forces'
    Returns element-wise force/moment for one load case + one girder.
    kwargs: name (load-case str), girder ('G1' etc.), component ('Vy_i')

category='moving_trace'
    Returns {x_pos, load_case, component (kN/kNm)} across all
    moving load cases for a girder.
    kwargs: name (LC filter), girder, component

category='envelopes'
    Returns {load_case, girder, Max Vy, Min Vy, Max Mz, Min Mz}
    for all (or filtered) moving LCs.
    kwargs: name (LC filter, optional), girder (optional)

category='critical_state'
    Returns governing {category, component, max_value, load_case, girder}.
    kwargs: name (vehicle category e.g. 'ClassA'), component ('Mz_i')

category='reactions'
    Returns {girder, Ra (kN), Rb (kN), span, case} per girder.
    kwargs: name (load-case str)

category='moving'
    Returns IRC:6 wheel layout table for one static vehicle load case.
    kwargs: name (load-case name e.g. 'Case1 ClassA L1')

EXAMPLE USAGE
-------------
    results = PlateGirderAnalysisResults(dataset=ds, bridge=bridge)

    # Programmatic (returns DataFrame):
    df, _ = results.query(category='moving', name='Case1 ClassA L1')
    df, _ = results.query(category='reactions', name='Case1 ClassA L1')
    df, _ = results.query(category='forces',
                          name='Case1 ClassA L1', girder='G3',
                          component='Mz_i')

    # Interactive terminal:
    results.run_interactive_viewer()
"""

import math
from collections import defaultdict, deque
import openseespy.opensees as ops
import pandas as pd
from osdagbridge.core.utils.common import kN, m, m2
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


class PlateGirderAnalysisResults:

    # ========================================================
    # INITIALIZATION
    # ========================================================
    def __init__(self, dataset, bridge, edge_dist=0):  # storing analysis result
        self.ds = dataset
        self.bridge = bridge
        self.model = getattr(bridge, 'model', None)
        self.edge_dist = edge_dist

    # ========================================================
    # DATASET BASED RESULTS (FORCES / MOMENTS)
    # ========================================================
    def get_beam_element_results(self, element_ids, loadcase, component):  # reads beam force and moment

        results = {}

        for eid in element_ids:
            try:
                val = self.ds.sel(
                    Loadcase=loadcase,
                    Element=eid,
                    Component=component
                )["forces"]

                results[eid] = val.values
            except Exception:
                results[eid] = None

        return results

    def get_available_loadcases(self):  # get loadcases
        return list(self.ds.coords["Loadcase"].values)

    # ========================================================
    # LOADCASE CLASSIFICATION AND DISPLAY
    # ========================================================
    def print_load_availability(self):
        """
        Prints a summarized view of available load cases/categories.
        """
        lc_groups = self.classify_loadcases()
        print("\nAvailable Load Categories:")
        if lc_groups["dead"]:
            print(f"- Dead Loads: {', '.join(lc_groups['dead'])}")
        if lc_groups["vehicle_static"]:
            unique_statics = sorted(list(set(lc_groups["vehicle_static"])))
            print(f"- Static Vehicles: {', '.join(unique_statics)}")
            
        if lc_groups["vehicle_moving"]:
            # Moving cases have many positions, extract unique base names
            moving_cases = []
            for lc in lc_groups["vehicle_moving"]:
                base_name = lc.split(" at global position ")[0] if " at global position " in str(lc) else str(lc)
                moving_cases.append(base_name)
            
            unique_moving = sorted(list(set(moving_cases)))
            print(f"- Moving Vehicles: {', '.join(unique_moving)} (Total positions: {len(lc_groups['vehicle_moving'])})")

    def classify_loadcases(self):

        all_lc = self.get_available_loadcases()

        vehicle_static    = []
        dead_loads        = []
        sw_cases          = []
        uls_basic         = []
        uls_accidental    = []
        uls_seismic       = []
        sls_frequent      = []
        sls_rare          = []
        sls_quasi         = []
        envelope_uls      = []
        envelope_sls      = []
        dl_ll_cases       = []
        fatigue_cases     = []

        for lc in all_lc:
            name       = str(lc)
            name_lower = name.lower()

            # Fatigue vehicle (IRC:6 Cl.204.6) — the static "Fatigue" case and every
            # increment of "Moving Fatigue at global position [...]". Matched early:
            # these names hit none of the rules below and would otherwise fall through
            # to the dead-load bucket at the end of the loop.
            if name_lower.startswith("fatigue") or name_lower.startswith("moving fatigue"):
                fatigue_cases.append(lc)
                continue

            # Envelope pseudo-LCs injected by create_envelope_load_case()
            if name == "Envelope ULS":
                envelope_uls.append(lc)
                continue
            if name == "Envelope SLS":
                envelope_sls.append(lc)
                continue

            # ULS combinations (BASIC_*, ACCIDENTAL_*, SEISMIC_*)
            if name.startswith("BASIC_"):
                uls_basic.append(lc)
                continue
            if name.startswith("ACCIDENTAL_"):
                uls_accidental.append(lc)
                continue
            if name.startswith("SEISMIC_"):
                uls_seismic.append(lc)
                continue

            # SLS combinations (SLS_FREQUENT_*, SLS_RARE_*, SLS_QP_*)
            if name.startswith("SLS_FREQUENT_"):
                sls_frequent.append(lc)
                continue
            if name.startswith("SLS_RARE_"):
                sls_rare.append(lc)
                continue
            if name.startswith("SLS_QP_") or name.startswith("SLS_OP_"):
                sls_quasi.append(lc)
                continue

            # Total-service combination from create_dl_ll_combination(), e.g. "1.0 DL + 1.0 LL".
            # Must be checked before the live-load rule below — it also ends in "LL" and
            # would otherwise be swallowed into vehicle_static (live-load-only) by mistake.
            if " DL + " in name and name_lower.endswith("ll"):
                dl_ll_cases.append(lc)
                continue

            # Live load: Class A, 70R, and LL envelope cases
            if name_lower.startswith("case") or "classa" in name_lower or "70r" in name_lower or name_lower.endswith("ll"):
                vehicle_static.append(lc)
                continue

            # Self-weight individual case
            if name == "SW":
                sw_cases.append(lc)
                dead_loads.append(lc)
                continue

            # Dead loads (DL, DD, DW, SIDL, etc.)
            dead_loads.append(lc)

        return {
            "all":                  all_lc,
            "dead":                 dead_loads,
            "vehicle_static":       vehicle_static,
            "vehicle_moving":       [],          # moving load cases removed from analyser
            "sw":                   sw_cases,
            "uls_basic":            uls_basic,
            "uls_accidental":       uls_accidental,
            "uls_seismic":          uls_seismic,
            "sls_frequent":         sls_frequent,
            "sls_rare":             sls_rare,
            "sls_quasi_permanent":  sls_quasi,
            "envelope_uls":         envelope_uls,
            "envelope_sls":         envelope_sls,
            "dl_ll":                dl_ll_cases,
            "fatigue":              fatigue_cases,
        }

    # ========================================================
    # OPENSEES NODAL DEFLECTION (FINAL STATE)
    # ========================================================
    # def get_girder_deflection(self, girder_nodes, direction):                       #give total deflection
    #
    #     dof_map = {"x": 1, "y": 2, "z": 3}
    #     dof = dof_map[direction]
    #
    #     disp = {}
    #     for n in girder_nodes:
    #         try:
    #             disp[n] = ops.nodeDisp(n, dof)
    #         except Exception:
    #             disp[n] = 0.0
    #
    #     return disp
    # # ========================================================
    # # OPENSEES DEFLECTION PER LOADCASE (RE-ANALYSIS)
    # # ========================================================
    # def get_deflection_per_loadcase(self, girder_nodes, loadcase, direction):
    #
    #     dof_map = {"x": 1, "y": 2, "z": 3}
    #     dof = dof_map[direction]
    #
    #     # reset previous analysis
    #     ops.wipeAnalysis()
    #
    #     # analyze only this loadcase
    #     self.model.analyze(load_case=[loadcase])
    #
    #     disp = {}
    #     for n in girder_nodes:
    #         try:
    #             disp[n] = ops.nodeDisp(n, dof)
    #         except Exception:
    #             disp[n] = 0.0
    #
    #     return disp

    # ========================================================
    # GRILLAGE CONNECTIVITY
    # ========================================================
    def build_grillage_connectivity(self):  # connectivity between nodes[raph for bfs]

        nodes = {}
        for n in ops.getNodeTags():
            nodes[n] = ops.nodeCoord(n)

        elements = {}
        for e in ops.getEleTags():
            elements[e] = ops.eleNodes(e)

        adj = defaultdict(set)

        for conn in elements.values():
            if len(conn) != 2:
                continue  # safety

            n1, n2 = conn

            adj[n1].add(n2)
            adj[n2].add(n1)

        return nodes, elements, adj

    # ========================================================
    # BFS SHORTEST PATH
    # ========================================================
    def bfs_shortest_path(self, adj, start, end):
        #                                                finds path shortest
        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == end:
                return path

            for nbr in adj[node]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(path + [nbr])

        return None

    def get_elements_along_path(self, path, elements):
        """
        Returns:
        - list of element IDs along the path
        - list of (eid, n1, n2) connectivity
        """

        path_elements = []
        element_map = []

        for i in range(len(path) - 1):
            n1 = path[i]
            n2 = path[i + 1]

            for eid, conn in elements.items():
                if set(conn) == {n1, n2}:
                    path_elements.append(eid)
                    element_map.append((eid, n1, n2))
                    break

        return path_elements, element_map

    # ========================================================
    # PATH LENGTH COMPUTATION
    # ========================================================
    def compute_path_distance(self, nodes, path):
        # calculate girder length
        dist = 0.0
        for i in range(len(path) - 1):
            x1, y1, z1 = nodes[path[i]]
            x2, y2, z2 = nodes[path[i + 1]]

            dist += math.sqrt(
                (x2 - x1) ** 2 +
                (y2 - y1) ** 2 +
                (z2 - z1) ** 2
            )

        return dist

    # ========================================================
    # BUILD LOGICAL GIRDERS (g1, g2, g3...)
    # ========================================================
    def build_girders(self, verbose=True):

        nodes, elements, adj = self.build_grillage_connectivity()

        # AUTO EXTRACT START / END — per-girder-line, skew-robust.
        # Each girder is a longitudinal line of nodes at a constant transverse
        # position z; its two supports are that line's extreme-x nodes. Grouping by
        # z (rather than a single global min_x/max_x) is what makes this work under
        # skew: a skewed deck staggers the supports in x, so global-equality matching
        # collapsed every girder onto one corner node and left no interior girders.
        z_lines = defaultdict(list)
        for n, coord in nodes.items():
            z_lines[round(coord[2], 6)].append(n)

        start_nodes, end_nodes = [], []
        for z in sorted(z_lines):                       # order girders across the width
            line = z_lines[z]
            start_nodes.append(min(line, key=lambda n: nodes[n][0]))   # furthest back  (min x)
            end_nodes.append(max(line, key=lambda n: nodes[n][0]))     # furthest ahead (max x)

        if verbose:
            print("\nStart edge nodes :", start_nodes)
            print("End edge nodes   :", end_nodes)

        # span length
        x_coords = [c[0] for c in nodes.values()]
        span_length = max(x_coords) - min(x_coords)

        if verbose:
            print(f"\nSpan length from geometry = {span_length}\n")

        girder_map = {}
        all_pairs = list(zip(start_nodes, end_nodes))
        num_pairs = len(all_pairs)

        for i, (s, e) in enumerate(all_pairs, start=1):
            # --- NAMING LOGIC ---
            name = f"G{i}"
            if self.edge_dist > 0:
                if i == 1:
                    name = "EB1"
                elif i == num_pairs:
                    name = "EB2"

            path = self.bfs_shortest_path(adj, s, e)
            path_elements, element_map = self.get_elements_along_path(path, elements)
            length = self.compute_path_distance(nodes, path)

            status = "VERIFIED" if abs(length - span_length) < 1e-6 else "NOT MATCHING"

            if verbose:
                print("----------------------------------------")
                print(f"Member: {name}")
                print("----------------------------------------")

                print("Path     :", path)
                print("Elements :", path_elements)

                print("\nElement connectivity:")
                for eid, n1, n2 in element_map:
                    print(f"{eid:<5}: {n1} -> {n2}")

                print(f"\nLength   : {length:.3f} m ({status})")
                print("----------------------------------------\n")

            girder_map[name] = {
                "start": s,
                "end": e,
                "path": path,
                "elements": path_elements,
                "element_map": element_map,
                "length": length
            }

        return girder_map, elements

    def filter_girders(self, girder_map):
        return girder_map

    # ========================================================
    # PRINT MOVING LOAD TRACE
    # ========================================================
    def print_moving_load_trace(self, load_case_filter=None, girder_filter=None, element_filter=None):
        """
        Prints the BMD and SFD for every point (element) when cars are moving.
        Iterates through all moving load cases and all girders.

        :param load_case_filter: (str or list) Print only load cases containing this string(s).
        :param girder_filter: (str or list) Print only girders matching this name(s) (e.g. "G1").
        :param element_filter: (int or list) Print only specific element IDs.
        """

        # Helper to normalize input to list
        def to_list(val):
            if val is None: return None
            return [val] if not isinstance(val, (list, tuple)) else val

        lc_filter = to_list(load_case_filter)
        g_filter = to_list(girder_filter)
        e_filter = to_list(element_filter)

        # 1. Classify loadcases to find moving ones
        lc_groups = self.classify_loadcases()
        moving_lcs = lc_groups["vehicle_moving"]

        if not moving_lcs:
            print("❌ No moving load cases found.")
            return

        # 2. Build girders
        girder_map, _ = self.build_girders(verbose=False)
        girder_map = self.filter_girders(girder_map)

        print("\n================ MOVING LOAD TRACE ================")

        # 3. Iterate through moving load cases
        for lc in moving_lcs:
            # Apply load case filter
            if lc_filter:
                # Check if ANY of the filter strings are in the load case name
                if not any(str(f) in lc for f in lc_filter):
                    continue

            print(f"\n>>> Load Case: {lc}")

            # 4. Iterate through girders
            for girder_name, girder_data in girder_map.items():
                # Apply girder filter
                if g_filter and girder_name not in g_filter:
                    continue

                print(f"  --- Girder: {girder_name} ---")

                elements = girder_data["elements"]

                # Filter elements if requested
                if e_filter:
                    elements = [e for e in elements if e in e_filter]
                    if not elements:
                        continue  # Skip if no elements match

                # 5. Get results for this girder and loadcase
                try:
                    subset = self.ds.sel(Loadcase=lc, Element=elements).copy()



                    # Extract values and create DataFrame
                    df = pd.DataFrame({
                        "Element": elements,
                        "Vx_i (kN)": subset.sel(Component="Vx_i")["forces"].values / 1000,
                        "Vx_j (kN)": subset.sel(Component="Vx_j")["forces"].values / 1000,
                        "Vy_i (kN)": subset.sel(Component="Vy_i")["forces"].values / 1000,
                        "Vy_j (kN)": subset.sel(Component="Vy_j")["forces"].values / 1000,
                        "Vz_i (kN)": subset.sel(Component="Vz_i")["forces"].values / 1000,
                        "Vz_j (kN)": subset.sel(Component="Vz_j")["forces"].values / 1000,
                        "Mx_i (kNm)": subset.sel(Component="Mx_i")["forces"].values / 1000,
                        "Mx_j (kNm)": subset.sel(Component="Mx_j")["forces"].values / 1000,
                        "My_i (kNm)": subset.sel(Component="My_i")["forces"].values / 1000,
                        "My_j (kNm)": subset.sel(Component="My_j")["forces"].values / 1000,
                        "Mz_i (kNm)": subset.sel(Component="Mz_i")["forces"].values / 1000,
                        "Mz_j (kNm)": subset.sel(Component="Mz_j")["forces"].values / 1000,
                    })
                    print(df.to_string(index=False))

                except Exception as e:
                    print(f"  ❌ Error retrieving results for girder {girder_name}: {e}")

        print("\n===================================================")

    # ========================================================
    # PRINT VEHICLE ENVELOPES
    # ========================================================
    def print_envelopes(self, load_case_filter=None, girder_filter=None):
        """
        Calculates and prints the max/min values for SFD and BMD for every moving load case position.
        """

        def to_list(val):
            if val is None: return None
            return [val] if not isinstance(val, (list, tuple)) else val

        lc_filter = to_list(load_case_filter)
        g_filter = to_list(girder_filter)

        lc_groups = self.classify_loadcases()
        moving_lcs = lc_groups["vehicle_moving"]

        if not moving_lcs:
            print("❌ No moving load cases found.")
            return

        if lc_filter:
            moving_lcs = [lc for lc in moving_lcs if any(str(f) in lc for f in lc_filter)]
            if not moving_lcs:
                print("❌ No moving load cases match the filter.")
                return

        girder_map, _ = self.build_girders(verbose=False)
        girder_map = self.filter_girders(girder_map)

        print("\n================ VEHICLE ENVELOPES (PER POSITION) ================")

        for lc in moving_lcs:
            print(f"\n>>> Load Case: {lc}")

            lc_data = []

            for girder_name, girder_data in girder_map.items():
                if g_filter and girder_name not in g_filter:
                    continue

                if self.edge_dist > 0 and girder_name in ["EB1", "EB2"]:
                    continue  # dont calculate it for calculating other values

                elements = girder_data["elements"]

                try:
                    # Select ONLY this loadcase and elements for this girder
                    subset = self.ds.sel(Loadcase=lc, Element=elements).copy()



                    # --- Compact envelope computation via _bound helper ---
                    _COMP_PAIRS = [
                        ("Vy", "Vy_i", "Vy_j", "kN"),
                        ("Vx", "Vx_i", "Vx_j", "kN"),
                        ("Vz", "Vz_i", "Vz_j", "kN"),
                        ("Mx", "Mx_i", "Mx_j", "kNm"),
                        ("My", "My_i", "My_j", "kNm"),
                        ("Mz", "Mz_i", "Mz_j", "kNm"),
                    ]
                    _COLS = [
                        f"{mm} {n} ({u})"
                        for n, ci, cj, u in _COMP_PAIRS
                        for mm in ("Max", "Min")
                    ]
                    crit_eles = defaultdict(lambda: dict.fromkeys(_COLS, "-"))

                    for label, ci, cj, unit in _COMP_PAIRS:
                        da = subset.sel(Component=ci)["forces"]
                        db = subset.sel(Component=cj)["forces"]
                        v_max, e_max, v_min, e_min = self._bound(da, db)
                        crit_eles[e_max][f"Max {label} ({unit})"] = f"{v_max:.3f}"
                        crit_eles[e_min][f"Min {label} ({unit})"] = f"{v_min:.3f}"

                    # Add to loadcase data
                    for eid in sorted(crit_eles.keys()):
                        row = {"Girder": girder_name, "Ele": eid}
                        row.update(crit_eles[eid])
                        lc_data.append(row)

                except Exception as e:
                    lc_data.append({"Girder": girder_name, "Ele": "ERROR", "Max Vy (kN)": str(e)})

            if lc_data:
                df = pd.DataFrame(lc_data)
                print(df.to_string(index=False))

        print("\n===================================================================")

    def print_critical_max_state(self):
        """
        Finds the global maximum for a selected component across all moving load cases
        within a selected category and displays the bridge-wide state at that critical position.
        """
        print("\n--- Critical Maximum Result Viewer ---")

        # 1. Component Selection
        print("Select Component:")
        print("1. Vy_i")
        print("2. Vy_j")
        print("3. Mz_i")
        print("4. Mz_j")
        print("0. Back")

        choice = input("Enter choice: ").strip()
        if choice == "0":
            return

        comp_map = {
            "1": "Vy_i",
            "2": "Vy_j",
            "3": "Mz_i",
            "4": "Mz_j",
        }
        if choice not in comp_map:
            print("❌ Invalid selection")
            return

        comp = comp_map[choice]

        # 2. Category Selection (Moving Load Cases)
        lc_groups = self.classify_loadcases()
        moving_lcs = lc_groups["vehicle_moving"]

        if not moving_lcs:
            print("❌ No moving load cases found.")
            return

        # Group by case type (e.g., "Case1 ClassA", "Case2 Class70R")
        case_types = {}
        for lc in moving_lcs:
            parts = lc.split()
            if len(parts) >= 3:
                case_type = f"{parts[1]} {parts[2]}"
                if case_type not in case_types:
                    case_types[case_type] = []
                case_types[case_type].append(lc)

        categories = sorted(case_types.keys())
        print("\nSelect Moving Load Category:")
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category}")
        print("0. Back")

        cat_choice = input("Enter choice: ").strip()
        if cat_choice == "0":
            return

        if not cat_choice.isdigit() or int(cat_choice) < 1 or int(cat_choice) > len(categories):
            print("❌ Invalid selection")
            return

        selected_category = categories[int(cat_choice) - 1]
        relevant_lcs = case_types[selected_category]

        girder_map, _ = self.build_girders(verbose=False)
        girder_map = self.filter_girders(girder_map)

        global_abs_max = -1.0
        crit_val = 0.0
        crit_lc = None
        crit_girder = None
        crit_ele = None

        print(f"\nSearching for absolute maximum {comp} in {selected_category} ({len(relevant_lcs)} positions)...")

        # 3. Search for absolute maximum within selected category
        for lc in relevant_lcs:
            for g_name, g_data in girder_map.items():
                if self.edge_dist > 0 and g_name in ["EB1", "EB2"]:
                    continue  # Skip EB1 and EB2 when finding maximum

                elements = g_data["elements"]
                try:
                    subset = self.ds.sel(Loadcase=lc, Element=elements, Component=comp)["forces"].copy()


                    # Find both max and min in this subset
                    s_max = float(subset.max())
                    s_min = float(subset.min())

                    # Determine which has larger magnitude
                    if abs(s_max) >= abs(s_min):
                        local_abs_max = abs(s_max)
                        local_val = s_max
                        local_ele = int(subset.idxmax())
                    else:
                        local_abs_max = abs(s_min)
                        local_val = s_min
                        local_ele = int(subset.idxmin())

                    if local_abs_max > global_abs_max:
                        global_abs_max = local_abs_max
                        crit_val = local_val
                        crit_lc = lc
                        crit_girder = g_name
                        crit_ele = local_ele
                except Exception:
                    continue

        if crit_lc is None:
            print("❌ No results found.")
            return     # reactions vy start ra and end rb, point load and line load , point-coordinate,line-start and end

        print("\n" + "=" * 100)
        print(" " * 35 + "GLOBAL CRITICAL MAXIMUM SUMMARY")
        print("=" * 100)

        # 3.1 Parse load case string for short name and position
        # Format usually: "Moving Case1 ClassA L2 at global position [23.95,0.00,0.00]"
        short_lc = crit_lc
        position_str = "-"
        if " at global position " in crit_lc:
            parts = crit_lc.split(" at global position ")
            short_lc = parts[0].replace("Moving ", "")  # e.g. "Case1 ClassA L2"
            position_str = parts[1]  # e.g. "[23.95,0.00,0.00]"

        summary_data = [{
            "Component": comp,
            "Girder": crit_girder,
            "Element": crit_ele,
            "Value (kN/kNm)": f"{crit_val / 1000:.3f}",
            "Loadcase (Short)": short_lc,
            "Position": position_str
        }]
        summary_df = pd.DataFrame(summary_data)
        print(summary_df.to_string(index=False))
        print("=" * 100)

        # 4. Print bridge-wide state at this critical load case position
        print(f"\n--- Bridge State at {crit_lc} ---")

        for g_name, g_data in girder_map.items():
            elements = g_data["elements"]
            print(f"\n>>> Girder: {g_name}")
            try:
                subset = self.ds.sel(Loadcase=crit_lc, Element=elements).copy()



                vx_i = subset.sel(Component="Vx_i")["forces"].values
                vx_j = subset.sel(Component="Vx_j")["forces"].values
                vy_i = subset.sel(Component="Vy_i")["forces"].values
                vy_j = subset.sel(Component="Vy_j")["forces"].values
                vz_i = subset.sel(Component="Vz_i")["forces"].values
                vz_j = subset.sel(Component="Vz_j")["forces"].values
                mx_i = subset.sel(Component="Mx_i")["forces"].values
                mx_j = subset.sel(Component="Mx_j")["forces"].values
                my_i = subset.sel(Component="My_i")["forces"].values
                my_j = subset.sel(Component="My_j")["forces"].values
                mz_i = subset.sel(Component="Mz_i")["forces"].values
                mz_j = subset.sel(Component="Mz_j")["forces"].values

                # Separate girder data collection
                girder_data = []
                for i, eid in enumerate(elements):
                    row = {
                        "Element": eid,
                        "Vx_i": f"{vx_i[i]:.3f}",
                        "Vx_j": f"{vx_j[i]:.3f}",
                        "Vy_i": f"{vy_i[i]:.3f}",
                        "Vy_j": f"{vy_j[i]:.3f}",
                        "Vz_i": f"{vz_i[i]:.3f}",
                        "Vz_j": f"{vz_j[i]:.3f}",
                        "Mx_i": f"{mx_i[i]:.3f}",
                        "Mx_j": f"{mx_j[i]:.3f}",
                        "My_i": f"{my_i[i]:.3f}",
                        "My_j": f"{my_j[i]:.3f}",
                        "Mz_i": f"{mz_i[i]:.3f}",
                        "Mz_j": f"{mz_j[i]:.3f}"
                    }
                    girder_data.append(row)

                df = pd.DataFrame(girder_data)
                print(df.to_string(index=False))
            except Exception as e:
                print(f"  ❌ Error for girder {g_name}: {e}")

        print("\n" + "=" * 80)

    def print_girder_reactions(self, load_case_filter=None, girder_filter=None):
        """
        Calculates and prints Ra (shear at start node) and Rb (shear at end node)
        for every girder under every selected load case.
        
        :param load_case_filter: (str or list) Filter load cases by name.
        :param girder_filter: (str or list) Filter girders by name.
        """
        def to_list(val):
            if val is None: return None
            return [val] if not isinstance(val, (list, tuple)) else val

        lc_filter = to_list(load_case_filter)
        g_filter = to_list(girder_filter)

        all_lcs = self.get_available_loadcases()

        if lc_filter:
            all_lcs = [lc for lc in all_lcs if any(str(f).lower() in str(lc).lower() for f in lc_filter)]

        if not all_lcs:
            print("❌ No load cases matched the filter.")
            return

        girder_map, _ = self.build_girders(verbose=False)
        girder_map = self.filter_girders(girder_map)

        print("\n" + "=" * 60)
        print(" " * 15 + "GIRDER REACTIONS (Ra, Rb) SUMMARY")
        print("=" * 60)

        for lc in all_lcs:
            print(f"\n>>> Load Case: {lc}")
            
            rows = []
            for g_name, g_data in girder_map.items():
                if g_filter and g_name not in g_filter:
                    continue

                element_map = g_data["element_map"]
                if not element_map:
                    continue
                
                # First element: Ra is at the start node n1
                eid_start, n1_start, _ = element_map[0]
                # Last element: Rb is at the end node n2
                eid_end, _, n2_end = element_map[-1]
                
                try:
                    # Identify components based on element connectivity in OpenSees
                    # ops.eleNodes(eid) returns [iNode, jNode]
                    nodes_start = ops.eleNodes(eid_start)
                    comp_ra = "Vy_i" if n1_start == nodes_start[0] else "Vy_j"
                    
                    nodes_end = ops.eleNodes(eid_end)
                    comp_rb = "Vy_j" if n2_end == nodes_end[1] else "Vy_i"

                    # Fetch raw values from dataset (divide by 1000 for kN)
                    ra_val = float(self.ds.sel(Loadcase=lc, Element=eid_start, Component=comp_ra)["forces"]) / 1000
                    # Rb is usually shown as negative at the end of a girder in SFDs
                    rb_val = -float(self.ds.sel(Loadcase=lc, Element=eid_end, Component=comp_rb)["forces"]) / 1000

                    
                    rows.append({
                        "Girder": g_name,
                        "Ra (kN)": f"{ra_val:.3f}",
                        "Rb (kN)": f"{rb_val:.3f}"
                    })
                except Exception as e:
                    rows.append({
                        "Girder": g_name,
                        "Ra (kN)": "ERR",
                        "Rb (kN)": "N/A"
                    })

            if rows:
                df = pd.DataFrame(rows)
                print(df.to_string(index=False))
                
        print("\n" + "=" * 60)

    def verify_sections(self):
        """
        Prints the section properties for a sample element of each member type
        from the bridge model to verify correct implementation.
        """
        print("\n" + "=" * 105)
        print(" " * 35 + "SECTION PROPERTIES VERIFICATION LOG")
        print("=" * 105)
        
        # Determine which section attribute was assigned to edge beams based on edge distance
        eb_attr_name = "edge_longitudinal_section" if self.edge_dist > 0 else "longitudinal_section"
        
        # Member categories to check vs the bridge instance attributes
        categories = [
            ("Edge Beams (EB)", "edge_beam", eb_attr_name),
            ("Interior Girders (G)", "interior_main_beam", "longitudinal_section"),
            ("Exterior Girders (G)", "exterior_main_beam_1", "longitudinal_section"),
            ("Transverse Slabs", "transverse_slab", "transverse_section")
        ]
        
        rows = []
        for label, m_type, attr_name in categories:
            try:
                # Find which elements belong to this category
                elements = self.bridge.model.get_element(member=m_type, options="elements")
                section_obj = getattr(self.bridge, attr_name, None)
                
                if not elements or section_obj is None:
                    continue
                
                eid = elements[0]
                
                # Extract properties from the ospgrillage section object
                rows.append({
                    "Girder Category": label,
                    "Assigned Section Object": f"bridge.{attr_name}",
                    "Sample ID": eid,
                    "Area (A)": f"{section_obj.A:.4f}",
                    "Torsion (J)": f"{section_obj.J:.4f}",
                    "Iz (strong)": f"{section_obj.Iz:.4f}",
                    "Iy (weak)": f"{section_obj.Iy:.4f}",
                    "Az": f"{section_obj.Az:.4f}",
                    "Ay": f"{section_obj.Ay:.4f}",
                })
                
            except Exception:
                continue

        if rows:
            df = pd.DataFrame(rows)
            print(df.to_string(index=False))
        else:
            print("❌ No section data could be retrieved for verification.")

        print("\n" + "=" * 105)
        print(" " * 30 + "End of Verification (Exiting Analysis Tools)")
        print("=" * 105)

    def print_load_extraction(self, include_moving=True):
        """
        Extracts and prints load information for all dead load cases and (optionally)
        moving load cases. Delegates to the same private helpers used by the
        interactive menu (Option 7), ensuring a single source of truth.
        """
        print("\n" + "=" * 110)
        print(" " * 40 + "LOAD EXTRACTION REPORT")
        print("=" * 110)

        # Build girder map for self-weight extraction
        nodes, _, _ = self.build_grillage_connectivity()
        g_map, _ = self.build_girders(verbose=False)
        g_map = self.filter_girders(g_map)

        # 1. Girder Self Weight
        self._print_girder_sw_extraction(g_map, nodes)

        # 2. Other Dead Loads (dynamically discovered)
        for attr_name in sorted(vars(self.bridge).keys()):
            val = getattr(self.bridge, attr_name)
            if (attr_name.endswith("_load_case")
                    and attr_name != "self_weight_load_case"
                    and val is not None):
                display_name = attr_name.replace("_", " ").title()
                self._print_single_dead_lc_extraction(display_name, val)

        # 3. Moving Loads (Vehicles)
        if include_moving and getattr(self.bridge, 'vehicle_load_cases_list', None):
            for lc in self.bridge.vehicle_load_cases_list:
                self._print_single_vehicle_extraction(lc)

        print("\n" + "=" * 110)


    def _get_active_pts(self, load_obj):
        """Helper to get non-None points from load attributes (fending off stale point_list)."""
        pts = []
        for i in range(1, 9):
            p = getattr(load_obj, f"load_point_{i}", None)
            if p:
                pts.append(p)
        return pts

    @staticmethod
    def _bound(da, db):
        """
        Returns (max_kN, max_ele, min_kN, min_ele) from two xarray DataArrays
        representing the i-node and j-node of a force/moment component.
        Picks the governing value (larger magnitude) between the two ends.
        """
        a_max, b_max = float(da.max()), float(db.max())
        a_min, b_min = float(da.min()), float(db.min())
        if a_max >= b_max:
            v_max, e_max = a_max / 1000.0, int(da.idxmax())
        else:
            v_max, e_max = b_max / 1000.0, int(db.idxmax())
        if a_min <= b_min:
            v_min, e_min = a_min / 1000.0, int(da.idxmin())
        else:
            v_min, e_min = b_min / 1000.0, int(db.idxmin())
        return v_max, e_max, v_min, e_min

    def query(self, category, **kwargs):
        """
        Public programmatic API for querying ALL bridge analysis results.
        Returns a nested list (array) of the requested data and the column headers.

        Parameters
        ----------
        category : str
            'girder_sw', 'dead', 'moving', 'reactions', 'forces', 
            'girder_paths', 'moving_trace', 'envelopes', 'critical_state'
        kwargs : dict
            - name : str (Load case or Category name)
            - girder : str (Optional girder name)
            - component : str (e.g., 'Vy_i', 'Mz_j')

        Returns
        -------
        data : list of lists, columns : list
        """
        df = None
        name = kwargs.get('name')
        girder = kwargs.get('girder')
        comp = kwargs.get('component')

        if category == "girder_paths":
            df = self._get_girder_paths_df(girder)
        elif category == "girder_sw":
            nodes, _, _ = self.build_grillage_connectivity()
            g_map, _ = self.build_girders(verbose=False)
            g_map = self.filter_girders(g_map)
            df = self._get_girder_sw_df(g_map, nodes)
        elif category == "dead":
            if not name: return [], []
            lc = getattr(self.bridge, name, None)
            df = self._get_dead_lc_df(name, lc)
        elif category == "moving":
            if not name: return [], []
            v_lcs = getattr(self.bridge, 'vehicle_load_cases_list', [])
            target_lc = next((lc for lc in v_lcs if lc.name == name), None)
            if target_lc:
                df = self._get_vehicle_df(target_lc)
        elif category == "reactions":
            if not name: return [], []
            df = self._get_reactions_df(name, girder)
        elif category == "forces":
            if not name or not girder or not comp: return [], []
            df = self._get_forces_df(name, girder, comp)
        elif category == "moving_trace":
            if not name or not girder or not comp: return [], []
            df = self._get_moving_trace_df(name, girder, comp)
        elif category == "envelopes":
            df = self._get_envelopes_df(name, girder)
        elif category == "critical_state":
            if not name or not comp: return [], []
            df = self._get_critical_state_df(name, comp)

        if df is not None and not df.empty:
            return df.values.tolist(), df.columns.tolist()
        return [], []

    def _get_girder_paths_df(self, girder_filter=None):
        """Internal helper for Girder Paths (BFS results)."""
        g_map, _ = self.build_girders(verbose=False)
        g_map = self.filter_girders(g_map)
        rows = []
        for g, data in g_map.items():
            if girder_filter and g != girder_filter:
                continue
            rows.append({"Girder": g, "Start": data["start"], "End": data["end"], "Length": round(data["length"], 3), "Nodes": str(data["path"])})
        return pd.DataFrame(rows)

    def _get_moving_trace_df(self, category_name, girder_name, component):
        """Internal helper for Moving Load Trace."""
        g_map, _ = self.build_girders(verbose=False)
        if girder_name not in g_map: return pd.DataFrame()
        elements = g_map[girder_name]["elements"]
        
        lc_groups = self.classify_loadcases()
        all_moving = lc_groups["vehicle_moving"]
        relevant = [lc for lc in all_moving if category_name in lc]
        
        rows = []
        for lc in relevant:
            try:
                x_pos = float(lc.split("L")[-1]) if "L" in lc else 0.0
                subset = self.ds.sel(Loadcase=lc, Element=elements, Component=component)["forces"]
                val = float(subset.max()) if "max" in component.lower() else float(subset.min())
                if abs(float(subset.min())) > abs(float(subset.max())): val = float(subset.min())
                rows.append({"X Pos": round(x_pos, 3), "LoadCase": lc, f"{component} (kN/kNm)": round(val/1000, 3)})
            except Exception: pass
        return pd.DataFrame(rows)

    def _get_envelopes_df(self, lc_filter=None, g_filter=None):
        """Internal helper for Max/Min Envelopes."""
        g_map, _ = self.build_girders(verbose=False)
        g_map = self.filter_girders(g_map)
        all_lcs = self.get_available_loadcases()
        if lc_filter: all_lcs = [lc for lc in all_lcs if lc_filter in str(lc)]
        
        rows = []
        for lc in all_lcs:
            for g_name, g_data in g_map.items():
                if g_filter and g_name != g_filter: continue
                try:
                    subset = self.ds.sel(Loadcase=lc, Element=g_data["elements"])["forces"]
                    rows.append({
                        "LoadCase": lc, "Girder": g_name,
                        "Max Vy": round(float(subset.sel(Component=["Vy_i", "Vy_j"]).max())/1000, 3),
                        "Min Vy": round(float(subset.sel(Component=["Vy_i", "Vy_j"]).min())/1000, 3),
                        "Max Mz": round(float(subset.sel(Component=["Mz_i", "Mz_j"]).max())/1000, 3),
                        "Min Mz": round(float(subset.sel(Component=["Mz_i", "Mz_j"]).min())/1000, 3)
                    })
                except Exception: pass
        return pd.DataFrame(rows)

    def _get_critical_state_df(self, category_name, component):
        """Internal helper for Critical Maximum State."""
        lc_groups = self.classify_loadcases()
        relevant = [lc for lc in lc_groups["vehicle_moving"] if category_name in lc]
        g_map, _ = self.build_girders(verbose=False)
        g_map = self.filter_girders(g_map)
        
        best_val, best_lc, best_g, best_e = 0, None, None, None
        for lc in relevant:
            for g, data in g_map.items():
                try:
                    subset = self.ds.sel(Loadcase=lc, Element=data["elements"], Component=component)["forces"]
                    v = float(subset.max()) if abs(float(subset.max())) >= abs(float(subset.min())) else float(subset.min())
                    if abs(v) > abs(best_val):
                        best_val, best_lc, best_g = v, lc, g
                except Exception: pass
        
        if best_lc:
            return pd.DataFrame([{
                "Category": category_name, "Component": component, 
                "Max Value": round(best_val/1000, 3), "LoadCase": best_lc, "Girder": best_g
            }])
        return pd.DataFrame()

    def _get_reactions_df(self, load_case, girder_filter=None):
        """Internal helper to build Reaction DataFrame for a specific load case."""
        nodes, _, _ = self.build_grillage_connectivity()
        g_map, _ = self.build_girders(verbose=False)
        g_map = self.filter_girders(g_map)
        
        rows = []
        for g_name, g_data in g_map.items():
            if girder_filter and g_name != girder_filter:
                continue
            
            el_map = g_data["element_map"]
            if not el_map: continue
            
            # Start node (Ra) from first element
            eid_s, n1_s, _ = el_map[0]
            # End node (Rb) from last element
            eid_e, _, n2_e = el_map[-1]
            
            try:
                nodes_s = ops.eleNodes(eid_s)
                c_ra = "Vy_i" if n1_s == nodes_s[0] else "Vy_j"
                nodes_e = ops.eleNodes(eid_e)
                c_rb = "Vy_j" if n2_e == nodes_e[1] else "Vy_i"

                ra = float(self.ds.sel(Loadcase=load_case, Element=eid_s, Component=c_ra)["forces"]) / 1000
                rb = -float(self.ds.sel(Loadcase=load_case, Element=eid_e, Component=c_rb)["forces"]) / 1000
                
                rows.append({"Girder": g_name, "Ra (kN)": round(ra, 3), "Rb (kN)": round(rb, 3)})
            except Exception: pass
        return pd.DataFrame(rows)

    def _get_forces_df(self, load_case, girder_name, component):
        """Internal helper to build Internal Force DataFrame for a girder's elements."""
        g_map, _ = self.build_girders(verbose=False)
        if girder_name not in g_map: return pd.DataFrame()

        elements = g_map[girder_name]["elements"]
        rows = []
        unit = "kN" if "V" in component else "kNm"

        for eid in elements:
            try:
                val = float(self.ds.sel(Loadcase=load_case, Element=eid, Component=component)["forces"]) / 1000
                rows.append({"Element": str(eid), f"{component} ({unit})": round(val, 3)})
            except Exception: pass
        return pd.DataFrame(rows)

    def _get_displacements_df(self, load_case: str, girder_name: str, component: str) -> pd.DataFrame:
        """
        Build per-node displacement DataFrame for a girder and load case.

        Parameters
        ----------
        load_case : str
            Load case name as stored in the dataset Loadcase coordinate.
        girder_name : str
            Girder identifier, e.g. ``"G1"``.
        component : str
            Displacement component — ospgrillage stores these as ``"dx"``,
            ``"dy"``, ``"dz"`` (translational) in the ``displacements``
            DataArray.

        Returns
        -------
        pd.DataFrame
            Columns: ``Node`` (int), ``<component>`` (float, mm).
            Rows are sorted by node X-coordinate so the array aligns with
            the longitudinal axis used by GirderGraphEngine.
            Empty DataFrame on any failure.
        """
        g_map, _ = self.build_girders(verbose=False)
        if girder_name not in g_map:
            return pd.DataFrame()

        node_path = g_map[girder_name]["path"]

        # Build node → X-coord map for sorting
        nodes_coords, _, _ = self.build_grillage_connectivity()

        disp_da = self.ds.get("displacements")
        if disp_da is None:
            return pd.DataFrame()

        # ospgrillage stores static displacements (from ops.nodeDisp) under the
        # single-letter components "x", "y", "z". The "dx"/"dy"/"dz" slots hold
        # nodal velocity (ops.nodeVel) which is NaN for a static analysis.
        # Map the graph-engine convention ("dy") to the live dataset key ("y").
        _DISP_COMPONENT_MAP = {"dx": "x", "dy": "y", "dz": "z"}
        ds_component = _DISP_COMPONENT_MAP.get(component, component)

        rows = []
        for nid in node_path:
            try:
                val_m = float(
                    disp_da.sel(
                        Loadcase=load_case, Node=nid, Component=ds_component
                    )
                )
                x_coord = nodes_coords[nid][0] if nid in nodes_coords else 0.0
                rows.append({"Node": nid, "_x": x_coord, component: round(val_m * 1000, 6)})
            except Exception:
                pass

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).sort_values("_x").drop(columns="_x").reset_index(drop=True)
        return df

    def _get_node_coords_df(self, girder_name: str) -> pd.DataFrame:
        """
        Build per-node coordinate DataFrame for a girder.

        Parameters
        ----------
        girder_name : str
            Girder identifier, e.g. ``"G1"``.

        Returns
        -------
        pd.DataFrame
            Columns: ``Node`` (int), ``X (m)``, ``Y (m)``, ``Z (m)``.
            Rows are sorted by X-coordinate (longitudinal axis).
            Empty DataFrame if the girder is not found.
        """
        nodes_coords, _, _ = self.build_grillage_connectivity()
        g_map, _ = self.build_girders(verbose=False)
        if girder_name not in g_map:
            return pd.DataFrame()

        rows = []
        for nid in g_map[girder_name]["path"]:
            if nid in nodes_coords:
                x, y, z = nodes_coords[nid]
                rows.append({"Node": nid, "X (m)": round(x, 6), "Y (m)": round(y, 6), "Z (m)": round(z, 6)})

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows).sort_values("X (m)").reset_index(drop=True)

    def _get_girder_sw_df(self, girder_map, nodes):
        """Internal helper to build the Girder Self weight DataFrame."""
        # 1. Identify magnitudes from bridge case
        sw_mag_map = {}
        if hasattr(self.bridge, 'self_weight_load_case') and self.bridge.self_weight_load_case:
            for lg in self.bridge.self_weight_load_case.load_groups:
                load = lg["load"]
                if "line" in type(load).__name__.lower():
                    pts = self._get_active_pts(load)
                    if pts:
                        sw_mag_map[round(pts[0].z, 3)] = pts[0].p / 1000.0
        
        sw_data = []
        total_v_audit = 0
        for g_name, g_data in girder_map.items():
            s, e = nodes[g_data["start"]], nodes[g_data["end"]]
            val = sw_mag_map.get(round(s[2], 3), 22.4)
            L = math.sqrt((e[0]-s[0])**2 + (e[2]-s[2])**2)
            total_v_audit += val * L
            
            sw_data.append({
                "Girder": g_name, "Type": "Line",
                "Start X": round(s[0], 3), "Start Y": round(s[1], 3), "Start Z": round(s[2], 3),
                "End X": round(e[0], 3), "End Y": round(e[1], 3), "End Z": round(e[2], 3),
                "Value (kN/m)": round(val, 2)
            })
        df = pd.DataFrame(sw_data)
        df.attrs["total_v"] = total_v_audit
        return df

    def _get_dead_lc_df(self, display_name, lc):
        """Internal helper to build Dead Load Case DataFrame."""
        if not lc or not lc.load_groups: return pd.DataFrame()

        case_data = []
        total_v_audit = 0
        for i, lg in enumerate(lc.load_groups, 1):
            load = lg["load"]
            cname = type(load).__name__.lower()
            pts = self._get_active_pts(load)
            row = {"ID": i}
            try:
                if "line" in cname and len(pts) >= 2:
                    p1, p2 = pts[0], pts[1]
                    val = p1.p / 1000.0
                    total_v_audit += val * math.sqrt((p2.x-p1.x)**2 + (p2.z-p1.z)**2)
                    row.update({"Type": "Line", "Start X": round(p1.x, 3), "Start Z": round(p1.z, 3), "End X": round(p2.x, 3), "End Z": round(p2.z, 3), "Value (kN/m)": round(val, 3)})
                elif "patch" in cname and len(pts) >= 4:
                    val = pts[0].p / 1000.0
                    area = (max(p.x for p in pts) - min(p.x for p in pts)) * (max(p.z for p in pts) - min(p.z for p in pts))
                    total_v_audit += val * area
                    row.update({"Type": "Patch", "P1 X": round(pts[0].x, 2), "P1 Z": round(pts[0].z, 2), "P2 X": round(pts[1].x, 2), "P2 Z": round(pts[1].z, 2), "P3 X": round(pts[2].x, 2), "P3 Z": round(pts[2].z, 2), "P4 X": round(pts[3].x, 2), "P4 Z": round(pts[3].z, 2), "Value (kN/m2)": round(val, 3)})
                elif "point" in cname and pts:
                    val = pts[0].p / 1000.0
                    total_v_audit += val
                    row.update({"Type": "Point", "X": round(pts[0].x, 3), "Z": round(pts[0].z, 3), "Value (kN)": round(val, 3)})
            except Exception: pass
            case_data.append(row)
        df = pd.DataFrame(case_data)
        df.attrs["total_v"] = total_v_audit
        return df

    def _get_vehicle_df(self, lc):
        """
        Build Moving Load (Vehicle) DataFrame using IRC6_2017 local geometry.

        For each vehicle in the load-case:
          - Detects vehicle type from the load-case name (Class70R / ClassA)
          - Reads the vehicle's global reference position from ospgrillage
          - Calls the matching IRC6_2017 method for local axle X positions,
            local wheel Z offsets, and per-axle loads
          - Global wheel position = vehicle_global + local_offset
          - Splits each axle load equally into 2 wheel loads (L / R)
          - Falls back to raw point data for unrecognised vehicle types
        """
        moving_data      = []
        total_v_audit    = 0.0
        lc_name          = lc.name   # e.g. "Case1" (new) or "Case1 ClassA L1" (legacy)
        vehicle_type_map = getattr(self.bridge, 'vehicle_type_map', {})

        for lg in lc.load_groups:
            load_obj = lg["load"]

            # ── 1. Recover global vehicle reference position ──────────────────
            global_x = 0.0
            global_z = 0.0
            gc = getattr(load_obj, 'global_coord', None)
            if gc is not None:
                global_x = float(getattr(gc, 'x', 0.0))
                global_z = float(getattr(gc, 'z', 0.0))

            # ── 2. Detect vehicle type → fetch IRC6 local geometry ────────────
            # New path: per-object lookup from analyser's vehicle_type_map
            vehicle_type = vehicle_type_map.get(id(load_obj))
            # Legacy fallback: detect from LC name (old per-vehicle LC format)
            if vehicle_type is None:
                if 'Class70R' in lc_name:
                    vehicle_type = 'Class70R'
                elif 'ClassA' in lc_name:
                    vehicle_type = 'ClassA'

            irc_data = None
            if vehicle_type == 'Class70R':
                try:
                    irc_data = IRC6_2017.cl_204_1_Class70R_vehicle_wheel()
                    irc_data['_type'] = 'Class70R(W)'
                except Exception:
                    pass
            elif vehicle_type == 'ClassA':
                try:
                    irc_data = IRC6_2017.cl_204_1_ClassA_vehicle()
                    irc_data['_type'] = 'ClassA'
                except Exception:
                    pass

            # ── 3a. IRC6 path: correct global positions + axle→wheel split ────
            if irc_data is not None:
                axle_x_local  = irc_data['x']           # local axle x positions (m)
                wheel_z_local = irc_data['z']           # local wheel z offsets, e.g. [-0.965, +0.965]
                axle_loads_N  = irc_data['wheel_loads'] # per-axle load in N  (kN=1000 in unit system)

                axle_counter  = 1
                wheel_counter = 1

                for local_x, axle_load_N in zip(axle_x_local, axle_loads_N):
                    global_axle_x = global_x + local_x          # global longitudinal position
                    axle_load_kN  = axle_load_N / 1000.0        # N → kN
                    wheel_load_kN = axle_load_kN / 2.0          # 2 wheels per axle
                    total_v_audit += axle_load_kN

                    for w_idx, local_z in enumerate(wheel_z_local):
                        side          = "L" if w_idx == 0 else "R"
                        global_wheel_z = global_z + local_z      # global transverse position

                        moving_data.append({
                            "Axle":            axle_counter,
                            "Axle Load (t)":   round(axle_load_kN,  2),
                            "Global Axle X (m)": round(global_axle_x, 3),
                            "Wheel":           f"A{axle_counter}{side}",
                            "Side":            side,
                            "Global X (m)":    round(global_axle_x,  3),
                            "Global Z (m)":    round(global_wheel_z, 3),
                            "Wheel Load (t)":  round(wheel_load_kN,  3),
                        })
                        wheel_counter += 1

                    axle_counter += 1

            # ── 3b. Fallback: read raw point data (unknown vehicle type) ──────
            else:
                sub_loads = (
                    load_obj.compound_load_obj_list
                    if hasattr(load_obj, 'compound_load_obj_list')
                    else [load_obj]
                )
                axle_counter  = 1
                wheel_counter = 1

                for sub_load in sub_loads:
                    pts = self._get_active_pts(sub_load)
                    if not pts:
                        continue
                    axle_load_kN = sum(p.p for p in pts) / 1000.0
                    total_v_audit += axle_load_kN

                    for p in pts:
                        moving_data.append({
                            "Axle":            axle_counter,
                            "Axle Load (t)":   round(axle_load_kN, 2),
                            "Global Axle X (m)": round(global_x + p.x, 3),
                            "Wheel":           wheel_counter,
                            "Side":            "-",
                            "Global X (m)":    round(global_x + p.x, 3),
                            "Global Z (m)":    round(global_z + p.z, 3),
                            "Wheel Load (t)":  round(p.p / 1000.0,    3),
                        })
                        wheel_counter += 1
                    axle_counter += 1

        df = pd.DataFrame(moving_data)
        df.attrs["total_v"] = total_v_audit
        return df

    def _print_girder_sw_extraction(self, girder_map, nodes):
        """Interactive view of girder self weight."""
        df = self._get_girder_sw_df(girder_map, nodes)
        print(f"\n{'='*110}\n>>> GIRDER SELF WEIGHT\n{'-'*110}")
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal Vertical Self-Weight: {df.attrs.get('total_v', 0):.2f} kN")
        print("=" * 110)

    def _print_single_dead_lc_extraction(self, display_name, lc):
        """Interactive view of dead load case."""
        df = self._get_dead_lc_df(display_name, lc)
        print(f"\n{'='*110}\n>>> {display_name}\n{'-'*110}")
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal Vertical Load in Case: {df.attrs.get('total_v', 0):.2f} kN")
        print("=" * 110)

    def _print_single_vehicle_extraction(self, lc):
        """Interactive view of vehicle load."""
        df = self._get_vehicle_df(lc)
        print(f"\n{'='*110}\n>>> MOVING LOAD CONFIGURATION: {lc.name}\n{'-'*110}")
        if not df.empty:
            print(df.to_string(index=False))
            print(f"\nTotal Vehicle Weight (Vertical): {df.attrs.get('total_v', 0):.2f} kN")
        print("=" * 110)

    def run_interactive_viewer(self):

        while True:

            print("==============================")
            print("Select Option:")
            print("1. Show girder paths (BFS)")
            print("2. Show Analysis Result")
            print("3. Show moving load trace")
            print("4. Show max/min envelopes")
            print("5. Show critical maximum state")
            print("6. Show girder reactions (Ra, Rb)")
            print("7. Load Extraction (Dead + Moving)")
            print("0. Exit")
            print("==============================")

            main_choice = input("Enter choice: ").strip()

            if main_choice == "0":
                self.verify_sections()
                break

            # ======================================================
            # OPTION 1 → SHOW SINGLE GIRDER PATH
            # ======================================================
            if main_choice == "1":

                # Build WITHOUT printing
                girder_map, _ = self.build_girders(verbose=False)

                print("\nAvailable Girders:")
                for g in girder_map.keys():
                    print(g)

                key = input("\nEnter girder : ").strip()

                if key not in girder_map:
                    print("❌ Invalid girder")
                    continue

                girder = girder_map[key]

                print("\n----------------------------------------")
                print(f"Girder {key}")
                print("----------------------------------------")
                print(f"Start node : {girder['start']}")
                print(f"End node   : {girder['end']}")
                print(f"Node Path  : {girder['path']}")
                print(f"Elements   : {girder['elements']}")

                print("\nElement connectivity:")
                for eid, n1, n2 in girder["element_map"]:
                    print(f"{eid:<5}: {n1} -> {n2}")

                print(f"\nLength     : {girder['length']:.3f} m")
                print("----------------------------------------")

                continue

            # ======================================================
            # OPTION 2 → EXISTING RESULT VIEWER
            # ======================================================
            if main_choice == "2":

                girder_map, elements = self.build_girders(verbose=False)
                girder_map = self.filter_girders(girder_map)
                loadcases = self.get_available_loadcases()

                component_map = {
                    "1": "Vx_i",
                    "2": "Vy_i",
                    "3": "Vz_i",
                    "4": "Mx_i",
                    "5": "My_i",
                    "6": "Mz_i",
                    # "7": "Dx",
                    # "8": "Dy",
                    # "9": "Dz"
                }

                while True:

                    print("\nSelect Girder:")
                    for i, g in enumerate(girder_map.keys(), 1):
                        print(f"{i}. {g}")
                    print("0. Back")

                    g = input().strip()

                    if g == "0":
                        break

                    if not g.isdigit():
                        print("❌ Invalid input")
                        continue

                    g = int(g)
                    if g < 1 or g > len(girder_map):
                        print("❌ Invalid girder number")
                        continue

                    key = list(girder_map.keys())[g - 1]
                    girder = girder_map[key]
                    girder_nodes = girder["path"]

                    girder_elements = [
                        eid for eid, conn in elements.items()
                        if conn[0] in girder_nodes and conn[1] in girder_nodes
                    ]

                    # ================= LOADCASE LOOP =================
                    while True:
                        self.print_load_availability()
                        print("\nSelect Loadcase:")
                        for i, lc in enumerate(loadcases, 1):
                            print(f"{i}. {lc}")
                        print("0. Back")

                        lc_in = input().strip()

                        if lc_in == "0":
                            break

                        if not lc_in.isdigit():
                            print("❌ Invalid input")
                            continue

                        lc_in = int(lc_in)
                        if lc_in < 1 or lc_in > len(loadcases):
                            print("❌ Invalid loadcase")
                            continue

                        lc = loadcases[lc_in - 1]
                        # Plotting disabled as per user request.
                        # ================= RESULT TYPE LOOP =================
                        while True:

                            print("\nSelect Result Type:")
                            for k, v in component_map.items():
                                print(f"{k}. {v}")
                            print("0. Back")

                            r = input().strip()

                            if r == "0":
                                break

                            if r not in component_map:
                                print("❌ Invalid selection")
                                continue

                            comp = component_map[r]

                            # ---------------- FORCES / MOMENTS ----------------
                            res = self.get_beam_element_results(
                                girder_elements, lc, comp
                            )

                            print(f"\nResults | {key} | {lc} | {comp}")

                            # Convert results to a pandas DataFrame for better formatting
                            data = []
                            for eid, val in res.items():
                                try:
                                    # Handle potential array values to get a clean scalar and convert to kN/kNm
                                    scalar_val = float(val) / 1000 if val is not None else val
                                except (TypeError, ValueError):
                                    scalar_val = val
                                unit = "kN" if "V" in comp else "kNm"
                                data.append({"Element": eid, f"{comp} ({unit})": scalar_val})

                            df = pd.DataFrame(data)
                            print(df.to_string(index=False))

                continue


            elif main_choice == "3":
                print("\n--- Moving Load Trace Configuration ---")
                lc_groups = self.classify_loadcases()
                moving_lcs = lc_groups["vehicle_moving"]
                if not moving_lcs:
                    print("❌ No moving load cases found.")
                    continue

                girder_map, _ = self.build_girders(verbose=False)
                girder_map = self.filter_girders(girder_map)
                g_list = list(girder_map.keys())

                print("\nSelect Girder:")
                for i, g in enumerate(g_list, 1):
                    print(f"{i}. {g}")
                print(f"{len(g_list)+1}. All Girders")
                print("0. Back")

                g_choice = input("Enter choice: ").strip()
                if g_choice == "0": continue
                
                if not g_choice:
                    g_input = None
                elif g_choice == str(len(g_list)+1):
                    g_input = None
                elif g_choice.isdigit() and 1 <= int(g_choice) <= len(g_list):
                    g_input = g_list[int(g_choice)-1]
                else:
                    print("❌ Invalid selection")
                    continue

                # Show available moving load cases
                self.print_load_availability()
                print("\nSelect Moving Load Category:")
                case_types = defaultdict(list)
                for lc in moving_lcs:
                    parts = lc.split()
                    if len(parts) >= 3:
                        case_types[f"{parts[1]} {parts[2]}"].append(lc)

                cats = sorted(case_types.keys())
                for i, cat in enumerate(cats, 1):
                    print(f"{i}. {cat}")
                print(f"{len(cats)+1}. All Categories")
                print("0. Back")

                lc_choice = input("Enter choice: ").strip()
                if lc_choice == "0": continue
                
                if not lc_choice or lc_choice == str(len(cats)+1):
                    lc_input = None
                elif lc_choice.isdigit() and 1 <= int(lc_choice) <= len(cats):
                    lc_input = cats[int(lc_choice)-1]
                else:
                    print("❌ Invalid selection")
                    continue

                self.print_moving_load_trace(load_case_filter=lc_input, girder_filter=g_input)
                continue

            elif main_choice == "4":
                print("\n--- Envelope Configuration ---")
                girder_map, _ = self.build_girders(verbose=False)
                girder_map = self.filter_girders(girder_map)
                g_list = list(girder_map.keys())
                
                print("\nSelect Girder:")
                for i, g in enumerate(g_list, 1):
                    print(f"{i}. {g}")
                print(f"{len(g_list)+1}. All Girders")
                print("0. Back")

                g_choice = input("Enter choice: ").strip()
                if g_choice == "0": continue
                
                if not g_choice or g_choice == str(len(g_list)+1):
                    g_input = None
                elif g_choice.isdigit() and 1 <= int(g_choice) <= len(g_list):
                    g_input = g_list[int(g_choice)-1]
                else:
                    print("❌ Invalid selection")
                    continue

                self.print_load_availability()
                lc_input = input("\nEnter Load Case Filter (e.g. 'ClassA') or leave blank for all: ").strip()
                if not lc_input: lc_input = None

                self.print_envelopes(load_case_filter=lc_input, girder_filter=g_input)
                continue

            elif main_choice == "5":
                self.print_critical_max_state()
                continue

            elif main_choice == "6":
                print("\n--- Girder Reactions Configuration ---")
                girder_map, _ = self.build_girders(verbose=False)
                girder_map = self.filter_girders(girder_map)
                g_list = list(girder_map.keys())
                
                print("\nSelect Girder:")
                for i, g in enumerate(g_list, 1):
                    print(f"{i}. {g}")
                print(f"{len(g_list)+1}. All Girders")
                print("0. Back")

                g_choice = input("Enter choice: ").strip()
                if g_choice == "0": continue
                
                if not g_choice or g_choice == str(len(g_list)+1):
                    g_input = None
                elif g_choice.isdigit() and 1 <= int(g_choice) <= len(g_list):
                    g_input = g_list[int(g_choice)-1]
                else:
                    print("❌ Invalid selection")
                    continue

                self.print_load_availability()
                lc_input = input("\nEnter Load Case Filter (e.g. 'ClassA' or 'Dead') or leave blank for all: ").strip()
                if not lc_input: lc_input = None

                self.print_girder_reactions(load_case_filter=lc_input, girder_filter=g_input)
                continue

            # ======================================================
            # OPTION 7 → LOAD EXTRACTION (LADDER-WISE)
            # ======================================================
            elif main_choice == "7":
                while True:
                    print("\n--- Load Extraction Category ---")
                    print("1. Dead Loads")
                    print("2. Moving Loads (Vehicles)")
                    print("0. Back")
                    
                    cat = input("Enter choice: ").strip()
                    if cat == "0": break
                    
                    if cat == "1":
                        # Dead Load Ladder - Dynamically discovered
                        avail_dead = [("Girder Self Weight", "self_weight_load_case")]
                        found_lcs = []
                        for attr in sorted(vars(self.bridge).keys()):
                            val = getattr(self.bridge, attr)
                            if attr.endswith("_load_case") and attr != "self_weight_load_case" and val is not None:
                                display_name = attr.replace("_", " ").title()
                                found_lcs.append((display_name, attr))
                        avail_dead.extend(found_lcs)

                        if not avail_dead:
                            print("❌ No dead load cases found.")
                            continue

                        while True:
                            print("\nSelect Dead Load Case:")
                            for i, (name, _) in enumerate(avail_dead, 1):
                                print(f"{i}. {name}")
                            print("0. Back")
                            
                            lc_idx = input("Enter choice: ").strip()
                            if lc_idx == "0": break
                            
                            if lc_idx.isdigit() and 1 <= int(lc_idx) <= len(avail_dead):
                                name, attr = avail_dead[int(lc_idx)-1]
                                lc = getattr(self.bridge, attr)
                                if name == "Girder Self Weight":
                                    nodes, elements, _ = self.build_grillage_connectivity()
                                    g_map, _ = self.build_girders(verbose=False)
                                    g_map = self.filter_girders(g_map)
                                    self._print_girder_sw_extraction(g_map, nodes)
                                else:
                                    self._print_single_dead_lc_extraction(name, lc)
                            else:
                                print("❌ Invalid selection")
                    
                    elif cat == "2":
                        # Moving Load Ladder
                        if not hasattr(self.bridge, 'vehicle_load_cases_list') or not self.bridge.vehicle_load_cases_list:
                            print("❌ No vehicle load cases found.")
                            continue
                        
                        v_lcs = self.bridge.vehicle_load_cases_list
                        while True:
                            print("\nSelect Vehicle Case:")
                            for i, lc in enumerate(v_lcs, 1):
                                print(f"{i}. {lc.name}")
                            print("0. Back")
                            
                            v_idx = input("Enter choice: ").strip()
                            if v_idx == "0": break
                            
                            if v_idx.isdigit() and 1 <= int(v_idx) <= len(v_lcs):
                                self._print_single_vehicle_extraction(v_lcs[int(v_idx)-1])
                            else:
                                print("❌ Invalid selection")
                    else:
                        print("❌ Invalid option")
                continue

            else:
                print("❌ Invalid option")

