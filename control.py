from MILP_lambda import create_model
from gurobipy import Model, GRB, quicksum
from parser import parse_json_from_file
import os
import csv

pfad= "TBLOP mit Hüllen/test"

TABLE_PATH = os.path.join(pfad, "runtime_table.txt")

def _ensure_table_header(path: str):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow([
                "instance", "runtime_sec", "status",
                "obj_val", "best_bound", "mip_gap", "node_count"
            ])

def _status_name(code: int) -> str:
    # kleine, praktische Abbildung der wichtigsten Gurobi-Statuscodes
    mapping = {
        GRB.LOADED: "LOADED",
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.CUTOFF: "CUTOFF",
        GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
        GRB.NODE_LIMIT: "NODE_LIMIT",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
    }
    return mapping.get(code, str(code))

# Stelle sicher, dass der Ausgabeordner existiert (hast du schon)
sol_dir = os.path.join(pfad, "sol")
os.makedirs(sol_dir, exist_ok=True)

# Stelle sicher, dass die Tabelle existiert (Header)
_ensure_table_header(TABLE_PATH)

for datei in os.listdir(pfad):
    full_path = os.path.join(pfad, datei)
    if os.path.isdir(full_path):
        continue

    print(datei)
    print(full_path)

    alpha_value = 0.5
    lambda_value = 0.01

    (pages, article, layouts, resorts, article_resorts, resort_page,
     layouts_pages, box_layouts, hull_layout_box, hull_article,
     article_length, hull_params, article_priority) = parse_json_from_file(full_path)

    model = create_model(pages, article, layouts, resorts, article_resorts,
                         resort_page, layouts_pages, box_layouts, hull_layout_box,
                         hull_article, article_length, hull_params, article_priority,
                         alpha_value, lambda_value)

    # Logfile je Instanz
    model.Params.LogFile = os.path.join(pfad, f"{datei}.log")
    # Zeitlimit
    model.setParam("TimeLimit", 3600)

    model.optimize()

    # ------ NEU: Zeile in TXT-Tabelle schreiben ------
    instance_name = os.path.splitext(datei)[0]
    status_code = model.Status
    status_str = _status_name(status_code)
    runtime = getattr(model, "Runtime", None)
    node_count = getattr(model, "NodeCount", None)

    # obj_val / best_bound / mip_gap vorsichtig lesen (je nach Problemtyp/Status evtl. nicht vorhanden)
    def _try_attr(obj, attr):
        try:
            return getattr(obj, attr)
        except Exception:
            return None

    obj_val = None
    if getattr(model, "SolCount", 0) > 0 or status_code in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        obj_val = _try_attr(model, "ObjVal")

    best_bound = _try_attr(model, "ObjBound")
    mip_gap = _try_attr(model, "MIPGap")  # nur bei MIPs definiert

    with open(TABLE_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow([
            instance_name,
            f"{runtime:.4f}" if runtime is not None else "",
            status_str,
            f"{obj_val:.6f}" if isinstance(obj_val, (int, float)) else "",
            f"{best_bound:.6f}" if isinstance(best_bound, (int, float)) else "",
            f"{mip_gap:.6f}" if isinstance(mip_gap, (int, float)) else "",
            node_count if node_count is not None else ""
        ])
    # ------ ENDE Tabelle ------

    if model.status == GRB.INFEASIBLE:
        print("Modell ist unlösbar. Berechne IIS...")
        model.computeIIS()
        model.write(os.path.join(sol_dir, f"{datei}.ilp"))
        for c in model.getConstrs():
            if c.IISConstr:
                print(f"IIS enthält Constraint: {c.ConstrName}")
        # Optional: auch hier .sol mit Runtime-Header erzeugen
        sol_path = os.path.join(sol_dir, f"{datei}.sol")
        with open(sol_path, "w", encoding="utf-8") as f:
            f.write(f"# Runtime: {model.Runtime:.2f} seconds\n")
            f.write("# INFEASIBLE\n")
    else:
        # LP und SOL schreiben
        lp_path = os.path.join(sol_dir, f"{datei}.lp")
        sol_path = os.path.join(sol_dir, f"{datei}.sol")
        model.write(lp_path)
        model.write(sol_path)

        # Rechenzeit oben in die .sol-Datei einfügen
        try:
            with open(sol_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            runtime_line = f"# Runtime: {model.Runtime:.2f} seconds\n"
            lines = [ln for ln in lines if not ln.strip().startswith("# Runtime:")]
            lines.insert(0, runtime_line)
            with open(sol_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Warnung: Konnte Runtime nicht in {sol_path} schreiben: {e}")

        # ... dein bestehender Lösungs-Print/Check bleibt unverändert ...


