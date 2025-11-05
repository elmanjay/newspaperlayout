import random
import json
import numpy as np

number_pages = 10
number_layouts = 5
number_article = 50
number_hulls = 20

def create_instance(number_pages,number_layouts,number_article,min_boxes,max_boxes,max_hulls):
    pages = [i for i in range(1,number_pages+1)]
    layouts = [i for i in range(1,number_layouts+1)]
    article = [i for i in range(1,number_article+1)]

    layouts_pages = {}
    for page in pages:
        # Wähle zufällig zwischen min_layouts und max_layouts Layouts
        num_layouts = random.randint(min(layouts), max(layouts))
        layouts_pages[page] = random.sample(layouts, num_layouts)
    
    box_layouts = {}
    for layout in layouts:
        # Anzahl der Boxen für das Layout zufällig auswählen
        num_boxes = random.randint(min_boxes, max_boxes)
        # Boxen-IDs beginnen ab 1 und sind fortlaufend
        box_layouts[layout] = list(range(1, num_boxes + 1))

    hulls = [i for i in range(1,max_hulls+1)]

    hull_params={}
    for h in hulls:
        maximum = random.randint(int(1000/max_boxes),int(1000/min_boxes))
        minimum = random.randint(int(maximum * 0.7),int(maximum * 0.8))
        hull_params[h] = {"min": minimum, "max": maximum}
        
    hull_layout_box = {}
    for layout in layouts:
        hull_layout_box[layout] = {}
        number_of_boxes = len(box_layouts[layout]) 
        for box in box_layouts[layout]:
            available_hulls = []
            for h in hulls:
                if hull_params[h]["max"] <= 1000 / number_of_boxes * 1.3:
                    available_hulls.append(h) 
            #Hier kann es sein, dass die available hulls mal leer sind, führt zu einem fehler
            num_hulls = random.randint(1, len(available_hulls))
            selected_hulls = random.sample(available_hulls, num_hulls)
            hull_layout_box[layout][box] = sorted(selected_hulls)

    list_max_boxes = []
    for j in pages:
        max_boxes = 0
        for l in layouts_pages[j]:
            if len(box_layouts[l]) > max_boxes:
                max_boxes = len(box_layouts[l])
        list_max_boxes.append(max_boxes)

    hull_article = {}
    for i in article:
        hull_article[i] = random.sample(hulls, random.randint(2,int(len(hulls)/2)))
    
    article_length = {}
    for i in article:
        article_length[i] = random.randint(int(1000/7),int(1000/2))

    article_page_layout_box = {}
    for j in pages:
        article_page_layout_box[j] = {}
        for l in layouts_pages[j]:
            article_page_layout_box[j][l]= {}
            for k in box_layouts[l]:
                article_page_layout_box[j][l][k] = random.sample(article,int(len(article))) # vorher /4 
    
    def min_max_normalize(data):
        min_val = np.min(data)  # Verwende np.min statt min für NumPy-Arrays
        max_val = np.max(data)  # Verwende np.max statt max
        return (data - min_val) / (max_val - min_val)  # Direkt mit NumPy-Operationen
    
    prioritäten = np.array([10, 5, 1])
    normierte_prioritäten = min_max_normalize(prioritäten)

    article_priority = {}
    for i in article:
        rand_value = random.random()  # Zufallswert zwischen 0 und 1

        if rand_value < 0.1:  # 10% Wahrscheinlichkeit für Priorität 10
            article_priority[i] = normierte_prioritäten[0]
        elif rand_value < 0.3:  # Weitere 20% (insgesamt 30%) für Priorität 5
            article_priority[i] = normierte_prioritäten[1]
        else:  # Die restlichen 70% für Priorität 1
            article_priority[i] = normierte_prioritäten[2]
    
            

    return pages, article, layouts, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length,hull_params ,article_page_layout_box, article_priority

# Die Instanz in eine JSON-Datei speichern
def save_instance_to_json(instance, filename):
    # Die Instanz in ein Dictionary umwandeln
    instance_dict = {
        "pages": instance[0],
        "article": instance[1],
        "layouts": instance[2],
        "layouts_pages": instance[3],
        "box_layouts": instance[4],
        "hull_layout_box": instance[5],
        "hull_article": instance[6],
        "article_length": instance[7],
        "hull_params": instance[8],
        "article_page_layout_box" : instance[9],
        "article_priority" : instance[10],
    }
    
    # Das Dictionary in eine JSON-Datei speichern
    with open(filename, 'w') as json_file:
        json.dump(instance_dict, json_file, indent=4)

def parse_json_from_file(file_name):
    with open(file_name, "r") as f:
        json_data = json.load(f)
    
    pages = json_data["pages"]
    article = json_data["article"]
    layouts = json_data["layouts"]
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
    article_page_layout_box = {
        int(j): {
            int(l): {
                int(k): v for k, v in l_data.items()
            } for l, l_data in j_data.items()
        } for j, j_data in json_data["article_page_layout_box"].items()
    }

    
    return pages, article, layouts, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length, hull_params, article_page_layout_box, article_priority


if __name__ == "__main__":
    instance = create_instance(number_article=19,number_pages=1,number_layouts=10,min_boxes=2,max_boxes=5,max_hulls=4)
    name = "maumau.json"
    #save_instance_to_json(instance,name)
    pages, article, layouts, layouts_pages, box_layouts, hull_layout_box, hull_article, article_length,hull_params,x,article_priority = parse_json_from_file(name)
    print(article_priority)