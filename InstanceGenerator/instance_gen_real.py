import json
import random
def create_instance(number_pages, number_layouts, number_article,
                     max_hulls):
    
    with open("TBLOP mit Hüllen/InstanceGenerator/example_layouts.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(data["1"])
    #print(data.keys())   
    pages = list(range(1, number_pages+1))
    layouts = list(range(1, max(map(int, data.keys()))+1))
    article = list(range(1, number_article+1))

    layouts_pages = {}
    for page in pages:
        num_layouts = random.randint(min(layouts)+1, max(map(int, data.keys())))
        layouts_pages[page] = random.sample(layouts, num_layouts//2)

    box_layouts = {}
    for layout in layouts:
        num_boxes = max(map(int, data[str(layout)].keys()))
        box_layouts[layout] = list(range(1, num_boxes+1))

    #hulls = list(range(2, max_hulls+1))
    next_hull_id = 1
    hull_layout_box = {}
    for layout in layouts:
        hull_layout_box[layout] = {}
        for box in box_layouts[layout]:
            # Ziehe die Anzahl der Hüllen für diese Box zufällig zwischen 1 und max_hulls
            num_hulls = random.randint(1, max_hulls)
            
            # Vergib fortlaufende Hüllen-IDs und erhöhe den Zähler
            assigned = list(range(next_hull_id, next_hull_id + num_hulls))
            next_hull_id += num_hulls
            
            # Speichere die sortierten IDs
            hull_layout_box[layout][box] = sorted(assigned)
    
    hull_params = {}
    for l in layouts:
        for b in box_layouts[l]:
            for h in hull_layout_box[l][b]:
                maximum = random.randint(int(0.8*int(data[str(l)][str(b)]["max"])),int(1.2*int(data[str(l)][str(b)]["max"])))
                minimum = random.randint(int(maximum * 0.85), int(maximum * 0.9))
                hull_params[h] = {"min": minimum, "max": maximum}
    
    max_hull = max(
    hull_id
    for boxes in hull_layout_box.values()
    for hull_ids in boxes.values()
    for hull_id in hull_ids
                        )

# 2. Erzeuge die Liste von 1 bis max_hull
    hulls = list(range(1, max_hull + 1))
    
    kategorien = ['A','B','C','D','E','F','G','H','I','J','K']
    article_priority = {
        art_id: random.choice(kategorien)
        for art_id in article
    }
    
    for i in article_priority:
        article_length = {
            i: random.randint(1200, 12000)
            for i in article
        }

    hull_article = {
        i: random.sample(hulls, random.randint(2, len(hulls)//10))
        for i in article
    }



    resorts = [1]  # Beispiel: ein Dictionary statt Set
    article_resorts = {1: article.copy()}
    resort_page = {j: resorts.copy() for j in pages}

    return {
        "pages": pages,
        "layouts": layouts,
        "article": article,
        "layouts_pages": layouts_pages,
        "box_layouts": box_layouts,
        "hull_layout_box": hull_layout_box,
        "hull_article": hull_article,
        "article_length": article_length,
        "hull_params": hull_params,
        "article_priority": article_priority,
        "resorts": resorts,
        "article_resorts": article_resorts,
        "resort_page": resort_page
    }

# Die Instanz in eine JSON-Datei speichern
def save_instance_to_json(instance, filename):
    # Das Dictionary in eine JSON-Datei speichern
    with open(filename, 'w') as json_file:
        json.dump(instance, json_file, indent=4)

def parse_json_from_file(file_name):
    with open(file_name, "r") as f:
        json_data = json.load(f)
    
    pages = json_data["pages"]
    article = json_data["article"]
    layouts = json_data["layouts"]
    resorts = json_data["resorts"]
    article_resorts = {int(k): v for k, v in json_data["article_resorts"].items()}
    resort_page = {int(k): v for k, v in json_data["resort_page"].items()}
    layouts_pages = {int(k): v for k, v in json_data["layouts_pages"].items()}
    box_layouts = {int(k): v for k, v in json_data["box_layouts"].items()}
    hull_layout_box = {
        int(layout): {int(box): hulls for box, hulls in boxes.items()}
        for layout, boxes in json_data["hull_layout_box"].items()
    }
    hull_article = {int(k): v for k, v in json_data["hull_article"].items()}
    article_length = {int(k): v for k, v in json_data["article_length"].items()}
    article_priority = {int(k): v for k, v in json_data["article_priority"].items()}
    hull_params = {int(k): v for k, v in json_data["hull_params"].items()}

    
    return pages, article, layouts, resorts, article_resorts, resort_page, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length, hull_params, article_priority

def save_instance_to_json(instance, filename):
    # Das Dictionary in eine JSON-Datei speichern
    with open(filename, 'w') as json_file:
        json.dump(instance, json_file, indent=4)

if __name__ == "__main__":
    name = "test_yolo.json"
    instance = create_instance(number_pages=20,number_article=120,number_layouts=60,max_hulls=30)
    save_instance_to_json(instance,name)