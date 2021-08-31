from modelseedpy.core.mstemplate import MSTemplateSpecies
from cobra.util import format_long_string


class NewModelTemplateCompound:

    def __init__(self, cpd_id, formula=None, name='', default_charge=None,
                 mass=None, delta_g=None, delta_g_error=None, is_cofactor=False,
                 abbreviation='', aliases=None):
        self.id = cpd_id
        self.formula = formula
        self.name = name
        self.abbreviation = abbreviation
        self.default_charge = default_charge
        self.mass = mass
        self.delta_g = delta_g
        self.delta_g_error = delta_g_error
        self.is_cofactor = is_cofactor
        self.aliases = []
        if aliases:
            self.aliases = aliases
        self.species = set()
        self._template = None

    @staticmethod
    def from_dict(d):
        return NewModelTemplateCompound(
            d['id'], d['formula'], d['name'],
            d['defaultCharge'], d['mass'],
            d['deltaG'], d['deltaGErr'],
            d['isCofactor'] == 1,
            d['abbreviation'],
            d['aliases']
        )

    def get_data(self):
        return {
            'id': self.id,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'aliases': [],
            'defaultCharge': self.default_charge,
            'deltaG': self.delta_g,
            'deltaGErr': self.delta_g_error,
            'formula': self.formula,
            'isCofactor': 1 if self.is_cofactor else 0,
            'mass': self.mass
        }

    def __repr__(self):
        return "<%s %s at 0x%x>" % (self.__class__.__name__, self.id, id(self))

    def __str__(self):
        return "{}:{}".format(self.id, self.name)

    def _repr_html_(self):
        return """
        <table>
            <tr>
                <td><strong>Compound identifier</strong></td><td>{id}</td>
            </tr><tr>
                <td><strong>Name</strong></td><td>{name}</td>
            </tr><tr>
                <td><strong>Memory address</strong></td>
                <td>{address}</td>
            </tr><tr>
                <td><strong>Formula</strong></td><td>{formula}</td>
            </tr><tr>
                <td><strong>In {n_species} species</strong></td><td>
                    {species}</td>
            </tr>
        </table>""".format(id=self.id, name=format_long_string(self.name),
                           formula=self.formula,
                           address='0x0%x' % id(self),
                           n_species=len(self.species),
                           species=format_long_string(
                               ', '.join(r.id for r in self.species), 200))


class NewModelTemplateCompCompound(MSTemplateSpecies):

    def __init__(self, comp_cpd_id, charge, compartment, cpd_id, max_uptake=0, template=None):
        super().__init__(comp_cpd_id, charge, compartment, cpd_id, max_uptake, template)

    @property
    def compound(self):
        return self._template_compound

    @property
    def name(self):
        if self._template_compound:
            return self._template_compound.name
        return ''

    @name.setter
    def name(self, value):
        if self._template_compound:
            self._template_compound.name = value

    @property
    def formula(self):
        if self._template_compound:
            return self._template_compound.formula
        return ''

    @formula.setter
    def formula(self, value):
        if self._template_compound:
            self._template_compound.formula = value

    @staticmethod
    def from_dict(d, template=None):
        return NewModelTemplateCompCompound(
            d['id'],
            d['charge'],
            d['templatecompartment_ref'].split('/')[-1],
            d['templatecompound_ref'].split('/')[-1],
            d['maxuptake'],
            template,
        )

    def get_data(self):
        return {
            'charge': self.charge,
            'id': self.id,
            'maxuptake': self.max_uptake,
            'templatecompartment_ref': '~/compartments/id/' + self.compartment,
            'templatecompound_ref': '~/compounds/id/' + self.cpd_id
        }
