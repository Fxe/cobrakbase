import json

def read_json(filename):
    data = None
    with open(filename, 'r') as f:
        data = json.loads(f.read())
    return data

def write_json(data, filename, pretty=False):
    with open(filename, 'w') as f:
        if pretty:
            f.write(json.dumps(data, indent=4, sort_keys=True))
        else:
            f.write(json.dumps(data))