
import sys
import json
import collections

class CityJSON:

    def __init__(self, file):
        self.j = json.loads(file.read())
        if "type" in self.j and self.j["type"] == "CityJSON":
            pass
        else:
            self.j = {}
            raise ValueError("Not a CityJSON file")

    def update_crs(self, newcrs):
        if "metadata" not in self.j:
            self.j["metadata"] = {}
        if "crs" not in self.j["metadata"]:
            self.j["metadata"]["crs"] = {} 
        if "epsg" not in self.j["metadata"]["crs"]:
            self.j["metadata"]["crs"]["epsg"] = None
        try:
            i = int(newcrs)
            self.j["metadata"]["crs"]["epsg"] = i
            return True
        except ValueError:
            return False

    def get_info(self):
        info = collections.OrderedDict()
        info["cityjson_version"] = self.j["version"]
        if "crs" in self.j["metadata"] and "epsg" in self.j["metadata"]["crs"]:
            info["crs"] = self.j["metadata"]["crs"]["epsg"]
        else:
            info["crs"] = None
        if "bbox" in self.j["metadata"]:
            info["box"] = self.j["metadata"]["bbox"]
        else:
            info["box"] = None
        info["cityobjects_total"] = len(self.j["CityObjects"])
        info["vertices_total"] = len(self.j["vertices"])
        d = set()
        for key in self.j["CityObjects"]:
            d.add(self.j['CityObjects'][key]['type'])
        info["cityobjects_present"] = list(d)
        d.clear()
        for key in self.j["CityObjects"]:
            for geom in self.j['CityObjects'][key]['geometry']:
                d.add(geom["type"])
        info["geom_primitives_present"] = list(d)
        info["materials"] = 'materials' in self.j['appearance']
        info["textures"] = 'textures' in self.j['appearance']
        return json.dumps(info, indent=2)




if __name__ == '__main__':
    # with open('example2.json', 'r') as cjfile:
    with open('bob.json', 'r') as cjfile:
        try:
            d = CityJSON(cjfile)
        except ValueError:
            print "oups"
            sys.exit()
            
    print d.update_crs(888)
    print d.update_crs("hguo")

    print d.j["metadata"]

    # print e.j
