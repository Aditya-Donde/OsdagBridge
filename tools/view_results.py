import json
import pandas as pd
from pathlib import Path

def json_to_dataframes(json_path):
    """
    Reads the bridge_plot_data.json and returns two flattened DataFrames:
    one for displacements and one for forces.
    """
    if not Path(json_path).exists():
        print(f"❌ Error: {json_path} not found.")
        return None, None

    with open(json_path, "r") as f:
        data = json.load(f)

    # --- 1. Flatten Displacements ---
    disp_rows = []
    for lc, nodes in data.get("displacements", {}).items():
        for node_id, components in nodes.items():
            row = {"loadcase": lc, "node_id": node_id}
            
            # Only add components that actually have valid numbers!
            for comp, val in components.items():
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    row[comp] = val
            
            disp_rows.append(row)
    
    df_disp = pd.DataFrame(disp_rows)

    # --- 2. Flatten Forces ---
    force_rows = []
    for lc, elements in data.get("forces", {}).items():
        for elem_id, components in elements.items():
            row = {"loadcase": lc, "element_id": elem_id}
            
            # Only add components that actually have valid numbers!
            for comp, val in components.items():
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    row[comp] = val
            
            force_rows.append(row)
            
    df_force = pd.DataFrame(force_rows)

    return df_disp, df_force

if __name__ == "__main__":
    current_dir = Path(__file__).parent
    json_file = current_dir / "bridge_plot_data.json"
    
    print(f"🔍 Looking for file at: {json_file.resolve()}")
    
    df_disp, df_force = json_to_dataframes(json_file)

    if df_disp is not None:
        print("\n--- NODAL DISPLACEMENTS (First 10 rows) ---")
        print(df_disp.head(10).to_string(index=False))
        
        print("\n--- ELEMENT FORCES (First 10 rows) ---")
        print(df_force.head(10).to_string(index=False))

        # --- Example: Search for Max Moment Mz ---
        if 'Mz_i' in df_force.columns:
            max_mom = df_force['Mz_i'].max()
            print(f"\n✅ Peak Positive Moment (Mz_i): {max_mom:.2f} kNm")

        # Optional: Save to Excel for manual checking
        df_force.to_excel("bridge_results_verification.xlsx")