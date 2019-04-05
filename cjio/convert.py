import numpy as np

from cjio import geom_help


def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def to_gltf(cj):
    """Main function from CityJSON2glTF"""
    cm = {
        "asset": {},
        "buffers": [],
        "bufferViews": [],
        "accessors": [],
        "materials": [],
        "meshes": [],
        "nodes": [],
        "scenes": []
    }
    lbin = bytearray()
    try:
        if len(cj['CityObjects']) == 0:
            return (cm, lbin)
    except KeyError as e:
        raise TypeError("Not a CityJSON")

    # asset
    asset = dict()
    asset["copyright"] = "Open data"
    asset["generator"] = "Generated using cjio's glTF exporter"
    asset["version"] = "2.0"
    cm["asset"] = asset

    # index bufferview
    bufferViewList = []
    meshList = []

    poscount = 0
    indexcount = 0
    nodeList = []
    nodeCount = []
    accessorsList = []
    matid = 0
    materialIDs = []

    vertexlist = np.array(cj["vertices"])

    for theid in cj['CityObjects']:
        forimax = []
        forimax2 = []

        if len(cj['CityObjects'][theid]['geometry']) != 0:

            comType = cj['CityObjects'][theid]['type']
            if (comType == "Building" or comType == "BuildingPart" or comType == "BuildingInstallation"):
                matid = 0
            elif (comType == "TINRelief"):
                matid = 1
            elif (comType == "Road" or comType == "Railway" or comType == "TransportSquare"):
                matid = 2
            elif (comType == "WaterBody"):
                matid = 3
            elif (comType == "PlantCover" or comType == "SolitaryVegetationObject"):
                matid = 4
            elif (comType == "LandUse"):
                matid = 5
            elif (comType == "CityFurniture"):
                matid = 6
            elif (
                    comType == "Bridge" or comType == "BridgePart" or comType == "BridgeInstallation" or comType == "BridgeConstructionElement"):
                matid = 7
            elif (comType == "Tunnel" or comType == "TunnelPart" or comType == "TunnelInstallation"):
                matid = 8
            elif (comType == "GenericCityObject"):
                matid = 9
            materialIDs.append(matid)

            for geom in cj['CityObjects'][theid]['geometry']:
                #                print (geom)
                poscount = poscount + 1
                if geom['type'] == "Solid":
                    #                    print (geom['type'])
                    triList = []
                    for shell in geom['boundaries']:
                        for face in shell:
                            tri = geom_help.triangulate_face(face, vertexlist)
                            for t in tri:
                                #                                print ("hi", type(t[0]))
                                triList.append(list(t))
                    trigeom = (flatten(triList))
                #                print (trigeom)

                elif (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface'):
                    #                    print (geom['type'])
                    triList = []
                    for face in geom['boundaries']:
                        #                        print (face)
                        tri = geom_help.triangulate_face(face, vertexlist)
                        for t in tri:
                            #                            print ("hi", type(t[0]))
                            triList.append(t)
                    trigeom = (flatten(triList))

                #                print (trigeom)
                flatgeom = trigeom
                forimax.append(flatgeom)
            #                print (forimax)

            flatgeom_np = np.array(flatten(forimax))
            #            print (flatgeom_np)
            bin_geom = flatgeom_np.astype(np.uint32).tostring()

            lbin.extend(bin_geom)

            #           forimax2.append(flatgeom)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteLength"] = len(bin_geom)
            bufferView["byteOffset"] = len(lbin) - len(bin_geom)
            bufferView["target"] = 34963
            bufferViewList.append(bufferView)

            # meshes
            mesh = dict()
            mesh["name"] = str(theid)
            mesh["primitives"] = [{"indices": indexcount, "material": matid}]
            meshList.append(mesh)

            node = {}
            node["mesh"] = indexcount
            node["name"] = str(theid)
            nodeList.append(node)

            nodeCount.append(indexcount)

            accessor = dict()
            accessor["bufferView"] = indexcount
            accessor["byteOffset"] = 0
            accessor["componentType"] = 5125
            accessor["count"] = len(flatten(forimax))
            accessor["type"] = "SCALAR"
            accessor["max"] = [int(max(flatten(forimax)))]
            accessor["min"] = [int(min(flatten(forimax)))]
            accessorsList.append(accessor)

            indexcount = indexcount + 1

    # scene
    scene = dict()
    scene["nodes"] = nodeCount

    ibin_length = len(lbin)

    # vertex bufferview
    vertex_bin = vertexlist.astype(np.float32).tostring()
    lbin.extend(vertex_bin)
    vertexBuffer = {
        "buffer": 0,
        "byteOffset": ibin_length,
        "byteLength": len(vertex_bin),
        "target": 34962
    }
    bufferViewList.append(vertexBuffer)
    cm["bufferViews"] = bufferViewList

    for m in meshList:
        m["primitives"][0]["attributes"] = {"POSITION": poscount}
    cm["meshes"] = meshList
    cm["nodes"] = nodeList
    cm["scenes"] = [scene]

    # accessors
    accessorsList.append({
        "bufferView": len(bufferViewList) - 1,
        "byteOffset": 0,
        "componentType": 5126,
        "count": len(cj["vertices"]),
        "type": "VEC3",
        "max": [float(np.amax(np.asarray(cj["vertices"]), axis=0)[0]),
                float(np.amax(np.asarray(cj["vertices"]), axis=0)[1]),
                float(np.amax(np.asarray(cj["vertices"]), axis=0)[2])],  # max(cj["vertices"]),
        "min": [float(np.amin(np.asarray(cj["vertices"]), axis=0)[0]),
                float(np.amin(np.asarray(cj["vertices"]), axis=0)[1]),
                float(np.amin(np.asarray(cj["vertices"]), axis=0)[2])]  # min(cj["vertices"])
    })
    cm["accessors"] = accessorsList

    # buffers
    buffer = dict()
    # buffer["uri"] = bufferbin
    buffer["byteLength"] = len(lbin)
    cm["buffers"] = [buffer]

    # materials
    materialsList = [
        {  # building red
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.000, 0.000, 0.000, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # terrain brown
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.588, 0.403, 0.211, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # transport grey
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.631, 0.607, 0.592, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # waterbody blue
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.070, 0.949, 0.972, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # vegetation green
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.000, 1.000, 0.000, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # landuse yellow
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.909, 0.945, 0.196, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # CityFurniture orange
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.894, 0.494, 0.145, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # bridge purple
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.466, 0.094, 0.905, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # tunnel black
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.011, 0.011, 0.007, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        },
        {  # GenericCityObject pink
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.909, 0.188, 0.827, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 1.0
            }
        }
    ]

    cm["materials"] = materialsList

    return (cm, lbin)
