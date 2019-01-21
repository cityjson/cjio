

import os
import json

fin = open('/Users/hugo/Dropbox/data/cityjson/examples/denhaag/v08/DenHaag_01.json')
cm = json.loads(fin.read())


class COClass:
    def __init__(self, theid, js):
        self.id = theid
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


Building = type('Building', (COClass,), dict())

for theid in cm['CityObjects']:
    if cm['CityObjects'][theid]['type'] == "BuildingPart":
        oneb = Building(theid, cm['CityObjects'][theid])
        oneb.add_attribute('potato', 'blue')
        break

print(oneb)
print(oneb.id)
print(oneb.attributes)

no = oneb.get_number_geometries()
print (no)