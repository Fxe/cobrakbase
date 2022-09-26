

class ModelReactionProteinSubunit:
    """
    typedef structure {
  string role;
  bool triggering;
  bool optionalSubunit;
  string note;
  list<feature_ref> feature_refs;
} ModelReactionProteinSubunit;
    """
    def __init__(self, role: str, triggering: bool, optional: bool, note: str, features: list):
        """

        @param role:  'role': 'ftr06142'
        @param triggering: 'triggering': 1
        @param optional: 'optionalSubunit': 0,
        @param note:
        @param features: ['~/genome/features/id/b2930', '~/genome/features/id/b3925']
        """
        self.role = role
        self.triggering = triggering
        self.optional = optional
        self.note = note
        self.features = features

    @staticmethod
    def from_json(data):
        return ModelReactionProteinSubunit(data['role'],
                                           data['triggering'] == 1,
                                           data['optionalSubunit'] == 1,
                                           data['note'],
                                           data['feature_refs'])

    def get_data(self):
        d = {
            'role': self.role,
            'note': self.note,
            'triggering': 1 if self.triggering else 0,
            'optionalSubunit': 1 if self.optional else 0,
            'feature_refs': self.features
        }
        return d


class ModelReactionProtein:
    """
    @optional source complex_ref
*/
typedef structure {
  complex_ref complex_ref;
  string note;
  list<ModelReactionProteinSubunit> modelReactionProteinSubunits;
  string source;
} ModelReactionProtein;
    """

    def __init__(self, note: str, source: str, subunits: list, cpx=None):
        """

        @param note:
        @param source:
        @param subunits: list of ModelReactionProteinSubunit
        @param cpx:  ~/template/complexes/name/cpx01517
        """
        self.subunits = subunits
        self.note = note
        self.source = source
        self.cpx = cpx

    @staticmethod
    def from_json(data):
        subunits = [ModelReactionProteinSubunit.from_json(o) for o in data['modelReactionProteinSubunits']]
        return ModelReactionProtein(data['note'], data['source'], subunits, data.get("complex_ref"))

    def get_data(self):
        d = {
            'note': self.note,
            'source': self.source,
            'modelReactionProteinSubunits': [x.get_data() for x in self.subunits]
        }
        if self.cpx:
            d['complex_ref'] = self.cpx

        return d

    def __repr__(self):
        ands = []
        for o in self.subunits:
            ors = {o.split('/')[-1] for o in o.features}
            rule = " or ".join(ors)
            if len(ors) > 1:
                ands.append(f"({rule})")
            else:
                ands.append(rule)
        return " and ".join(ands)

    def __str__(self):
        return self.__repr__()
