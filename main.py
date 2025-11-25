from ControlScripts import control_gurobi
import os

if __name__ == "__main__":
    instance_size = "Large"
    #instance_names = ["M20P80(A)","M20P80(B)","M20P100(A)","M20P100(A)","M20P100(B)","M20P120(A)","M20P120(B)"]
    instance_type = "L30P120(B)"
    #for instance_type in instance_names:
    base_dir = os.path.dirname(__file__)
    instance_dir = os.path.join(base_dir, "Instances", "Diss", f"{instance_size}",f"{instance_type}")
    control_gurobi.solve_instances(instance_dir=instance_dir)