
import os
import sys
import re
import shutil

import json
import collections
import jsonref
import urllib
from pkg_resources import resource_filename
from pkg_resources import resource_listdir
import copy
import random
from io import StringIO
import numpy as np
import pyproj
from sys import platform

MODULE_EARCUT_AVAILABLE = True
try:
    import mapbox_earcut
except ImportError as e:
    MODULE_EARCUT_AVAILABLE = False

from cjio import validation
from cjio import subset
from cjio import geom_help
from cjio import errors
from cjio.errors import InvalidOperation


CITYJSON_VERSIONS_SUPPORTED = ['0.6', '0.8', '0.9', '1.0']

TOPLEVEL = ('Building',
            'Bridge',
            'CityObjectGroup',
            'CityFurniture',
            'GenericCityObject',
            'LandUse',
            'PlantCover',
            'Railway',
            'Road',
            'SolitaryVegetationObject',
            'TINRelief',
            'TransportSquare',
            'Tunnel',
            'WaterBody')


def reader(file, ignore_duplicate_keys=False):
    return CityJSON(file=file, ignore_duplicate_keys=ignore_duplicate_keys)

def off2cj(file):
    l = file.readline()
    # print(l)
    while (len(l) <= 1) or (l[0] == '#') or (l[:3] == 'OFF'):
        l = file.readline()
        # print(l)
        # print ('len', len(l))
    numVertices = int(l.split()[0])
    numFaces    = int(l.split()[1])
    lstVertices = []
    for i in range(numVertices):
        lstVertices.append(list(map(float, file.readline().split())))
    lstFaces = []
    for i in range(numFaces):
        lstFaces.append(list(map(int, file.readline().split()[1:])))
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "0.6"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    for v in lstVertices:
        cm["vertices"].append(v)
    g = {'type': 'Solid'}
    shell = []
    for f in lstFaces:
        shell.append([f])
    g['boundaries'] = [shell]
    g['lod'] = 1
    o = {'type': 'GenericCityObject'}
    o['geometry'] = [g]
    cm["CityObjects"]["id-1"] = o
    return CityJSON(j=cm)


def poly2cj(file):
    l = file.readline()
    numVertices = int(l.split()[0])
    lstVertices = []
    for i in range(numVertices):
        lstVertices.append(list(map(float, file.readline().split()))[1:])
    numFaces = int(file.readline().split()[0])
    lstFaces = []
    holes = []
    for i in range(numFaces):
        l = file.readline()
        irings = int(l.split()[0]) - 1
        face = []
        face.append(list(map(int, file.readline().split()[1:])))
        for r in range(irings):
            face.append(list(map(int, file.readline().split()[1:])))
            file.readline()
        lstFaces.append(face)
    cm = {}
    cm["type"] = "CityJSON"
    cm["version"] = "0.6"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    for v in lstVertices:
        cm["vertices"].append(v)
    g = {'type': 'Solid'}
    shell = []
    for f in lstFaces:
        shell.append(f)
    g['boundaries'] = [shell]
    g['lod'] = 1
    o = {'type': 'GenericCityObject'}
    o['geometry'] = [g]
    cm["CityObjects"]["id-1"] = o
    return CityJSON(j=cm)


class CityJSON:

    def __init__(self, file=None, j=None, ignore_duplicate_keys=False):
        if file is not None:
            self.read(file, ignore_duplicate_keys)
            self.path = os.path.abspath(file.name)
        elif j is not None:
            self.j = j
        else: #-- create an empty one
            self.j = {}
            self.j["type"] = "CityJSON"
            self.j["version"] = CITYJSON_VERSIONS_SUPPORTED[-1]
            self.j["CityObjects"] = {}
            self.j["vertices"] = []


    def __repr__(self):
        return self.get_info()


    def get_version(self):
        return self.j["version"]


    def get_epsg(self):
        if "metadata" not in self.j:
            return None
        if "crs" in self.j["metadata"] and "epsg" in self.j["metadata"]["crs"]:
            return self.j["metadata"]["crs"]["epsg"]
        elif "referenceSystem" in self.j["metadata"]:
            s = self.j["metadata"]["referenceSystem"]
            return int(s[s.find("::")+2:])
        else:
            return None


    def is_empty(self):
        if len(self.j["CityObjects"]) == 0:
            return True
        else:
            return False

    def read(self, file, ignore_duplicate_keys=False):
        if ignore_duplicate_keys == True:
            self.j = json.loads(file.read())
        else:
            try:
                self.j = json.loads(file.read(), object_pairs_hook=validation.dict_raise_on_duplicates)
            except ValueError as err:
                raise ValueError(err)
        #-- a CityJSON file?
        if "type" in self.j and self.j["type"] == "CityJSON":
            pass
        else:
            self.j = {}
            raise ValueError("Not a CityJSON file")

            
    def fetch_schema(self, folder_schemas=None):
        v = "-1"
        if folder_schemas is None:
            #-- fetch latest from x.y version (x.y.z)
            tmp = resource_listdir(__name__, '/schemas/')
            tmp.sort()
            v = tmp[-1]
            try:
                schema = resource_filename(__name__, '/schemas/%s/cityjson.schema.json' % (v))
            except:
                return (False, None, '')
        else:
            schema = os.path.join(folder_schemas, 'cityjson.schema.json')  
        #-- open the schema
        try:
            fins = open(schema)
        except: 
            return (False, None, '')
        abs_path = os.path.abspath(os.path.dirname(schema))
        #-- because Windows uses \ and not /        
        if platform == "darwin" or platform == "linux" or platform == "linux2":
            base_uri = 'file://{}/'.format(abs_path)
        else:
            base_uri = 'file:///{}/'.format(abs_path.replace('\\', '/'))
        js = jsonref.loads(fins.read(), jsonschema=True, base_uri=base_uri)
        if v == "-1":
            v = schema
        return (True, js, v)


    def fetch_schema_cityobjects(self, folder_schemas=None):
        if folder_schemas is None:
            #-- fetch proper schema from the stored ones 
            tmp = resource_listdir(__name__, '/schemas/')
            tmp.sort()
            v = tmp[-1]
            try:
                schema = resource_filename(__name__, '/schemas/%s/cityjson.schema.json' % (v))
            except:
                return (False, None)
        else:
            schema = os.path.join(folder_schemas, 'cityjson.schema.json')  
        abs_path = os.path.abspath(os.path.dirname(schema))
        sco_path = abs_path + '/cityobjects.schema.json'
        #-- because Windows uses \ and not /        
        if platform == "darwin" or platform == "linux" or platform == "linux2":
            base_uri = 'file://{}/'.format(abs_path)
        else:
            base_uri = 'file:///{}/'.format(abs_path.replace('\\', '/'))
        jsco = jsonref.loads(open(sco_path).read(), jsonschema=True, base_uri=base_uri)
        # jsco = json.loads(open(sco_path).read())
        return (True, jsco)


    def validate_extensions(self, folder_schemas=None):
        print ('-- Validating the Extensions')
        if "extensions" not in self.j:
            print ("--- No extensions in the file.")
            return (True, [])
        if folder_schemas is None:
            #-- fetch proper schema from the stored ones 
            tmp = resource_listdir(__name__, '/schemas/')
            tmp.sort()
            v = tmp[-1]
            try:
                schema = resource_filename(__name__, '/schemas/%s/cityjson.schema.json' % (v))
                folder_schemas = os.path.abspath(os.path.dirname(schema))
            except:
                return (False, None)
        isValid = True
        es = []
        base_uri = os.path.join(folder_schemas, "extensions")
        base_uri = os.path.abspath(base_uri)
        allnewco = set()
        #-- iterate over each Extensions, and verify each of the properties
        #-- in the file. Other way around is more cumbersome
        for ext in self.j["extensions"]:
            s = self.j["extensions"][ext]["url"]
            s = s[s.rfind('/') + 1:]
            print ('\t%s [%s]' % (ext, s))
            schemapath = os.path.join(base_uri, s)
            if os.path.isfile(schemapath) == False:
                return (False, ["Schema file '%s' can't be found" % s])
            js = json.loads(open(schemapath).read())

            #-- 1. extraCityObjects
            if "extraCityObjects" in js:
                for nco in js["extraCityObjects"]:
                    allnewco.add(nco)
                    jtmp = {}
                    jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
                    jtmp["type"] = "object"
                    jtmp["$ref"] = "file://%s#/extraCityObjects/%s" % (schemapath, nco)
                    jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
                    for theid in self.j["CityObjects"]:
                        if self.j["CityObjects"][theid]["type"] == nco:
                            nco1 = self.j["CityObjects"][theid]
                            v, errs = validation.validate_against_schema(nco1, jsotf)
                            if (v == False):
                                isValid = False
                                es += errs

            #-- 2. extraRootProperties
            if "extraRootProperties" in js:
                for nrp in js["extraRootProperties"]:
                    jtmp = {}
                    jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
                    jtmp["type"] = "object"
                    jtmp["$ref"] = "file://%s#/extraRootProperties/%s" % (schemapath, nrp)
                    jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
                    for p in self.j:
                        if p == nrp:
                            thep = self.j[p]
                            v, errs = validation.validate_against_schema(thep, jsotf)
                            if (v == False):
                                isValid = False
                                es += errs

            #-- 3. extraAttributes
            if "extraAttributes" in js:
                for thetype in js["extraAttributes"]:
                    for ea in js["extraAttributes"][thetype]:
                        jtmp = {}
                        jtmp["$schema"] = "http://json-schema.org/draft-07/schema#"
                        jtmp["type"] = "object"
                        jtmp["$ref"] = "file://%s#/extraAttributes/%s/%s" % (schemapath, thetype, ea)
                        jsotf = jsonref.loads(json.dumps(jtmp), jsonschema=True, base_uri=base_uri)
                        for theid in self.j["CityObjects"]:
                            if ( (self.j["CityObjects"][theid]["type"] == thetype) and 
                                 ("attributes" in self.j["CityObjects"][theid])    and
                                 (ea in self.j["CityObjects"][theid]["attributes"]) ):
                                a = self.j["CityObjects"][theid]["attributes"][ea]
                                v, errs = validation.validate_against_schema(a, jsotf)
                                if (v == False):
                                    isValid = False
                                    es += errs


        #-- 4. check if there are CityObjects that do not have a schema
        for theid in self.j["CityObjects"]:
            if ( (self.j["CityObjects"][theid]["type"][0] == "+") and
                 (self.j["CityObjects"][theid]["type"] not in allnewco) ):
                s = "ERROR:   CityObject " + self.j["CityObjects"][theid]["type"] + " doesn't have a schema."
                es.append(s)
                isValid = False

        return (isValid, es)


    def validate(self, skip_schema=False, folder_schemas=None):
        #-- only latest version, otherwise a mess with versions and different schemas
        #-- this is it, sorry people
        if (self.j["version"] != CITYJSON_VERSIONS_SUPPORTED[-1]):
            return (False, False, ["Only files with version v%s can be validated." % (CITYJSON_VERSIONS_SUPPORTED[-1])], "")
        es = []
        ws = []
        #-- 1. schema
        if skip_schema == False:
            print ('-- Validating the syntax of the file')
            b, js, v = self.fetch_schema(folder_schemas)
            if b == False:
                return (False, False, ["Can't find the schema."], [])
            else:
                print ('\t(using the schemas %s)' % (v))
                isValid, errs = validation.validate_against_schema(self.j, js)
                if (isValid == False):
                    es += errs
                    return (False, False, es, [])
        #-- 2. schema for Extensions
        if "extensions" in self.j:
            b, es = self.validate_extensions(folder_schemas)
            if b == False:
                return (b, True, es, [])


        #-- 3. ERRORS
        print ('-- Validating the internal consistency of the file (see docs for list)')
        isValid = True

        if float(self.j["version"]) == 0.6:
            b, errs = validation.building_parts(self.j) 
            if b == False:
                isValid = False
                es += errs
            b, errs = validation.building_installations(self.j)
            if b == False:
                isValid = False
                es += errs
            b, errs = validation.building_pi_parent(self.j)
            if b == False:
                isValid = False
                es += errs
        #-- for v0.7+ (where the parent-child concept was introduced)                
        else:
            b, errs = validation.parent_children_consistency(self.j)
            if b == False:
                isValid = False
                es += errs

        print("\t--Vertex indices coherent")
        b, errs = validation.wrong_vertex_index(self.j)
        if b == False:
            isValid = False
            es += errs
        print("\t--Specific for CityGroups")
        b, errs = validation.city_object_groups(self.j) 
        if b == False:
            isValid = False
            es += errs
        print("\t--Semantic arrays coherent with geometry")
        b, errs = validation.semantics_array(self.j)
        if b == False:
            isValid = False
            es += errs
        #-- 4. WARNINGS
        woWarnings = True
        print("\t--Root properties")
        b, errs = validation.cityjson_properties(self.j, js)
        if b == False:
            woWarnings = False
            ws += errs
        print("\t--Empty geometries")
        b, errs = validation.geometry_empty(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        print("\t--Duplicate vertices")
        b, errs = validation.duplicate_vertices(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        print("\t--Orphan vertices")
        b, errs = validation.orphan_vertices(self.j)
        if b == False:
            woWarnings = False
            ws += errs
        #-- fetch schema cityobjects.json
        print("\t--CityGML attributes")
        b, jsco = self.fetch_schema_cityobjects(folder_schemas)
        b, errs = validation.citygml_attributes(self.j, jsco)
        if b == False:
            woWarnings = False
            ws += errs
        # TODO: validate address attributes?
        return (isValid, woWarnings, es, ws)


    def get_bbox(self):
        if "metadata" not in self.j:
            return self.calculate_bbox()
        if "geographicalExtent" not in self.j["metadata"]:
            return self.calculate_bbox()
        return self.j["metadata"]["geographicalExtent"]


    def calculate_bbox(self):
        bbox = [9e9, 9e9, 9e9, -9e9, -9e9, -9e9]    
        for v in self.j["vertices"]:
            for i in range(3):
                if v[i] < bbox[i]:
                    bbox[i] = v[i]
            for i in range(3):
                if v[i] > bbox[i+3]:
                    bbox[i+3] = v[i]
        if "transform" in self.j:
            for i in range(3):
                bbox[i] = (bbox[i] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
            for i in range(3):
                bbox[i+3] = (bbox[i+3] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
        return bbox


    def update_bbox(self):
        """
        Update the bbox (["metadata"]["bbox"]) of the CityJSON.
        If there is none then it is added.
        """
        if "metadata" not in self.j:
            self.j["metadata"] = {}
        if self.is_empty() == True:
            bbox = [0, 0, 0, 0, 0, 0]    
            self.j["metadata"]["geographicalExtent"] = bbox
            return bbox
        bbox = self.calculate_bbox()
        self.j["metadata"]["geographicalExtent"] = bbox
        return bbox        


    def set_epsg(self, newepsg):
        if newepsg == None:
            if "metadata" in self.j:
                if "referenceSystem" in self.j["metadata"]:
                    del self.j["metadata"]["referenceSystem"]
            return True
        try:
            i = int(newepsg)
        except ValueError:
            return False
        if "metadata" not in self.j:
            self.j["metadata"] = {}
        if float(self.get_version()) < 0.7:
            if "crs" not in self.j["metadata"]:
                self.j["metadata"]["crs"] = {} 
            if "epsg" not in self.j["metadata"]["crs"]:
                self.j["metadata"]["crs"]["epsg"] = {}
            self.j["metadata"]["crs"]["epsg"] = i
            return True
        else:
            if "referenceSystem" not in self.j["metadata"]:
                self.j["metadata"]["referenceSystem"] = {}
            s = 'urn:ogc:def:crs:EPSG::' + str(i)
            self.j["metadata"]["referenceSystem"] = s
            return True


    def add_bbox_each_cityobjects(self):
        def recusionvisit(a, vs):
          for each in a:
            if isinstance(each, list):
                recusionvisit(each, vs)
            else:
                vs.append(each)
        for co in self.j["CityObjects"]:
            vs = []
            bbox = [9e9, 9e9, 9e9, -9e9, -9e9, -9e9]    
            for g in self.j['CityObjects'][co]['geometry']:
                recusionvisit(g["boundaries"], vs)
                for each in vs:
                    v = self.j["vertices"][each]
                    for i in range(3):
                        if v[i] < bbox[i]:
                            bbox[i] = v[i]
                    for i in range(3):
                        if v[i] > bbox[i+3]:
                            bbox[i+3] = v[i]
                if "transform" in self.j:
                    for i in range(3):
                        bbox[i] = (bbox[i] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
                    for i in range(3):
                        bbox[i+3] = (bbox[i+3] * self.j["transform"]["scale"][i]) + self.j["transform"]["translate"][i]
                self.j["CityObjects"][co]["geographicalExtent"] = bbox


    def get_centroid(self, coid):
        def recusionvisit(a, vs):
          for each in a:
            if isinstance(each, list):
                recusionvisit(each, vs)
            else:
                vs.append(each)
        #-- find the 3D centroid
        centroid = [0, 0, 0]
        total = 0
        for g in self.j['CityObjects'][coid]['geometry']:
            vs = []
            recusionvisit(g["boundaries"], vs)
            for each in vs:
                v = self.j["vertices"][each]
                total += 1
                centroid[0] += v[0]
                centroid[1] += v[1]
                centroid[2] += v[2]
        if (total != 0):
            centroid[0] /= total
            centroid[1] /= total
            centroid[2] /= total
            if "transform" in self.j:
                centroid[0] = (centroid[0] * self.j["transform"]["scale"][0]) + self.j["transform"]["translate"][0]
                centroid[1] = (centroid[1] * self.j["transform"]["scale"][1]) + self.j["transform"]["translate"][1]
                centroid[2] = (centroid[2] * self.j["transform"]["scale"][2]) + self.j["transform"]["translate"][2]
            return centroid
        else:
            return None


    def get_subset_bbox(self, bbox, exclude=False):
        # print ('get_subset_bbox')
        #-- new sliced CityJSON object
        cm2 = CityJSON()
        cm2.j["version"] = self.j["version"]
        cm2.path = self.path
        if "transform" in self.j:
            cm2.j["transform"] = self.j["transform"]
        re = set()            
        for coid in self.j["CityObjects"]:
            centroid = self.get_centroid(coid)
            if ((centroid is not None) and
                (centroid[0] >= bbox[0]) and
                (centroid[1] >= bbox[1]) and
                (centroid[0] <  bbox[2]) and
                (centroid[1] <  bbox[3]) ):
                re.add(coid)
        re2 = copy.deepcopy(re)
        if exclude == True:
            allkeys = set(self.j["CityObjects"].keys())
            re = allkeys ^ re
        #-- also add the parent-children
        for theid in re2:
            if "children" in self.j['CityObjects'][theid]:
                for child in self.j['CityObjects'][theid]['children']:
                    re.add(child)
            if "parents" in self.j['CityObjects'][theid]:
                for each in self.j['CityObjects'][theid]['parents']:
                    re.add(self.j['CityObjects'][each])

        
        for each in re:
            cm2.j["CityObjects"][each] = self.j["CityObjects"][each]
        #-- geometry
        subset.process_geometry(self.j, cm2.j)
        #-- templates
        subset.process_templates(self.j, cm2.j)
        #-- appearance
        if ("appearance" in self.j):
            cm2.j["appearance"] = {}
            subset.process_appearance(self.j, cm2.j)
        #-- metadata
        if ("metadata" in self.j):
            cm2.j["metadata"] = self.j["metadata"]
        cm2.update_bbox()
        return cm2


    def is_co_toplevel(self, co):
        if ('toplevel' in co):
            return co['toplevel']
        if co["type"] in TOPLEVEL:
            return True
        else:
            return False




    def get_subset_random(self, number=1, exclude=False):
        random.seed()
        total = len(self.j["CityObjects"])
        if number > total:
            number = total
        allkeys = list(self.j["CityObjects"].keys())
        re = set()
        count = 0
        while (count < number):
            t = allkeys[random.randint(0, total - 1)]
            if self.is_co_toplevel(self.j["CityObjects"][t]):
                re.add(t)
                count += 1
        if exclude == True:
            sallkeys = set(self.j["CityObjects"].keys())
            re = sallkeys ^ re
        re = list(re)
        return self.get_subset_ids(re)


    def get_subset_ids(self, lsIDs, exclude=False):
        #-- new sliced CityJSON object
        cm2 = CityJSON()
        cm2.j["version"] = self.j["version"]
        cm2.path = self.path
        if "transform" in self.j:
            cm2.j["transform"] = self.j["transform"]
        #-- copy selected CO to the j2
        re = subset.select_co_ids(self.j, lsIDs)
        if exclude == True:
            allkeys = set(self.j["CityObjects"].keys())
            re = allkeys ^ re
        for each in re:
            cm2.j["CityObjects"][each] = self.j["CityObjects"][each]
        #-- geometry
        subset.process_geometry(self.j, cm2.j)
        #-- templates
        subset.process_templates(self.j, cm2.j)
        #-- appearance
        if ("appearance" in self.j):
            cm2.j["appearance"] = {}
            subset.process_appearance(self.j, cm2.j)
        #-- metadata
        if ("metadata" in self.j):
            cm2.j["metadata"] = self.j["metadata"]
        cm2.update_bbox()
        return cm2


    def get_subset_cotype(self, cotype, exclude=False):
        # print ('get_subset_cotype')
        lsCOtypes = [cotype]
        if cotype == 'Building':
            lsCOtypes.append('BuildingInstallation')
            lsCOtypes.append('BuildingPart')
        if cotype == 'Bridge':
            lsCOtypes.append('BridgePart')
            lsCOtypes.append('BridgeInstallation')
            lsCOtypes.append('BridgeConstructionElement')
        if cotype == 'Tunnel':
            lsCOtypes.append('TunnelInstallation')
            lsCOtypes.append('TunnelPart')
        #-- new sliced CityJSON object
        cm2 = CityJSON()
        cm2.j["version"] = self.j["version"]
        cm2.path = self.path
        if "transform" in self.j:
            cm2.j["transform"] = self.j["transform"]
        #-- copy selected CO to the j2
        for theid in self.j["CityObjects"]:
            if exclude == False:
                if self.j["CityObjects"][theid]["type"] in lsCOtypes:
                    cm2.j["CityObjects"][theid] = self.j["CityObjects"][theid]
            else:
                if self.j["CityObjects"][theid]["type"] not in lsCOtypes:
                    cm2.j["CityObjects"][theid] = self.j["CityObjects"][theid]
        #-- geometry
        subset.process_geometry(self.j, cm2.j)
        #-- templates
        subset.process_templates(self.j, cm2.j)
        #-- appearance
        if ("appearance" in self.j):
            cm2.j["appearance"] = {}
            subset.process_appearance(self.j, cm2.j)
        #-- metadata
        if ("metadata" in self.j):
            cm2.j["metadata"] = self.j["metadata"]
        cm2.update_bbox()
        return cm2
        

    def get_textures_location(self):
        """Get the location of the texture files
        
        Assumes that all textures are in the same location. Relative paths
        are expanded to absolute paths.
        
        :returns: path to the directory or URL of the texture files
        :rtype: string (path) or None (on failure)
        :raises: NotADirectoryError
        """
        if "appearance" in self.j:
            if "textures" in self.j["appearance"]:
                p = self.j["appearance"]["textures"][0]["image"]
                cj_dir = os.path.dirname(self.path)
                url = re.match('http[s]?://|www\.', p)
                if url:
                    return url
                else:
                    d = os.path.dirname(p)
                    if len(d) == 0:
                        # textures are in the same dir as the cityjson file
                        return cj_dir
                    elif not os.path.isabs(d):
                        if os.path.isdir(os.path.abspath(d)):
                            # texture dir is not necessarily in the same dir 
                            # as the input file
                            return os.path.abspath(d)
                        elif os.path.isdir(os.path.join(cj_dir, d)):
                            # texture dir is a subdirectory at the input file
                            return os.path.join(cj_dir, d)
                        else:
                            raise NotADirectoryError("Texture directory '%s' not found" % d)
                            return None
            else:
                print("This file does not have textures")
                return None
        else:
            print("This file does not have textures")
            return None


    def update_textures_location(self, new_loc, relative=True):
        """Updates the location of the texture files
        
        If the new location is a directory in the local file system, it is
        expected to exists with the texture files in it.
        
        :param new_loc: path to new texture directory
        :type new_loc: string
        :param relative: create texture links relative to the CityJSON file
        :type relative: boolean
        :returns: None -- modifies the CityJSON
        :raises: InvalidOperation, NotADirectoryError
        """
        curr_loc = self.get_textures_location()
        if curr_loc:
            if re.match('http[s]?://|www\.', new_loc):
                apath = new_loc
                for t in self.j["appearance"]["textures"]:
                    f = os.path.basename(t["image"])
                    t["image"] = os.path.join(apath, f)
            else:
                apath = os.path.abspath(new_loc)
                if not os.path.isdir(apath):
                    raise NotADirectoryError("%s does not exits" % apath)
                elif relative:
                    rpath = os.path.relpath(apath, os.path.dirname(self.path))
                    for t in self.j["appearance"]["textures"]:
                        f = os.path.basename(t["image"])
                        t["image"] = os.path.join(rpath, f)
                else:
                    for t in self.j["appearance"]["textures"]:
                        f = os.path.basename(t["image"])
                        t["image"] = os.path.join(apath, f)
        else:
            raise InvalidOperation("Cannot update textures in a city model without textures")


    def copy_textures(self, new_loc, json_path):
        """Copy the texture files to a new location        
        :param new_loc: path to new texture directory
        :type new_loc: string
        :param json_path: path to the CityJSON file directory
        :type json_path: string
        :returns: None -- modifies the CityJSON
        :raises: InvalidOperation, IOError
        """
        curr_loc = self.get_textures_location()
        if curr_loc:
            apath = os.path.abspath(new_loc)
            if not os.path.isdir(apath):
                os.mkdir(apath)
            if not os.path.abspath(json_path):
                jpath = os.path.abspath(json_path)
            else:
                jpath = json_path
            curr_path = self.path
            try:
                self.path = jpath
                for t in self.j["appearance"]["textures"]:
                    f = os.path.basename(t["image"])
                    curr_path = os.path.join(curr_loc, f)
                    shutil.copy(curr_path, apath)
                # update the location relative to the CityJSON file
                self.update_textures_location(apath, relative=True)
                print("Textures copied to", apath)
            except IOError:
                raise
            finally:
                self.path = curr_path
        else:
            raise InvalidOperation("Cannot copy textures from a city model without textures")


    def validate_textures(self):
        """Check if the texture files exist"""
        raise NotImplemented


    def remove_textures(self):
        for i in self.j["CityObjects"]:
            if "texture" in self.j["CityObjects"][i]:
                del self.j["CityObjects"][i]["texture"]
        if "appearance" in self.j:
            if "textures" in self.j["appearance"]:
                del self.j["appearance"]["textures"]
            if "vertices-texture" in self.j["appearance"]:
                del self.j["appearance"]["vertices-texture"]
            if "default-theme-texture" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-texture"]
        # print (len(self.j["appearance"]))
        if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
            del self.j["appearance"]
        return True


    def remove_materials(self):
        for i in self.j["CityObjects"]:
            if "material" in self.j["CityObjects"][i]:
                del self.j["CityObjects"][i]["material"]
        if "appearance" in self.j:
            if "materials" in self.j["appearance"]:
                del self.j["appearance"]["materials"]
            if "default-theme-material" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-material"]
        if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
            del self.j["appearance"]
        return True


    def number_city_objects(self):
        total = 0
        for id in self.j["CityObjects"]:
            if self.is_co_toplevel(self.j["CityObjects"][id]):
                total += 1
        return total


    def get_info(self):
        info = collections.OrderedDict()
        info["cityjson_version"] = self.get_version()
        info["epsg"] = self.get_epsg()
        info["bbox"] = self.get_bbox()
        if "extensions" in self.j:
            d = set()
            for i in self.j["extensions"]:
                d.add(i)
            info["extensions"] = sorted(list(d))
        info["cityobjects_total"] = self.number_city_objects()
        d = set()
        for key in self.j["CityObjects"]:
            d.add(self.j['CityObjects'][key]['type'])
        info["cityobjects_present"] = sorted(list(d))
        info["vertices_total"] = len(self.j["vertices"])
        info["transform/compressed"] = "transform" in self.j
        d.clear()
        for key in self.j["CityObjects"]:
            for geom in self.j['CityObjects'][key]['geometry']:
                d.add(geom["type"])
        info["geom_primitives_present"] = list(d)
        if 'appearance' in self.j:
            info["materials"] = 'materials' in self.j['appearance']
            info["textures"] = 'textures' in self.j['appearance']
        else:
            info["materials"] = False
            info["textures"] =  False
        return json.dumps(info, indent=2)


    def remove_orphan_vertices(self):
        def visit_geom(a, oldnewids, newvertices):
          for i, each in enumerate(a):
            if isinstance(each, list):
                visit_geom(each, oldnewids, newvertices)
            else:
                if each not in oldnewids:
                    oldnewids[each] = len(newvertices)
                    newvertices.append(each)
        def update_face(a, oldnewids):
          for i, each in enumerate(a):
            if isinstance(each, list):
                update_face(each, oldnewids)
            else:
                a[i] = oldnewids[each]
        #--
        totalinput = len(self.j["vertices"])        
        oldnewids = {}
        newvertices = []
        #-- visit each geom to gather used ids 
        for theid in self.j["CityObjects"]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    visit_geom(g["boundaries"], oldnewids, newvertices)
        #-- update the faces ids
        for theid in self.j["CityObjects"]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    update_face(g["boundaries"], oldnewids)
        #-- replace the vertices, innit?
        newv2 = []
        for v in newvertices:
            newv2.append(self.j["vertices"][v])
        self.j["vertices"] = newv2
        return (totalinput - len(self.j["vertices"]))


    def remove_duplicate_vertices(self):
        def update_geom_indices(a, newids):
          for i, each in enumerate(a):
            if isinstance(each, list):
                update_geom_indices(each, newids)
            else:
                a[i] = newids[each]
        #--            
        totalinput = len(self.j["vertices"])        
        h = {}
        newids = [-1] * len(self.j["vertices"])
        newvertices = []
        for i, v in enumerate(self.j["vertices"]):
            s = str(v[0]) + " " + str(v[1]) + " " + str(v[2])
            if s not in h:
                newid = len(h)
                newids[i] = newid
                h[s] = newid
                newvertices.append(s)
            else:
                newids[i] = h[s]
        #-- update indices
        for theid in self.j["CityObjects"]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    update_geom_indices(g["boundaries"], newids)
        #-- replace the vertices, innit?
        newv2 = []
        for v in newvertices:
            if "transform" in self.j:
                a = list(map(int, v.split()))
            else:
                a = list(map(float, v.split()))
            newv2.append(a)
        self.j["vertices"] = newv2
        return (totalinput - len(self.j["vertices"]))


    def compress(self, important_digits=3):
        if "transform" in self.j:
            raise Exception("CityJSON already compressed")
            return True
        #-- find the minx/miny/minz
        bbox = [9e9, 9e9, 9e9]    
        for v in self.j["vertices"]:
            for i in range(3):
                if v[i] < bbox[i]:
                    bbox[i] = v[i]
        #-- convert vertices in self.j to int
        n = [0, 0, 0]
        p = '%.' + str(important_digits) + 'f' 
        for v in self.j["vertices"]:
            for i in range(3):
                n[i] = v[i] - bbox[i]
            for i in range(3):
                v[i] = int((p % n[i]).replace('.', ''))
        #-- put transform
        self.j["transform"] = {}
        ss = '0.'
        ss += '0'*(important_digits - 1)
        ss += '1'
        ss = float(ss)
        self.j["transform"]["scale"] = [ss, ss, ss]
        self.j["transform"]["translate"] = [bbox[0], bbox[1], bbox[2]]
        #-- clean the file
        re = self.remove_duplicate_vertices()
        # print ("Remove duplicates:", re)
        re = self.remove_orphan_vertices()
        # print ("Remove orphans:", re)
        return True


    def decompress(self):
        if "transform" in self.j:
            for v in self.j["vertices"]:
                v[0] = (v[0] * self.j["transform"]["scale"][0]) + self.j["transform"]["translate"][0]
                v[1] = (v[1] * self.j["transform"]["scale"][1]) + self.j["transform"]["translate"][1]
                v[2] = (v[2] * self.j["transform"]["scale"][2]) + self.j["transform"]["translate"][2]
            del self.j["transform"]
            return True
        else: 
            return False


    def merge(self, lsCMs):
        # decompress() everything
        # updates CityObjects
        # updates vertices
        # updates geometry-templates
        # updates textures
        # updates materials
        #############################
        def update_geom_indices(a, offset):
          for i, each in enumerate(a):
            if isinstance(each, list):
                update_geom_indices(each, offset)
            else:
                if each is not None:
                    a[i] = each + offset
        def update_texture_indices(a, toffset, voffset):
          for i, each in enumerate(a):
            if isinstance(each, list):
                update_texture_indices(each, toffset, voffset)
            else:
                if each is not None:
                    if i == 0:
                        a[i] = each + toffset
                    else:
                        a[i] = each + voffset
        #-- decompress current CM                        
        self.decompress()
        for cm in lsCMs:
            #-- decompress 
            cm.decompress()
            #-- add each CityObjects
            coadded = 0
            for theid in cm.j["CityObjects"]:
                if theid in self.j["CityObjects"]:
                    print ("ERROR: CityObject #", theid, "already present. Skipped.")
                else:
                    self.j["CityObjects"][theid] = cm.j["CityObjects"][theid]
                    coadded += 1
            if coadded == 0:
                continue
            #-- add the vertices + update the geom indices
            offset = len(self.j["vertices"])
            self.j["vertices"] += cm.j["vertices"]
            for theid in cm.j["CityObjects"]:
                for g in cm.j['CityObjects'][theid]['geometry']:
                    update_geom_indices(g["boundaries"], offset)
            #-- templates
            if "geometry-templates" in cm.j:
                if "geometry-templates" in self.j:
                    notemplates = len(self.j["geometry-templates"]["templates"])
                    novtemplate = len(self.j["geometry-templates"]["vertices-templates"])
                else:
                    self.j["geometry-templates"] = {}
                    self.j["geometry-templates"]["templates"] = []
                    self.j["geometry-templates"]["vertices-templates"] = []
                    notemplates = 0
                    novtemplate = 0
                #-- copy templates
                for t in cm.j["geometry-templates"]["templates"]:
                    self.j["geometry-templates"]["templates"].append(t)
                    tmp = self.j["geometry-templates"]["templates"][-1]
                    update_geom_indices(tmp["boundaries"], novtemplate)
                #-- copy vertices
                self.j["geometry-templates"]["vertices-templates"] += cm.j["geometry-templates"]["vertices-templates"]
                #-- update the "template" in each GeometryInstance
                for theid in cm.j["CityObjects"]:
                    for g in self.j['CityObjects'][theid]['geometry']:
                        if g["type"] == 'GeometryInstance':
                            g["template"] += notemplates
            #-- materials
            if ("appearance" in cm.j) and ("materials" in cm.j["appearance"]):
                if ("appearance" in self.j) and ("materials" in self.j["appearance"]):
                    offset = len(self.j["appearance"]["materials"])
                else:
                    if "appearance" not in self.j:
                        self.j["appearance"] = {}
                    if "materials" not in self.j["appearance"]:
                        self.j["appearance"]["materials"] = {}
                    offset = 0
                #-- copy materials
                for m in cm.j["appearance"]["materials"]:
                    self.j["appearance"]["materials"].append(m)
                #-- update the "material" in each Geometry
                for theid in cm.j["CityObjects"]:
                    for g in self.j['CityObjects'][theid]['geometry']:
                        if 'material' in g:
                            for m in g['material']:
                                update_geom_indices(g['material'][m]['values'], offset)
            #-- textures
            if ("appearance" in cm.j) and ("textures" in cm.j["appearance"]):
                if ("appearance" in self.j) and ("textures" in self.j["appearance"]):
                    toffset = len(self.j["appearance"]["textures"])
                    voffset = len(self.j["appearance"]["vertices-texture"])
                else:
                    if "appearance" not in self.j:
                        self.j["appearance"] = {}
                    if "textures" not in self.j["appearance"]:
                        self.j["appearance"]["textures"] = []
                    if "vertices-texture" not in self.j["appearance"]:
                        self.j["appearance"]["vertices-texture"] = []                        
                    toffset = 0
                    voffset = 0
                #-- copy vertices-texture
                self.j["appearance"]["vertices-texture"] += cm.j["appearance"]["vertices-texture"]
                #-- copy textures
                for t in cm.j["appearance"]["textures"]:
                    self.j["appearance"]["textures"].append(t)
                #-- update the "texture" in each Geometry
                for theid in cm.j["CityObjects"]:
                    for g in self.j['CityObjects'][theid]['geometry']:
                        if 'texture' in g:
                            for m in g['texture']:
                                update_texture_indices(g['texture'][m]['values'], toffset, voffset)
        # self.remove_duplicate_vertices()
        # self.remove_orphan_vertices()
        return True


    def upgrade_version_v06_v08(self):
        #-- version 
        self.j["version"] = "0.8"
        #-- crs/epgs
        epsg = self.get_epsg()
        self.j["metadata"] = {}
        if epsg is not None:
            if "crs" in self.j["metadata"]:
                del self.j["metadata"]["crs"]
            self.set_epsg(epsg)
        #-- bbox
        self.update_bbox()
        for id in self.j["CityObjects"]:
            if "bbox" in self.j['CityObjects'][id]:
                self.j["CityObjects"][id]["geographicalExtent"] = self.j["CityObjects"][id]["bbox"]
                del self.j["CityObjects"][id]["bbox"]
        # #-- parent-children: do children have the parent too?
        subs = ['Parts', 'Installations', 'ConstructionElements']
        for id in self.j["CityObjects"]:
            children = []
            for sub in subs:
                if sub in self.j['CityObjects'][id]:
                    for each in self.j['CityObjects'][id][sub]:
                        children.append(each)
                        b = True
            if len(children) > 0:
                #-- remove the Parts/Installations
                self.j['CityObjects'][id]['children'] = children
                for sub in subs:
                    if sub in self.j['CityObjects'][id]:
                         del self.j['CityObjects'][id][sub]
                #-- put the "parent" in each children
                for child in children:
                    if child in self.j['CityObjects']:
                        self.j['CityObjects'][child]['parent'] = id


    def upgrade_version_v08_v09(self, reasons):
        #-- version 
        self.j["version"] = "0.9"
        #-- parent --> parents[]
        allids = []
        for id in self.j["CityObjects"]:
            allids.append(id)
        for id in allids:
            if "parent" in self.j["CityObjects"][id]:
                self.j["CityObjects"][id]["parents"] = [self.j["CityObjects"][id]["parent"]]
                del self.j["CityObjects"][id]["parent"]
        #-- extensions
        if "extensions" in self.j:
            reasons += "Extensions have changed completely in v0.9, update them manually."
            return (False, reasons)
        return (True, "")


    def upgrade_version_v09_v10(self, reasons):
        #-- version 
        self.j["version"] = "1.0"
        #-- extensions
        if "extensions" in self.j:
            for ext in self.j["extensions"]:
                theurl = self.j["extensions"][ext]
                self.j["extensions"][ext] = {"url": theurl, "version": "0.1"}
        return (True, "")


    def upgrade_version(self, newversion):
        re = True
        reasons = ""
        if CITYJSON_VERSIONS_SUPPORTED.count(newversion) == 0:
            return (False, "This version is not supported")
        #-- from v0.6 
        if (self.get_version() == CITYJSON_VERSIONS_SUPPORTED[0]):
            self.upgrade_version_v06_v08()
        #-- v0.8
        if (self.get_version() == CITYJSON_VERSIONS_SUPPORTED[1]):
            (re, reasons) = self.upgrade_version_v08_v09(reasons)
        #-- v0.9
        if (self.get_version() == CITYJSON_VERSIONS_SUPPORTED[2]):
            (re, reasons) = self.upgrade_version_v09_v10(reasons)
        return (re, reasons)


    def triangulate_face(self, face, vnp):


        sf = np.array([], dtype=np.int32)
        for ring in face:
            sf = np.hstack( (sf, np.array(ring)) )
        sfv = vnp[sf]
        # print(sf)
        # print(sfv)
        rings = np.zeros(len(face), dtype=np.int32)
        total = 0
        for i in range(len(face)):
            total += len(face[i])
            rings[i] = total
        # print(rings)

        # 1. normal with Newell's method
        n, b = geom_help.get_normal_newell(sfv)
        #-- if already a triangle then return it
        if ( (len(face) == 1) and (len(face[0]) == 3) ):
            return (face, True, n)
        if b == False:
            return (n, False, n)
        
        # print ("Newell:", n)
        # 2. project to the plane to get xy
        sfv2d = np.zeros( (sfv.shape[0], 2))
        # print (sfv2d)
        for i,p in enumerate(sfv):
            xy = geom_help.to_2d(p, n)
            # print("xy", xy)
            sfv2d[i][0] = xy[0]
            sfv2d[i][1] = xy[1]
        result = mapbox_earcut.triangulate_float64(sfv2d, rings)
        # print (result.reshape(-1, 3))

        for i,each in enumerate(result):
            # print (sf[i])        
            result[i] = sf[each]
        
        # print (result.reshape(-1, 3))
        return (result.reshape(-1, 3), True, n)


    def export2obj(self):
        out = StringIO()
        #-- write vertices
        for v in self.j['vertices']:
            out.write('v ' + str(v[0]) + ' ' + str(v[1]) + ' ' + str(v[2]) + '\n')
        vnp = np.array(self.j["vertices"])
        #-- translate to minx,miny
        minx = 9e9
        miny = 9e9
        for each in vnp:
            if each[0] < minx:
                    minx = each[0]
            if each[1] < miny:
                    miny = each[1]
        for each in vnp:
            each[0] -= minx
            each[1] -= miny
        # print ("min", minx, miny)
        # print(vnp)
        #-- start with the CO
        for theid in self.j['CityObjects']:
            for geom in self.j['CityObjects'][theid]['geometry']:
                out.write('o ' + str(theid) + '\n')
                if ( (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface') ):
                    for face in geom['boundaries']:
                        re, b, n = self.triangulate_face(face, vnp)
                        if b == True:
                            for t in re:
                                out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
                elif (geom['type'] == 'Solid'):
                    for shell in geom['boundaries']:
                        for i, face in enumerate(shell):
                            re, b, n = self.triangulate_face(face, vnp)
                            if b == True:
                                for t in re:
                                    out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
        return out

    def export2stl(self):
        #TODO: refectoring, duplicated code from 2obj()
        out = StringIO()
        out.write("solid\n")

        #-- translate to minx,miny
        vnp = np.array(self.j["vertices"])
        minx = 9e9
        miny = 9e9
        for each in vnp:
            if each[0] < minx:
                    minx = each[0]
            if each[1] < miny:
                    miny = each[1]
        for each in vnp:
            each[0] -= minx
            each[1] -= miny
        # print ("min", minx, miny)
        # print(vnp)
        #-- start with the CO
        for theid in self.j['CityObjects']:
            for geom in self.j['CityObjects'][theid]['geometry']:
                #out.write('o ' + str(theid) + '\n')
                if ( (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface') ):
                    for face in geom['boundaries']:
                        re, b, n = self.triangulate_face(face, vnp)
                        if b == True:
                            for t in re:
                                out.write("facet normal %f %f %f\nouter loop\n" % (n[0], n[1], n[2]))
                                out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[0]][0]), str(self.j["vertices"][t[0]][1]), str(self.j["vertices"][t[0]][2])))
                                out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[1]][0]), str(self.j["vertices"][t[1]][1]), str(self.j["vertices"][t[1]][2])))
                                out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[2]][0]), str(self.j["vertices"][t[2]][1]), str(self.j["vertices"][t[2]][2])))
                                out.write("endloop\nendfacet\n")
                elif (geom['type'] == 'Solid'):
                    for shell in geom['boundaries']:
                        for i, face in enumerate(shell):
                            re, b, n = self.triangulate_face(face, vnp)
                            if b == True:
                                for t in re:
                                    out.write("facet normal %f %f %f\nouter loop\n" % (n[0], n[1], n[2]))
                                    out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[0]][0]), str(self.j["vertices"][t[0]][1]), str(self.j["vertices"][t[0]][2])))
                                    out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[1]][0]), str(self.j["vertices"][t[1]][1]), str(self.j["vertices"][t[1]][2])))
                                    out.write("vertex %s %s %s\n" % (str(self.j["vertices"][t[2]][0]), str(self.j["vertices"][t[2]][1]), str(self.j["vertices"][t[2]][2])))
                                    out.write("endloop\nendfacet\n")
        out.write("endsolid")
        return out

    def reproject(self, epsg):
        wascompressed = False
        if "transform" in self.j:
            self.decompress()
            wascompressed = True
        p1 = pyproj.Proj(init='epsg:%d' % (self.get_epsg()))
        p2 = pyproj.Proj(init='epsg:%d' % (epsg))
        for v in self.j['vertices']:
            x, y, z = pyproj.transform(p1, p2, v[0], v[1], v[2])
            v[0] = x
            v[1] = y
            v[2] = z
        self.set_epsg(epsg)
        if wascompressed == True:
            self.compress()


    def extract_lod(self, thelod):
        for co in self.j["CityObjects"]:
            re = []
            for i, g in enumerate(self.j['CityObjects'][co]['geometry']):
                if int(g['lod']) != thelod:
                    re.append(g)  
                    # print (g)      
            for each in re:
                self.j['CityObjects'][co]['geometry'].remove(each)
        self.remove_duplicate_vertices()
        self.remove_orphan_vertices()        


    def translate(self, values, minimum_xyz):
        if minimum_xyz == True:
            #-- find the minimums
            bbox = [9e9, 9e9, 9e9]    
            for v in self.j["vertices"]:
                for i in range(3):
                    if v[i] < bbox[i]:
                        bbox[i] = v[i]
            bbox[0] = -bbox[0]
            bbox[1] = -bbox[1]
            bbox[2] = -bbox[2]
        else:
            bbox = values
        for v in self.j['vertices']:
            v[0] = v[0] + bbox[0]
            v[1] = v[1] + bbox[1]
            v[2] = v[2] + bbox[2]
        self.set_epsg(None)
        self.update_bbox()
        return bbox
