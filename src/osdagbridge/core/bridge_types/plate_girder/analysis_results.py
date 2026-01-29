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
    def __init__(self, dataset, model):        #storing analysis result
        self.ds = dataset
        self.model = model


    # ========================================================
    # DATASET BASED RESULTS (FORCES / MOMENTS)
    # ========================================================
    def get_beam_element_results(self, element_ids, loadcase, component):                   #reads beam force and moment

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


    def get_available_loadcases(self):                                              #get loadcases
        return list(self.ds.coords["Loadcase"].values)


    # ========================================================
    # OPENSEES NODAL DEFLECTION (FINAL STATE)
    # ========================================================
    def get_girder_deflection(self, girder_nodes, direction):                       #give total deflection

        dof_map = {"x": 1, "y": 2, "z": 3}
        dof = dof_map[direction]

        disp = {}
        for n in girder_nodes:
            try:
                disp[n] = ops.nodeDisp(n, dof)
            except Exception:
                disp[n] = 0.0

        return disp
    # ========================================================
    # OPENSEES DEFLECTION PER LOADCASE (RE-ANALYSIS)
    # ========================================================
    def get_deflection_per_loadcase(self, girder_nodes, loadcase, direction):

        dof_map = {"x": 1, "y": 2, "z": 3}
        dof = dof_map[direction]

        # reset previous analysis
        ops.wipeAnalysis()

        # analyze only this loadcase
        self.model.analyze(load_case=[loadcase])

        disp = {}
        for n in girder_nodes:
            try:
                disp[n] = ops.nodeDisp(n, dof)
            except Exception:
                disp[n] = 0.0

        return disp


    # ========================================================
    # GRILLAGE CONNECTIVITY
    # ========================================================
    def build_grillage_connectivity(self):          #connectivity between nodes[raph for bfs]

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


    def get_elements_along_path(self, path, elements):
        """
        Returns:
        - list of element IDs along the girder
        - connectivity info for printing
        """

        path_elements = []
        element_map = []

        for eid, conn in elements.items():
            if len(conn) != 2:
                continue

            n1, n2 = conn

            # element lies on girder if both nodes are in BFS path
            if n1 in path and n2 in path:
                path_elements.append(eid)
                element_map.append((eid, n1, n2))

        return path_elements, element_map
    # ========================================================
    # BUILD LOGICAL GIRDERS (g1, g2, g3...)
    # ========================================================
    def build_girders(self):                                                        #create girder

        nodes, elements, adj = self.build_grillage_connectivity()

        start_nodes = self.model.get_element(
            member="start_edge", options="nodes"
        )
        end_nodes = self.model.get_element(
            member="end_edge", options="nodes"
        )

        print("\nStart edge nodes :", start_nodes)
        print("End edge nodes   :", end_nodes)

        # span length
        x_coords = [c[0] for c in nodes.values()]
        span_length = max(x_coords) - min(x_coords)

        print(f"\nSpan length from geometry = {span_length}\n")

        girder_map = {}

        for i, (s, e) in enumerate(zip(start_nodes, end_nodes), start=1):
            path = self.bfs_shortest_path(adj, s, e)
            path_elements, element_map = self.get_elements_along_path(path, elements)
            length = self.compute_path_distance(nodes, path)

            status = "VERIFIED" if abs(length - span_length) < 1e-6 else "NOT MATCHING"

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

    def print_girder_paths_with_input(self):
        """
        Asks user for basic grillage info and prints
        girder-wise BFS paths in formatted form.
        """

        # -----------------------------
        # User input
        # -----------------------------
        try:
            n_long = int(input("Enter number of longitudinal beams: "))
            n_trans = int(input("Enter number of transverse slabs: "))
            spacing = float(input("Enter spacing / distance (m): "))
        except:
            print("❌ Invalid input")
            return

        nodes, elements, adj = self.build_grillage_connectivity()

        start_nodes = self.model.get_element(
            member="start_edge", options="nodes"
        )

        end_nodes = self.model.get_element(
            member="end_edge", options="nodes"
        )

        print("\nStart edge nodes:", start_nodes)
        print("End edge nodes  :", end_nodes)
        print()

        # -----------------------------
        # Loop over girders
        # -----------------------------
        for i, (s, e) in enumerate(zip(start_nodes, end_nodes), start=1):

            path = self.bfs_shortest_path(adj, s, e)
            path_elements, element_map = self.get_elements_along_path(path, elements)
            length = self.compute_path_distance(nodes, path)

            print("----------------------------------------")
            print(f"Girder g{i}")
            print("----------------------------------------")

            print(f"Start node : {s}")
            print(f"End node   : {e}")
            print(f"Path       : {path}")
            print(f"Elements   : {path_elements}")

            print("\nElement connectivity:")
            for eid, n1, n2 in element_map:
                print(f"{eid:<5}: {n1} -> {n2}")

            print(f"\nLength     : {length:.3f} m")
            print("----------------------------------------\n")

    # ========================================================
    # INTERACTIVE VIEWER
    # ========================================================
    def run_interactive_viewer(self):

        while True:

            print("\n==============================")
            print("Select Option:")
            print("1. Show girder paths (BFS)")
            print("2. Show analysis results")
            print("0. Exit")
            print("==============================")

            main_choice = input("Enter choice: ").strip()

            if main_choice == "0":
                break

            # ======================================================
            # OPTION 1 → ONLY BFS / GIRDER CONNECTIVITY
            # ======================================================
            if main_choice == "1":
                self.print_girder_paths_with_input()
                continue

            # ======================================================
            # OPTION 2 → EXISTING RESULT VIEWER (UNCHANGED)
            # ======================================================
            if main_choice == "2":

                girder_map, elements = self.build_girders()
                loadcases = self.get_available_loadcases()

                component_map = {
                    "1": "Vx_i",
                    "2": "Vy_i",
                    "3": "Vz_i",
                    "4": "Mx_i",
                    "5": "My_i",
                    "6": "Mz_i",
                    "7": "Dx",
                    "8": "Dy",
                    "9": "Dz"
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

                            # ---------------- DEFLECTION ----------------
                            if comp in ["Dx", "Dy", "Dz"]:

                                direction = comp[-1].lower()

                                disp = self.get_deflection_per_loadcase(
                                    girder_nodes, lc, direction
                                )

                                print(f"\nDeflection ({comp}) | {lc}")
                                print("--------------------------------")
                                for n, v in disp.items():
                                    print(f"Node {n}: {v}")
                                print("--------------------------------")
                                continue

                            # ---------------- FORCES ----------------
                            res = self.get_beam_element_results(
                                girder_elements, lc, comp
                            )

                            print(f"\nResults | {key} | {lc} | {comp}")
                            for eid, val in res.items():
                                print(f"Element {eid}: {val}")

                continue

            else:
                print("❌ Invalid option")