
import json
import collections

def print_info(j):

    info = collections.OrderedDict()
    # info = {}
    info["cityjson_version"] = j["version"]
    if "crs" in j["metadata"] and "epsg" in j["metadata"]["crs"]:
        info["crs"] = j["metadata"]["crs"]["epsg"]
    else:
        info["crs"] = None
    if "bbox" in j["metadata"]:
        info["box"] = j["metadata"]["bbox"]
    else:
        info["box"] = None

    info["cityobjects_total"] = len(j["CityObjects"])
    info["vertices_total"] = len(j["vertices"])

    d = set()
    for key in j["CityObjects"]:
        d.add(j['CityObjects'][key]['type'])
    info["cityobjects_present"] = list(d)

    d.clear()
    for key in j["CityObjects"]:
        for geom in j['CityObjects'][key]['geometry']:
            d.add(geom["type"])
    info["geom_primitives_present"] = list(d)
    
    info["materials"] = 'materials' in j['appearance']
    info["textures"] = 'textures' in j['appearance']

    return json.dumps(info, indent=2)

