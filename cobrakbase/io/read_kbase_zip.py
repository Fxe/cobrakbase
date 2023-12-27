import zipfile
import json

def read_kbase_zip(path):
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
