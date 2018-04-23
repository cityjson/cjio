
import os
import json
import jsonschema
import jsonref
import urllib
from pkg_resources import resource_filename


def dict_raise_on_duplicates(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           raise ValueError("Invalid CityJSON file, duplicate key for City Object IDs: %r" % (k))
        else:
           d[k] = v
    return d


def city_object_groups(j):
    isValid = True
    es = ""
    for id in j["CityObjects"]:
        if j['CityObjects'][id]['type'] == 'CityObjectGroup':
            for each in j['CityObjects'][id]['members']:
                if each in j['CityObjects']:
                    pass
                else:
                    es += "ERROR:   CityObjectGroup (#" + id + ") contains member #" + each + ", but it doesn't exist.\n" 
                    isValid = False
    return (isValid, es)

def building_parts(j):
    isValid = True
    es = ""
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] == 'Building') and ('Parts' in j['CityObjects'][id]):
            for each in j['CityObjects'][id]['Parts']:
                if (each in j['CityObjects']) and (j['CityObjects'][each]['type'] == 'BuildingPart'):
                    pass
                else:
                    es += "ERROR:   BuildingPart #" + each + " doesn't exist.\n"
                    es += "\t(Building #" + id + " references it)\n"   
                    isValid = False
    return (isValid, es)

def building_installations(j):
    isValid = True
    es = ""
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] == 'Building') and ('Installations' in j['CityObjects'][id]):
            for each in j['CityObjects'][id]['Installations']:
                if (each in j['CityObjects']) and (j['CityObjects'][each]['type'] == 'BuildingInstallation'):
                    pass
                else:
                    es += "ERROR:   BuildingInstallation #" + each + " doesn't exist.\n"
                    es += "\t(Building #" + id + " references it)\n"
                    isValid = False
    return (isValid, es)


def building_pi_parent(j):
    isValid = True
    es = ""
    pis = set()
    for id in j["CityObjects"]:
        if j['CityObjects'][id]['type'] == 'BuildingPart' or j['CityObjects'][id]['type'] == 'BuildingInstallation':
            pis.add(id)
    for id in j["CityObjects"]:
        if j['CityObjects'][id]['type'] == 'Building':
            if 'Parts' in j['CityObjects'][id]:
                for pid in j['CityObjects'][id]['Parts']:
                    if pid in pis:
                        pis.remove(pid)
        if j['CityObjects'][id]['type'] == 'Building':
            if 'Installations' in j['CityObjects'][id]:
                for pid in j['CityObjects'][id]['Installations']:
                    if pid in pis:
                        pis.remove(pid)
    if len(pis) > 0:
        isValid = False
        es += "ERROR:   BuildingParts and/or BuildingInstallations don't have a parent:\n"
        for each in pis:
            es += "\t#" + each + "\n"
    return (isValid, es)

def semantics(j):
    isValid = True
    es = ""
    for id in j["CityObjects"]:
        geomid = 0
        for g in j['CityObjects'][id]['geometry']:
            if 'semantics' not in g:
                continue
            else:
                sem = g['semantics']
                if g['type'] == 'Solid':
                    shellid = 0
                    for shell in g["boundaries"]:
                        surfaceid = 0
                        for surface in shell:
                            i = None
                            if sem['values'] is not None:
                                if sem['values'][shellid] is not None:
                                    i = sem['values'][shellid][surfaceid]
                            if i is not None:
                                if i > (len(sem['surfaces']) - 1):
                                    es += "ERROR:   semantics arrays problems ( #" + id
                                    es += "; geom=" + str(geomid) + ",shell=" + str(shellid) + ",surface=" + str(surfaceid) + " )\n"
                                    isValid = False;
                                    break

                            surfaceid += 1
                        shellid += 1
                if g['type'] == 'MultiSurface' or g['type'] == 'CompositeSurface':
                    surfaceid = 0
                    for surface in g["boundaries"]:
                        i = None
                        if sem['values'] is not None:
                            if sem['values'][surfaceid] is not None:
                                i = sem['values'][surfaceid]
                        if i is not None:
                            if i > (len(sem['surfaces']) - 1):
                                es += "ERROR:   semantics arrays problems ( #" + id
                                es += "; geom=" + str(geomid) + ",surface=" + str(surfaceid) + " )\n"
                                isValid = False;
                                break
                        surfaceid += 1
            geomid += 1            
    return (isValid, es)

def validate_schema(j):
    isValid = True
    #-- fetch proper schema
    if j["version"] == "0.6":
        schema = resource_filename(__name__, '/schemas/v06/cityjson.json')
    elif j["version"] == "0.5":
        schema = resource_filename(__name__, '/schemas/cityjson-v05.schema.json')
    else:
        return False
    #-- open the schema
    fins = open(schema)
    jtmp = json.loads(fins.read())
    fins.seek(0)
    if "$id" in jtmp:
        u = urllib.urlparse(jtmp['$id'])
        os.path.dirname(u.path)
        base_uri = u.scheme + "://" + u.netloc + os.path.dirname(u.path) + "/" 
    else:
        abs_path = os.path.abspath(os.path.dirname(schema))
        base_uri = 'file://{}/'.format(abs_path)
    js = jsonref.loads(fins.read(), jsonschema=True, base_uri=base_uri)
    #-- load the schema for the cityobjects.json
    sco_path = os.path.abspath(os.path.dirname(schema))
    sco_path += '/cityobjects.json'
    jsco = json.loads(open(sco_path).read())
    #-- validate the file against the schema
    try:
        jsonschema.validate(j, js)
    except jsonschema.ValidationError as e:
        # print ("ERROR:   ", e.message)
        raise Exception(e.message)
        return False
    except jsonschema.SchemaError as e:
        # print ("ERROR:   ", e)
        raise Exception(e.message)
        return False
    return isValid