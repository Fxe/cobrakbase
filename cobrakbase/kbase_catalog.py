from cobrakbase.kbase_object_info import KBaseObjectInfo

PROD_WS_MEDIA = 'KBaseMedia'
PROD_WS_GENOMES = '?'
PROD_WS_TEMPLATES = 'NewKBaseModelTemplates'


class KBaseCatalogItem:

    def __init__(self, api, info):
        self.api = api
        self.info = info

    def get(self):
        return self.api.get_from_ws(str(self.info))

    def info(self):
        return self.info


class KBaseCatalog:

    def __init__(self, api, ws):
        self._ws = ws
        self._api = api
        self._items = {}
        self._update_catalog()

    def _update_catalog(self):
        res = self._api.list_objects(self._ws)
        for o in res:
            info = KBaseObjectInfo.from_kbase_json(o)
            # print(str(info), info.id)
            opt = info.id.replace('-', '_')
            item = KBaseCatalogItem(self._api, info)
            self._items[opt] = item
            self.__dict__[opt] = item

    def __getitem__(self, key: str):
        key = key.replace('-', '_')
        return self.__dict__[key].get()

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return self._items.__iter__()
