"""Module containing metadata related functions"""

import uuid
import os
import re
import collections, functools, operator
import sys
from datetime import date
import platform

def generate_metadata(citymodel: dict,
                      filename: str = None,
                      overwrite_values: bool = False):
    """Returns a tuple containing a dictionary of the metadata and a list of errors.

    Keyword arguments:
    citymodel -- Dictionary containing the city model
    filename  -- String with the name of the original file
    overwrite_values -- Boolean that forces to overwrite existing values if True (default: False)
    """

    def fileIdentifier_func():
        return os.path.basename(filename)

    def metadataDateStamp_func():
        return str(date.today())

    def is_present_in_appearance(k):
        if "appearance" in citymodel:
            if k in citymodel["appearance"]:
                if len(citymodel["appearance"][k]) > 0:
                    if any(len(d) > 0 for d in citymodel["appearance"][k]):
                        return "present"
        
        return "absent"

    def textures_func():
        return is_present_in_appearance("textures")

    def materials_func():
        return is_present_in_appearance("materials")

    def cityfeatureMetadata_func():
        children = ("Part", "Installation", "ConstructionElement")
        parent = lambda x: x[0:[match.start() for match in re.finditer ("[A-Z]", x)][1]]

        def LoD_func():
            presentLoDs = CityObjects_md[cm_type]["presentLoDs"]
            if "geometry" in CityObjects[c_o]:
                for g in CityObjects[c_o]["geometry"]:
                    if "template" in g.keys():
                        LoD = str(citymodel["geometry-templates"]["templates"][g["template"]]["lod"])
                else:
                    LoD = str(g["lod"])
                if LoD in presentLoDs:
                    presentLoDs[LoD] += 1
                else:
                    presentLoDs[LoD] = 1

        CityObjects = citymodel["CityObjects"]
        CityObjects_md = {}

        c_o_p = list(set([v["type"] for k,v in CityObjects.items()]))
        c_o_c = [c_o_p.pop(c_o_p.index(x)) for x in c_o_p[:] if any(child in x for child in children)]

        for c in c_o_p:
            CityObjects_md[c] = {
                    "uniqueFeatureCount":0,
                    "aggregateFeatureCount":0,
                    "presentLoDs":{}
            }
            if c == "TINRelief":
                CityObjects_md[c]["triangleCount"] = 0
            elif c == "CityObjectGroup":
                del CityObjects_md[c]["aggregateFeatureCount"]

        for c in c_o_c: CityObjects_md[parent(c)][c+"s"] = 0

        for c_o in CityObjects:
            cm_type = CityObjects[c_o]["type"]
            if cm_type == "CityObjectGroup":
                CityObjects_md[cm_type]["uniqueFeatureCount"] += 1
                LoD_func()
            elif any(child in cm_type for child in children):
                CityObjects_md[parent(cm_type)][cm_type+"s"] += 1
            else:
                CityObjects_md[cm_type]["uniqueFeatureCount"] += 1
                if "geometry" in CityObjects[c_o]:
                    CityObjects_md[cm_type]["aggregateFeatureCount"] += len(CityObjects[c_o]["geometry"])
                LoD_func()
                if cm_type == "TINRelief":
                    CityObjects_md[cm_type]["triangleCount"] += sum([len(b) for g in CityObjects[c_o].get("geometry", []) for b in g["boundaries"]])
        return CityObjects_md

    def thematicModels_func():
        return [*metadata["cityfeatureMetadata"]]

    def presentLoDs_func():
        return dict(functools.reduce(operator.add, 
                map(collections.Counter, 
                [v["presentLoDs"] for k,v in metadata["cityfeatureMetadata"].items() if k != "CityObjectGroup"])))

    md_dictionary = {
        "datasetCharacterSet": "UTF-8",
        "datasetTopicCategory": "geoscientificInformation",
        "metadataStandard": "ISO 19115 - Geographic Information - Metadata",
        "metadataStandardVersion": "ISO 19115:2014(E)",
        "metadataCharacterSet": "UTF-8",
        "metadataDateStamp": metadataDateStamp_func,
        "textures": textures_func,
        "materials": materials_func,
        "cityfeatureMetadata": cityfeatureMetadata_func
        }

    md_dependent_dictionary = {
        "presentLoDs":presentLoDs_func,
        "thematicModels":thematicModels_func
        }

    error = lambda x: bad_list.append(x + " = " + str(sys.exc_info()[1]) + "\n")
    def populate_metadata_dict(d):
        def compute_item(key, value):
            try:
                metadata[key] = value if isinstance(v, str) else value()
            except:
                error(key)
                pass
        for k, v in d.items():
            if overwrite_values or k not in metadata:
                compute_item(k, v)

    if "+metadata-extended" in citymodel:
        metadata = citymodel["+metadata-extended"].copy()
    else:
        metadata = {}
 

    bad_list = []
    populate_metadata_dict(md_dictionary)
    populate_metadata_dict(md_dependent_dictionary)

    return metadata, bad_list
