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


class PlateGirderAnalysisResults:

    # ========================================================
    # INITIALIZATION
    # ========================================================
    def __init__(self, dataset, model):  # storing analysis result
        self.ds = dataset
        self.model = model

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
    # LOADCASE CLASSIFICATION
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

        for i, (s, e) in enumerate(zip(start_nodes, end_nodes), start=1):
            path = self.bfs_shortest_path(adj, s, e)
            path_elements, element_map = self.get_elements_along_path(path, elements)
            length = self.compute_path_distance(nodes, path)

            status = "VERIFIED" if abs(length - span_length) < 1e-6 else "NOT MATCHING"

            if verbose:
                print("----------------------------------------")
                print(f"Girder g{i}")
                print("----------------------------------------")

                print("Path     :", path)
                print("Elements :", path_elements)

                print("\nElement connectivity:")
                for eid, n1, n2 in element_map:
                    print(f"{eid:<5}: {n1} -> {n2}")

                print(f"\nLength   : {length:.3f} m ({status})")
                print("----------------------------------------\n")

            girder_map[f"g{i}"] = {
                "start": s,
                "end": e,
                "path": path,
                "elements": path_elements,
                "element_map": element_map,
                "length": length
            }

        return girder_map, elements

    # ========================================================
    # PRINT MOVING LOAD TRACE
    # ========================================================
    def print_moving_load_trace(self, load_case_filter=None, girder_filter=None, element_filter=None):
        """
        Prints the BMD and SFD for every point (element) when cars are moving.
        Iterates through all moving load cases and all girders.

        :param load_case_filter: (str or list) Print only load cases containing this string(s).
        :param girder_filter: (str or list) Print only girders matching this name(s) (e.g. "g1").
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
                print(
                    f"  {'Element':<10} | {'Vy_i (kN)':<12} | {'Vy_j (kN)':<12} | {'Mz_i (kNm)':<12} | {'Mz_j (kNm)':<12}")
                print("  " + "-" * 70)

                elements = girder_data["elements"]

                # Filter elements if requested
                if e_filter:
                    elements = [e for e in elements if e in e_filter]
                    if not elements:
                        continue  # Skip if no elements match

                # 5. Get results for this girder and loadcase
                # Retrieve all required components at once for efficiency
                try:
                    # Using dataset directly for speed scaling with multiple elements
                    # Select specific loadcase and elements
                    subset = self.ds.sel(Loadcase=lc, Element=elements)

                    # Extract values
                    vy_i = subset.sel(Component="Vy_i")["forces"].values
                    vy_j = subset.sel(Component="Vy_j")["forces"].values
                    mz_i = subset.sel(Component="Mz_i")["forces"].values
                    mz_j = subset.sel(Component="Mz_j")["forces"].values

                    # 6. Print results for each element
                    for idx, eid in enumerate(elements):
                        print(
                            f"  {eid:<10} | {vy_i[idx]:<12.3f} | {vy_j[idx]:<12.3f} | {mz_i[idx]:<12.3f} | {mz_j[idx]:<12.3f}")

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

        print("\n================ VEHICLE ENVELOPES (PER POSITION) ================")

        for lc in moving_lcs:
            print(f"\n>>> Load Case: {lc}")
            print(
                f"{'Girder':<10} | {'Max Vy (kN)':<12} | {'Min Vy (kN)':<12} | {'Max Mz (kNm)':<12} | {'Min Mz (kNm)':<12}")
            print("-" * 75)

            for girder_name, girder_data in girder_map.items():
                if g_filter and girder_name not in g_filter:
                    continue

                elements = girder_data["elements"]

                try:
                    # Select ONLY this loadcase and elements for this girder
                    subset = self.ds.sel(Loadcase=lc, Element=elements)

                    # Get max/min across elements and both i/j components for this specific loadcase
                    vy_max = max(subset.sel(Component="Vy_i")["forces"].max().values,
                                 subset.sel(Component="Vy_j")["forces"].max().values)
                    vy_min = min(subset.sel(Component="Vy_i")["forces"].min().values,
                                 subset.sel(Component="Vy_j")["forces"].min().values)
                    mz_max = max(subset.sel(Component="Mz_i")["forces"].max().values,
                                 subset.sel(Component="Mz_j")["forces"].max().values)
                    mz_min = min(subset.sel(Component="Mz_i")["forces"].min().values,
                                 subset.sel(Component="Mz_j")["forces"].min().values)

                    print(
                        f"{girder_name:<10} | {float(vy_max):<12.3f} | {float(vy_min):<12.3f} | {float(mz_max):<12.3f} | {float(mz_min):<12.3f}")
                except Exception as e:
                    print(f"{girder_name:<10} | ❌ Error: {e}")

        print("\n===================================================================")

    def run_interactive_viewer(self):

        while True:

            print("\n==============================")
            print("Select Option:")
            print("1. Show girder paths (BFS)")
            print("2. Show Analysis Result")
            print("3. Show moving load trace")
            print("4. Show max/min envelopes")
            print("0. Exit")
            print("==============================")

            main_choice = input("Enter choice: ").strip()

            if main_choice == "0":
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
                        import plots_widget
                        plots_widget.CURRENT_LOADCASE = lc
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

                            # ---------------- FORCES ----------------
                            res = self.get_beam_element_results(
                                girder_elements, lc, comp
                            )

                            print(f"\nResults | {key} | {lc} | {comp}")
                            for eid, val in res.items():
                                print(f"Element {eid}: {val}")

                continue


            elif main_choice == "3":
                print("\n--- Moving Load Trace Configuration ---")

                # Get moving load cases
                lc_groups = self.classify_loadcases()
                moving_lcs = lc_groups["vehicle_moving"]

                if not moving_lcs:
                    print("❌ No moving load cases found.")
                    continue

                # Show available girders
                girder_map, _ = self.build_girders(verbose=False)
                print("\nAvailable Girders:")
                for g in girder_map.keys():
                    print(f"  - {g}")

                g_input = input("Enter Girder Name (or leave blank for all): ").strip()
                if not g_input:
                    g_input = None

                # Show available moving load cases
                print("\nAvailable Moving Load Cases:")
                # Group by case type for better readability
                case_types = {}
                for lc in moving_lcs:
                    # Extract case type (e.g., "Case1 ClassA" from "Moving Case1 ClassA L1 at...")
                    parts = lc.split()
                    if len(parts) >= 3:
                        case_type = f"{parts[1]} {parts[2]}"  # e.g., "Case1 ClassA"
                        if case_type not in case_types:
                            case_types[case_type] = []
                        case_types[case_type].append(lc)

                for case_type in sorted(case_types.keys()):
                    print(f"  - {case_type} ({len(case_types[case_type])} positions)")

                print("\nEnter Load Case Filter (e.g., 'Case1', 'ClassA', 'Case2 Class70R')")
                lc_input = input("Filter (or leave blank for all): ").strip()
                if not lc_input:
                    lc_input = None

                print("\n")
                self.print_moving_load_trace(load_case_filter=lc_input, girder_filter=g_input)

                continue

            elif main_choice == "4":
                print("\n--- Envelope Configuration ---")

                # Show available girders
                girder_map, _ = self.build_girders(verbose=False)
                print("\nAvailable Girders:")
                for g in girder_map.keys():
                    print(f"  - {g}")

                g_input = input("Enter Girder Name (or leave blank for all): ").strip()
                if not g_input:
                    g_input = None

                lc_input = input("Enter Load Case Filter (or leave blank for all): ").strip()
                if not lc_input:
                    lc_input = None

                self.print_envelopes(load_case_filter=lc_input, girder_filter=g_input)
                continue

            else:
                print("❌ Invalid option")
