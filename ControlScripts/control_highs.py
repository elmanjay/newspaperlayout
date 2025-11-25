import os
import time
import csv
import highspy


def solve_all_mps(
    instance_dir: str,
    sol_dir: str = "highs_sol",
    csv_path: str = "highs_results.csv",
    time_limit: float = 3600.0,
):
    # Ordner für Lösungen erstellen
    os.makedirs(sol_dir, exist_ok=True)

    # CSV erstellen
    with open(csv_path, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow(["instance_name", "status", "runtime_s", "objective", "mip_gap"])

        # Instanzen durchlaufen
        for filename in sorted(os.listdir(mps_dir)):
            if not filename.lower().endswith(".mps"):
                continue

            instance_name = os.path.splitext(filename)[0]
            mps_path = os.path.join(mps_dir, filename)
            sol_path = os.path.join(sol_dir, instance_name + ".sol")

            print(f"\n=== Löse Instanz: {filename} ===")

            highs = highspy.Highs()

            # Optionen
            highs.setOptionValue("threads", 1)       # Single Thread
            highs.setOptionValue("time_limit", float(time_limit))
            highs.setOptionValue("log_to_console", True)

            # Modell laden
            print(mps_path)
            status = highs.readModel(mps_path)
            if status != highspy.HighsStatus.kOk:
                print(f"Fehler beim Lesen von {filename}")
                writer.writerow([instance_name, "READ_ERROR", "", "", ""])
                continue

            # Solven + Zeit messen
            start = time.time()
            highs.run()
            runtime = time.time() - start

            model_status = highs.modelStatusToString(highs.getModelStatus())
            info = highs.getInfo()
            print(info)

            objective = ""
            mip_gap = ""

            if getattr(info, "valid", False):
                objective = info.objective_function_value
                mip_gap = getattr(info, "mip_gap", "")

            # Lösung speichern
            try:
                highs.writeSolution(sol_path)
            except Exception as e:
                print(f"Konnte Lösung nicht speichern: {e}")

            # CSV schreiben
            writer.writerow([
                instance_name,
                model_status,
                f"{runtime:.6f}",
                "" if objective == "" else f"{objective:.10g}",
                "" if mip_gap == "" else f"{mip_gap:.10g}"
            ])

            print(f"Status:   {model_status}")
            print(f"Laufzeit: {runtime:.2f} s")
            print(f"Objektiv: {objective}")
            print(f"MIP-Gap:  {mip_gap}")


if __name__ == "__main__":
    # Dein gewünschter Pfad:
    base_dir = os.path.dirname(__file__)
    instance_dir = os.path.join(base_dir, "Instances", "Diss", "Small", "S10P40(A)")
    mps_dir = os.path.join(instance_dir,"lp","mps")

    solve_all_mps(instance_dir)

