from cobrakbase.kbase_object_info import KBaseObjectInfo


class AttributeMapping:
    """
    factors - list of supplied factors
    conditions - mapping of instance_labels to a list of attribute values in the same order as
    the attributes array

    ontology_mapping_method - One of “User curation”, “Closest matching string”

    @metadata ws ontology_mapping_method as Mapping Method
    @metadata ws length(attributes) as Number of Attributes
    @metadata ws length(instances) as Number of Instances

    typedef structure {
      mapping<string, list<string>> instances;
      list<Attribute> attributes;
      string ontology_mapping_method;
    } AttributeMapping;
    """

    OBJECT_TYPE = "KBaseExperiments.AttributeMapping"

    def __init__(
        self,
        instances: dict,
        attributes: list,
        ontology_mapping_method: str,
        info=None,
        args=None,
    ):
        self.instances = instances
        self.attributes = attributes
        self.ontology_mapping_method = ontology_mapping_method
        self.info = (
            info if info else KBaseObjectInfo(object_type=AttributeMapping.OBJECT_TYPE)
        )
        self.args = args

    @staticmethod
    def from_dict(data, info=None, args=None):
        if info is None:
            info = KBaseObjectInfo(object_type=AttributeMapping.OBJECT_TYPE)
        return AttributeMapping(
            data["instances"],
            data["attributes"],
            data["ontology_mapping_method"],
            info,
            args,
        )

    def get_data(self):
        return {
            "attributes": self.attributes,
            "instances": self.instances,
            "ontology_mapping_method": self.ontology_mapping_method,
        }
