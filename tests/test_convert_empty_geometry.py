"""Synthetic, decoded public-export regressions for mixed geometry."""

import copy
import json
import struct

import numpy as np
import pytest

from cjio import cityjson


def model(geometries, vertices=None):
    return cityjson.CityJSON(
        j={
            "type": "CityJSON",
            "version": "2.0",
            "vertices": vertices or [[0, 0, 0], [2, 0, 0], [0, 2, 0]],
            "CityObjects": {"one": {"type": "Building", "geometry": geometries}},
        }
    )


def geometry(kind, empty=False):
    surfaces = [] if empty else [[[0, 1, 2]]]
    return {
        "type": kind,
        "lod": "1",
        "boundaries": [surfaces] if kind == "Solid" else surfaces,
    }


def decode(glb):
    raw = glb.getvalue()
    magic, version, length = struct.unpack_from("<4sII", raw)
    assert (magic, version, length) == (b"glTF", 2, len(raw))
    json_length, json_kind = struct.unpack_from("<I4s", raw, 12)
    assert json_kind == b"JSON"
    doc = json.loads(raw[20 : 20 + json_length])
    binary_length, binary_kind = struct.unpack_from("<I4s", raw, 20 + json_length)
    assert binary_kind == b"BIN\x00"
    binary = raw[28 + json_length :]
    assert len(binary) == binary_length

    def accessor(index):
        acc = doc["accessors"][index]
        view = doc["bufferViews"][acc["bufferView"]]
        assert view["byteOffset"] + view["byteLength"] <= len(binary)
        count = acc["count"]
        scalar = acc["type"] == "SCALAR"
        dtype = "<u4" if acc["componentType"] == 5125 else "<f4"
        start = view["byteOffset"] + acc.get("byteOffset", 0)
        return np.frombuffer(
            binary, dtype=dtype, count=count if scalar else count * 3, offset=start
        ).reshape((-1,) if scalar else (-1, 3))

    result = []
    for mesh in doc["meshes"]:
        primitive = mesh["primitives"][0]
        result.append(
            (
                accessor(primitive["attributes"]["POSITION"]),
                accessor(primitive["attributes"]["NORMAL"]),
                accessor(primitive["indices"]),
            )
        )
    return doc, result


@pytest.mark.parametrize("kind", ["MultiSurface", "CompositeSurface", "Solid"])
@pytest.mark.parametrize("do_triangulate", [False, True])
@pytest.mark.parametrize("order", ["empty-first", "empty-last", "between"])
def test_mixed_empty_geometry_preserves_every_triangle(kind, do_triangulate, order):
    valid = geometry(kind)
    empty = geometry(kind, empty=True)
    geoms = {
        "empty-first": [empty, valid],
        "empty-last": [valid, empty],
        "between": [valid, empty, valid],
    }[order]
    cm = model(copy.deepcopy(geoms))
    before = copy.deepcopy(cm.j)
    _, meshes = decode(cm.export2glb(do_triangulate=do_triangulate))
    assert cm.j == before
    assert len(meshes) == 1
    positions, normals, indices = meshes[0]
    repetitions = 2 if order == "between" else 1
    np.testing.assert_array_equal(
        positions, np.tile([[0, 0, 0], [2, 0, 0], [0, 2, 0]], (repetitions, 1))
    )
    np.testing.assert_array_equal(normals, np.tile([0, 0, -1], (3 * repetitions, 1)))
    np.testing.assert_array_equal(indices, np.arange(3 * repetitions))
    assert np.isfinite(normals).all()
    assert indices.max() < len(positions)


@pytest.mark.parametrize("do_triangulate", [False, True])
def test_all_empty_geometry_has_a_clear_error(do_triangulate):
    cm = model([geometry("MultiSurface", True), geometry("Solid", True)])
    with pytest.raises(ValueError, match="No triangles to export for CityObject one"):
        cm.export2glb(do_triangulate=do_triangulate)


@pytest.mark.parametrize("do_triangulate", [False, True])
def test_different_geometry_normals_keep_their_vertex_order(do_triangulate):
    first = geometry("MultiSurface")
    second = geometry("MultiSurface")
    second["boundaries"] = [[[0, 2, 3]]]
    vertices = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]]
    cm = model([first, geometry("MultiSurface", True), second], vertices)
    _, meshes = decode(cm.export2glb(do_triangulate=do_triangulate))
    positions, normals, indices = meshes[0]
    np.testing.assert_array_equal(positions, np.array(vertices)[[0, 1, 2, 0, 2, 3]])
    np.testing.assert_array_equal(normals, [[0, 0, -1]] * 3 + [[-1, 0, 0]] * 3)
    np.testing.assert_array_equal(indices, np.arange(6))


@pytest.mark.parametrize("do_triangulate", [False, True])
def test_closed_solid_keeps_all_faces(do_triangulate):
    vertices = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]]
    faces = [[[0, 2, 1]], [[0, 1, 3]], [[0, 3, 2]], [[1, 2, 3]]]
    solid = {"type": "Solid", "lod": "1", "boundaries": [faces]}
    cm = model([solid], vertices)
    _, meshes = decode(cm.export2glb(do_triangulate=do_triangulate))
    positions, normals, indices = meshes[0]
    expected_vertices = np.array(vertices)[[0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]]
    np.testing.assert_array_equal(positions, expected_vertices)
    np.testing.assert_array_equal(indices, np.arange(12))
    assert normals.shape == (12, 3)
    assert np.isfinite(normals).all()
    np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1, rtol=1e-6)


@pytest.mark.parametrize(
    "vertices,ring",
    [
        ([[0, 0, 0], [1, 0, 0], [2, 0, 0]], [0, 1, 2]),
        ([[0, 0, 0], [1, 0, 0], [0, 2, 0]], [0, 0, 1]),
    ],
)
def test_existing_degenerate_triangle_fallback_stays_finite(vertices, ring):
    valid = geometry("MultiSurface")
    valid["boundaries"] = [[ring]]
    cm = model([geometry("MultiSurface", True), valid], vertices)
    _, meshes = decode(cm.export2glb(do_triangulate=False))
    positions, normals, indices = meshes[0]
    assert len(positions) == len(normals) == len(indices) == 3
    np.testing.assert_array_equal(positions, np.array(vertices)[ring])
    np.testing.assert_array_equal(normals, np.tile([1, 0, 0], (3, 1)))
    assert np.isfinite(normals).all()


def test_malformed_triangle_still_fails_instead_of_disappearing():
    malformed = geometry("MultiSurface")
    malformed["boundaries"] = [[[0, 1]]]
    with pytest.raises(IndexError):
        model([geometry("MultiSurface", True), malformed]).export2glb(
            do_triangulate=False
        )
