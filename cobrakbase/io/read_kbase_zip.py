import zipfile
import json
from cobrakbase.core.kbase_object_factory import KBaseObjectFactory

def read_json(filename):
    data = None
    with open(filename, "r") as f:
        data = json.loads(f.read())
    return data


def write_json(data, filename, pretty=False):
    with open(filename, "w") as f:
        if pretty:
            f.write(json.dumps(data, indent=4, sort_keys=True))
        else:
            f.write(json.dumps(data))


def _read_kbase_zip(path):
    with zipfile.ZipFile(path, 'r') as zf:
        item_info = None
        item_data = None
        for f in zf.filelist:
            if f.filename.startswith('KBase_object_details_'):
                with zf.open(f) as arch:
                    item_info = json.load(arch)
            else:
                with zf.open(f) as arch:
                    item_data = json.load(arch)
        return item_info, item_data


def load_kbase_zip_object(filename):
    item_info, item_data = _read_kbase_zip(filename)
    if item_info is None:
        raise ValueError('invalid kbase zip file. unable to detect object workspace info')
    if item_data is None:
        raise ValueError('invalid kbase zip file. unable to detect object data')
    legacy = 'info' not in item_info
    if legacy:
        data = {
            'data': [
                {
                    'info': item_info['metadata'][0],
                    'provenance': [item_info['provenance'][0]['provenance'][0]],
                    'data': item_data
                }
            ]
        }
        return KBaseObjectFactory().create(data, None)
    else:
        data = {
            'data': [
                {
                    'info': item_info['info'],
                    'provenance': [],
                    'data': item_data
                }
            ]
        }
        return KBaseObjectFactory().create(data, None)
