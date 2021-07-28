from cobra.util import format_long_string


class NewModelTemplateRole:

    def __init__(self, role_id, name,
                 features=None, source='', aliases=None):
        """

        :param role_id:
        :param name:
        :param features:
        :param source:
        :param aliases:
        """
        self.id = role_id
        self.name = name
        self.source = source
        self.features = [] if features is None else features
        self.aliases = [] if aliases is None else aliases
        self._complexes = set()
        self._template = None

    @staticmethod
    def from_dict(d):
        return NewModelTemplateRole(d['id'], d['name'], d['features'], d['source'], d['aliases'])

    def get_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'aliases': self.aliases,
            'features': self.features,
            'source': self.source
        }

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def __str__(self):
        return "{}:{}".format(self.id, self.name)

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>Role identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Function</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>In {n_complexes} complexes</strong></td><td>
                    {complexes}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           address='0x0%x' % id(self),
                           n_complexes=len(self._complexes),
                           complexes=format_long_string(
                               ', '.join(r.id for r in self._complexes), 200))


class NewModelTemplateComplex:

    def __init__(self, complex_id, name, source='', reference='', confidence=0, template=None):
        """

        :param complex_id:
        :param name:
        :param source:
        :param reference:
        :param confidence:
        :param template:
        """
        self.id = complex_id
        self.name = name
        self.source = source
        self.reference = reference
        self.confidence = confidence
        self.roles = {}
        self._template = template

    @staticmethod
    def from_dict(d, template):
        protein_complex = NewModelTemplateComplex(
            d['id'], d['name'],
            d['source'], d['reference'], d['confidence'],
            template
        )
        for o in d['complexroles']:
            role = template.roles.get_by_id(o['templaterole_ref'].split('/')[-1])
            protein_complex.add_role(role, o['triggering'] == 1, o['optional_role'] == 1)
        return protein_complex

    def add_role(self, role: NewModelTemplateRole, triggering=True, optional=False):
        """
        Add role (function) to the complex
        :param role: 
        :param triggering: 
        :param optional: 
        :return: 
        """
        self.roles[role] = (triggering, optional)

    def get_data(self):
        complex_roles = []
        for role in self.roles:
            triggering, optional = self.roles[role]
            complex_roles.append({
                'triggering': 1 if triggering else 0,
                'optional_role': 1 if optional else 0,
                'templaterole_ref': '~/roles/id/' + role.id
            })
        return {
            'id': self.id,
            'name': self.name,
            'reference': self.reference,
            'confidence': self.confidence,
            'source': self.source,
            'complexroles': complex_roles,
        }

    def __str__(self):
        return " and ".join(map(lambda x: "{}{}{}".format(
            x[0].id,
            ":trig" if x[1][0] else "",
            ":optional" if x[1][1] else ""), self.roles.items()))

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def _repr_html_(self):

        return """
        <table>
            <tr>
                <td><strong>Complex identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Name</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Contains {n_complexes} role(s)</strong></td><td>
                    {complexes}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           address='0x0%x' % id(self),
                           n_complexes=len(self.roles),
                           complexes=format_long_string(
                               ', '.join("{}:{}:{}:{}".format(r[0].id, r[0].name, r[1][0], r[1][1]) for r in
                                         self.roles.items()), 200))
