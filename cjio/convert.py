from io import BytesIO
import json

from cjio import geom_help

MODULE_NUMPY_AVAILABLE = True
try:
    import numpy as np
except ImportError as e:
    MODULE_NUMPY_AVAILABLE = False

def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


def byte_offset(x, byte_boundary):
    """Compute the byteOffset for glTF bufferView

    The bufferViews need to be aligned to a 4-byte boundary so the accessors can be aligned to them
    """
    remainder = x % byte_boundary
    padding = byte_boundary - remainder if remainder > 0 else 0
    res = x + padding
    return (res, padding)


def to_b3dm(cm, glb):
    """Convert a CityJSON to batched 3d model"""
    # glb is a buffered I/O, as the output of to_gltf()
    assert isinstance(glb, BytesIO)
    b3dm_bin = BytesIO()
    if glb.tell() == 0:
        return b3dm_bin

    #-- Feature table
    # the gltf must have a batchId per CityObject, and this setup expects that there is 1 mesh.primitive per CityObject
    feature_table_header_b = json.dumps({
        'BATCH_LENGTH': len(cm.j['CityObjects'])
    }).encode('utf-8')
    # The JSON header must end on an 8-byte boundary within the containing tile binary. The JSON header must be padded with trailing Space characters (0x20) to satisfy this requirement.
    offset, padding = byte_offset(len(feature_table_header_b), 8)
    for i in range(padding):
        feature_table_header_b += ' '.encode('utf-8')

    #-- Batch table
    attributes = set()
    for coid,co in cm.j['CityObjects'].items():
        try:
            attributes |= set(co['attributes'].keys())
        except KeyError:
            pass
    if len(attributes) > 0:
        batch_table = {attribute: [] for attribute in attributes}
        for coid,co in cm.j['CityObjects'].items():
            for attribute in attributes:
                try:
                    batch_table[attribute].append(co['attributes'][attribute])
                except KeyError:
                    batch_table[attribute].append(None)
    else:
        batch_table = dict()
    # TODO B: write the attributes into the binary body of the the batch table
    batch_table_header_b = json.dumps(batch_table).encode('utf-8')
    offset, padding = byte_offset(len(batch_table_header_b), 8)
    for i in range(padding):
        batch_table_header_b += ' '.encode('utf-8')

    #-- binary glTF
    offset, padding = byte_offset(glb.tell(), 8)
    glb.write(bytearray(padding))

    # the b3dm header is 28-bytes
    byte_length = 28 + len(feature_table_header_b) + len(batch_table_header_b) + glb.tell()
    #-- b3dm Header
    magic = "b3dm"
    version = 1
    feature_table_json_blen = len(feature_table_header_b)
    feature_table_bin_blen = 0
    batch_table_json_blen = len(batch_table_header_b)
    batch_table_bin_blen = 0

    b3dm_bin.write(magic.encode('utf-8'))
    b3dm_bin.write(version.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(byte_length.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(feature_table_json_blen.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(feature_table_bin_blen.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(batch_table_json_blen.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(batch_table_bin_blen.to_bytes(4, byteorder='little', signed=False))
    b3dm_bin.write(feature_table_header_b)
    b3dm_bin.write(batch_table_header_b)
    b3dm_bin.write(glb.getvalue())

    assert b3dm_bin.tell() == byte_length

    return b3dm_bin

def to_glb(j):
    """Convert to Binary glTF (.glb)

    Adapted from CityJSON2glTF: https://github.com/tudelft3d/CityJSON2glTF
    """
    gltf_json = {
        "asset": {},
        "buffers": [],
        "bufferViews": [],
        "accessors": [],
        "materials": [],
        "meshes": [],
        "nodes": [],
        "scenes": []
    }
    gltf_bin = bytearray()
    glb = BytesIO()
    try:
        if len(j['CityObjects']) == 0:
            return glb
    except KeyError as e:
        raise TypeError("Not a CityJSON")

    # asset
    asset = dict()
    asset["copyright"] = "Open data"
    asset["generator"] = "Generated using cjio's glTF exporter"
    asset["version"] = "2.0"
    gltf_json["asset"] = asset

    # index bufferview
    bufferViews = []
    meshes = []
    poscount = 0
    nodes = []
    node_indices = []
    accessors = []
    matid = 0
    material_ids = []

    vertexlist = np.array(j["vertices"])

    for coi,theid in enumerate(j['CityObjects']):
        forimax = []

        if len(j['CityObjects'][theid]['geometry']) != 0:

            comType = j['CityObjects'][theid]['type']
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
            material_ids.append(matid)

            for geom in j['CityObjects'][theid]['geometry']:
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
            bpos = len(gltf_bin)
            offset, padding = byte_offset(bpos, 4)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteLength"] = len(bin_geom)
            bufferView["target"] = 34963 # For 'target' property constants see: https://github.com/KhronosGroup/glTF-Tutorials/blob/master/gltfTutorial/gltfTutorial_005_BuffersBufferViewsAccessors.md#bufferviews
            # write to the buffer
            gltf_bin.extend(bin_geom)
            gltf_bin.extend(bytearray(padding))
            bufferViews.append(bufferView)

            #-- geometry vertices bufferView
            bpos = len(gltf_bin)
            offset, padding = byte_offset(bpos, 4)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteStride"] = 12
            bufferView["byteLength"] = len(bin_vtx)
            bufferView["target"] = 34962
            # write to the buffer
            gltf_bin.extend(bin_vtx)
            gltf_bin.extend(bytearray(padding))
            bufferViews.append(bufferView)

            #-- batchid bufferView
            bpos = len(gltf_bin)
            offset, padding = byte_offset(bpos, 4)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            bufferView["byteStride"] = 4
            bufferView["byteLength"] = len(bin_batchid)
            bufferView["target"] = 34962
            # write to the buffer
            gltf_bin.extend(bin_batchid)
            gltf_bin.extend(bytearray(padding))
            bufferViews.append(bufferView)

            # ----- accessors

            # accessor for geometry indices bufferView
            accessor = dict()
            accessor["bufferView"] = 0 if coi == 0  else coi * 3
            accessor["componentType"] = 5125
            accessor["count"] = int(vtx_idx_np.size)
            accessor["type"] = "SCALAR"
            accessor["max"] = [int(vtx_idx_np.max())]
            accessor["min"] = [int(vtx_idx_np.min())]
            accessors.append(accessor)

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
            accessors.append(accessor)

            # accessor for batchid bufferView
            accessor = dict()
            accessor["bufferView"] = 2 if coi == 0  else coi * 3 + 2
            accessor["componentType"] = 5123
            accessor["count"] = int(vtx_idx_np.size)
            accessor["type"] = "SCALAR"
            accessors.append(accessor)

            # ----- meshes
            # one mesh per CityObject
            mesh = dict()
            mesh["name"] = str(theid)
            mesh["primitives"] = [{
                "indices": len(accessors) - 3,
                "material": matid,
                "attributes": {
                    "_BATCHID": len(accessors) - 1,
                    "POSITION": len(accessors) - 2,
                }
            }]
            meshes.append(mesh)

            # ----- nodes
            # a node has a mesh, and the mesh is referenced by its index in the meshes
            # , "matrix": [1,0,0,0,0,0,-1,0,0,1,0,0,0,0,0,1]}
            nodes.append({"mesh": coi})
            # one node per CityObject
            node_indices.append(coi)

    #-- buffers
    buffer = dict()
    offset, padding = byte_offset(len(gltf_bin), 4)
    gltf_bin.extend(bytearray(padding))
    buffer["byteLength"] = len(gltf_bin)
    gltf_json["buffers"] = [buffer]

    gltf_json["bufferViews"] = bufferViews
    gltf_json["accessors"] = accessors
    gltf_json["meshes"] = meshes
    gltf_json["nodes"] = nodes

    scene = dict()
    scene["nodes"] = node_indices
    gltf_json["scenes"] = [scene]

    #-- materials
    materials = [
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
    gltf_json["materials"] = materials
    
    #-- Chunk 0 (JSON)
    chunk_0 = json.dumps(gltf_json).encode('utf-8')
    offset, padding = byte_offset(len(chunk_0), 4)
    for i in range(padding):
        chunk_0 += ' '.encode('utf-8')
    #-- Binary glTF header
    magic = 'glTF'
    version = 2
    length = 12 + 8 + len(chunk_0) + 8 + len(gltf_bin)

    # header
    glb.write(magic.encode('utf-8'))
    glb.write(version.to_bytes(4, byteorder='little', signed=False))
    glb.write(length.to_bytes(4, byteorder='little', signed=False))
    # chunk 0
    glb.write(len(chunk_0).to_bytes(4, byteorder='little', signed=False))
    glb.write('JSON'.encode('utf-8'))
    glb.write(chunk_0)
    # chunk 1
    glb.write(len(gltf_bin).to_bytes(4, byteorder='little', signed=False))
    glb.write(bytearray.fromhex('42494e00')) # == BIN + 1 empty byte for padding
    glb.write(gltf_bin)
    assert length == glb.tell()

    return glb
