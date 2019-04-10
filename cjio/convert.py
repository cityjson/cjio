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


def byte_offset(x):
    """Compute the byteOffset for glTF bufferView

    The bufferViews need to be aligned to a 4-byte boundary so the accessors can be aligned to them
    """
    remainder = x % 4
    padding = 4 - remainder if remainder > 0 else 0
    res = x + padding
    return (res, padding)


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
    nodeList = []
    nodes = []
    accessorsList = []
    matid = 0
    materialIDs = []

    vertexlist = np.array(cj["vertices"])

    for coi,theid in enumerate(cj['CityObjects']):
        forimax = []

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
                poscount = poscount + 1
                if geom['type'] == "Solid":
                    triList = []
                    for shell in geom['boundaries']:
                        for face in shell:
                            tri = geom_help.triangulate_face(face, vertexlist)
                            for t in tri:
                                triList.append(list(t))
                    trigeom = (flatten(triList))

                elif (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface'):
                    triList = []
                    for face in geom['boundaries']:
                        tri = geom_help.triangulate_face(face, vertexlist)
                        for t in tri:
                            triList.append(t)
                    trigeom = (flatten(triList))
                flatgeom = trigeom
                forimax.append(flatgeom)

            #----- buffer and bufferView
            flatgeom = flatten(forimax)
            vtx_np = np.zeros((len(flatgeom), 3))
            vtx_idx_np = np.zeros(len(flatgeom))
            # need to reindex the vertices, otherwise if the vtx index exceeds the nr. of vertices in the
            # accessor then we get "ACCESSOR_INDEX_OOB" error
            for i,v in enumerate(flatgeom):
                vtx_np[i] = vertexlist[v]
                vtx_idx_np[i] = i
            bin_vtx = vtx_np.astype(np.float32).tostring()
            # convert geometry indices to binary
            bin_geom = vtx_idx_np.astype(np.uint32).tostring()
            # convert batchid to binary
            batchid_np = np.array([i for g in vtx_idx_np])
            bin_batchid = batchid_np.astype(np.uint32).tostring()

            #-- geometry indices bufferView
            bpos = len(lbin)
            offset, padding = byte_offset(bpos)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteLength"] = len(bin_geom)
            bufferView["target"] = 34963 # For 'target' property constants see: https://github.com/KhronosGroup/glTF-Tutorials/blob/master/gltfTutorial/gltfTutorial_005_BuffersBufferViewsAccessors.md#bufferviews
            # write to the buffer
            lbin.extend(bin_geom)
            lbin.extend(bytearray(padding))
            bufferViewList.append(bufferView)

            #-- geometry vertices bufferView
            bpos = len(lbin)
            offset, padding = byte_offset(bpos)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteStride"] = 12
            bufferView["byteLength"] = len(bin_vtx)
            bufferView["target"] = 34962
            # write to the buffer
            lbin.extend(bin_vtx)
            lbin.extend(bytearray(padding))
            bufferViewList.append(bufferView)

            #-- batchid bufferView
            bpos = len(lbin)
            offset, padding = byte_offset(bpos)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteStride"] = 4
            bufferView["byteLength"] = len(bin_batchid)
            bufferView["target"] = 34962
            # write to the buffer
            lbin.extend(bin_batchid)
            lbin.extend(bytearray(padding))
            bufferViewList.append(bufferView)

            # ----- accessors

            # accessor for geometry indices bufferView
            accessor = dict()
            accessor["bufferView"] = 0 if coi == 0  else coi * 3
            accessor["componentType"] = 5125
            accessor["count"] = int(vtx_idx_np.size)
            accessor["type"] = "SCALAR"
            accessor["max"] = [int(vtx_idx_np.max())]
            accessor["min"] = [int(vtx_idx_np.min())]
            accessorsList.append(accessor)

            # accessor for geometry vertices bufferView
            accessor = dict()
            accessor["bufferView"] = 1 if coi == 0  else coi * 3 + 1
            accessor["componentType"] = 5126
            accessor["count"] = int(vtx_idx_np.size)
            accessor["type"] = "VEC3"
            accessor["max"] = [float(np.amax(vtx_np, axis=0)[0]),
                               float(np.amax(vtx_np, axis=0)[1]),
                               float(np.amax(vtx_np, axis=0)[2])]
            accessor["min"] = [float(np.amin(vtx_np, axis=0)[0]),
                               float(np.amin(vtx_np, axis=0)[1]),
                               float(np.amin(vtx_np, axis=0)[2])]
            accessorsList.append(accessor)

            # accessor for batchid bufferView
            accessor = dict()
            accessor["bufferView"] = 2 if coi == 0  else coi * 3 + 2
            accessor["componentType"] = 5123
            accessor["count"] = int(vtx_idx_np.size)
            accessor["type"] = "SCALAR"
            accessorsList.append(accessor)

            # ----- meshes
            # one mesh per CityObject
            mesh = dict()
            mesh["name"] = str(theid)
            mesh["primitives"] = [{
                "indices": len(accessorsList) - 3,
                "material": matid,
                "attributes": {
                    "_BATCHID": len(accessorsList) - 1,
                    "POSITION": len(accessorsList) - 2,
                }
            }]
            meshList.append(mesh)

            # ----- nodes
            # a node has a mesh, and the mesh is referenced by its index in the meshList
            nodeList.append({"mesh": coi})
            # one node per CityObject
            nodes.append(coi)

    #-- buffers
    buffer = dict()
    buffer["byteLength"] = len(lbin)
    cm["buffers"] = [buffer]

    cm["bufferViews"] = bufferViewList
    cm["accessors"] = accessorsList
    cm["meshes"] = meshList
    cm["nodes"] = nodeList

    scene = dict()
    scene["nodes"] = nodes
    cm["scenes"] = [scene]

    #-- materials
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
