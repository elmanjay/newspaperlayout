from gurobipy import Model, GRB, quicksum
import csv
from parser import parse_json_from_file
import numpy as np
import os


def min_max_normalize(data):
    min_val = np.min(data)  # Verwende np.min statt min für NumPy-Arrays
    max_val = np.max(data)  # Verwende np.max statt max
    return (data - min_val) / (max_val - min_val)  # Direkt mit NumPy-Operationen

strafen = np.array([10**12, 10**10, 10**8, 10**6, 10**4, 0])

prioritäten = np.array([10,5,1,0])
kategorien = ["A","B","C","D"]
normierte_strafen = min_max_normalize(strafen)
print(normierte_strafen)
normierte_prio = min_max_normalize(prioritäten)
prio_dict = dict(zip(kategorien, normierte_prio))


def create_model(pages, article, layouts, resorts, article_resorts, resort_page, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length, hull_params, article_priority, alpha_value, lambda_value):
    hulls = [i for i in range(1,90+1)]
    g_under_fix = 0.5
    g_under_var = 0.49
    g_over_fix = 0.1
    g_over_var = 0.39
    g_fehlt = 1
    alpha = alpha_value
    T_over = 0.3
    T_under = 0.15
    M_prio = 1

    #Bestimmung von M aus maximum aus Artikel und Boxlängen
    max_hull_value = max(hull["max"] for hull in hull_params.values())
    max_article_length = max(article_length.values())
    M  = max(max_hull_value, max_article_length) +100000

    min_boxes = min(len(v) for v in box_layouts.values())
    max_boxes = max(len(v) for v in box_layouts.values())
    print(min_boxes)
            

    hull_layout_box_article = {}
    # Iteriere über alle Boxen
    for l in layouts:
        hull_layout_box_article[l]= {}
        for k in hull_layout_box[l]:
            hull_layout_box_article[l][k] = {}
            # Iteriere über alle Artikel
            for i in article:
                # Finde die gemeinsamen Hüllen (Schnittmenge)
                common_hulls = list(set(hull_layout_box[l][k]) & set(hull_article[i]))
                # Falls gemeinsame Hüllen vorhanden sind, speichere sie
                if common_hulls:
                    hull_layout_box_article[l][k][i] = common_hulls
                else:
                    hull_layout_box_article[l][k][i] = []

    model = Model("milp_model")
    #print(hull_layout_box_article[1][2][1])
    x = {}
    #hier muss in zukunft nur ein i erezugt werden wenn der artikel die resort bestimmungen article_page_layout_hull erfüllt
    for i in article:
        for j in pages:
            for l in layouts_pages[j]:
                for k in box_layouts[l]:
                    # Überprüfe, ob der Schlüssel vorhanden ist, bevor du darauf zugreifst
                        if i in hull_layout_box_article.get(l, {}).get(k, {}) and any(i in article_resorts[r] for r in resort_page[j]):
                            for h in hull_layout_box_article[l][k][i]:
                                x[i, j, l, k, h] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}_{l}_{k}_{h}")

    y = {}
    f_page_layout = {}
    for j in pages:
        for l in layouts_pages[j]:
            y[j,l] = model.addVar(vtype=GRB.BINARY, name=f"y_{j}_{l}")
            f_page_layout[j,l] = model.addVar(lb=-max_boxes,vtype=GRB.CONTINUOUS, name=f"f_page_layout_{j}_{l}")

    z = {}
    for j in pages:
        for l in layouts_pages[j]:
            for k in box_layouts[l]:
                for h in hull_layout_box[l][k]:
                    z[j,l,k,h] = model.addVar(vtype=GRB.BINARY, name=f"z_{j}_{l}_{k}_{h}")

    min_hull = {}
    max_hull = {}
    c_box = {}
    p_box = {}
    v = {}
    delta_over = {}
    delta_under = {}
    e_over = {}
    e_under = {}
    c_box_under = {}
    c_box_over = {}
    under_ratio = {}
    over_ratio = {}
    f_box = {}
    test= {}

    for j in pages:
        for l in layouts_pages[j]:
            for k in box_layouts[l]:
                c_box[j, l, k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"c_box_{j}_{l}_{k}")
                f_box[j, l, k] = model.addVar(lb=-1,vtype=GRB.CONTINUOUS, name=f"f_box_{j}_{l}_{k}")
                p_box[j, l, k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"p_box_{j}_{l}_{k}")
                v[j, l, k] = model.addVar(vtype=GRB.BINARY, name=f"v_{j}_{l}_{k}")
                delta_over[j, l, k] = model.addVar(vtype=GRB.BINARY, name=f"delta_over_{j}_{l}_{k}")
                delta_under[j, l, k] = model.addVar(vtype=GRB.BINARY, name=f"delta_under_{j}_{l}_{k}")
                e_over[j, l, k] = model.addVar(vtype=GRB.BINARY, name=f"e_over_{j}_{l}_{k}")
                e_under[j, l, k] = model.addVar(vtype=GRB.BINARY, name=f"e_under_{j}_{l}_{k}")
                c_box_under[j, l, k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"c_box_under_{j}_{l}_{k}")
                c_box_over[j, l, k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"c_box_over_{j}_{l}_{k}")
                under_ratio[j,l,k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"under_ratio_{j}_{l}_{k}")
                over_ratio[j,l,k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"over_ratio_{j}_{l}_{k}")
                test[j,l,k] = model.addVar(lb=0,vtype=GRB.CONTINUOUS, name=f"test_{j}_{l}_{k}")

    for j in pages:
        for l in layouts_pages[j]:
            for k in box_layouts[l]:
                hull_length_min = []
                hull_length_max = []
                for h in hull_layout_box[l][k]:
                    hull_length_min.append(hull_params[h]["min"])
                    hull_length_max.append(hull_params[h]["max"])
                if len(hull_length_min) > 1:
                    min_hull[j, l, k] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=max(hull_length_min), name=f"min_hull_{j}_{l}_{k}")
                    max_hull[j, l, k] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=max(hull_length_max), name=f"max_hull_{j}_{l}_{k}")
                else:
                    min_hull[j, l, k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"min_hull_{j}_{l}_{k}")
                    max_hull[j, l, k] = model.addVar(vtype=GRB.CONTINUOUS, name=f"max_hull_{j}_{l}_{k}")
    c_page = {}
    for j in pages:
        c_page[j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"c_page_{j}")


    p_page = {}
    f_page = {}
    for j in pages:
        p_page[j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"p_page_{j}")
        f_page[j] = model.addVar(lb= -1, vtype=GRB.CONTINUOUS, name=f"f_page_{j}")

    p_page_layout = {}
    for j in pages:
        for l in layouts_pages[j]:
            p_page_layout[j,l] = model.addVar(vtype=GRB.CONTINUOUS, name=f"p_page_layout_{j}_{l}")


    objective2 = quicksum(f_page[j] for j in pages)
    model.setObjective(objective2, GRB.MAXIMIZE)

    #NB2
    model.addConstrs((quicksum(y[j, l] for l in layouts_pages[j]) == 1 for j in pages),name=f"NB2_{j}_{l}")

    #NB3
    model.addConstrs((quicksum(z[j, l, k, h] for h in hull_layout_box[l][k]) == y[j, l] for j in pages for l in layouts_pages[j] for k in box_layouts[l]),name=f"NB3_{j}_{l}_{k}_{h}")

    #NB4 
    model.addConstrs((quicksum(x[i, j, l, k, h] for r in resort_page[j] for i in article_resorts[r] if h in hull_article[i]) <= z[j, l, k, h]for j in pages for l in layouts_pages[j] for k in box_layouts[l] for h in hull_layout_box[l][k]),name=f"NB4_{i}_{j}_{l}_{k}_{h}")


    #NB5
    model.addConstrs((quicksum(x[i, j, l, k, h] for j in pages for l in layouts_pages[j] for k in box_layouts[l] if any(i in article_resorts[r] for r in resort_page[j]) for h in hull_layout_box_article[l][k][i]) <= 1 for i in article),name=f"NB5_{i}_{j}_{l}_{k}_{h}")

    #NB6
    model.addConstrs((min_hull[j, l, k] == quicksum(hull_params[h]["min"] * z[j, l, k, h] for h in hull_layout_box[l][k]) for j in pages for l in layouts_pages[j] for k in box_layouts[l]),name=f"NB6_{i}_{j}_{l}_{k}_{h}")

    #NB7
    model.addConstrs((max_hull[j, l, k] == quicksum(hull_params[h]["max"] * z[j, l, k, h] for h in hull_layout_box[l][k]) for j in pages for l in layouts_pages[j] for k in box_layouts[l]),name=f"NB7_{i}_{j}_{l}_{k}_{h}")

    #NB8
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] for r in resort_page[j] for i in article_resorts[r] for h in hull_layout_box_article[l][k][i]) == y[j,l] - v[j, l, k]
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB8_{i}_{j}_{l}_{k}_{h}"
    )

    #NB9a
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i] for r in resort_page[j] for i in article_resorts[r] for h in hull_layout_box_article[l][k][i])
        >= min_hull[j, l, k]
        - M * (delta_under[j, l, k]+v[j,l,k])
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB9a_{i}_{j}_{l}_{k}_{h}"
    )

    #NB9b
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i] for r in resort_page[j] for i in article_resorts[r] for h in hull_layout_box_article[l][k][i])
        <= min_hull[j, l, k] 
        + M * (1-delta_under[j, l, k]-v[j, l, k]) 
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB9b_{i}_{j}_{l}_{k}_{h}"
    )

    #NB10a
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i] for r in resort_page[j] for i in article_resorts[r] for h in hull_layout_box_article[l][k][i])
        <= max_hull[j, l, k] + M * delta_over[j, l, k]
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB10a_{i}_{j}_{l}_{k}_{h}"
    )

    #NB10b
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i] for r in resort_page[j] for i in article_resorts[r] for h in hull_layout_box_article[l][k][i])
        >= max_hull[j, l, k] - M * (1-delta_over[j, l, k])
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB10b_{i}_{j}_{l}_{k}_{h}"
    )

    #NB11a 
    model.addConstrs(
            (quicksum(x[i, j, l, k, h] * article_length[i]
                    for r in resort_page[j] for i in article_resorts[r]for h in hull_layout_box_article[l][k][i])
        <= (1 + T_over)* max_hull[j,l,k] + M * e_over[j, l, k]
        for j in pages
        for l in layouts_pages[j]
        for k in box_layouts[l]), 
        f"NB11a_{i}_{j}_{l}_{k}_{h}"
                    )

    #NB11b 
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i]
                    for r in resort_page[j] for i in article_resorts[r]for h in hull_layout_box_article[l][k][i])
        >= (1+T_over) * max_hull[j,l,k]  - M *(1- e_over[j, l, k])
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB11b_{i}_{j}_{l}_{k}_{h}"
    )

    # NB12a 
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i]
                    for r in resort_page[j] for i in article_resorts[r]for h in hull_layout_box_article[l][k][i])
        <= (1-T_under)*min_hull[j,l,k]
        + M *  (1-e_under[j, l, k] )
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB12a_{i}_{j}_{l}_{k}_{h}"
    )

    # NB12b 
    model.addConstrs(
        (quicksum(x[i, j, l, k, h] * article_length[i]
                    for r in resort_page[j] for i in article_resorts[r]for h in hull_layout_box_article[l][k][i])
        >= (1-T_under)* min_hull[j,l,k]
        - M * (e_under[j, l, k] + v[j,l,k])
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB12b_{i}_{j}_{l}_{k}_{h}"
    )

    # NB13
    model.addConstrs(
        (
            p_box[j, l, k] <= quicksum(
                x[i, j, l, k, h] * prio_dict[article_priority[i]] 
                for r in resort_page[j]
                for i in article_resorts[r]
                for h in hull_layout_box_article[l][k][i]
            ) - M_prio * (e_over[j,l,k]+ e_under[j,l,k])
            for j in pages
            for l in layouts_pages[j]
            for k in box_layouts[l]
        ),
        name=f"NB13_{j}_{l}_{k}"
    )

    # for j in pages:
    #     for l in layouts_pages[j]:
    #         for k in box_layouts[l]:
    #             model.addGenConstrIndicator(e_over[j,l,k],  1, p_box[j,l,k] == 0.0, name=f"IND_pbox_zero_over_{j}_{l}_{k}")
    #             model.addGenConstrIndicator(e_under[j,l,k], 1, p_box[j,l,k] == 0.0, name=f"IND_pbox_zero_under_{j}_{l}_{k}")

    # NB14
    model.addConstrs(
        (
            c_box_under[j, l, k]
            >= g_under_fix + g_under_var*
            quicksum(
                x[i, j, l, k, h]
                * (
                    article_length[i] / hull_params[h]["min"]
                    - 1
                )
                for r in resort_page[j]
                for i in article_resorts[r]
                for h in hull_layout_box_article[l][k][i]
            )
            / T_under *-1 -((1 - delta_under[j, l, k])
                + e_under[j, l, k])
             * M
            for j in pages
            for l in layouts_pages[j]
            for k in box_layouts[l]
        ),
        name=f"NB14_{j}_{l}_{k}"
)

    # NB15
    model.addConstrs(
        (
            c_box_over[j, l, k]
            >= g_over_fix + g_over_var *
            quicksum(
                x[i, j, l, k, h]
                * (
                    article_length[i] / hull_params[h]["max"]
                    - 1
                )
                for r in resort_page[j]
                for i in article_resorts[r]
                for h in hull_layout_box_article[l][k][i]
            )
            / T_over -((1 - delta_over[j, l, k])
                + e_over[j, l, k])
             * M
            for j in pages
            for l in layouts_pages[j]
            for k in box_layouts[l]
        ),
        name=f"NB15_{j}_{l}_{k}"
)


    #NB16
    model.addConstrs(
        (c_box[j, l, k] == c_box_under[j, l, k] + c_box_over[j, l, k]+ (e_over[j, l, k] + e_under[j, l, k] + v[j, l, k]) * g_fehlt
        for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB16_{j}_{l}_{k}"
    )

    #NB17
    model.addConstrs(
        (f_box[j, l, k] == alpha* p_box[j,l,k] - (1-alpha)* c_box[j, l, k] for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB17_{j}_{l}_{k}"
    )
    
    model.addConstrs(
        (
            f_page_layout[j, l]
            == (1 + lambda_value * (len(box_layouts[l]) - min_boxes)) * 
            quicksum(
                (1.0 / len(box_layouts[l])) * f_box[j, l, k]
                for k in box_layouts[l]
                )
            for j in pages
            for l in layouts_pages[j]
        ),
        name=f"NB_Test_{j}_{l}"
    )

    #NB18
    model.addConstrs(
        (f_page[j] ==
        quicksum(f_page_layout[j,l] for l in layouts_pages[j])for j in pages),
        name=f"NB18_{j}_{l}_{k}"
    )

    #NB19
    model.addConstrs(
        (delta_over[j, l, k] <= y[j,l] for j in pages for l in layouts_pages[j] for k in box_layouts[l]),
        name=f"NB19_{j}_{l}_{k}"
    )

    # print(hulls)
    # for j in pages:
    #     for l in layouts_pages[j]:                         # alle Layouts, die auf Seite j möglich sind
    #         for h in hulls :                          # alle Shells
    #             model.addConstr(
    #                 quicksum(z[j, l, k, h] for k in box_layouts[l] if h in hull_layout_box[l][k]) <= 1,
    #                 name=f"shell_unique_page{j}_layout{l}_shell{h}"
    #             )

    #model.addConstr(y[1,1] == 1)
    #model.addConstr(x[1,1,1,1,1] == 1)
    #model.addConstr(c_box[1,10,3] >= 0.1)
    #model.addConstr(v[1,1,1] == 1)
    #model.addConstr(x[1,1,1,1,1] == 1)
    #model.addConstr(v[1,1,1] == 0)
    #model.addConstr(v[1,1,3] == 1)
    #model.addConstr(v[1,1,4] == 1)

    return model




if __name__ == "__main__":

    # print(normierte_prio)
    # instance = create_instance(number_article=150,number_pages=30,number_layouts=15,min_boxes=2,max_boxes=5,max_hulls=10)
    instance_name = "Instance_3_30_1"
    name = f"TBLOP mit Hüllen/Instances/Diss/Medium/Instance_10_60_1.json"
    output_dir = "TBLOP mit Hüllen/Solutions"
    alpha_value = 0.5
    lambda_value = 0.01
    pages, article, layouts, resorts, article_resorts, resort_page, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length, hull_params, article_priority = parse_json_from_file(name)
    #print(hull_layout_box[50][1])
    model = create_model(pages, article, layouts, resorts, article_resorts, resort_page, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length, hull_params, article_priority, alpha_value, lambda_value)
    model.Params.LogFile = os.path.join(output_dir, f"{instance_name}.log")
    model.optimize()

    if model.status == GRB.INFEASIBLE:
        print("Modell ist unlösbar. Berechne IIS...")
        model.computeIIS()
        model.write("model.ilp")
        for c in model.getConstrs():
            if c.IISConstr:
                print(f"IIS enthält Constraint: {c.ConstrName}")

    else:
        model.write(os.path.join(output_dir, f"{instance_name}.lp"))
        model.write(os.path.join(output_dir, f"{instance_name}.sol"))
        solution_dict = {}
        for v in model.getVars():
            if v.X != 0:
                print(f"{v.VarName}: {v.X}")
                if v.VarName[0] == "x":
                    parts = v.VarName.split("_")
                    solution_dict[int(parts[1])] = int(parts[-1])
        
        print("--------------------------------")
        for i in solution_dict:
            if article_length[i] < hull_params[solution_dict[i]]["min"]:
                underfill_rate = round(-100* (article_length[i] - hull_params[solution_dict[i]]["min"]) / hull_params[solution_dict[i]]["min"],3) 
                print(f"Artikel {i} unterfüllt Hülle {solution_dict[i]} um {underfill_rate}%")
            
            if article_length[i] > hull_params[solution_dict[i]]["max"]:
                underfill_rate = 100* (article_length[i] - hull_params[solution_dict[i]]["max"]) / hull_params[solution_dict[i]]["max"] 
                print(f"Artikel {i} überfüllt Hülle {solution_dict[i]} um {underfill_rate}%")
