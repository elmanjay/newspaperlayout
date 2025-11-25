from MILPmI import create_model
import os
from gurobipy import  GRB
from Models.parser import parse_json_from_file
import numpy as np

# Annahme: Diese Funktionen/Module existieren und werden importiert
# from your_module import parse_json_from_file, create_model

def list_instance_files(folder_path):
    """
    Gibt alle Dateipfade in einem Verzeichnis zurück, die reguläre Dateien sind.
    """
    return [
        os.path.join(folder_path, filename)
        for filename in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, filename))
    ]

def min_max_normalize(array):
    """
    Führt Min-Max-Normalisierung eines numpy-Arrays auf [0,1] durch.
    """
    array = np.array(array, dtype=float)
    return (array - array.min()) / (array.max() - array.min())

def solve_for_alphas(pages, article, layouts, resorts,
                     article_resorts, resort_page, layouts_pages,
                     box_layouts, hull_layout_box, hull_article,
                     article_length, hull_params, article_priority,
                     alpha_list, instance_name, output_dir):
    """
    Löst das Modell für jede α in alpha_list und sammelt Ergebnis-Metriken.
    """
    results = {}
    for alpha in alpha_list:
        model = create_model(
            pages, article, layouts, resorts, article_resorts,
            resort_page, layouts_pages, box_layouts, hull_layout_box,
            hull_article, article_length, hull_params, article_priority,
            alpha_value=alpha
        )
        # Log-Datei
        log_file = os.path.join(output_dir, f"{instance_name}_alpha{alpha:.1f}.log")
        model.Params.LogFile = log_file
        model.optimize()

        if model.status == GRB.INFEASIBLE:
            model.computeIIS()
            model.write(os.path.join(output_dir, f"{instance_name}_alpha{alpha:.1f}.ilp"))
            results[alpha] = {"error": "infeasible"}
            continue

        # Lösungen speichern
        model.write(os.path.join(output_dir, f"{instance_name}_alpha{alpha:.1f}.lp"))
        model.write(os.path.join(output_dir, f"{instance_name}_alpha{alpha:.1f}.sol"))

        # Extract x and c variable values
        solution_dict = {}
        for v in model.getVars():
            if v.X > 0 and v.VarName.startswith("x_"):
                parts = v.VarName.split("_")
                solution_dict[int(parts[1])] = int(parts[-1])

        # Prioritäten normalisieren und aufsummieren
        kategorien = ['A','B','C','D','E','F','G','H','I','J','K']
        prioritäten = np.array([10,9,8,7,6,5,4,3,2,1,0])
        norm_prio = min_max_normalize(prioritäten)
        prio_dict = dict(zip(kategorien, norm_prio))

        sum_prio = sum(prio_dict[article_priority[i]] for i in solution_dict)

        # Summe der c-Variablen
        sum_c = sum(v.X for v in model.getVars() if v.VarName.startswith("c_"))

        results[alpha] = {
            "sum_prio": float(sum_prio),
            "sum_c": float(sum_c)
        }

    return results

def analyze_instances(instance_folder, output_dir, alpha_list):
    """
    Iteriert über alle Instanzdateien im Ordner, löst sie und sammelt alle Resultate.
    """
    all_results = {}
    for file_path in list_instance_files(instance_folder):
        instance_name = os.path.splitext(os.path.basename(file_path))[0]
        # JSON parsen
        pages, article, layouts, resorts, article_resorts, resort_page, \
        layouts_pages, box_layouts, hull_layout_box, hull_article, \
        article_length, hull_params, article_priority = parse_json_from_file(file_path)

        # Für diese Instanz lösen
        results = solve_for_alphas(
            pages, article, layouts, resorts, article_resorts,
            resort_page, layouts_pages, box_layouts, hull_layout_box,
            hull_article, article_length, hull_params, article_priority,
            alpha_list, instance_name, output_dir
        )
        all_results[instance_name] = results

    return all_results

def invert_results(results):
    """
    Baut ein Dict auf mit α als oberster Ebene und Instanznamen als zweiter Ebene:
    {
      alpha1: {inst1: metrics, inst2: metrics, ...},
      alpha2: {inst1: metrics, inst2: metrics, ...},
      ...
    }
    """
    global_dict = {}
    for inst_name, inst_results in results.items():
        for alpha, metrics in inst_results.items():
            global_dict.setdefault(alpha, {})[inst_name] = metrics
    return global_dict

def aggregate_across_instances(global_results):
    """
    Liefert pro α die Summe bzw. den Durchschnitt der Metriken über alle Instanzen.
    """
    agg = {}
    for alpha, inst_data in global_results.items():
        sum_prio = sum(d.get("sum_prio", 0) for d in inst_data.values())
        sum_c    = sum(d.get("sum_c",    0) for d in inst_data.values())
        count = len(inst_data)
        agg[alpha] = {
            "total_prio": sum_prio,
            "total_c":    sum_c,
            "avg_prio":   sum_prio / count if count else 0,
            "avg_c":      sum_c / count if count else 0
        }
    return agg

if __name__ == "__main__":
    alpha_list = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    instance_folder = "TBLOP mit Hüllen/Instances/pareto_test"
    output_dir = "TBLOP mit Hüllen/Solutions"

    # Sicherstellen, dass das Ausgabe-Verzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # Analyse für alle Instanzen durchführen
    results = analyze_instances(instance_folder, output_dir, alpha_list)

    # Globales Tracking (invertiert nach alpha)
    global_results = invert_results(results)

    # Aggregation über alle Instanzen
    agg_results = aggregate_across_instances(global_results)

    # Ergebnis-Ausgabe
    print("Ergebnisse pro Instanz und α:")
    for inst_name, res in results.items():
        print(f"\nInstanz '{inst_name}':")
        for alpha, metrics in res.items():
            if "error" in metrics:
                print(f"  α={alpha:.1f}: Fehler ({metrics['error']})")
            else:
                print(f"  α={alpha:.1f}: Summe Prio={metrics['sum_prio']:.3f}, Summe c={metrics['sum_c']:.3f}")

    print("\nGlobales Tracking (α → Instanzen):")
    for alpha, inst_data in global_results.items():
        print(f"α={alpha:.1f}: {inst_data}")

    print("\nAggregierte Kennzahlen über alle Instanzen:")
    for alpha, metrics in agg_results.items():
        print(f"α={alpha:.1f}: Total Prio={metrics['total_prio']:.3f}, Total c={metrics['total_c']:.3f}, "
              f"Avg Prio={metrics['avg_prio']:.3f}, Avg c={metrics['avg_c']:.3f}")

    print("\nFERTIG")
