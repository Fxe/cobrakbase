import copy
import logging
from cobra.core import Reaction

logger = logging.getLogger(__name__)


class Biomass(Reaction):
    """
    typedef structure {
        biomass_id id;
        string name;
        list<BiomassCompound> biomasscompounds;
        list<BiomassCompound> removedcompounds; @optional
    } Biomass;


    typedef structure {
        modelcompound_ref modelcompound_ref;
        float coefficient;
        mapping<gapfill_id, bool> gapfill_data; @optional
    } BiomassCompound;
    """
    def __init__(self, reaction_id=None, name='',
                 dna=0, rna=0, protein=0,
                 lipid=0, cell_wall=0, cofactor=0,
                 energy=0, other=0, removed_compounds=None):
        """
        @param reaction_id:
        @param name:
        @param dna: DNA fraction of biomass
        @param rna: RNA fraction of biomass
        @param protein: Protein fraction of biomass
        @param lipid: Lipid fraction of biomass
        @param cell_wall: Cell Wall fraction of biomass
        @param cofactor: Cofactor's fraction of biomass
        @param energy: Energy fraction of biomass
        @param other: Other metabolite fraction of biomass
        @param removed_compounds:
        """
        super().__init__(reaction_id,
                         name,
                         "",
                         0, 1000)
        self.dna = dna
        self.rna = rna
        self.protein = protein
        self.lipid = lipid
        self.cell_wall = cell_wall
        self.cofactor = cofactor
        self.energy = energy
        self.other = other
        self.removed_compounds = removed_compounds
        self.metabolite_gap_fill_data = {}  # mapping<gapfill_id, bool> gapfill_data; @optional of BiomassCompound

    @staticmethod
    def from_json(data):
        data_copy = copy.deepcopy(data)
        biomass = Biomass(data_copy['id'], data_copy['name'],
                          data_copy.get('dna'), data_copy.get('rna'), data_copy.get('protein'),
                          data_copy.get('lipid'), data_copy.get('cellwall'), data_copy.get('cofactor'),
                          data_copy.get('energy'), data_copy.get('other'), data_copy.get('removedcompounds'))
        return biomass

    @staticmethod
    def from_cobra_reaction(rxn: Reaction):

        pass

    def _to_json(self):
        biomass_compounds = []
        for m, v in self.metabolites.items():
            compound_data = {
                'coefficient': v,
                'modelcompound_ref': f'~/modelcompounds/id/{m.id}',
                'edits': {}
            }
            if m in self.metabolite_gap_fill_data:
                compound_data['gapfill_data'] = self.metabolite_gap_fill_data[m]
            biomass_compounds.append(compound_data)
        d = {
            'id': self.id,
            'name': self.name,
            'biomasscompounds': biomass_compounds,
            'deleted_compounds': {},
            'dna': self.dna,
            'rna': self.rna,
            'lipid': self.lipid,
            'cellwall': self.cell_wall,
            'cofactor': self.cofactor,
            'protein': self.protein,
            'energy': self.energy,
            'other': self.other,
            'edits': {}
        }
        if self.removed_compounds:
            d['removedcompounds'] = self.removed_compounds
        return d
