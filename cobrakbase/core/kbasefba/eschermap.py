from cobrakbase.kbase_object_info import KBaseObjectInfo


class EscherMap:

    def __init__(self, map_data, info=None, args=None):
        self.info = info if info else KBaseObjectInfo(object_type='KBaseFBA.EscherMap')

        self.authors = map_data[0]['authors'] if 'authors' in map_data[0] else []
        self.homepage = map_data[0]['homepage']
        self.map_description = map_data[0]['map_description']
        self.map_id = map_data[0]['map_id']
        self.map_name = map_data[0]['map_name']
        self.schema = map_data[0]['schema']

        # TODO: better support for these objects
        self.canvas = map_data[1]['canvas']
        self.nodes = map_data[1]['nodes']
        self.text_labels = map_data[1]['text_labels']
        self.reactions = map_data[1]['reactions']
        self.args = args

    @staticmethod
    def from_dict(data, info, args=None):
        """
        Transform KBase data back to original booleans and add missing segments

        :param data:
        :param info:
        :param args:
        :return:
        """
        import copy
        map_data = [
            copy.deepcopy(data['metadata']),
            copy.deepcopy(data['layout'])
        ]
        for uid in map_data[1]['nodes']:
            o = map_data[1]['nodes'][uid]
            if 'node_is_primary' in o:
                if o['node_is_primary']:
                    o['node_is_primary'] = True
                else:
                    o['node_is_primary'] = False
        for uid in map_data[1]['reactions']:
            o = map_data[1]['reactions'][uid]
            if 'reversibility' in o:
                if o['reversibility']:
                    o['reversibility'] = True
                else:
                    o['reversibility'] = False
            for seg_uid in o['segments']:
                seg = o['segments'][seg_uid]
                if 'b1' not in seg:
                    seg['b1'] = None
                if 'b2' not in seg:
                    seg['b2'] = None
        return EscherMap(map_data, info, args)

    def get_data(self):
        return self.adapt_map_to_kbase(self.to_json())

    def to_json(self):
        d = [
            {
                'authors': self.authors,  # modelseed escher attribute
                'map_name': self.map_name,
                'map_id': self.map_id,
                'map_description': self.map_description,
                'homepage': self.homepage,
                'schema': self.schema
            },
            {
                'reactions': self.reactions,
                'nodes': self.nodes,
                'canvas': self.canvas,
                'text_labels': self.text_labels
            }
        ]
        return d

    @staticmethod
    def adapt_map_to_kbase(refactored_escher_data2, map_id=None):  # FIXME: move this to get_data
        """
        Adapt data to KBase, True/False to 0/1 and remove None segments
        
        :param refactored_escher_data2:
        :param map_id:
        :return:
        """
        import copy
        refactored_escher_data = copy.deepcopy(refactored_escher_data2)
        if map_id:
            refactored_escher_data[0]['map_name'] = map_id

        if 'authors' not in refactored_escher_data[0]:
            refactored_escher_data[0]['authors'] = []

        # for node_uid in refactored_escher_data[1]['nodes']:
        #    node = refactored_escher_data[1]['nodes'][node_uid]
            # if node['node_type'] == 'metabolite':
            #    node['bigg_id'] = node['bigg_id'][:-3]

        for rxn_uid in refactored_escher_data[1]['reactions']:
            rxn_node = refactored_escher_data[1]['reactions'][rxn_uid]
            rxn_node['reversibility'] = 1 if rxn_node['reversibility'] else 0
            # rxn_node['genes'] = []
            for seg_uid in rxn_node['segments']:
                seg = rxn_node['segments'][seg_uid]
                if seg['b1'] is None:
                    del seg['b1']
                if seg['b2'] is None:
                    del seg['b2']

        for node_uid in refactored_escher_data[1]['nodes']:
            node = refactored_escher_data[1]['nodes'][node_uid]
            if 'node_is_primary' in node:
                node['node_is_primary'] = 1 if node['node_is_primary'] else 0

        kbase_escher = {
            "metadata": refactored_escher_data[0],
            "layout": refactored_escher_data[1]
        }

        return kbase_escher
