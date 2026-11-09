import copy
import json
import struct

import numpy as np
import pytest

from cjio import cityjson


def read_mesh(glb):
    data = glb.getvalue()
    json_size = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + json_size])
    binary = data[28 + json_size :]
    attributes = document["meshes"][0]["primitives"][0]["attributes"]

    def vectors(attribute):
        accessor = document["accessors"][attributes[attribute]]
        view = document["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        return np.frombuffer(
            binary, dtype="<f4", count=3 * accessor["count"], offset=offset
        ).reshape(-1, 3)

    matrix = np.array(document["nodes"][0]["matrix"]).reshape((4, 4), order="F")
    return vectors("POSITION"), vectors("NORMAL"), matrix


def triangle_model():
    vertices = [[0, 0, 0], [3, 0, 0], [0, 2, 1]]
    return {
        "type": "CityJSON",
        "version": "2.0",
        "CityObjects": {
            "house": {
                "type": "Building",
                "geometry": [
                    {"type": "MultiSurface", "lod": "1", "boundaries": [[[0, 1, 2]]]}
                ],
            }
        },
        "vertices": vertices,
        "transform": {"scale": [0.125, 0.25, 0.5], "translate": [0, 0, 0]},
    }


@pytest.mark.parametrize("triangulate", [False, True])
def test_glb_preserves_small_edges_at_a_large_world_origin(triangulate):
    model = triangle_model()
    origin = [100000000, -200000000, 300000000]
    translated = copy.deepcopy(model)
    translated["transform"]["translate"] = origin
    cm = cityjson.CityJSON(j=copy.deepcopy(translated))

    local, normals, _ = read_mesh(cityjson.CityJSON(j=model).export2glb(triangulate))
    positions, shifted_normals, matrix = read_mesh(cm.export2glb(triangulate))
    assert sorted(map(tuple, local)) == [(0, 0, 0), (0, 0.5, 0.5), (0.375, 0, 0)]
    np.testing.assert_array_equal(positions, local)
    np.testing.assert_array_equal(shifted_normals, normals)
    np.testing.assert_allclose(np.linalg.norm(shifted_normals, axis=1), 1)
    # Local CityJSON (x, y, z) becomes glTF (x, z, -y), including the origin.
    world = positions @ matrix[:3, :3].T + matrix[:3, 3]
    xyz = local.astype(float) + origin
    np.testing.assert_array_equal(
        world, np.column_stack((xyz[:, 0], xyz[:, 2], -xyz[:, 1]))
    )
    assert cm.j == translated


def test_glb_without_a_transform_keeps_decoded_positions():
    model = triangle_model()
    del model["transform"]
    positions, _, matrix = read_mesh(cityjson.CityJSON(j=model).export2glb(False))
    assert sorted(map(tuple, positions)) == sorted(map(tuple, model["vertices"]))
    np.testing.assert_array_equal(matrix[:3, 3], [0, 0, 0])


@pytest.mark.parametrize("triangulate", [False, True])
@pytest.mark.parametrize(
    "origin",
    [[3.125e-8, -2.5e-8, 1.25e-8], [0.123456789, -0.234567891, 0.345678912]],
)
def test_glb_preserves_fractional_world_origin(triangulate, origin):
    model = triangle_model()
    model["transform"]["translate"] = origin
    positions, _, matrix = read_mesh(cityjson.CityJSON(j=model).export2glb(triangulate))
    np.testing.assert_array_equal(matrix[:3, 3], [origin[0], origin[2], -origin[1]])
    # The vertex at the local origin must retain even a sub-micro world shift.
    local_origin = np.flatnonzero(np.all(positions == 0, axis=1))
    assert len(local_origin) == 1
    world = positions[local_origin[0]] @ matrix[:3, :3].T + matrix[:3, 3]
    np.testing.assert_array_equal(world, [origin[0], origin[2], -origin[1]])


@pytest.mark.parametrize("triangulate", [False, True])
def test_glb_bounds_match_the_stored_float32_values(triangulate):
    model = triangle_model()
    model["transform"]["scale"] = [0.123456789, 0.234567891, 0.345678912]
    glb = cityjson.CityJSON(j=model).export2glb(triangulate)
    positions, normals, _ = read_mesh(glb)
    data = glb.getvalue()
    json_size = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + json_size])
    attributes = document["meshes"][0]["primitives"][0]["attributes"]
    for name, values in (("POSITION", positions), ("NORMAL", normals)):
        accessor = document["accessors"][attributes[name]]
        np.testing.assert_array_equal(accessor["min"], values.min(axis=0))
        np.testing.assert_array_equal(accessor["max"], values.max(axis=0))


def test_glb_serialization_does_not_change_cityjson_float_formatting():
    before = json.dumps({"probe": 0.123456789})
    encoder = json.encoder.float
    c_encoder = json.encoder.c_make_encoder
    cityjson.CityJSON(j=triangle_model()).export2glb(False)
    assert before == '{"probe": 0.123457}'
    assert json.dumps({"probe": 0.123456789}) == before
    assert json.encoder.float is encoder
    assert json.encoder.c_make_encoder is c_encoder
