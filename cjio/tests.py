

import os
import json



class CityModel:
    def __init__(self, js):
        self.js = js
        self.cityobjects = {}
        Building = type('Building', (COClass,), dict())
        for theid in js['CityObjects']:
            if js['CityObjects'][theid]['type'] == "BuildingPart":
                oneb = Building(theid, js['CityObjects'][theid])
                oneb.add_attribute('potato', 'blue')
                self.cityobjects[theid] = oneb
                # break
    def get_co(self, theid):
        print(theid)
        if theid not in self.cityobjects:
            return None
        else:
            return self.cityobjects[theid]


class COClass:
    def __init__(self, theid, js):
        self.id = theid
        # print(theid)
        self.geometries = []
        if 'attributes' in js:
            self.attributes = js['attributes']
        else:
            self.attributes = {}
        #-- create a geometry object?
        for jg in js['geometry']:
            Geometry = type(jg['type'], (GeomClass,), dict())
            self.geometries.append(Geometry(jg))

    def add_attribute(self, name, jsvalue):
        self.attributes[name] = jsvalue
    def get_id(self):
        return self.id
    def get_number_geometries(self):
        return len(self.geometries)


class GeomClass:
    def __init__(self, js):
        self.lod = js['lod']
        self.boundaries = js['boundaries']
    def get_sf(self): #-- get SimpleFeatures
        pass




fin = open('/Users/hugo/Dropbox/data/cityjson/examples/denhaag/v08/DenHaag_01.json')
js = json.loads(fin.read())


cm = CityModel(js)

# print(cm.cityobjects)

# Building = type('Building', (COClass,), dict())

# for theid in cm['CityObjects']:
#     if cm['CityObjects'][theid]['type'] == "BuildingPart":
#         oneb = Building(theid, cm['CityObjects'][theid])
#         oneb.add_attribute('potato', 'blue')
#         break

oneb = cm.get_co('GUID_8CE54418-E2F7-49A7-9A8D-C3D172BA62C4_2')

print(oneb)
print(oneb.id)
print(oneb.attributes)

no = oneb.get_number_geometries()
print (no)