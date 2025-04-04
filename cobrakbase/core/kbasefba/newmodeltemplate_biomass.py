from modelseedpy.core.mstemplate import MSTemplateBiomass, MSTemplateBiomassComponent


class NewModelTemplateBiomass(MSTemplateBiomass):
    @staticmethod
    def from_dict(d, template):
        biomass = NewModelTemplateBiomass(
            d["id"],
            d["name"],
            d["type"],
            d.get("dna", 0.0),
            d.get("rna", 0.0),
            d.get("protein", 0.0),
            d.get("lipid", 0.0),
            d.get("cellwall", 0.0),
            d.get("cofactor", 0.0),
            d.get("pigment", 0.0),
            d.get("carbohydrate", 0.0),
            d.get("energy", 0.0),
            d.get("other", 0.0),
        )

        # for backwards compatibility in case of mismatch modelseedpy cobrakbase versions (param position change)
        # this will be removed in future versions
        biomass.dna = d.get("dna", 0.0)
        biomass.rna = d.get("rna", 0.0)
        biomass.protein = d.get("protein", 0.0)
        biomass.lipid = d.get("lipid", 0.0)
        biomass.cellwall = d.get("cellwall", 0.0)
        biomass.cofactor = d.get("cofactor", 0.0)
        biomass.energy = d.get("energy", 0.0)
        biomass.other = d.get("other", 0.0)

        for item in d["templateBiomassComponents"]:
            biocomp = MSTemplateBiomassComponent.from_dict(item, template)
            biomass.templateBiomassComponents.add(biocomp)
        biomass._template = template
        return biomass
