import json
import random
def create_instance(number_pages, number_layouts, number_article, number_hulls,
                    min_boxes, max_boxes, min_layouts,max_layouts, max_hulls):
    pages = list(range(1, number_pages+1))
    layouts = list(range(1, number_layouts+1))
    article = list(range(1, number_article+1))

    layouts_pages = {}
    for page in pages:
        num_layouts = random.randint(min_layouts, max_layouts)
        layouts_pages[page] = random.sample(layouts, num_layouts)

    box_layouts = {}
    for layout in layouts:
        num_boxes = random.randint(min_boxes, max_boxes)
        box_layouts[layout] = list(range(1, num_boxes+1))

    hulls = list(range(2, number_hulls+1))

    hull_params = {}
    for h in hulls:
        maximum = random.randint(500, 12000)
        minimum = random.randint(int(maximum * 0.8), int(maximum * 0.9))
        hull_params[h] = {"min": minimum, "max": maximum}

    hull_layout_box = {}
    for layout in layouts:
        hull_layout_box[layout] = {}
        for box in box_layouts[layout]:
            num_hulls = random.randint(1, max_hulls)
            selected_hulls = random.sample(hulls, num_hulls)
            hull_layout_box[layout][box] = sorted(selected_hulls)

    hull_article = {
        i: random.sample(hulls, random.randint(2, len(hulls)//2))
        for i in article
    }

    article_length = {
        i: random.randint(1200, 12000)
        for i in article
    }

    max_frac_A = 0.15   # höchstens 15% A
    max_frac_B = 0.10   # höchstens 10% B
    alpha = 1.2      # Stärke des Längeneffekts für A (>=1 erhöht den Bias auf lange Artikel)

    def weighted_sample_without_replacement(items, weights, k):
        """Efraimidis–Spirakis: Ziehe k Elemente ohne Zurücklegen proportional zu weights."""
        eps = 1e-9
        keys = {i: random.random() ** (1.0 / max(weights[i], eps)) for i in items}
        return sorted(keys, key=keys.get, reverse=True)[:k]

    n = len(article)

    # ---------- Schritt 1: A vergeben (bevorzugt lange Artikel)
    min_len = min(article_length.values())
    weights_A = {i: (article_length[i] - min_len + 1) ** alpha for i in article}
    k_A = min(int(n * max_frac_A), n)
    A_set = set(weighted_sample_without_replacement(article, weights_A, k_A))

    # ---------- Schritt 2: B vergeben (aus Rest; LÄNGE EGAL -> reines Zufallssampling)
    remaining = [i for i in article if i not in A_set]
    k_B = min(int(n * max_frac_B), len(remaining))   # Cap 10% des Gesamtbestands
    B_set = set(random.sample(remaining, k_B)) if k_B > 0 else set()

    # ---------- Schritt 3: Rest ist C
    article_priority = {}
    for i in article:
        if i in A_set:
            article_priority[i] = 'A'
        elif i in B_set:
            article_priority[i] = 'B'
        else:
            article_priority[i] = 'C'

    #Für jede Seite wird Resort 1 festgelget
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

    for i in range(1,11):
        number_pages = 15
        number_article = 150
        name = f"Instance_{number_pages}_{number_article}_{i}.json"
        instance = create_instance(number_pages=number_pages,number_article=number_article,number_layouts=200,number_hulls=100,min_boxes=2,max_boxes=5,max_hulls=15)
        save_instance_to_json(instance,name)