
import json

def select_co_bbox(j, bbox):
    #-- select the CO whose
    pass

def select_co_ids(j, IDs):
    IDs = list(IDs)
    re = set()
    for theid in j["CityObjects"]:
        if theid in IDs:
            re.add(theid)
    for theid in IDs:
        if theid not in j["CityObjects"]:
            IDs.remove(theid)
            print ("WARNING: ID", theid, "not found in input file; ignored.")
    #-- deal with CityObjectGroup
    for each in j["CityObjects"]:
        if each in IDs:
            if j["CityObjects"][each]["type"] == "CityObjectGroup" and "members" in j["CityObjects"][each]:
                for member in j["CityObjects"][each]["members"]:
                    re.add(member)
    #-- also add the children
    for id in j["CityObjects"]:
        if id in IDs:
            if "children" in j['CityObjects'][id]:
                for child in j['CityObjects'][id]['children']:
                    re.add(child)
            if "parent" in j['CityObjects'][id]:
                re.add(j['CityObjects'][id]['parent']) 
                #-- add siblings
                if "children" in j['CityObjects'][id]['parent']:
                    for child in j['CityObjects'][id]['parent']:
                        re.add(child)
    return re                



def process_geometry(j, j2):
    #-- update vertex indices
    oldnewids = {}
    newvertices = []    
    for each in j2["CityObjects"]:
        for geom in j2['CityObjects'][each]['geometry']:
            update_array_indices(geom["boundaries"], oldnewids, j["vertices"], newvertices, -1)
    j2["vertices"] = newvertices


def process_templates(j, j2):
    dOldNewIDs = {}
    newones = []
    for each in j2["CityObjects"]:
        for geom in j2['CityObjects'][each]['geometry']:
            if geom["type"] == "GeometryInstance": 
                t = geom["template"] 
                if t in dOldNewIDs:
                    geom["template"] = dOldNewIDs[t]
                else:
                    geom["template"] = len(newones)
                    dOldNewIDs[t] = len(newones)
                    newones.append(j["geometry-templates"]["templates"][t])      
    if len(newones) > 0:
        j2["geometry-templates"] = {}
        j2["geometry-templates"]["vertices-templates"] = j["geometry-templates"]["vertices-templates"]
        j2["geometry-templates"]["templates"] = newones


def process_appearance(j, j2):
    #-- materials
    dOldNewIDs = {}
    newmats = []
    for each in j2["CityObjects"]:
        for geom in j2['CityObjects'][each]['geometry']:
            if "material" in geom:
                for each in geom["material"]:
                    if 'value' in geom["material"][each]:
                        v = geom["material"][each]["value"]
                        if v in dOldNewIDs:
                            geom["material"][each]["value"] = dOldNewIDs[v]
                        else:
                            geom["material"][each]["value"] = len(newmats)
                            dOldNewIDs[v] = len(newmats)
                            newmats.append(j["appearance"]["materials"][v])      
                    if 'values' in geom["material"][each]:
                        update_array_indices(geom["material"][each]['values'], dOldNewIDs, j["appearance"]["materials"], newmats, -1)
    if len(newmats) > 0:
        j2["appearance"]["materials"] = newmats

    #-- textures references (first int in the arrays)
    dOldNewIDs = {}
    newtextures = []
    for each in j2["CityObjects"]:
        for geom in j2['CityObjects'][each]['geometry']:
            if "texture" in geom:
                for each in geom["texture"]:
                    if 'values' in geom["texture"][each]:
                        update_array_indices(geom["texture"][each]['values'], dOldNewIDs, j["appearance"]["textures"], newtextures, 0)
    if len(newtextures) > 0:
        j2["appearance"]["textures"] = newtextures
    #-- textures vertices references (1+ int in the arrays)
    dOldNewIDs = {}
    newtextures = []
    for each in j2["CityObjects"]:
        for geom in j2['CityObjects'][each]['geometry']:
            if "texture" in geom:
                for each in geom["texture"]:
                    if 'values' in geom["texture"][each]:
                        update_array_indices(geom["texture"][each]['values'], dOldNewIDs, j["appearance"]["vertices-texture"], newtextures, 1)
    if len(newtextures) > 0:
        j2["appearance"]["vertices-texture"] = newtextures


def update_array_indices(a, dOldNewIDs, oldarray, newarray, slicearray):
    #-- slicearray: -1=none ; 0=use-only-first (for textures) ; 1=use-1+ (for textures)
    #-- a must be an array
    #-- issue with passing integer is that it's non-mutable, thus can't update
    #-- (or I don't know how...)
    for i, each in enumerate(a):
        if isinstance(each, list):
            update_array_indices(each, dOldNewIDs, oldarray, newarray, slicearray)
        elif each is not None:
            if ( (slicearray == -1) or (slicearray == 0 and i == 0) or (slicearray == 1 and i > 0) ):
                if each in dOldNewIDs:
                    a[i] = dOldNewIDs[each]
                else:
                    a[i] = len(newarray)
                    dOldNewIDs[each] = len(newarray)
                    newarray.append(oldarray[each])      
