from modelseedpy.core.mstemplate import MSTemplateBiomass, MSTemplateBiomassComponent


class NewModelTemplateBiomass(MSTemplateBiomass):
    @staticmethod
    def from_dict(d, template):
        self = NewModelTemplateBiomass(
            d["id"],
            d["name"],
            d["type"],
            d["dna"],
            d["rna"],
            d["protein"],
            d["lipid"],
            d["cellwall"],
            d["cofactor"],
            d["energy"],
            d["other"],
        )
        for item in d["templateBiomassComponents"]:
            biocomp = MSTemplateBiomassComponent.from_dict(item, template)
            self.templateBiomassComponents.add(biocomp)
        self._template = template
        return self
