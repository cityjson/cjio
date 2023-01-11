import math
from io import BytesIO
import json

from cjio import geom_help

import numpy as np

from cjio.geom_help import triangle_normal, average_normal


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
    for coi_node_idxd,co in cm.j['CityObjects'].items():
        try:
            attributes |= set(co['attributes'].keys())
        except KeyError:
            pass
    if len(attributes) > 0:
        batch_table = {attribute: [] for attribute in attributes}
        for coi_node_idxd,co in cm.j['CityObjects'].items():
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

def to_glb(cm, do_triangulate=True):
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
        if len(cm.j['CityObjects']) == 0:
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
    child_node_indices = []
    accessors = []
    matid = 0
    material_ids = []

    vertexlist = np.array(cm.j["vertices"])

    # gltf uses a right-handed coordinate system. 
    # glTF defines +Y as up, +Z as forward, and -X as right, thus the front of a glTF 
    # asset faces +Z.
    # The root node of the scene contains the y-up to z-up transformation matrix,
    # which is needed for inherently z-up data. 
    # See https://github.com/CesiumGS/3d-tiles/tree/main/specification#y-up-to-z-up
    nodes.append({
        "matrix": [1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        "children": [],
        "name": cm.j.get("metadata", "citymodel").get("identifier", "citymodel")
    })
    root_node_idx = 0

    # CityObject index with geometry that goes into the glb and is represented by a
    # mesh.
    mesh_idx = 0
    # Since we have an empty root node (without a mesh), but then we have a flat
    # hierarchy (single level) under the root node, each mesh is represented by one
    # (child) node. Technically, we could use 'mesh_idx + 1' in the code below as the
    # child node index, but we use a separate variable for extra clarity.
    child_node_idx = 1

    for theid in cm.j['CityObjects']:
        forimax = []
        normals_per_geom = []

        if "geometry" in cm.j['CityObjects'][theid] and len(cm.j['CityObjects'][theid]['geometry']) != 0:

            comType = cm.j['CityObjects'][theid]['type']
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
            elif (comType == "Bridge" or comType == "BridgePart" or comType == "BridgeInstallation" or comType == "BridgeConstructionElement"):
                matid = 7
            elif (comType == "Tunnel" or comType == "TunnelPart" or comType == "TunnelInstallation"):
                matid = 8
            elif (comType == "GenericCityObject"):
                matid = 9
            material_ids.append(matid)

            #----- computing vertex normals
            # We are computing soft-shading, which means computing the weighted average
            # normal for each vertex.
            # http://wiki.polycount.com/w/images/e/e5/FrostSoft_doc-3.png

            if do_triangulate:
                for geom in cm.j['CityObjects'][theid]['geometry']:
                    normals_per_vertex = {i: [] for i in range(len(vertexlist))}
                    poscount = poscount + 1
                    if geom['type'] == "Solid":
                        triList = []
                        for shell in geom['boundaries']:
                            for face in shell:
                                tri, success = geom_help.triangulate_face(face, vertexlist)
                                if success:
                                    for t in tri:
                                        triList.append(list(t))
                                        tri_normal = triangle_normal(t, vertexlist, weighted=True)
                                        if tri_normal is not None:
                                            # for gltf, we need to invert the vector
                                            tri_normal = tri_normal * -1.0
                                            normals_per_vertex[t[0]].append(tri_normal)
                                            normals_per_vertex[t[1]].append(tri_normal)
                                            normals_per_vertex[t[2]].append(tri_normal)
                                else:
                                    # TODO: logging
                                    print(f"Failed to triangulate face in CityObject {theid}")
                        trigeom = (flatten(triList))

                    elif (geom['type'] == 'MultiSurface') or (geom['type'] == 'CompositeSurface'):
                        triList = []
                        for face in geom['boundaries']:
                            tri, success = geom_help.triangulate_face(face, vertexlist)
                            if success:
                                for t in tri:
                                    triList.append(list(t))
                                    tri_normal = triangle_normal(t, vertexlist, weighted=True)
                                    if tri_normal is not None:
                                        tri_normal = tri_normal * -1.0
                                        normals_per_vertex[t[0]].append(tri_normal)
                                        normals_per_vertex[t[1]].append(tri_normal)
                                        normals_per_vertex[t[2]].append(tri_normal)
                            else:
                                # TODO: logging
                                print(f"Failed to triangulate face in CityObject {theid}")
                        trigeom = (flatten(triList))

                    forimax.append(trigeom)
                    # Computing smooth-shading (smooth-normal) for a vertex, as the sum of
                    # normals weighted by the triangle area of the adjacent triangles.
                    normals_per_vertex_smooth = {i: None for i in
                                                 range(len(vertexlist))}
                    for v, normals in normals_per_vertex.items():
                        normals_per_vertex_smooth[v] = average_normal(normals)
                    del normals_per_vertex
                    normals_per_geom.append(
                        list(normals_per_vertex_smooth[v] for v in trigeom))
            else:
                # If the caller says it's triangulate, then we trust that it's
                # triangulated.
                for geom in cm.j['CityObjects'][theid]['geometry']:
                    normals_per_vertex = {i: [] for i in range(len(vertexlist))}
                    poscount = poscount + 1
                    if geom['type'] == "Solid":
                        triList = []
                        for shell in geom['boundaries']:
                            for face in shell:
                                for t in face:
                                    triList.append(t)
                                    tri_normal = triangle_normal(t, vertexlist, weighted=True)
                                    if tri_normal is not None:
                                        tri_normal = tri_normal * -1.0
                                        normals_per_vertex[t[0]].append(tri_normal)
                                        normals_per_vertex[t[1]].append(tri_normal)
                                        normals_per_vertex[t[2]].append(tri_normal)

                        trigeom = (flatten(triList))

                    elif (geom['type'] == 'MultiSurface') or (
                            geom['type'] == 'CompositeSurface'):
                        triList = []
                        for face in geom['boundaries']:
                            for t in face:
                                triList.append(t)
                                tri_normal = triangle_normal(t, vertexlist, weighted=True)
                                if tri_normal is not None:
                                    tri_normal = tri_normal * -1.0
                                    normals_per_vertex[t[0]].append(tri_normal)
                                    normals_per_vertex[t[1]].append(tri_normal)
                                    normals_per_vertex[t[2]].append(tri_normal)
                        trigeom = (flatten(triList))

                    forimax.append(trigeom)
                    # Computing smooth-shading (smooth-normal) for a vertex, as the sum of
                    # normals weighted by the triangle area of the adjacent triangles.
                    normals_per_vertex_smooth = {i: None for i in
                                                 range(len(vertexlist))}
                    for v, normals in normals_per_vertex.items():
                        normals_per_vertex_smooth[v] = average_normal(normals)
                    del normals_per_vertex
                    normals_per_geom.append(list(normals_per_vertex_smooth[v] for v in trigeom))

            # Flatten the triangle-vertex lists for each CityObject geometry into a
            # single list. Each consecutive set of three vertices defines a
            # single triangle primitive.
            flatgeom = flatten(forimax)
            # Same for the normal-vertex lists
            normals_np = np.concatenate(normals_per_geom)
            if len(normals_np) != len(flatgeom):
                raise RuntimeError("The length of vertices and normals should be equal")
            del normals_per_geom

            #----- buffer and bufferView
            # allocate for vertex coordinates
            vtx_np = np.zeros((len(flatgeom), 3))
            # allocate for vertex indices
            vtx_idx_np = np.zeros(len(flatgeom))
            # need to reindex the vertices, otherwise if the vtx index exceeds the nr. of vertices in the
            # accessor then we get "ACCESSOR_INDEX_OOB" error
            for i,v in enumerate(flatgeom):
                try:
                    vtx_np[i] = np.array(
                        (vertexlist[v][0], vertexlist[v][1], vertexlist[v][2]))
                except IndexError as e:
                    print(i, v)
                vtx_idx_np[i] = i
            bin_vtx = vtx_np.astype(np.float32).tostring()
            # convert geometry indices to binary
            bin_geom = vtx_idx_np.astype(np.uint32).tostring()
            del flatgeom
            # convert the normal to binary
            bin_normals = normals_np.astype(np.float32).tostring()
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

            #-- geometry vertices (POSITION) bufferView
            bpos = len(gltf_bin)
            offset, padding = byte_offset(bpos, 4)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            # bufferView["byteStride"] = 12
            bufferView["byteLength"] = len(bin_vtx)
            bufferView["target"] = 34962
            # write to the buffer
            gltf_bin.extend(bin_vtx)
            gltf_bin.extend(bytearray(padding))
            bufferViews.append(bufferView)

            #-- vertex normals (NORMAL) bufferView
            bpos = len(gltf_bin)
            offset, padding = byte_offset(bpos, 4)
            bufferView = dict()
            bufferView["buffer"] = 0
            bufferView["byteOffset"] = offset
            # bufferView["byteStride"] = 12
            bufferView["byteLength"] = len(bin_normals)
            bufferView["target"] = 34962
            # write to the buffer
            gltf_bin.extend(bin_normals)
            gltf_bin.extend(bytearray(padding))
            bufferViews.append(bufferView)

            # #-- batchid bufferView
            # bpos = len(gltf_bin)
            # offset, padding = byte_offset(bpos, 4)
            # bufferView = dict()
            # bufferView["buffer"] = 0
            # bufferView["byteOffset"] = offset
            # bufferView["byteStride"] = 4
            # bufferView["byteLength"] = len(bin_batchid)
            # bufferView["target"] = 34962
            # # write to the buffer
            # gltf_bin.extend(bin_batchid)
            # gltf_bin.extend(bytearray(padding))
            # bufferViews.append(bufferView)

            # ----- accessors

            # accessor for geometry indices bufferView
            accessor = dict()
            # We start the bufferViews with i==1, because the root node does not have
            # a bufferView, because it is empty (does not have a mesh)
            # Without a root node we would need  = 0 if coi_node_idx == 0  else coi_node_idx * 3
            accessor["bufferView"] = mesh_idx * 3
            accessor["componentType"] = 5125
            accessor["count"] = len(vtx_idx_np)
            accessor["type"] = "SCALAR"
            accessor["max"] = [int(vtx_idx_np.max())]
            accessor["min"] = [int(vtx_idx_np.min())]
            accessors.append(accessor)

            # accessor for geometry vertices (POSITION) bufferView
            accessor = dict()
            # without an empty root node we would need = 1 if coi_node_idx == 0  else coi_node_idx * 3 + 1
            accessor["bufferView"] = mesh_idx * 3 + 1
            accessor["componentType"] = 5126
            accessor["count"] = len(vtx_np)
            accessor["type"] = "VEC3"
            accessor["max"] = [float(np.amax(vtx_np, axis=0)[0]),
                               float(np.amax(vtx_np, axis=0)[1]),
                               float(np.amax(vtx_np, axis=0)[2])]
            accessor["min"] = [float(np.amin(vtx_np, axis=0)[0]),
                               float(np.amin(vtx_np, axis=0)[1]),
                               float(np.amin(vtx_np, axis=0)[2])]
            accessors.append(accessor)

            # accessor for vertex normals (NORMAL) bufferView
            accessor = dict()
            accessor["bufferView"] = mesh_idx * 3 + 2
            accessor["componentType"] = 5126
            accessor["count"] = len(normals_np)
            accessor["type"] = "VEC3"
            accessor["max"] = [float(np.amax(normals_np, axis=0)[0]),
                               float(np.amax(normals_np, axis=0)[1]),
                               float(np.amax(normals_np, axis=0)[2])]
            accessor["min"] = [float(np.amin(normals_np, axis=0)[0]),
                               float(np.amin(normals_np, axis=0)[1]),
                               float(np.amin(normals_np, axis=0)[2])]
            accessors.append(accessor)

            # # accessor for batchid bufferView
            # accessor = dict()
            # # without an empty root node we would need = 2 if coi_node_idx == 0  else coi_node_idx * 3 + 2
            # accessor["bufferView"] = mesh_idx * 3 + 3
            # accessor["componentType"] = 5123
            # accessor["count"] = len(batchid_np)
            # accessor["type"] = "SCALAR"
            # accessors.append(accessor)

            # ----- meshes
            # one mesh per CityObject
            mesh = dict()
            mesh["name"] = str(theid)
            mesh["primitives"] = [{
                "indices": len(accessors) - 3,
                "material": matid,
                "attributes": {
                    # "_BATCHID": len(accessors) - 1,
                    "NORMAL": len(accessors) - 1,
                    "POSITION": len(accessors) - 2,
                }
            }]
            meshes.append(mesh)

            # ----- nodes
            # a node has a mesh, and the mesh is referenced by its index in the meshes
            nodes.append({"mesh": mesh_idx})
            # one node per CityObject
            child_node_indices.append(child_node_idx)

            mesh_idx += 1
            child_node_idx += 1

    #-- buffers
    buffer = dict()
    offset, padding = byte_offset(len(gltf_bin), 4)
    gltf_bin.extend(bytearray(padding))
    buffer["byteLength"] = len(gltf_bin)
    gltf_json["buffers"] = [buffer]

    gltf_json["bufferViews"] = bufferViews
    gltf_json["accessors"] = accessors
    gltf_json["meshes"] = meshes

    nodes[root_node_idx]["children"] = child_node_indices
    gltf_json["nodes"] = nodes

    scene = dict()
    scene["nodes"] = [root_node_idx,]
    gltf_json["scenes"] = [scene]

    #-- materials
    materials = [
        {  # building red
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.7200, 0.320, 0.220, 1.0],
                "metallicFactor": 0.0,
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
