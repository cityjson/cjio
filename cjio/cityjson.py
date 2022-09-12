
import os
import sys
import re

import json
import urllib.request
import math
import uuid
import shutil
import copy
import random
from io import StringIO

from click import progressbar
from datetime import datetime

from cjio import errors

MODULE_NUMPY_AVAILABLE = True
MODULE_PYPROJ_AVAILABLE = True
MODULE_TRIANGLE_AVAILABLE = True
MODULE_EARCUT_AVAILABLE = True
MODULE_PANDAS_AVAILABLE = True
MODULE_CJVAL_AVAILABLE = True

import numpy as np
try:
    from pyproj.transformer import TransformerGroup
except ImportError as e:
    MODULE_PYPROJ_AVAILABLE = False
try:
    import triangle
except ImportError as e:
    MODULE_TRIANGLE_AVAILABLE = False
try:
    import mapbox_earcut
except ImportError as e:
    MODULE_EARCUT_AVAILABLE = False
try:
    import pandas
except ImportError as e:
    MODULE_PANDAS_AVAILABLE = False
try:
    import cjvalpy
except ImportError as e:
    MODULE_CJVAL_AVAILABLE = False


from cjio import subset, geom_help, convert, models
from cjio.errors import CJInvalidOperation
from cjio.metadata import generate_metadata


CITYJSON_VERSIONS_SUPPORTED = ['0.6', '0.8', '0.9', '1.0', '1.1']

METADATAEXTENDED_VERSION = "0.5"

CITYJSON_PROPERTIES = ["type", 
                       "version", 
                       "extensions", 
                       "transform", 
                       "metadata", 
                       "CityObjects", 
                       "vertices", 
                       "appearance", 
                       "geometry-templates",
                       "+metadata-extended"
                      ]


def load(path, transform: bool = True):
    """Load a CityJSON file for working with it though the API

    :param path: Absolute path to a CityJSON file
    :param transform: Apply the coordinate transformation to the vertices (if applicable)
    :return: A CityJSON object
    """
    with open(path, 'r') as fin:
        try:
            cm = CityJSON(file=fin)
        except OSError as e:
            raise FileNotFoundError
    cm.cityobjects = dict()
    cm.load_from_j(transform=transform)
    return cm

def read_stdin():
    lcount = 1
    #-- read first line
    j1 = json.loads(sys.stdin.readline())
    cm = CityJSON(j=j1)
    if "CityObjects" not in cm.j:
        cm.j["CityObjects"] = {}
    if "vertices" not in cm.j:
        cm.j["vertices"] = []
    while True:
        lcount += 1
        line = sys.stdin.readline()
        if line != '':
            j1 = json.loads(line)
            # TODO: put CityJSONFeature schema and validate here? defensive programming?
            if not( "type" in j1 and j1["type"] == 'CityJSONFeature'):
               raise IOError("Line {} is not of type 'CityJSONFeature'.".format(lcount)) 
            cm.add_cityjsonfeature(j1)
        else:
            break
    return cm


def save(citymodel, path: str, indent: bool = False):
    """Save a city model to a CityJSON file

    :param citymodel: A CityJSON object
    :param path: Absolute path to a CityJSON file
    """
    citymodel.add_to_j()
    # if citymodel.is_transformed:
    #     # FIXME: here should be compression, however the current compression does not work with immutable tuples, but requires mutable lists for the points
    #     pass
    citymodel.remove_duplicate_vertices()
    citymodel.remove_orphan_vertices()
    try:
        with open(path, 'w') as fout:
            if indent:
                json_str = json.dumps(citymodel.j, indent="\t")
            else:
                json_str = json.dumps(citymodel.j, separators=(',',':'))
            fout.write(json_str)
    except IOError as e:
        raise IOError('Invalid output file: %s \n%s' % (path, e))

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
    cm["version"] = CITYJSON_VERSIONS_SUPPORTED[-1]
    cm["extensions"] = {}
    cm["extensions"]["Generic"]= {}
    cm["extensions"]["Generic"]["url"] = "https://cityjson.org/extensions/download/generic.ext.json"
    cm["extensions"]["Generic"]["version"] = "1.0"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    for v in lstVertices:
        cm["vertices"].append(v)
    g = {'type': 'Solid'}
    shell = []
    for f in lstFaces:
        shell.append([f])
    g['boundaries'] = [shell]
    g['lod'] = "1"
    o = {'type': '+GenericCityObject'}
    o['geometry'] = [g]
    cm["CityObjects"]["id-1"] = o
    j = CityJSON(j=cm)
    j.compress()
    return j


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
    cm["version"] = CITYJSON_VERSIONS_SUPPORTED[-1]
    cm["extensions"] = {}
    cm["extensions"]["Generic"]= {}
    cm["extensions"]["Generic"]["url"] = "https://cityjson.org/extensions/download/generic.ext.json"
    cm["extensions"]["Generic"]["version"] = "1.0"
    cm["CityObjects"] = {}
    cm["vertices"] = []
    for v in lstVertices:
        cm["vertices"].append(v)
    g = {'type': 'Solid'}
    shell = []
    for f in lstFaces:
        shell.append(f)
    g['boundaries'] = [shell]
    g['lod'] = "1"
    o = {'type': 'GenericCityObject'}
    o['geometry'] = [g]
    cm["CityObjects"]["id-1"] = o
    j = CityJSON(j=cm)
    j.compress()
    return j

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

class CityJSON:

    def __init__(self, file=None, j=None, ignore_duplicate_keys=False):
        if file is not None:
            self.read(file, ignore_duplicate_keys)
            self.path = os.path.abspath(file.name)
            self.reference_date = datetime.fromtimestamp(os.path.getmtime(file.name)).strftime('%Y-%m-%d')
            self.cityobjects = {}
        elif j is not None:
            self.j = j
            self.cityobjects = {}
            self.path = None
            self.reference_date = datetime.now().strftime('%Y-%m-%d')
        else: #-- create an empty one
            self.j = {}
            self.j["type"] = "CityJSON"
            self.j["version"] = CITYJSON_VERSIONS_SUPPORTED[-1]
            self.j["CityObjects"] = {}
            self.j["vertices"] = []
            self.cityobjects = {}
            self.path = None
            self.reference_date = datetime.now().strftime('%Y-%m-%d')


    def __repr__(self):
        return os.linesep.join(self.get_info())


    ##-- API functions
    # TODO BD: refactor this whole CityJSON class

    def load_from_j(self, transform: bool = True):
        """Populates the CityJSON API members from the json schema member 'j'.

        If the CityJSON API members have values, they are removed and updated.
        """
        # Delete everything first
        self.cityobjects.clear()
        # Then do update
        if 'transform' in self.j:
            self.transform = self.j.pop('transform')
        else:
            self.transform = None
        if transform:
            # Because I can choose to work with untransformed vertices in the API,
            # even though there is a Transform Object in self.transform. So, when the
            # citymodel is written back to json, I we check if we need to transform
            # the vertices.
            # Also, this is very nasty, to have:
            #   - CityJSON.is_transformed ––> the vertices in the API Geometry have been transformed
            #   - CityJSON.transform --> stores the Transform Object for the API
            #   - CityJSON.is_transform() --> checks if the json has a 'transform' property
            self.is_transformed = True if self.transform is not None else False
            do_transform = self.transform
        else:
            self.is_transformed = False
            do_transform = None
        appearance = self.j['appearance'] if 'appearance' in self.j else None
        for co_id, co in self.j['CityObjects'].items():
            # TODO BD: do some verification here
            children = co['children'] if 'children' in co else None
            parents = co['parents'] if 'parents' in co else None
            attributes = co['attributes'] if 'attributes' in co else None
            geometry = []
            for geom in co.get('geometry',[]):
                semantics = geom['semantics'] if 'semantics' in geom else None
                texture = geom['texture'] if 'texture' in geom else None
                geometry.append(
                    models.Geometry(
                        type=geom['type'],
                        lod=geom.get('lod'),
                        boundaries=geom['boundaries'],
                        semantics_obj=semantics,
                        texture_obj=texture,
                        appearance=appearance,
                        vertices=self.j['vertices'],
                        transform=do_transform
                    )
                )
            self.cityobjects[co_id] = models.CityObject(
                id=co_id,
                type=co['type'],
                attributes=attributes,
                children=children,
                parents=parents,
                geometry=geometry
            )

    def get_cityobjects(self, type=None, id=None):
        """Return a subset of CityObjects

        :param type: CityObject type. If a list of types are given, then all types in the list are returned.
        :param id: CityObject ID. If a list of IDs are given, then all objects matching the IDs in the list are returned.
        """
        if type is None and id is None:
            return self.cityobjects
        elif (type is not None) and (id is not None):
            raise AttributeError("Please provide either 'type' or 'id'")
        elif type is not None:
            if isinstance(type, str):
                type_list = [type.lower()]
            elif isinstance(type, list) and isinstance(type[0], str):
                type_list = [t.lower() for t in type]
            else:
                raise TypeError("'type' must be a string or list of strings")
            return {i:co for i,co in self.cityobjects.items() if co.type.lower() in type_list}
        elif id is not None:
            if isinstance(id, str):
                id_list = [id]
            elif isinstance(id, list) and isinstance(id[0], str):
                id_list = id
            else:
                raise TypeError("'id' must be a string or list of strings")
            return {i:co for i,co in self.cityobjects.items() if co.id in id_list}


    def set_cityobjects(self, cityobjects):
        """Creates or updates CityObjects

        .. note:: If a CityObject with the same ID already exists in the model, it will be overwritten

        :param cityobjects: Dictionary of CityObjects, where keys are the CityObject IDs. Same structure as returned by get_cityobjects()
        """
        for co_id, co in cityobjects.items():
            self.cityobjects[co_id] = co


    def to_dataframe(self):
        """Converts the city model to a Pandas data frame where fields are CityObject attributes"""
        if not MODULE_PANDAS_AVAILABLE:
            raise ModuleNotFoundError("Modul 'pandas' is not available, please install it")
        return pandas.DataFrame([co.attributes for co_id,co in self.cityobjects.items()],
                                index=list(self.cityobjects.keys()))


    def reference_geometry(self):
        """Build a coordinate list and index the vertices for writing out to
        CityJSON."""
        cityobjects = dict()
        vertex_lookup = dict()
        vertex_idx = 0
        for co_id, co in self.cityobjects.items():
            j_co = co.to_json()
            geometry, vertex_lookup, vertex_idx = co.build_index(vertex_lookup, vertex_idx)
            j_co['geometry'] = geometry
            cityobjects[co_id] = j_co
        return cityobjects, vertex_lookup


    def add_to_j(self):
        cityobjects, vertex_lookup = self.reference_geometry()
        self.j['vertices'] = [[vtx[0], vtx[1], vtx[2]] for vtx in vertex_lookup.keys()]
        self.j['CityObjects'] = cityobjects

    ##-- end API functions

    def get_version(self):
        return self.j["version"]

    def check_version(self):
        if not isinstance(self.get_version(), str):
            str1 = "CityJSON version should be a string 'X.Y' (eg '1.0')"
            raise errors.CJInvalidVersion(str1)
        pattern = re.compile("^(\d\.)(\d)$")  # -- correct pattern for version
        pattern2 = re.compile("^(\d\.)(\d\.)(\d)$")  # -- wrong pattern with X.Y.Z
        if pattern.fullmatch(self.get_version()) == None:
            if pattern2.fullmatch(self.get_version()) != None:
                str1 = "CityJSON version should be only X.Y (eg '1.0') and not X.Y.Z (eg '1.0.1')"
                raise errors.CJInvalidVersion(str1)
            else:
                str1 = "CityJSON version is wrongly formatted"
                raise errors.CJInvalidVersion(str1)
        if (self.get_version() not in CITYJSON_VERSIONS_SUPPORTED):
            allv = ""
            for v in CITYJSON_VERSIONS_SUPPORTED:
                allv = allv + v + "/"
            str1 = "CityJSON version %s not supported (only versions: %s), not every operators will work.\nPerhaps it's time to upgrade cjio? 'pip install cjio -U'" % (
                self.get_version(), allv)
            raise errors.CJInvalidVersion(str1)
        elif (self.get_version() != CITYJSON_VERSIONS_SUPPORTED[-1]):
            str1 = "v%s is not the latest version, and not everything will work.\n" % self.get_version()
            str1 += "Upgrade the file with 'upgrade' command: 'cjio input.json upgrade save out.json'"
            errors.CJWarning(str1).warn()


    def get_epsg(self):
        if "metadata" not in self.j:
            return None
        if "referenceSystem" in self.j["metadata"]:
            s = self.j["metadata"]["referenceSystem"]
            if "opengis.net/def/crs" not in s or s.rfind("/") < 0:
                raise ValueError(f"Invalid CRS string '{s}'. CRS needs to be formatted according to the OGC Name Type Specification: 'http://www.opengis.net/def/crs/{{authority}}/{{version}}/{{code}}'")
            return int(s[s.rfind("/")+1:])
        else:
            return None


    def is_empty(self):
        if len(self.j["CityObjects"]) == 0:
            return True
        else:
            return False

    def is_transform(self):
        return ("transform" in self.j)

    def read(self, file, ignore_duplicate_keys=False):
        if ignore_duplicate_keys == True:
            try:
                self.j = json.loads(file.read())
            except json.decoder.JSONDecodeError as err:
                raise err
        else:
            try:
                self.j = json.loads(file.read(), object_pairs_hook=self.dict_raise_on_duplicates)
            except ValueError as err:
                raise ValueError(err)
        #-- a CityJSON file?
        if "type" in self.j and self.j["type"] == "CityJSON":
            pass
        else:
            self.j = {}
            raise ValueError("Not a CityJSON file")

    def dict_raise_on_duplicates(self, ordered_pairs):
        d = {}
        for k, v in ordered_pairs:
            if k in d:
               raise ValueError("Invalid CityJSON file, duplicate key for City Object IDs: %r" % (k))
            else:
               d[k] = v
        return d


    def validate(self):
        #-- only latest version, otherwise a mess with versions and different schemas
        #-- this is it, sorry people
        if (self.j["version"] != CITYJSON_VERSIONS_SUPPORTED[-1]):
            s = "Only files with version v%s can be validated. " % (CITYJSON_VERSIONS_SUPPORTED[-1])
            raise Exception(s)
        #-- fetch extensions from the URLs given
        js = []
        js.append(json.dumps(self.j))
        # print("Downloading the Extension JSON schema file(s):")
        if "extensions" in self.j:
            for ext in self.j["extensions"]:
                theurl = self.j["extensions"][ext]["url"]
                try:
                    with urllib.request.urlopen(self.j["extensions"][ext]["url"]) as f:
                        # print("\t- %s" % self.j["extensions"][ext]["url"])
                        # s = theurl[theurl.rfind('/') + 1:]
                        # s = os.path.join(os.getcwd(), s)
                        # tmp = json.loads(f.read().decode('utf-8'))
                        sf = f.read().decode('utf-8')
                        js.append(sf)
                except:
                    s = "'%s' cannot be downloaded\nAbort" % self.j["extensions"][ext]["url"]
                    raise Exception(s)
        val = cjvalpy.CJValidator(js)
        val.validate()
        re = val.get_report()
        return re


    def get_bbox(self):
        if "metadata" not in self.j:
            return self.calculate_bbox()
        if "geographicalExtent" not in self.j["metadata"]:
            return self.calculate_bbox()
        return self.j["metadata"]["geographicalExtent"]


    def calculate_bbox(self):
        """
        Calculate the bbox of the CityJSON.
        """
        if len(self.j["vertices"]) == 0:
            return [0, 0, 0, 0, 0, 0]
        x, y, z = zip(*self.j["vertices"])
        bbox = [min(x), min(y), min(z), max(x), max(y), max(z)]
        if "transform" in self.j:
            s = self.j["transform"]["scale"]
            t = self.j["transform"]["translate"]
            bbox = [a * b + c for a, b, c in zip(bbox, (s + s), (t + t))]
        return bbox


    def update_metadata(self):
        self.update_bbox()
        self.update_metadata_identifier()


    def update_bbox(self):
        """
        Update the bbox (["metadata"]["geographicalExtent"]) of the CityJSON.
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

    def update_metadata_identifier(self):
        """
        Replaces the metadata/identifier (if present) by a new one (UUID)
        """
        if "metadata" in self.j:
            if "identifier" in self.j["metadata"]:
                self.j["metadata"]["identifier"] = str(uuid.uuid4())


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
        if "referenceSystem" not in self.j["metadata"]:
            self.j["metadata"]["referenceSystem"] = {}
        s = 'https://www.opengis.net/def/crs/EPSG/0/' + str(i)
        self.j["metadata"]["referenceSystem"] = s
        return True


    def update_bbox_each_cityobjects(self, addifmissing=False):
        def recusionvisit(a, vs):
          for each in a:
            if isinstance(each, list):
                recusionvisit(each, vs)
            else:
                vs.append(each)
        for co in self.j["CityObjects"]:
            if addifmissing == True or "geographicalExtent" in self.j["CityObjects"][co]:
                vs = []
                bbox = [9e9, 9e9, 9e9, -9e9, -9e9, -9e9]
                if 'geometry' in self.j['CityObjects'][co]:
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
        if 'geometry' in self.j['CityObjects'][coid]:
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


    def get_identifier(self):
        """
        Returns the identifier of this file.

        If there is one in metadata, it will be returned. Otherwise, the filename will.
        """
        if "metadata" in self.j:
            if "identifier" in self.j["metadata"]:
                cm_id = self.j["metadata"]["identifier"]
        if cm_id:
            template = "{cm_id} ({file_id})"
        else:
            template = "{file_id}"
        if "metadata" in self.j:
            if "identifier" in self.j["metadata"]:
                return template.format(cm_id=cm_id, file_id=self.j["metadata"]["identifier"])
        if self.path:
            return os.path.basename(self.path)
        return "unknown"


    def get_title(self):
        """
        Returns the description of this file from metadata.

        If there is none, the identifier will be returned, instead.
        """

        if "metadata" in self.j:
            if "title" in self.j["metadata"]:
                return self.j["metadata"]["title"]
        
        return self.get_identifier()

    def get_subset_bbox(self, bbox, exclude=False):
        # print ('get_subset_bbox')
        re = set()            
        for coid in self.j["CityObjects"]:
            centroid = self.get_centroid(coid)
            if ((centroid is not None) and
                (centroid[0] >= bbox[0]) and
                (centroid[1] >= bbox[1]) and
                (centroid[0] <  bbox[2]) and
                (centroid[1] <  bbox[3]) ):
                re.add(coid)
        return self.subset(lsIDs=re, exclude=exclude)

    def get_subset_radius(self, x, y, radius, exclude=False):
        re = set()            
        for coid in self.j["CityObjects"]:
            centroid = self.get_centroid(coid)
            if (centroid is not None):
                dist = ((centroid[0] - x)**2) + ((centroid[1] - y)**2)
                if dist < radius**2: 
                    re.add(coid)
        return self.subset(lsIDs=re, exclude=exclude)

    def is_co_toplevel(self, co):
        return ("parents" not in co)

    def number_top_co(self):
        count = 0
        allkeys = list(self.j["CityObjects"].keys())
        for k in allkeys:
            if self.is_co_toplevel(self.j["CityObjects"][k]):
                count += 1
        return count

    def get_ordered_ids_top_co(self, limit, offset):
        re = []
        allkeys = list(self.j["CityObjects"].keys())
        for k in allkeys:
            if self.is_co_toplevel(self.j["CityObjects"][k]):
                re.append(k)
        return re[offset:(offset+limit)]


    def subset(self, lsIDs, exclude=False):
        #-- copy selected CO to the j2
        re = subset.select_co_ids(self.j, lsIDs)
        #-- exclude
        if exclude == True:
            sallkeys = set(self.j["CityObjects"].keys())
            re = sallkeys - re
        re = list(re)
        #-- new sliced CityJSON object
        cm2 = CityJSON()
        cm2.j["version"] = copy.deepcopy(self.j["version"])
        cm2.path = copy.deepcopy(self.path)
        if "extensions" in self.j:
            cm2.j["extensions"] = copy.deepcopy(self.j["extensions"])
        if "transform" in self.j:
            cm2.j["transform"] = copy.deepcopy(self.j["transform"])
        #-- select only the COs
        for each in re:
            cm2.j["CityObjects"][each] = copy.deepcopy(self.j["CityObjects"][each])
        #-- geometry
        subset.process_geometry(self.j, cm2.j)
        #-- templates
        subset.process_templates(self.j, cm2.j)
        #-- appearance
        if ("appearance" in self.j):
            cm2.j["appearance"] = {}
            subset.process_appearance(self.j, cm2.j)
        #-- copy all other non mandatory properties
        for p in self.j:
            if p not in CITYJSON_PROPERTIES:
                cm2.j[p] = copy.deepcopy(self.j[p])
        #-- metadata
        if "metadata" in self.j:
            cm2.j["metadata"] = copy.deepcopy(self.j["metadata"])
            cm2.update_metadata()
        if self.has_metadata_extended():
            try:
                cm2.j["+metadata-extended"] = copy.deepcopy(self.j["+metadata-extended"])
                cm2.update_metadata_extended(overwrite=True)
                fids = [fid for fid in cm2.j["CityObjects"]]
                cm2.add_lineage_item("Subset of {}".format(self.get_identifier()), features=fids)
            except:
                pass
        return cm2


    def get_subset_random(self, number=1, exclude=False):
        """Get a random sample of CityObjects without replacement."""
        top_level_cos = [id for id, co in self.j["CityObjects"].items()
                         if self.is_co_toplevel(co)]
        try:
            random_ids = random.sample(top_level_cos, k=number)
        except ValueError:
            # If the sample size 'k' is larger than the number of CityObjects
            random_ids = top_level_cos
        return self.subset(lsIDs=random_ids, exclude=exclude)


    def get_subset_ids(self, lsIDs, exclude=False):
        return self.subset(lsIDs=set(lsIDs), exclude=exclude)


    def get_subset_cotype(self, cotypes, exclude=False):
        # random.seed()
        # total = len(self.j["CityObjects"])
        # if number > total:
        #     number = total
        # allkeys = list(self.j["CityObjects"].keys())
        # re = set()
        # count = 0
        # while (count < number):
        #     t = allkeys[random.randint(0, total - 1)]
        #     if self.is_co_toplevel(self.j["CityObjects"][t]):
        #         re.add(t)
        #         count += 1
        # return self.subset(lsIDs=re, exclude=exclude)
        re = set()
        for theid in self.j["CityObjects"]:
            if self.j["CityObjects"][theid]["type"] in cotypes:
                re.add(theid)
        return self.subset(lsIDs=re, exclude=exclude)

        

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
                url = re.match(r'http[s]?://|www\.', p)
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
                return None
        else:
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
            if re.match(r'http[s]?://|www\.', new_loc):
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
            raise CJInvalidOperation("Cannot update textures in a city model without textures")


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
                raise IOError()
            finally:
                self.path = curr_path
        else:
            raise CJInvalidOperation("Cannot copy textures from a city model without textures")


    def validate_textures(self):
        """Check if the texture files exist"""
        # TODO: implement validate_textures
        raise NotImplemented


    def remove_textures(self):
        for co in self.j["CityObjects"].values():
            for geom in co["geometry"]:
                if "texture" in geom:
                    del geom["texture"]
        if "appearance" in self.j:
            if "textures" in self.j["appearance"]:
                del self.j["appearance"]["textures"]
            if "vertex-texture" in self.j["appearance"]:
                del self.j["appearance"]["vertex-texture"]
            if "default-theme-texture" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-texture"]
        if "appearance" in self.j:
            if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
                del self.j["appearance"]
        return True

    def remove_materials(self):
        for co in self.j["CityObjects"].values():
            for geom in co["geometry"]:
                if "material" in geom:
                    del geom["material"]
        if "appearance" in self.j:
            if "materials" in self.j["appearance"]:
                del self.j["appearance"]["materials"]
            if "default-theme-material" in self.j["appearance"]:
                del self.j["appearance"]["default-theme-material"]
        if "appearance" in self.j:
            if self.j["appearance"] is None or len(self.j["appearance"]) == 0:
                del self.j["appearance"]
        return True


    def number_city_objects_level1(self):
        total = 0
        for id in self.j["CityObjects"]:
            if self.is_co_toplevel(self.j["CityObjects"][id]):
                total += 1
        return total


    def get_info(self, long=False):
        s = []
        s.append("CityJSON version = {}".format(self.get_version()))
        s.append("EPSG = {}".format(self.get_epsg()))
        s.append("bbox = {}".format(self.get_bbox()))
        if "extensions" in self.j:
            d = set()
            for i in self.j["extensions"]:
                d.add(i)
            s.append("Extensions = {}".format(sorted(list(d))))
        #-- hierarchy tree for CityObjects
        s.append("=== CityObjects ===")
        d = {}
        for key in self.j["CityObjects"]:
            ty = self.j['CityObjects'][key]['type']
            if 'parents' not in self.j['CityObjects'][key]:
                if ty not in d:
                    d[ty] = 1
                else: 
                    d[ty] += 1
                self.info_children_dfs(key, ty, d)
        for each in d:
            if each.count('/') == 0:
                s2 = "|-- {} ({})".format(each, d[each])
                s.append(s2)
                self.print_info_tree(s, d, each, 1)
        s.append("===================")
        if 'appearance' in self.j:
            s.append("materials = {}".format('materials' in self.j['appearance']))
            s.append("textures = {}".format('textures' in self.j['appearance']))
        else:
            s.append("materials = {}".format(False))
            s.append("textures = {}".format(False))
        if long == False:
            return s    
        #-- all/long version
        s.append("vertices_total = {}".format(len(self.j["vertices"])))
        s.append("is_triangulated = {}".format(self.is_triangulated()))
        geoms = set()
        lod = set()
        sem_srf = set()
        co_attributes = set()
        for key in self.j["CityObjects"]:
            if 'attributes' in self.j['CityObjects'][key]:
                for attr in self.j['CityObjects'][key]['attributes'].keys():
                    co_attributes.add(attr)
            if 'geometry' in self.j['CityObjects'][key]:
                for geom in self.j['CityObjects'][key]['geometry']:
                    geoms.add(geom["type"])
                    if "lod" in geom:
                        lod.add(geom["lod"])
                    else: #-- it's a geometry-template
                        lod.add(self.j["geometry-templates"]["templates"][geom["template"]]["lod"])
                    if "semantics" in geom:
                        for srf in geom["semantics"]["surfaces"]:
                            sem_srf.add(srf["type"])
        getsorted = lambda a : sorted(list(a))
        s.append("geom primitives = {}".format(getsorted(geoms)))
        s.append("LoD = {}".format(getsorted(lod)))
        s.append("semantics surfaces = {}".format(getsorted(sem_srf)))
        s.append("attributes = {}".format(getsorted(co_attributes)))
        return s


    def print_info_tree(self, s, d, t, level):
        for each in d:
            if each.startswith(t + '/') == True and each.count('/') == level:
                x = each.rsplit("/")[-1]
                s2 = "{}|-- {} ({})".format(" "*4*level, x, d[each])    
                s.append(s2)
                self.print_info_tree(s, d, each, level+1)

    def info_children_dfs(self, key, typeparent, d):
        if 'children' in self.j['CityObjects'][key]:
            for c in self.j['CityObjects'][key]['children']:
                ct = self.j['CityObjects'][c]['type']
                s = typeparent + '/' + ct
                # print(s)
                if s not in d:
                    d[s] = 1
                else: 
                    d[s] += 1
                self.info_children_dfs(c, s, d)


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
            if 'geometry' in self.j['CityObjects'][theid]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    visit_geom(g["boundaries"], oldnewids, newvertices)
        #-- update the faces ids
        for theid in self.j["CityObjects"]:
            if 'geometry' in self.j['CityObjects'][theid]:
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
            s = "{x} {y} {z}".format(x=v[0], y=v[1], z=v[2])
            if s not in h:
                newid = len(h)
                newids[i] = newid
                h[s] = newid
                newvertices.append(s)
            else:
                newids[i] = h[s]
        #-- update indices
        for theid in self.j["CityObjects"]:
            if 'geometry' in self.j['CityObjects'][theid]:
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
            return False
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

    
    def add_cityjsonfeature(self, j):
        offset = len(self.j["vertices"])
        self.j["vertices"] += j["vertices"]
        #-- add each CityObjects
        for theid in j["CityObjects"]:
            self.j["CityObjects"][theid] = j["CityObjects"][theid]
            if 'geometry' in self.j['CityObjects'][theid]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    update_geom_indices(g["boundaries"], offset)

        #-- materials
        if ("appearance" in j) and ("materials" in j["appearance"]):
            if ("appearance" in self.j) and ("materials" in self.j["appearance"]):
                offset = len(self.j["appearance"]["materials"])
            else:
                if "appearance" not in self.j:
                    self.j["appearance"] = {}
                if "materials" not in self.j["appearance"]:
                    self.j["appearance"]["materials"] = []
                offset = 0
            #-- copy materials
            for m in j["appearance"]["materials"]:
                self.j["appearance"]["materials"].append(m)
            #-- update the "material" in each Geometry
            for theid in j["CityObjects"]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    if 'material' in g:
                        for m in g['material']:
                            if 'values' in g['material'][m]:
                                update_geom_indices(g['material'][m]['values'], offset)
                            else:
                                g['material'][m]['value'] = g['material'][m]['value'] + offset
        #-- textures
        if ("appearance" in j) and ("textures" in j["appearance"]):
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
            self.j["appearance"]["vertices-texture"] += j["appearance"]["vertices-texture"]
            #-- copy textures
            for t in j["appearance"]["textures"]:
                self.j["appearance"]["textures"].append(t)
            #-- update the "texture" in each Geometry
            for theid in j["CityObjects"]:
                for g in self.j['CityObjects'][theid]['geometry']:
                    if 'texture' in g:
                        for m in g['texture']:
                            if 'values' in g['texture'][m]:
                                update_texture_indices(g['texture'][m]['values'], toffset, voffset)
                            else:
                                raise KeyError(f"The member 'values' is missing from the texture '{m}' in CityObject {theid}")

        self.remove_duplicate_vertices()
        self.remove_orphan_vertices()
        self.update_bbox()                    


    def merge(self, lsCMs):
        # decompress() everything
        # updates CityObjects
        # updates vertices
        # updates geometry-templates
        # updates textures
        # updates materials
        #############################

        #-- decompress current CM
        imp_digits = math.ceil(abs(math.log(self.j["transform"]["scale"][0], 10)))
        self.decompress()

        for cm in lsCMs:
            #-- decompress 
            if math.ceil(abs(math.log(cm.j["transform"]["scale"][0], 10))) > imp_digits:
                imp_digits = math.ceil(abs(math.log(cm.j["transform"]["scale"][0], 10)))
            cm.decompress()
            offset = len(self.j["vertices"])
            self.j["vertices"] += cm.j["vertices"]
            #-- add each CityObjects
            for theid in cm.j["CityObjects"]:
                if theid in self.j["CityObjects"]:
                    #-- merge attributes if not present (based on the property name only)
                    if "attributes" in cm.j["CityObjects"][theid]:
                        for a in cm.j["CityObjects"][theid]["attributes"]:
                            if a not in self.j["CityObjects"][theid]["attributes"]:
                                self.j["CityObjects"][theid]["attributes"][a] = cm.j["CityObjects"][theid]["attributes"][a]
                    #-- merge geoms if not present (based on LoD only)
                    if 'geometry' in self.j['CityObjects'][theid]:
                        for g in cm.j['CityObjects'][theid]['geometry']:
                            thelod = str(g["lod"])
                            # print ("-->", thelod)
                            b = False
                            for g2 in self.j['CityObjects'][theid]['geometry']:
                                if g2["lod"] == thelod:
                                    b = True
                                    break
                            if b == False:
                                self.j['CityObjects'][theid]['geometry'].append(g)
                                update_geom_indices(self.j['CityObjects'][theid]['geometry'][-1]["boundaries"], offset)
                else:
                    #-- copy the CO
                    self.j["CityObjects"][theid] = cm.j["CityObjects"][theid]
                    if 'geometry' in self.j['CityObjects'][theid]:
                        for g in self.j['CityObjects'][theid]['geometry']:
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
                    if 'geometry' in self.j['CityObjects'][theid]:
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
                        self.j["appearance"]["materials"] = []
                    offset = 0
                #-- copy materials
                for m in cm.j["appearance"]["materials"]:
                    self.j["appearance"]["materials"].append(m)
                #-- update the "material" in each Geometry
                for theid in cm.j["CityObjects"]:
                    for g in self.j['CityObjects'][theid].get('geometry',[]):
                        if 'material' in g:
                            for m in g['material']:
                                if 'values' in g['material'][m]:
                                    update_geom_indices(g['material'][m]['values'], offset)
                                else:
                                    g['material'][m]['value'] = g['material'][m]['value'] + offset
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
                    for g in self.j['CityObjects'][theid].get('geometry',[]):
                        if 'texture' in g:
                            for m in g['texture']:
                                if 'values' in g['texture'][m]:
                                    update_texture_indices(g['texture'][m]['values'], toffset, voffset)
                                else:
                                    raise KeyError(f"The member 'values' is missing from the texture '{m}' in CityObject {theid}")
            #-- metadata
            if self.has_metadata_extended() or cm.has_metadata_extended():
                try:
                    fids = [fid for fid in cm.j["CityObjects"]]
                    src = {
                        "description": cm.get_title(),
                        "sourceReferenceSystem": "urn:ogc:def:crs:EPSG::{}".format(cm.get_epsg()) if cm.get_epsg() else None
                    }
                    self.add_lineage_item("Merge {} into {}".format(cm.get_identifier(), self.get_identifier()), features=fids, source=[src])
                except:
                    pass
        self.remove_duplicate_vertices()
        self.remove_orphan_vertices()
        self.update_bbox()
        self.compress(imp_digits)
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


    def upgrade_version_v10_v11(self, reasons, digit):
        #-- version
        self.j["version"] = "1.1"
        #-- compress for "transform"
        self.compress(digit)
        #-- lod=string
        for theid in self.j["CityObjects"]:
            if "geometry" in self.j['CityObjects'][theid]:
                for each, geom in enumerate(self.j['CityObjects'][theid]['geometry']):
                    if self.j['CityObjects'][theid]['geometry'][each]["type"] != "GeometryInstance":
                        self.j['CityObjects'][theid]['geometry'][each]['lod'] = str(self.j['CityObjects'][theid]['geometry'][each]['lod'])
        if "geometry-templates" in self.j:
            for i, g in enumerate(self.j["geometry-templates"]["templates"]):
                self.j["geometry-templates"]["templates"][i]["lod"] = str(self.j["geometry-templates"]["templates"][i]["lod"])
        #-- CityObjectGroup
            # members -> children
            # add parents to children
        for theid in self.j["CityObjects"]:
            if self.j["CityObjects"][theid]['type'] == 'CityObjectGroup':
                self.j["CityObjects"][theid]['children'] = self.j["CityObjects"][theid]['members']
                del self.j["CityObjects"][theid]['members']
                for ch in self.j["CityObjects"][theid]['children']:
                    if 'parents' not in self.j["CityObjects"][ch]:
                        self.j["CityObjects"][ch]["parents"] = []
                    if theid not in self.j["CityObjects"][ch]["parents"]:
                        self.j["CityObjects"][ch]["parents"].append(theid)
        #-- empty geometries
        for theid in self.j["CityObjects"]:
            if ("geometry" in self.j['CityObjects'][theid]) and (len(self.j['CityObjects'][theid]['geometry']) == 0):
                del self.j['CityObjects'][theid]['geometry']
        #-- BridgeConstructionElement -> BridgeConstructiveElement
        for theid in self.j["CityObjects"]:
            if self.j["CityObjects"][theid]['type'] == 'BridgeConstructionElement':
                self.j["CityObjects"][theid]['type'] = 'BridgeConstructiveElement'
        #-- CRS: use the new OGC scheme
        if "metadata" in self.j and "referenceSystem" in self.j["metadata"]:
            s = self.j["metadata"]["referenceSystem"]
            if "epsg" in s.lower():
                self.j["metadata"]["referenceSystem"] = "https://www.opengis.net/def/crs/EPSG/0/%d" % int(s[s.find("::")+2:])
        #-- addresses are now arrays TODO
        for theid in self.j["CityObjects"]:
            if "address" in self.j["CityObjects"][theid]:
                self.j["CityObjects"][theid]["address"] = [self.j["CityObjects"][theid]["address"]]
        #-- metadata calculate
        if "metadata" in self.j:
            v11_properties = {
                "citymodelIdentifier": "identifier", 
                "datasetPointOfContact": "pointOfContact", 
                "datasetTitle": "title", 
                "datasetReferenceDate": "referenceDate", 
                "geographicalExtent": "geographicalExtent", 
                "referenceSystem": "referenceSystem"
            }
            to_delete = []
            for each in self.j["metadata"]:
                if each not in v11_properties:
                    self.add_metadata_extended_property()
                    self.j["+metadata-extended"][each] = self.j["metadata"][each]
                    if each == "spatialRepresentationType":
                        self.j["+metadata-extended"][each] = [self.j["metadata"][each]]
                    to_delete.append(each)
            for each in to_delete:
                del self.j["metadata"][each]
            #-- rename to the names
            for each in v11_properties:
                if each in self.j["metadata"]:
                    tmp = self.j["metadata"][each]
                    self.j["metadata"].pop(each)
                    self.j["metadata"][v11_properties[each]] = tmp
        #-- GenericCityObject is no longer, add the Extension GenericCityObject
        gco = False
        for theid in self.j["CityObjects"]:
            if self.j["CityObjects"][theid]['type'] == 'GenericCityObject':
                self.j["CityObjects"][theid]['type'] = '+GenericCityObject'
                gco = True
        if gco == True:
            reasons = '"GenericCityObject" is no longer in v1.1, instead Extensions are used.'
            reasons += ' Your "GenericCityObject" have been changed to "+GenericCityObject"'
            reasons += ' and the simple Extension "Generic" is used.'
            if "extensions" not in self.j:
                self.j["extensions"] = {}
            self.j["extensions"]["Generic"]= {}
            #-- TODO: change URL for Generic Extension
            self.j["extensions"]["Generic"]["url"] = "https://cityjson.org/extensions/download/generic.ext.json"
            self.j["extensions"]["Generic"]["version"] = "1.0"
            return (False, reasons)
        else:
            return (True, "")


    def upgrade_version(self, newversion, digit):
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
        #-- v1.0
        if (self.get_version() == CITYJSON_VERSIONS_SUPPORTED[3]):
            (re, reasons) = self.upgrade_version_v10_v11(reasons, digit)
        return (re, reasons)


    def export2b3dm(self):
        glb = convert.to_glb(self)
        b3dm = convert.to_b3dm(self, glb)
        return b3dm


    def export2glb(self):
        self.decompress()
        glb = convert.to_glb(self)
        return glb

    def export2jsonl(self):
        out = StringIO()
        j2 = {}
        j2["type"] = "CityJSON"
        j2["version"] = CITYJSON_VERSIONS_SUPPORTED[-1]
        j2["CityObjects"] = {}
        j2["vertices"] = []
        j2["transform"] = self.j["transform"]
        if "metadata" in self.j:
            j2["metadata"] = self.j["metadata"]
        if "+metadata-extended" in self.j:
            j2["+metadata-extended"] = self.j["+metadata-extended"]            
        if "extensions" in self.j:
            j2["extensions"] = self.j["extensions"]
        json_str = json.dumps(j2, separators=(',',':'))
        out.write(json_str + '\n')
        #-- take each IDs and create on CityJSONFeature
        idsdone = set()
        theallowedproperties = ["type", "id", "CityObjects", "vertices", "appearance"]
        for theid in self.j["CityObjects"]:
            if ("parents" not in self.j["CityObjects"][theid]) and (theid not in idsdone):
                cm2 = self.get_subset_ids([theid])
                cm2.j["type"] = "CityJSONFeature"
                cm2.j["id"] = theid
                # allp = cm2.j
                todelete = []
                for p in cm2.j:
                    if p not in theallowedproperties:
                        todelete.append(p)
                for p in todelete:
                    del cm2.j[p]
                #-- TODO: remove and deal with geometry-templates here
                #--       they need to be deferenced
                if "geometry-templates" in cm2.j:
                    errors.CJWarning("PANIC! geometry-templates cannot be processed yet").warn()
                json_str = json.dumps(cm2.j, separators=(',',':'))
                out.write(json_str + '\n')
                for theid2 in cm2.j["CityObjects"]:
                    idsdone.add(theid)
        return out

    def export2obj(self, sloppy):
        imp_digits = math.ceil(abs(math.log(self.j["transform"]["scale"][0], 10)))
        ids = "." + str(imp_digits) + "f"
        self.decompress()
        out = StringIO()
        #-- write vertices
        for v in self.j['vertices']:
            s = format("v {} {} {}\n".format(format(v[0], ids), format(v[1], ids), format(v[2], ids)))
            out.write(s)
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
            if 'geometry' not in self.j['CityObjects'][theid]:
                continue
            for geom in self.j['CityObjects'][theid]['geometry']:
                out.write('o ' + str(theid) + '\n')
                if ( (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface') ):
                    for face in geom['boundaries']:
                        re, b = geom_help.triangulate_face(face, vnp, sloppy)
                        if b == True:
                            for t in re:
                                out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
                elif (geom['type'] == 'Solid'):
                    for shell in geom['boundaries']:
                        for i, face in enumerate(shell):
                            re, b = geom_help.triangulate_face(face, vnp, sloppy)
                            if b == True:
                                for t in re:
                                    out.write("f %d %d %d\n" % (t[0] + 1, t[1] + 1, t[2] + 1))
        self.compress(imp_digits)
        return out

    def export2stl(self, sloppy):
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
                if ( (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface') ):
                    for face in geom['boundaries']:
                        re, b = geom_help.triangulate_face(face, vnp, sloppy)
                        n, bb = geom_help.get_normal_newell(face)
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
                            re, b = geom_help.triangulate_face(face, vnp, sloppy)
                            n, bb = geom_help.get_normal_newell(face)
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
        if not MODULE_PYPROJ_AVAILABLE:
            raise ModuleNotFoundError("Modul 'pyproj' is not available, please install it from https://pypi.org/project/pyproj/")
        imp_digits = math.ceil(abs(math.log(self.j["transform"]["scale"][0], 10)))
        self.decompress()
        # Using TransformerGroup instead of Transformer, because we cannot retrieve the
        # transformer defintion from it.
        # See https://github.com/pyproj4/pyproj/issues/753#issuecomment-737249093
        tg = TransformerGroup(f"EPSG:{self.get_epsg():d}",
                              f"EPSG:{epsg:d}",
                              always_xy=True)
        # TODO: log.info(f"Transformer: {tg.transformers[0].description}")
        with progressbar(self.j['vertices']) as vertices:
            for v in vertices:
                x, y, z = tg.transformers[0].transform(v[0], v[1], v[2])
                v[0] = x
                v[1] = y
                v[2] = z
        self.set_epsg(epsg)
        self.update_bbox()
        self.update_bbox_each_cityobjects(False)
        #-- recompress by using the number of digits we had in original file
        self.compress(imp_digits)

    def remove_attribute(self, attr):
        for co in self.j["CityObjects"]:
            if "attributes" in self.j["CityObjects"][co]:
                if attr in self.j["CityObjects"][co]["attributes"]:
                    del self.j["CityObjects"][co]["attributes"][attr]

    def extract_lod(self, thelod):
        def lod_to_string(lod):
            if lod is None:
                return None
            elif isinstance(lod, float):
                return str(round(lod, 1))
            elif isinstance(lod, int):
                return str(lod)
            elif isinstance(lod, str):
                return lod
            else:
                raise ValueError(f"Type {type(lod)} is not allowed as input")

    def rename_attribute(self, oldattr, newattr):
        for co in self.j["CityObjects"]:
            if "attributes" in self.j["CityObjects"][co]:
                if oldattr in self.j["CityObjects"][co]["attributes"]:
                    tmp = self.j["CityObjects"][co]["attributes"][oldattr]
                    self.j["CityObjects"][co]["attributes"][newattr] = tmp
                    del self.j["CityObjects"][co]["attributes"][oldattr]

    def filter_lod(self, thelod):
        for co in self.j["CityObjects"]:
            re = []
            if 'geometry' in self.j['CityObjects'][co]:
                for i, g in enumerate(self.j['CityObjects'][co]['geometry']):
                    if str(g['lod']) != thelod:
                        re.append(g)
                        # print (g)
                for each in re:
                    self.j['CityObjects'][co]['geometry'].remove(each)
        self.remove_duplicate_vertices()
        self.remove_orphan_vertices()
        self.update_bbox()
        #-- metadata
        if self.has_metadata_extended():
            try:
                self.update_metadata_extended(overwrite=True)
                fids = [fid for fid in self.j["CityObjects"]]
                self.add_lineage_item("Extract LoD{} from {}".format(thelod, self.get_identifier()), features=fids)
            except:
                pass


    def translate(self, values, minimum_xyz):
        if minimum_xyz == True:
            self.j["transform"]["translate"][0] -= bbox[0]
            self.j["transform"]["translate"][1] -= bbox[1]
            self.j["transform"]["translate"][2] -= bbox[2]
        else:
            bbox = values
            self.j["transform"]["translate"][0] += bbox[0]
            self.j["transform"]["translate"][1] += bbox[1]
            self.j["transform"]["translate"][2] += bbox[2]
        self.set_epsg(None)
        self.update_bbox()
        return bbox

    
    def has_metadata(self):
        """
        Returns whether metadata exist in this CityJSON file or not
        """
        return "metadata" in self.j

    def has_metadata_extended(self):
        """
        Returns whether +metadata-extended exist in this CityJSON file or not
        """
        return "+metadata-extended" in self.j

    def metadata_extended_remove(self):
        """
        Remove the +metadata-extended in this CityJSON file (if present)
        """
        if "+metadata-extended" in self.j:
            del self.j["+metadata-extended"]
        if "extensions" in self.j and "MetadataExtended" in self.j["extensions"]:
            del self.j["extensions"]["MetadataExtended"]

    def add_metadata_extended_property(self):
        """
        Adds the +metadata-extended + the link to Extension
        """
        if "+metadata-extended" not in self.j:
            self.j["+metadata-extended"] = {}
            if "extensions" not in self.j:
                self.j["extensions"] = {}
            self.j["extensions"]["MetadataExtended"]= {}
            self.j["extensions"]["MetadataExtended"]["url"] = "https://raw.githubusercontent.com/cityjson/metadata-extended/{}/metadata-extended.ext.json".format(METADATAEXTENDED_VERSION)
            self.j["extensions"]["MetadataExtended"]["version"] = METADATAEXTENDED_VERSION

    def get_metadata(self):
        """
        Returns the "metadata" property of this CityJSON file

        Raises a KeyError exception if metadata is missing
        """
        if not "metadata" in self.j:
            raise KeyError("Metadata is missing")
        return self.j["metadata"]

    def get_metadata_extended(self):
        """
        Returns the "+metadata-extended" property of this CityJSON file

        Raises a KeyError exception if metadata is missing
        """
        if not "+metadata-extended" in self.j:
            raise KeyError("MetadataExtended is missing")
        return self.j["+metadata-extended"]


    def compute_metadata_extended(self, overwrite=False):
        """
        Returns the +metadata-extended of this CityJSON file
        """
        return generate_metadata(citymodel=self.j,
                                 filename=self.path,
                                 overwrite_values=overwrite)


    def update_metadata_extended(self, overwrite=False):
        """
        Computes and updates the "metadata" property of this CityJSON dataset
        """
        self.add_metadata_extended_property()
        metadata, errors = self.compute_metadata_extended(overwrite)
        self.j["+metadata-extended"] = metadata
        self.update_bbox()
        return (True, errors)


    def add_lineage_item(self, description: str, features: list = None, source: list = None, processor: dict = None):
        """Adds a lineage item in metadata.

        :param description: A string with the description of the process
        :param features: A list of object ids that are affected by it
        :param source: A list of sources. Every source is a dict with
            the respective info (description, sourceReferenceSystem etc.)
        :param processor: A dict with contact information for the
            person that conducted the processing
        """
        nu = datetime.now()
        new_item = {
            "processStep": {
                "description": description,
                "stepDateTime": str(nu.isoformat()) + "Z"
            }
        }
        if isinstance(features, list):
            new_item["featureIDs"] = features
        if isinstance(source, list):
            new_item["source"] = source
        if isinstance(processor, dict):
            new_item["processStep"]["processor"] = processor
        if not self.has_metadata_extended():
            self.add_metadata_extended_property()
        if not "lineage" in self.j["+metadata-extended"]:
            self.j["+metadata-extended"]["lineage"] = []
        self.j["+metadata-extended"]["lineage"].append(new_item)
        

    def triangulate(self, sloppy):
        """Triangulate the CityJSON file face by face together with the texture information.

        :param sloppy: A boolean, True=mapbox-earcut False=Shewchuk-robust
        """
        vnp = np.array(self.j["vertices"])
        for theid in self.j['CityObjects']:
            # print(theid)
            if 'geometry' not in self.j['CityObjects'][theid]:
                continue
            for geom in self.j['CityObjects'][theid]['geometry']:
                sflag = False
                mflag = False
                tflag = False
                slist = []
                mlist = []
                texlist = []
                material = {}
                texture = {}
                # 1.semantics
                if 'semantics' in geom:
                    sflag = True
                # 2. materials
                if 'material' in geom:
                    material = geom['material']
                    for item in material.items():
                        if list(item[1].keys())[0] == 'value':
                            mlist.append(item[1]['value'])
                        elif list(item[1].keys())[0] == 'values':
                            mlist.append([])
                    mflag = True
                # 3. texture
                if 'texture' in geom:
                    texture = geom['texture']
                    tkeys = []
                    for item in texture.items():
                        texlist.append([])
                    for key in texture.keys():
                        tkeys.append(key)
                    tflag = True


                # triangulate the geometry type MultiSurface and CompositeSurface
                if (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface'):
                    tlist1 = []
                    for i, face in enumerate(geom['boundaries']):
                        tposition = 0
                        tmaplist = []
                        if tflag:
                            for key in tkeys:
                                tmap = {}
                                for ii, f in enumerate(face):
                                    for iii, ff in enumerate(f):
                                        if texture[key]['values'][i][ii][0] is None:
                                            break
                                        else:
                                            tposition = texture[key]['values'][i][ii][0]
                                            tmap[ff] = texture[key]['values'][i][ii][iii + 1]
                                tmaplist.append(tmap)
                        if ((len(face) == 1) and (len(face[0]) == 3)):
                            re = np.array(face)
                            b = True
                        else:
                            re, b = geom_help.triangulate_face(face, vnp, sloppy)
                            # re, b = geom_help.triangulate_face(face, vnp)

                        if b == True:
                            for t in re:
                                tlist2 = []
                                tlist2.append(t.tolist())
                                tlist1.append(tlist2)

                                if sflag:
                                    if geom['semantics']['values'] is None:
                                        slist = None
                                        break
                                    else:
                                        slist.append(geom['semantics']['values'][i])

                                if mflag:
                                    for j,l in enumerate(mlist):
                                        if type(l).__name__ == 'list':
                                            l.append(material[list(material.keys())[j]]['values'][i])
                                        else:
                                            continue

                                if tflag:
                                    for jj in range(len(tmaplist)):
                                        texlist1 = []
                                        texlist2 = [tposition]

                                        if bool(tmaplist[jj]):

                                            for vindex in t:
                                                texlist2.append(tmaplist[jj][vindex])
                                        else:
                                            texlist2[0] = None
                                        texlist1.append(texlist2)
                                        texlist[jj].append(texlist1)


                    geom['boundaries'] = tlist1
                    if sflag:
                        geom['semantics']['values'] = slist

                    if mflag:
                        for j, item in enumerate(material.items()):
                            item[1][list(item[1].keys())[0]] = mlist[j]
                        geom['material'] = material

                    if tflag:
                        for j,item in enumerate(texture.items()):
                            item[1][list(item[1].keys())[0]] = texlist[j]
                        geom['texture'] = texture



                # triangulate the geometry type Solid
                elif (geom['type'] == 'Solid'):
                    tlist1 = []
                    minit = copy.deepcopy(mlist)
                    texinit = copy.deepcopy(texlist)
                    for sidx, shell in enumerate(geom['boundaries']):
                        slist1 = []
                        tlist2 = []
                        texlist0 = copy.deepcopy(texinit)
                        mlist1 = copy.deepcopy(minit)
                        for i, face in enumerate(shell):
                            tposition = 0
                            tmaplist = []
                            if tflag:
                                for key in tkeys:
                                    tmap = {}
                                    for ii, f in enumerate(face):
                                        for iii, ff in enumerate(f):
                                            if texture[key]['values'][sidx][i][ii][0] is None:
                                                break
                                            else:
                                                tposition = texture[key]['values'][sidx][i][ii][0]
                                                tmap[ff] = texture[key]['values'][sidx][i][ii][iii + 1]
                                    tmaplist.append(tmap)
                            if ((len(face) == 1) and (len(face[0]) == 3)):
                                re = np.array(face)
                                b = True
                            else:
                                re, b = geom_help.triangulate_face(face, vnp, sloppy)
                            if b == True:
                                for t in re:
                                    tlist3 = []
                                    tlist3.append(t.tolist())
                                    tlist2.append(tlist3)
                                    if sflag:
                                        if geom['semantics']['values'] is None:
                                            slist = None
                                            break
                                        elif geom['semantics']['values'][sidx] is None:
                                            slist1 = None
                                            break
                                        else:
                                            slist1.append(geom['semantics']['values'][sidx][i])
                                    if mflag:
                                        for j, l in enumerate(mlist1):
                                            if type(l).__name__ == 'list':
                                                l.append(material[list(material.keys())[j]]['values'][0][i])
                                            else:
                                                continue

                                    if tflag:

                                        for jj in range(len(tmaplist)):
                                            texlist1 = []
                                            texlist2 = [tposition]

                                            if bool(tmaplist[jj]):

                                                for vindex in t:
                                                    texlist2.append(tmaplist[jj][vindex])
                                            else:
                                                texlist2[0] = None
                                            texlist1.append(texlist2)
                                            texlist0[jj].append(texlist1)

                        tlist1.append(tlist2)
                        if slist is not None:
                            slist.append(slist1)
                        for j,l in enumerate(mlist):
                            if type(l).__name__ == 'list' and len(mlist1[j])!=0:
                                l.append(mlist1[j])
                            else:
                                continue
                        for j,l in enumerate(texlist):
                            l.append(texlist0[j])

                    geom['boundaries'] = tlist1
                    if sflag:
                        geom['semantics']['values'] = slist

                    if mflag:
                        for j, item in enumerate(material.items()):
                            item[1][list(item[1].keys())[0]] = mlist[j]
                        geom['material'] = material

                    if tflag:
                        for j,item in enumerate(texture.items()):
                            item[1][list(item[1].keys())[0]] = texlist[j]
                        geom['texture'] = texture


                # triangulate the geometry type MultiSolid and CompositeSolid
                elif ((geom['type'] == 'MultiSolid') or (geom['type'] == 'CompositeSolid')):
                    tlist1 = []
                    minit = copy.deepcopy(mlist)
                    texinit = copy.deepcopy(texlist)
                    for solididx, solid in enumerate(geom['boundaries']):
                        slist1 = []
                        tlist2 = []
                        mlist1 = copy.deepcopy(minit)
                        texlist0 = copy.deepcopy(texinit)
                        for sidx, shell in enumerate(solid):
                            slist2 = []
                            tlist3 = []
                            mlist2 = copy.deepcopy(minit)
                            texlist1 = copy.deepcopy(texinit)
                            for i, face in enumerate(shell):
                                tposition = 0
                                tmaplist = []
                                if tflag:
                                    for key in tkeys:
                                        tmap = {}
                                        for ii, f in enumerate(face):
                                            for iii, ff in enumerate(f):
                                                if texture[key]['values'][solididx][sidx][i][ii][0] is None:
                                                    break
                                                else:
                                                    tposition = texture[key]['values'][solididx][sidx][i][ii][0]
                                                    tmap[ff] = texture[key]['values'][solididx][sidx][i][ii][iii + 1]
                                        tmaplist.append(tmap)
                                if ((len(face) == 1) and (len(face[0]) == 3)):
                                    re = np.array(face)
                                    b = True
                                else:
                                    re, b = geom_help.triangulate_face(face, vnp, sloppy)
                                if b == True:
                                    for t in re:
                                        tlist4 = []
                                        tlist4.append(t.tolist())
                                        tlist3.append(tlist4)


                                        if sflag:
                                            if geom['semantics']['values'] is None:
                                                slist = None
                                                break
                                            if geom['semantics']['values'][solididx] is None:
                                                slist1 = None
                                                break
                                            elif geom['semantics']['values'][solididx][sidx] is None:
                                                slist2 = None
                                                break
                                            else:
                                                slist2.append(geom['semantics']['values'][solididx][sidx][i])

                                        if mflag:
                                            for j, l in enumerate(mlist2):
                                                if type(l).__name__ == 'list':
                                                    l.append(material[list(material.keys())[j]]['values'][0][0][i])
                                                else:
                                                    continue

                                        if tflag:
                                            for jj in range(len(tmaplist)):
                                                texlist2 = []
                                                texlist3 = [tposition]

                                                if bool(tmaplist[jj]):

                                                    for vindex in t:
                                                        texlist3.append(tmaplist[jj][vindex])
                                                else:
                                                    texlist3[0] = None
                                                texlist2.append(texlist3)
                                                texlist1[jj].append(texlist2)

                            tlist2.append(tlist3)
                            if slist1 is not None:
                                slist1.append(slist2)
                            for j, l in enumerate(mlist1):
                                if type(l).__name__ == 'list' and len(mlist2[j]) != 0:
                                    l.append(mlist2[j])
                                else:
                                    continue
                            for j, l in enumerate(texlist0):
                                l.append(texlist1[j])

                        tlist1.append(tlist2)
                        if slist is not None:
                            slist.append(slist1)
                        for j, l in enumerate(mlist):
                            if type(l).__name__ == 'list' and len(mlist1[j]) != 0:
                                l.append(mlist1[j])
                            else:
                                continue
                        for j,l in enumerate(texlist):
                            l.append(texlist0[j])

                    geom['boundaries'] = tlist1
                    if sflag:
                        geom['semantics']['values'] = slist
                    if mflag:
                        for j, item in enumerate(material.items()):
                            item[1][list(item[1].keys())[0]] = mlist[j]
                        geom['material'] = material
                    if tflag:
                        for j,item in enumerate(texture.items()):
                            item[1][list(item[1].keys())[0]] = texlist[j]
                        geom['texture'] = texture


    def is_triangulated(self):
        """
        Check if the CityJSON file is *fully* triangulated. Return true if it's triangulated, return false if it's not.
        """

        for theid in self.j['CityObjects']:
            if 'geometry' in self.j['CityObjects'][theid]:
                for geom in self.j['CityObjects'][theid]['geometry']:
                    if ((geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface')):
                        for face in geom['boundaries']:
                            for f in face:
                                if len(f) != 3:
                                    return False
                    elif (geom['type'] == 'Solid'):
                        for shell in geom['boundaries']:
                            for face in shell:
                                for f in face:
                                    if len(f) != 3:
                                        return False
                    elif ((geom['type'] == 'MultiSolid') or (geom['type'] == 'CompositeSolid')):
                        for solid in geom['boundaries']:
                            for shell in solid:
                                for face in shell:
                                    for f in face:
                                        if len(f) != 3:
                                            return False
        return True

