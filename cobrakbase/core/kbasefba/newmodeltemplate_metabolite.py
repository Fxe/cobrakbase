from modelseedpy.core.mstemplate import MSTemplateSpecies, MSTemplateMetabolite
from cobra.util import format_long_string


class NewModelTemplateCompound(MSTemplateMetabolite):
    """
    typedef structure {
      templatecompound_id id;
      @optional compound_ref compound_ref;
      @optional string md5;
      string name;
      string abbreviation;
      bool isCofactor;
      list<string> aliases;
      float defaultCharge;
      float mass;
      float deltaG;
      float deltaGErr;
      string formula;
    } TemplateCompound;
    """

    def __init__(self, cpd_id, formula=None, name='', default_charge=None,
                 mass=None, delta_g=None, delta_g_error=None, is_cofactor=False,
                 abbreviation='', aliases=None):
        super().__init__(cpd_id, formula, name, default_charge, mass,
                         delta_g, delta_g_error, is_cofactor, abbreviation, aliases)

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
    """
    typedef structure {
      string id;
      float charge;
      float maxuptake;
      @optional string formula;
      string templatecompound_ref;
      templatecompartment_ref templatecompartment_ref;
    } TemplateCompCompound;
    """

    def __init__(self, comp_cpd_id, charge, compartment, cpd_id, max_uptake=0, template=None):
        super().__init__(comp_cpd_id, charge, compartment, cpd_id, max_uptake, template)

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
            'id': self.id,
            'charge': self.charge,
            'maxuptake': self.max_uptake,
            'templatecompartment_ref': '~/compartments/id/' + self.compartment,
            'templatecompound_ref': '~/compounds/id/' + self.cpd_id
        }
