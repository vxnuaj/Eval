import json

def load_dataset(filename):
    dataset = []
    with open(filename, 'r') as file:
        for line in file:
            dataset.append(json.loads(line)) 
    return dataset