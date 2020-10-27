
import os
import json
import jsonschema
import jsonref

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
    es = []
    for id in j["CityObjects"]:
        if j['CityObjects'][id]['type'] == 'CityObjectGroup':
            for each in j['CityObjects'][id]['members']:
                if each in j['CityObjects']:
                    pass
                else:
                    s = "ERROR:   CityObjectGroup (#" + id + ") contains member #" + each + ", but it doesn't exist." 
                    es.append(s)
                    isValid = False
    return (isValid, es)


def parent_children_consistency(j):
    isValid = True
    es = []
    #-- do children have the parent too?
    for theid in j["CityObjects"]:
        if "children" in j['CityObjects'][theid]:
            for child in j['CityObjects'][theid]['children']:
                if (child not in j['CityObjects']):
                    s = "ERROR:   CityObject #" + child + " doesn't exist."
                    es.append(s)
                    s = "\t(CityObject #" + theid + " references it as children)"   
                    es.append(s)
                    isValid = False
                else:
                    if theid not in j['CityObjects'][child]['parents']:    
                        s = "ERROR:   CityObject #" + child + " doesn't reference correct parent."
                        es.append(s)
                        s = "\t(Parent should be CityObject #" + theid + ")"   
                        es.append(s)
                        isValid = False
    #-- are there orphans?
    for theid in j["CityObjects"]:
        if "parents" in j['CityObjects'][theid]:
            for parent in j['CityObjects'][theid]['parents']:
                if (parent not in j['CityObjects']):
                    s = "ERROR:   CityObject #" + theid + " is an orphan (parent #" + parent + " doesn't exist)."
                    es.append(s)
                    isValid = False
    return (isValid, es)


def building_parts(j):
    isValid = True
    es = []
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] == 'Building') and ('Parts' in j['CityObjects'][id]):
            for each in j['CityObjects'][id]['Parts']:
                if (each in j['CityObjects']) and (j['CityObjects'][each]['type'] == 'BuildingPart'):
                    pass
                else:
                    s = "ERROR:   BuildingPart #" + each + " doesn't exist."
                    es.append(s)
                    s = "\t(Building #" + id + " references it)"   
                    es.append(s)
                    isValid = False
    return (isValid, es)


def building_installations(j):
    isValid = True
    es = []
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] == 'Building') and ('Installations' in j['CityObjects'][id]):
            for each in j['CityObjects'][id]['Installations']:
                if (each in j['CityObjects']) and (j['CityObjects'][each]['type'] == 'BuildingInstallation'):
                    pass
                else:
                    s = "ERROR:   BuildingInstallation #" + each + " doesn't exist."
                    es.append(s)
                    s = "\t(Building #" + id + " references it)"
                    es.append(s)
                    isValid = False
    return (isValid, es)


def building_pi_parent(j):
    isValid = True
    es = []
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
        s = "ERROR:   BuildingParts and/or BuildingInstallations don't have a parent:"
        es.append(s)
        for each in pis:
            s = "\t#" + each
            es.append(s)
    return (isValid, es)


def semantics_array(j):
    isValid = True
    es = []
    for id in j["CityObjects"]:
        # print("--", id)
        geomid = 0
        for g in j['CityObjects'][id]['geometry']:
            if 'semantics' not in g:
                continue
            else:
                sem = g['semantics']
                # TODO: CompositeSolid
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
                                if ( (type(i) is not int) or (i > (len(sem['surfaces']) - 1)) ):
                                    s = "ERROR:   semantics arrays problems ( #" + id
                                    es.append(s)
                                    s = "; geom=" + str(geomid) + ",shell=" + str(shellid) + ",surface=" + str(surfaceid) + " )"
                                    es.append(s)
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
                            if ( (type(i) is not int) or (i > (len(sem['surfaces']) - 1)) ):
                                s = "ERROR:   semantics arrays problems ( #" + id
                                es.append(s)
                                s = "; geom=" + str(geomid) + ",surface=" + str(surfaceid) + " )"
                                es.append(s)
                                isValid = False;
                                break
                        surfaceid += 1
            geomid += 1            
    return (isValid, es)


def get_list_attributes_from_schema(n, ls):
    if ( (type(n) is dict) or (type(n) is jsonref.JsonRef) ):
        if "attributes" in n:
            for each in n["attributes"]["properties"]:
                ls.append(each)
        for p in n:
            if ( (type(n[p]) is list) or (type(n[p]) is dict) ):
                get_list_attributes_from_schema(n[p], ls)
    elif (type(n) is list):
        for each in n:
            if ( (type(each) is dict) or (type(each) is jsonref.JsonRef) or (type(each) is list) ):
                get_list_attributes_from_schema(each, ls)


    # if 'address' in j['CityObjects'][id]:
    #     tmp = js[str(cotype)]["properties"]["address"]["properties"]                        
    #     for a in j['CityObjects'][id]['address']:
    #         if a not in tmp:
    #             isValid = False;
    #             s = "WARNING: address attributes '" + a + "' not in CityGML schema"
    #             if s not in thewarnings:
    #                 thewarnings[s] = [id]
    #             else:
    #                 thewarnings[s].append(id)                        

def citygml_attributes(j, js):
    isValid = True
    thewarnings = {}
    for id in j["CityObjects"]:
        cotype = j['CityObjects'][id]['type']
        if cotype[0] == "+":
            continue
            # TODO : implement for attributes of Extensions?
        ls = []
        get_list_attributes_from_schema(js[cotype], ls)
        if 'attributes' in j['CityObjects'][id]:
            for a in j['CityObjects'][id]['attributes']:
                if ( (a[0] != "+") and (a not in ls) ):
                    isValid = False;
                    s = "WARNING: attributes '" + a + "' not in CityGML schema"
                    if s not in thewarnings:
                        thewarnings[s] = [id]
                    else:
                        thewarnings[s].append(id)
    ws = []
    for each in thewarnings:
        ws.append(each)
        s = ""
        if len(thewarnings[each]) < 3:
            s += "\t("
            for coid in thewarnings[each]:
                s += " #" + coid + " "
            s += ")"
        else:
            s += "\t(" + str(len(thewarnings[each])) + " CityObjects have this warning)"
        ws.append(s)
    return (isValid, ws)


def geometry_empty(j):
    isValid = True
    ws = []
    for id in j["CityObjects"]:
        if (j['CityObjects'][id]['type'] != 'CityObjectGroup') and (len(j['CityObjects'][id]['geometry']) == 0):
            isValid = False
            s = "WARNING: " + j['CityObjects'][id]['type'] + " #" + id + " has no geometry."
            ws.append(s)
    return (isValid, ws)


def wrong_vertex_index(j):
    def recusionvisit(a, co, errs):
      for each in a:
        if isinstance(each, list):
            recusionvisit(each, co, errs)
        else:
            if (each >= len(j['vertices'])):
                es = []
                s = "ERROR:   CityObject #" + co + " has geometry with wrong vertex."
                es.append(s)
                s = "\t(vertex #" + str(each) + " doesn't exist)"   
                es.append(s)
                errs.append(es)
    errs = []
    for co in j["CityObjects"]:
        for g in j['CityObjects'][co]['geometry']:
            recusionvisit(g["boundaries"], co, errs)    
    es = []
    if (len(errs) > 0):
        isValid = False
        es += errs
    else:
        isValid = True
    return (isValid, es)    


def cityjson_properties(j, js):
    isValid = True
    ws = []
    thewarnings = {}
    for property in j:
        if ( ((property[0] != "+") and (property[0] != "@")) and (property not in js["properties"]) ):
            isValid = False
            s = "WARNING: root property '" + property + "' not in CityJSON schema, might be ignored by some parsers"
            ws.append(s)
    return (isValid, ws)


def duplicate_vertices(j):
    isValid = True
    ws = []
    thev = set()
    duplicates = set()
    for v in j["vertices"]:
        s = str(v[0]) + " " + str(v[1]) + " " + str(v[2])
        if s in thev:
            duplicates.add(s)
        else:
            thev.add(s)
    if len(duplicates) > 0:
        s = 'WARNING: there are ' + str(len(duplicates)) + ' duplicate vertices in j["vertices"]'
        ws.append(s)
        isValid = False
    if len(duplicates) < 10:
        for v in duplicates:
            s = '\t(' + v + ')'
            ws.append(s)
    return (isValid, ws)


def orphan_vertices(j):
    def recusionvisit(a, ids):
      for each in a:
        if isinstance(each, list):
            recusionvisit(each, ids)
        else:
            ids.add(each)
    isValid = True
    ws = []
    ids = set()
    for co in j["CityObjects"]:
        for g in j['CityObjects'][co]['geometry']:
            recusionvisit(g["boundaries"], ids)
    noorphans = len(j["vertices"]) - len(ids)
    if noorphans > 0:
        s = 'WARNING: there are ' + str(noorphans) + ' orphan vertices in j["vertices"]'
        ws.append(s)
        isValid = False
    if noorphans > 5:
        all = set()
        for i in range(len(j["vertices"])):
            all.add(i)
        symdiff = all.symmetric_difference(ids)
        s = '\t['
        for each in symdiff:
            s += str(each) + ', '
        s += ']'
        ws.append(s)
    return (isValid, ws)


def validate_against_schema(j, js):
    isValid = True
    es = []
    #-- lazy validation to catch as many as possible
    myvalidator = jsonschema.Draft7Validator(js, format_checker=jsonschema.FormatChecker())
    for err in sorted(myvalidator.iter_errors(j), key=str):
        isValid = False
        es.append(err.message)
    return (isValid, es)

    # try:
    #     jsonschema.Draft4Validator(js, format_checker=jsonschema.FormatChecker()).validate(j)
    # except jsonschema.ValidationError as e:
    #     raise Exception(e.message)
    #     return False
    # except jsonschema.SchemaError as e:
    #     raise Exception(e.message)
    #     return False
    
    # try:
    #     jsonschema.validate(j, js, format_checker=jsonschema.FormatChecker())
    # except jsonschema.ValidationError as e:
    #     raise Exception(e.message)
    #     return False
    # except jsonschema.SchemaError as e:
    #     raise Exception(e.message)
    #     return False