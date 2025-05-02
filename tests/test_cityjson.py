"""Test the CityJSON class"""

import pytest
import copy
from cjio import cityjson
from math import isclose
import json


class TestCityJSON:
    def test_subset_ids(self, zurich_subset):
        # Parent ID
        subset = zurich_subset.get_subset_ids(
            ["UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30"]
        )
        expected = [
            "UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30",
            "UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80",
            "UUID_5bd1cee6-b3f0-40fb-a6ae-833e88305e31",
        ]
        assert set(expected).issubset(subset.j["CityObjects"])
        # Child ID
        subset2 = zurich_subset.get_subset_ids(
            ["UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80"]
        )
        expected = []
        assert set(expected).issubset(set(subset2.j["CityObjects"]))

    def test_subset_bbox(self, zurich_subset):
        cm = zurich_subset
        extent = cm.j["metadata"]["geographicalExtent"]
        bbox = [
            extent[0],
            extent[1],
            extent[3] - ((extent[3] - extent[0]) / 2),
            extent[4] - ((extent[4] - extent[1]) / 2),
        ]
        subset = cm.get_subset_bbox(bbox)
        for coid in subset.j["CityObjects"]:
            centroid = subset.get_centroid(coid)
            if centroid is not None:
                assert (
                    (centroid[0] >= bbox[0])
                    and (centroid[1] >= bbox[1])
                    and (centroid[0] < bbox[2])
                    and (centroid[1] < bbox[3])
                )

    def test_subset_bbox_loop(self, delft):
        """Issue #10"""
        _ = delft.update_bbox()
        subs_box = (
            84873.68845606346,
            447503.6748565406,
            84919.65679078053,
            447548.4091420035,
        )
        nr_cos = []
        for i in range(4):
            s = delft.get_subset_bbox(subs_box)
            nr_cos.append(len(s.j["CityObjects"]))
        _f = nr_cos[0]
        assert all(i == _f for i in nr_cos)

    def test_subset_random(self, zurich_subset):
        subset = zurich_subset.get_subset_random(10)
        cnt = sum(
            1 for co in subset.j["CityObjects"].values() if co["type"] == "Building"
        )
        assert cnt == 10

    def test_subset_cotype(self, delft):
        subset = delft.get_subset_cotype(("Building", "LandUse"))
        types = [
            "LandUse",
            "Building",
            "BuildingPart",
            "BuildingInstallation",
            "BuildingConstructiveElement",
            "BuildingFurniture",
            "BuildingStorey",
            "BuildingRoom",
            "BuildingUnit",
        ]

        for co in subset.j["CityObjects"]:
            assert subset.j["CityObjects"][co]["type"] in types

    def test_calculate_bbox(self):
        """Test the calculate_bbox function"""

        data = {"vertices": [[0, 0, 0], [1, 1, 1]]}

        cm = cityjson.CityJSON(j=data)
        bbox = cm.calculate_bbox()

        assert bbox == [0, 0, 0, 1, 1, 1]

    def test_calculate_bbox_with_transform(self):
        """Test the calculate_bbox function"""

        data = {
            "vertices": [[0, 0, 0], [1, 1, 1]],
            "transform": {"scale": [0.001, 0.001, 0.001], "translate": [100, 100, 100]},
        }

        cm = cityjson.CityJSON(j=data)
        bbox = cm.calculate_bbox()

        assert bbox == [100, 100, 100, 100.001, 100.001, 100.001]

    def test_de_compression(self, delft):
        cm = copy.deepcopy(delft)
        assert cm.decompress()
        cm2 = copy.deepcopy(cm)
        cm.compress(3)
        assert cm.j["transform"]["scale"][0] == 0.001
        assert len(delft.j["vertices"]) == len(cm.j["vertices"])
        v1 = cm2.j["vertices"][0][0]
        v2 = cm.j["vertices"][0][0]
        assert isinstance(v1, float)
        assert isinstance(v2, int)

    def test_de_compression_2(self, cube):
        cubec = copy.deepcopy(cube)
        cubec.decompress()
        assert cube.j["vertices"][0][0] == cubec.j["vertices"][0][0]
        assert cubec.compress(2)
        assert len(cube.j["vertices"]) == len(cubec.j["vertices"])

    def test_reproject(self, delft_1b):
        cm = copy.deepcopy(delft_1b)
        cm.reproject(4937)  # -- z values should stay the same
        x = (
            cm.j["vertices"][0][0] * cm.j["transform"]["scale"][0]
            + cm.j["transform"]["translate"][0]
        )
        y = (
            cm.j["vertices"][0][1] * cm.j["transform"]["scale"][1]
            + cm.j["transform"]["translate"][1]
        )
        z = (
            cm.j["vertices"][0][2] * cm.j["transform"]["scale"][2]
            + cm.j["transform"]["translate"][2]
        )
        print(x, y, z)
        assert x == pytest.approx(52.011288184126094)
        assert y == pytest.approx(4.36772776578513)
        assert z == pytest.approx(49.50418078666017)
        assert isclose(
            cm.j["metadata"]["geographicalExtent"][5]
            - cm.j["metadata"]["geographicalExtent"][2],
            6.1,
            abs_tol=0.001,
        )

        cm.reproject(7415)
        x = (
            cm.j["vertices"][0][0] * cm.j["transform"]["scale"][0]
            + cm.j["transform"]["translate"][0]
        )
        y = (
            cm.j["vertices"][0][1] * cm.j["transform"]["scale"][1]
            + cm.j["transform"]["translate"][1]
        )
        z = (
            cm.j["vertices"][0][2] * cm.j["transform"]["scale"][2]
            + cm.j["transform"]["translate"][2]
        )
        print(x, y, z)
        x_d = (
            delft_1b.j["vertices"][0][0] * delft_1b.j["transform"]["scale"][0]
            + delft_1b.j["transform"]["translate"][0]
        )
        y_d = (
            delft_1b.j["vertices"][0][1] * delft_1b.j["transform"]["scale"][1]
            + delft_1b.j["transform"]["translate"][1]
        )
        z_d = (
            delft_1b.j["vertices"][0][2] * delft_1b.j["transform"]["scale"][2]
            + delft_1b.j["transform"]["translate"][2]
        )
        assert x == pytest.approx(x_d)
        assert y == pytest.approx(y_d)
        assert z == pytest.approx(z_d)

    def test_convert_to_stl(self, delft):
        cm = copy.deepcopy(delft)
        _ = cm.export2stl(sloppy=True)

    def test_triangulate(self, materials):
        cm = materials
        cm.triangulate(sloppy=False)

    def test_is_triangulate(self, triangulated):
        cm = triangulated
        assert cm.is_triangulated()

    def test_convert_to_jsonl(self, delft):
        cm = copy.deepcopy(delft)
        jsonl = cm.export2jsonl()
        for line in jsonl.readlines():
            json.loads(line)

    def test_filter_lod(self, multi_lod):
        cm = multi_lod
        cm.filter_lod("1.3")
        for coid in cm.j["CityObjects"]:
            if "geometry" in cm.j["CityObjects"]:
                for geom in cm.j["CityObjects"][coid]["geometry"]:
                    assert geom["lod"] == "1.3"

    def test_merge_materials(self, materials_two):
        """Testing #100
        Merging two files with materials. One has the member 'values', the other has the
        member 'value' on their CityObjects.
        """
        cm1, cm2 = materials_two
        # cm1 contains the CityObject with 'value'. During the merge, the Material Object
        # from cm1 is appended to the list of Materials in cm2
        assert cm2.merge([cm1])
        assert len(cm2.j["CityObjects"]) == 4
        # The value of 'value' in the CityObject from cm1 must be updated to point to the
        # correct Material Object in the materials list
        assert (
            cm2.j["CityObjects"]["NL.IMBAG.Pand.0518100001755018-0"]["geometry"][0][
                "material"
            ]["default"]["value"]
            == 1
        )
