
import os
import json
import jsonschema

#-- ERRORS
 # validate_against_schema
 # parent_children_consistency
 # city_object_groups
 # semantics_array
 # wrong_vertex_index
 # building_parts
 # building_installations
 # building_pi_parent

#-- WARNINGS
 # metadata
 # cityjson_properties
 # citygml_attributes
 # geometry_empty
 # duplicate_vertices
 # orphan_vertices



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


def parent_children_consistency(j):
    isValid = True
    es = ""
    #-- do children have the parent too?
    for id in j["CityObjects"]:
        if "children" in j['CityObjects'][id]:
            for child in j['CityObjects'][id]['children']:
                if (child not in j['CityObjects']):
                    es += "ERROR:   CityObject #" + child + " doesn't exist.\n"
                    es += "\t(CityObject #" + id + " references it as children)\n"   
                    isValid = False
                else:
                    if j['CityObjects'][child]['parent'] != id:    
                        es += "ERROR:   CityObject #" + child + " doesn't reference correct parent.\n"
                        es += "\t(Parent should be CityObject #" + id + ")\n"   
                        isValid = False
    #-- are there orphans?
    for id in j["CityObjects"]:
        if "parent" in j['CityObjects'][id]:
            if (j['CityObjects'][id]['parent'] not in j['CityObjects']):
                    es += "ERROR:   CityObject #" + id + " is an orphan (no parent exists).\n"
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


def semantics_array(j):
    isValid = True
    es = ""
    for id in j["CityObjects"]:
        # print("--", id)
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
                            # print(surfaceid)
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


def citygml_attributes(j, js):
    isValid = True
    ws = ""
    thewarnings = {}
    for id in j["CityObjects"]:
        cotype = j['CityObjects'][id]['type']
        if cotype[0] == "+":
            continue
        tmp = js[str(cotype)]["properties"]["attributes"]["properties"]
        if 'attributes' in j['CityObjects'][id]:
            for a in j['CityObjects'][id]['attributes']:
                if a not in tmp:
                    isValid = False;
                    s = "WARNING: attributes '" + a + "' not in CityGML schema"
                    if s not in thewarnings:
                        thewarnings[s] = [id]
                    else:
                        thewarnings[s].append(id)
        if 'address' in j['CityObjects'][id]:
            tmp = js[str(cotype)]["properties"]["address"]["properties"]                        
            for a in j['CityObjects'][id]['address']:
                if a not in tmp:
                    isValid = False;
                    s = "WARNING: address attributes '" + a + "' not in CityGML schema"
                    if s not in thewarnings:
                        thewarnings[s] = [id]
                    else:
                        thewarnings[s].append(id)                        
    for each in thewarnings:
        ws += each
        if len(thewarnings[each]) < 3:
            ws += " ("
            for coid in thewarnings[each]:
                ws += " #" + coid + " "
            ws += ")\n"
        else:
            ws += " (" + str(len(thewarnings[each])) + " CityObjects have this warning)\n"
    return (isValid, ws)


def geometry_empty(j):
    isValid = True
    ws = ""
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] != 'CityObjectGroup') and (len(j['CityObjects'][id]['geometry']) == 0):
            isValid = False
            ws += "WARNING: " + j['CityObjects'][id]['type'] + " #" + id + " has no geometry.\n"
    return (isValid, ws)


def wrong_vertex_index(j):
    def recusionvisit(a, co, errs):
      for each in a:
        if isinstance(each, list):
            recusionvisit(each, co, errs)
        else:
            if (each >= len(j['vertices'])):
                es = ""
                es += "ERROR:   CityObject #" + co + " has geometry with wrong vertex.\n"
                es += "\t(vertex #" + str(each) + " doesn't exist)\n"   
                errs.append(es)
    errs = []
    for co in j["CityObjects"]:
        for g in j['CityObjects'][co]['geometry']:
            recusionvisit(g["boundaries"], co, errs)    
    es = ""
    if (len(errs) > 0):
        isValid = False
        for each in errs:
            es += each
    else:
        isValid = True
    return (isValid, es)    


def cityjson_properties(j, js):
    isValid = True
    ws = ""
    thewarnings = {}
    for property in j:
        if property not in js["properties"]:
            isValid = False
            ws += "WARNING: root property '" + property + "' not in CityJSON schema, might be ignored by some parsers\n"
    return (isValid, ws)


def duplicate_vertices(j):
    isValid = True
    ws = ""
    thev = set()
    duplicates = set()
    for v in j["vertices"]:
        s = str(v[0]) + " " + str(v[1]) + " " + str(v[2])
        if s in thev:
            duplicates.add(s)
        else:
            thev.add(s)
    if len(duplicates) > 0:
        ws += 'WARNING: there are ' + str(len(duplicates)) + ' duplicate vertices in j["vertices"]\n'
        isValid = False
    if len(duplicates) < 10:
        for v in duplicates:
            ws += '\t(' + v + ')\n'
    return (isValid, ws)


def orphan_vertices(j):
    def recusionvisit(a, ids):
      for each in a:
        if isinstance(each, list):
            recusionvisit(each, ids)
        else:
            ids.add(each)
    isValid = True
    ws = ""
    ids = set()
    for co in j["CityObjects"]:
        for g in j['CityObjects'][co]['geometry']:
            recusionvisit(g["boundaries"], ids)
    noorphans = len(j["vertices"]) - len(ids)
    if noorphans > 0:
        ws += 'WARNING: there are ' + str(noorphans) + ' orphan vertices in j["vertices"]\n'
        isValid = False
    if noorphans > 5:
        all = set()
        for i in range(len(j["vertices"])):
            all.add(i)
        symdiff = all.symmetric_difference(ids)
        ws += '\t['
        for each in symdiff:
            ws += str(each) + ', '
        ws += ']\n'
    return (isValid, ws)


def metadata(j, js):
    isValid = True
    ws = ""
    jtmp = js['properties']['metadata']['properties']
    if 'metadata' in j:
        for each in j['metadata']:
            if each not in jtmp:
                isValid = False
                ws += "WARNING: Metadata '" + each + "' not in CityJSON schema.\n"
    return (isValid, ws)


def validate_against_schema(j, js):
    isValid = True
    #-- load the schema for the cityobjects.json
    # sco_path = os.path.abspath(os.path.dirname(schema))
    # sco_path += '/cityobjects.json'
    # jsco = json.loads(open(sco_path).read())
    #-- validate the file against the schema
    try:
        jsonschema.validate(j, js)
    except jsonschema.ValidationError as e:
        raise Exception(e.message)
        return False
    except jsonschema.SchemaError as e:
        raise Exception(e.message)
        return False
    return isValid