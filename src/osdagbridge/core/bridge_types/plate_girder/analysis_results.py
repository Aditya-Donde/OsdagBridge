# ============================================================
# Plate Girder Analysis Results
# ============================================================
# 1. Reads OpenSees result dataset (forces, moments)
# 2. Builds logical girders using BFS
# 3. Allows girder-wise interactive result viewing
# ============================================================

import math
from collections import defaultdict, deque
import openseespy.opensees as ops
import pandas as pd


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

        vehicle_static = []
        vehicle_moving = []
        dead_loads = []

        for lc in all_lc:

            name = str(lc).lower()

            # -----------------------------
            # MOVING VEHICLES
            # -----------------------------
            if "moving" in name:
                vehicle_moving.append(lc)
                continue

            # -----------------------------
            # STATIC VEHICLES
            # Detect your naming pattern
            # -----------------------------
            if name.startswith("case"):
                vehicle_static.append(lc)
                continue

            if "classa" in name or "70r" in name:
                vehicle_static.append(lc)
                continue

            # -----------------------------
            # DEAD LOADS
            # -----------------------------
            dead_loads.append(lc)

        return {
            "all": all_lc,
            "dead": dead_loads,
            "vehicle_static": vehicle_static,
            "vehicle_moving": vehicle_moving,
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

        # AUTO EXTRACT START / END
        x_coords = {n: coord[0] for n, coord in nodes.items()}

        min_x = min(x_coords.values())
        max_x = max(x_coords.values())

        start_nodes = [n for n, x in x_coords.items() if x == min_x]
        end_nodes = [n for n, x in x_coords.items() if x == max_x]

        start_nodes.sort(key=lambda n: nodes[n][2])
        end_nodes.sort(key=lambda n: nodes[n][2])

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



                    # --- Vy Envelope ---
                    vy_i = subset.sel(Component="Vy_i")["forces"]
                    vy_j = subset.sel(Component="Vy_j")["forces"]

                    # --- Vx Envelope ---
                    vx_i = subset.sel(Component="Vx_i")["forces"]
                    vx_j = subset.sel(Component="Vx_j")["forces"]

                    # --- Vz Envelope ---
                    vz_i = subset.sel(Component="Vz_i")["forces"]
                    vz_j = subset.sel(Component="Vz_j")["forces"]

                    # --- Mx Envelope ---
                    mx_i = subset.sel(Component="Mx_i")["forces"]
                    mx_j = subset.sel(Component="Mx_j")["forces"]

                    # --- My Envelope ---
                    my_i = subset.sel(Component="My_i")["forces"]
                    my_j = subset.sel(Component="My_j")["forces"]

                    # --- Mz Envelope ---
                    mz_i = subset.sel(Component="Mz_i")["forces"]
                    mz_j = subset.sel(Component="Mz_j")["forces"]

                    # Compute max/min for Vy
                    mxi, mxj = float(vy_i.max()), float(vy_j.max())
                    if mxi >= mxj:
                        v_max, v_max_e = mxi / 1000, int(vy_i.idxmax())
                    else:
                        v_max, v_max_e = mxj / 1000, int(vy_j.idxmax())

                    mni, mnj = float(vy_i.min()), float(vy_j.min())
                    if mni <= mnj:
                        v_min, v_min_e = mni / 1000, int(vy_i.idxmin())
                    else:
                        v_min, v_min_e = mnj / 1000, int(vy_j.idxmin())

                    # Compute max/min for Vx
                    mx_i_val, mx_j_val = float(vx_i.max()), float(vx_j.max())
                    if mx_i_val >= mx_j_val:
                        vx_max, vx_max_e = mx_i_val / 1000, int(vx_i.idxmax())
                    else:
                        vx_max, vx_max_e = mx_j_val / 1000, int(vx_j.idxmax())

                    mn_i_val, mn_j_val = float(vx_i.min()), float(vx_j.min())
                    if mn_i_val <= mn_j_val:
                        vx_min, vx_min_e = mn_i_val / 1000, int(vx_i.idxmin())
                    else:
                        vx_min, vx_min_e = mn_j_val / 1000, int(vx_j.idxmin())

                    # Compute max/min for Vz
                    mz_i_val, mz_j_val = float(vz_i.max()), float(vz_j.max())
                    if mz_i_val >= mz_j_val:
                        vz_max, vz_max_e = mz_i_val / 1000, int(vz_i.idxmax())
                    else:
                        vz_max, vz_max_e = mz_j_val / 1000, int(vz_j.idxmax())

                    mnz_i_val, mnz_j_val = float(vz_i.min()), float(vz_j.min())
                    if mnz_i_val <= mnz_j_val:
                        vz_min, vz_min_e = mnz_i_val / 1000, int(vz_i.idxmin())
                    else:
                        vz_min, vz_min_e = mnz_j_val / 1000, int(vz_j.idxmin())

                    # Compute max/min for Mx
                    mx_i_val, mx_j_val = float(mx_i.max()), float(mx_j.max())
                    if mx_i_val >= mx_j_val:
                        mx_max, mx_max_e = mx_i_val / 1000, int(mx_i.idxmax())
                    else:
                        mx_max, mx_max_e = mx_j_val / 1000, int(mx_j.idxmax())

                    mnx_i_val, mnx_j_val = float(mx_i.min()), float(mx_j.min())
                    if mnx_i_val <= mnx_j_val:
                        mx_min, mx_min_e = mnx_i_val / 1000, int(mx_i.idxmin())
                    else:
                        mx_min, mx_min_e = mnx_j_val / 1000, int(mx_j.idxmin())

                    # Compute max/min for My
                    my_i_val, my_j_val = float(my_i.max()), float(my_j.max())
                    if my_i_val >= my_j_val:
                        my_max, my_max_e = my_i_val / 1000, int(my_i.idxmax())
                    else:
                        my_max, my_max_e = my_j_val / 1000, int(my_j.idxmax())

                    mny_i_val, mny_j_val = float(my_i.min()), float(my_j.min())
                    if mny_i_val <= mny_j_val:
                        my_min, my_min_e = mny_i_val / 1000, int(my_i.idxmin())
                    else:
                        my_min, my_min_e = mny_j_val / 1000, int(my_j.idxmin())

                    # Compute max/min for Mz
                    mmxi, mmxj = float(mz_i.max()), float(mz_j.max())
                    if mmxi >= mmxj:
                        m_max, m_max_e = mmxi / 1000, int(mz_i.idxmax())
                    else:
                        m_max, m_max_e = mmxj / 1000, int(mz_j.idxmax())

                    mmni, mmnj = float(mz_i.min()), float(mz_j.min())
                    if mmni <= mmnj:
                        m_min, m_min_e = mmni / 1000, int(mz_i.idxmin())
                    else:
                        m_min, m_min_e = mmnj / 1000, int(mz_j.idxmin())

                    # Group results by element to avoid redundant rows
                    crit_eles = defaultdict(
                        lambda: {
                            "Max Vy (kN)": "-",
                            "Min Vy (kN)": "-",
                            "Max Vx (kN)": "-",
                            "Min Vx (kN)": "-",
                            "Max Vz (kN)": "-",
                            "Min Vz (kN)": "-",
                            "Max Mx (kNm)": "-",
                            "Min Mx (kNm)": "-",
                            "Max My (kNm)": "-",
                            "Min My (kNm)": "-",
                            "Max Mz (kNm)": "-",
                            "Min Mz (kNm)": "-",
                        })
                    crit_eles[v_max_e]["Max Vy (kN)"] = f"{v_max:.3f}"
                    crit_eles[v_min_e]["Min Vy (kN)"] = f"{v_min:.3f}"
                    crit_eles[vx_max_e]["Max Vx (kN)"] = f"{vx_max:.3f}"
                    crit_eles[vx_min_e]["Min Vx (kN)"] = f"{vx_min:.3f}"
                    crit_eles[vz_max_e]["Max Vz (kN)"] = f"{vz_max:.3f}"
                    crit_eles[vz_min_e]["Min Vz (kN)"] = f"{vz_min:.3f}"
                    crit_eles[mx_max_e]["Max Mx (kNm)"] = f"{mx_max:.3f}"
                    crit_eles[mx_min_e]["Min Mx (kNm)"] = f"{mx_min:.3f}"
                    crit_eles[my_max_e]["Max My (kNm)"] = f"{my_max:.3f}"
                    crit_eles[my_min_e]["Min My (kNm)"] = f"{my_min:.3f}"
                    crit_eles[m_max_e]["Max Mz (kNm)"] = f"{m_max:.3f}"
                    crit_eles[m_min_e]["Min Mz (kNm)"] = f"{m_min:.3f}"

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

    def run_interactive_viewer(self):

        while True:

            print("\n==============================")
            print("Select Option:")
            print("1. Show girder paths (BFS)")
            print("2. Show Analysis Result")
            print("3. Show moving load trace")
            print("4. Show max/min envelopes")
            print("5. Show critical maximum state")
            print("6. Show girder reactions (Ra, Rb)")
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

            else:
                print("❌ Invalid option")

