import os
import json


STATISTICS_EMPTY = {'win': 0, 'lost': 0, 'lastgame': None}

def load_static(file_name = 'statistics.json'):
    if os.path.exists(file_name):
            with open(file_name, "r", ) as r:
                data = json.load(r)
                print(data)
                return data
    else:
        return {}

def save_static(data: dict, file_name= 'statistics.json'):
        with open(file_name, "w") as s:
            json.dump(data, s)

