from MILP_lambda import create_model
from gurobipy import Model, GRB, quicksum
from Models.parser import parse_json_from_file
import os
import csv
import os
from gurobipy import GRB

def solve_instances(instance_dir):
    # Ausgabe-Ordner (falls noch nicht vorhanden) anlegen
    lp_dir  = os.path.join(instance_dir, "lp")
    lp_mps_dir = os.path.join(instance_dir, "lp", "mps")
    sol_dir = os.path.join(instance_dir, "sol")
    os.makedirs(lp_dir, exist_ok=True)
    os.makedirs(lp_mps_dir, exist_ok=True)
    os.makedirs(sol_dir, exist_ok=True)

    # --- NEU: Pfad für Zusammenfassungsdatei (CSV-Text) ---
    summary_path = os.path.join(sol_dir, "summary_results.csv")
    # Header nur einmal schreiben, falls Datei noch nicht existiert
    if not os.path.exists(summary_path):
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["instance_name", "status", "runtime_s", "objective", "mip_gap"])

    alpha_value = 0.5
    lambda_value = 0.01

    # Über alle JSON-Instanzen in dem Ordner iterieren
    for fname in os.listdir(instance_dir):
        if not fname.endswith(".json"):
            continue  # nur JSONs betrachten

        instance_name = os.path.splitext(fname)[0]
        name = os.path.join(instance_dir, fname)

        print(f"=== Löse Instanz: {instance_name} ===")

        # Instanz einlesen
        pages, article, layouts, resorts, article_resorts, resort_page, \
        layouts_pages, box_layouts, hull_layout_box, hull_article, \
        article_length, hull_params, article_priority = parse_json_from_file(name)

        # Modell bauen
        model = create_model(
            pages, article, layouts, resorts, article_resorts, resort_page,
            layouts_pages, box_layouts, hull_layout_box, hull_article,
            article_length, hull_params, article_priority,
            alpha_value, lambda_value
        )

        # Gurobi-Parameter
        model.setParam('TimeLimit', 3600)
        model.Params.LogFile = os.path.join(sol_dir, f"{instance_name}.log")
        model.Params.Threads = 1

        # Modell-Dateien schreiben
        model.write(os.path.join(lp_mps_dir, f"{instance_name}.mps"))

        # Optimieren
        model.optimize()

        # --- NEU: Kennzahlen für Zusammenfassung auslesen ---
        status = model.Status
        runtime = model.Runtime  # Lösungsdauer in Sekunden

        # Default-Werte für den Fall, dass keine Lösung gefunden wurde
        obj_val = None
        mip_gap = None

        if model.SolCount > 0:
            obj_val = model.ObjVal
            # MIP-Gap nur sinnvoll bei MIPs, sonst 0.0 setzen
            try:
                mip_gap = model.MIPGap
            except AttributeError:
                mip_gap = 0.0

        # In CSV-Zusammenfassung schreiben (auch wenn infeasible oder TimeLimit)
        with open(summary_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([instance_name, status, runtime, obj_val, mip_gap])

        if model.status == GRB.INFEASIBLE:
            print(f"Modell {instance_name} ist unlösbar. Berechne IIS...")
            model.computeIIS()
            model.write(os.path.join(lp_dir, f"{instance_name}.ilp"))
            for c in model.getConstrs():
                if c.IISConstr:
                    print(f"IIS enthält Constraint: {c.ConstrName}")
            continue  # nächste Instanz

        # Nur wenn nicht infeasible:
        model.write(os.path.join(lp_dir, f"{instance_name}.lp"))
        model.write(os.path.join(sol_dir, f"{instance_name}.sol"))

        solution_dict = {}
        for v in model.getVars():
            if v.X != 0:
                # Debug-Ausgabe (optional)
                print(f"{v.VarName}: {v.X}")
                if v.VarName[0] == "x":
                    parts = v.VarName.split("_")
                    solution_dict[int(parts[1])] = int(parts[-1])

        print("--------------------------------")
        for i in solution_dict:
            if article_length[i] < hull_params[solution_dict[i]]["min"]:
                underfill_rate = round(
                    -100 * (article_length[i] - hull_params[solution_dict[i]]["min"]) /
                    hull_params[solution_dict[i]]["min"], 3
                )
                print(f"Artikel {i} unterfüllt Hülle {solution_dict[i]} um {underfill_rate}%")
            
            if article_length[i] > hull_params[solution_dict[i]]["max"]:
                overfill_rate = 100 * (
                    article_length[i] - hull_params[solution_dict[i]]["max"]
                ) / hull_params[solution_dict[i]]["max"]
                print(f"Artikel {i} überfüllt Hülle {solution_dict[i]} um {overfill_rate}%")

        # z- und v-Variablen zählen
        z_count = 0
        v_count = 0

        for v in model.getVars():
            if abs(v.X) > 1e-9:
                if v.VarName.startswith("z"):
                    z_count += 1
                if v.VarName.startswith("v"):
                    v_count += 1

        print("================================")
        print(f"Instanz: {instance_name}")
        print(f"Anzahl z-Variablen != 0: {z_count}")
        print(f"Anzahl v-Variablen != 0: {v_count}")
        print("================================\n")

if __name__ == "__main__":
    instance_size = "Large"
    instance_type = "L30P180(B)"
    base_dir = os.path.dirname(__file__)
    instance_dir = os.path.join(base_dir, "Instances", "Diss", f"{instance_size}",f"{instance_type}")
    solve_instances(base_dir=base_dir, isntance_dir=instance_dir)
