"""Test the CityJSON class"""

import pytest
import copy
from cjio import cityjson, models
from math import isclose
import json


@pytest.fixture(scope='module')
def cm_zur_subset(zurich_subset):
    zurich_subset.cityobjects = dict()
    for co_id, co in zurich_subset.j['CityObjects'].items():
        # do some verification here
        children = co['children'] if 'children' in co else None
        parents = co['parents'] if 'parents' in co else None
        attributes = co['attributes'] if 'attributes' in co else None
        # cast to objects
        geometry = []
        if 'geometry' in co:
            for geom in co['geometry']:
                semantics = geom['semantics'] if 'semantics' in geom else None
                geometry.append(
                    models.Geometry(
                        type=geom['type'],
                        lod=geom['lod'],
                        boundaries=geom['boundaries'],
                        semantics_obj=semantics,
                        vertices=zurich_subset.j['vertices']
                    )
                )
        zurich_subset.cityobjects[co_id] = models.CityObject(
            id=co_id,
            type=co['type'],
            attributes=attributes,
            children=children,
            parents=parents,
            geometry=geometry
        )
    return zurich_subset

class TestCityJSON:
    def test_get_cityobjects_type(self,cm_zur_subset):
        cm = cm_zur_subset
        buildings = cm.get_cityobjects(type='building')
        assert len(buildings) > 0 and all([co.type == 'Building' for i,co in buildings.items()])
        buildings_parts = cm.get_cityobjects(type=['building', 'buildingpart'])
        types = [co.type for i,co in buildings_parts.items()]
        assert ('Building' in types) and ('BuildingPart' in types)

    def test_get_cityobjects_ids(self,cm_zur_subset):
        cm = cm_zur_subset
        res_id = ['UUID_2e5320be-a782-4517-bd0e-ab2cc2407649',
                  'UUID_942e02c4-45cc-4d51-bdde-625df1c81410']
        buildings = cm.get_cityobjects(id=['UUID_2e5320be-a782-4517-bd0e-ab2cc2407649',
                                           'UUID_942e02c4-45cc-4d51-bdde-625df1c81410'])
        assert len(buildings) > 0 and all([co.id in res_id for i,co in buildings.items()])

    def test_get_cityobjects_all(self,cm_zur_subset):
        cm = cm_zur_subset
        all_cos = cm.get_cityobjects()
        assert len(all_cos) == len(cm.cityobjects)

    def test_reference_geometry(self, cm_zur_subset):
        """Test build a coordinate list and index the vertices"""
        cm = cm_zur_subset
        cityobjects, vertex_lookup = cm.reference_geometry()
        assert len(cityobjects) == len(cm.j['CityObjects'])

    def test_get_children(self):
        """# TODO BD: Get all childeren of a CityObject"""

    def test_get_parents(self):
        """# TODO BD: Get all parents of a CityObject"""
        
    def test_subset_ids(self, zurich_subset):
        # Parent ID
        subset = zurich_subset.get_subset_ids(['UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30'])
        expected = ['UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30', 'UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80', 'UUID_5bd1cee6-b3f0-40fb-a6ae-833e88305e31']
        assert set(expected).issubset(subset.j['CityObjects']) == True
        # Child ID
        subset2 = zurich_subset.get_subset_ids(['UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80'])
        expected = ['UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30', 'UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80', 'UUID_5bd1cee6-b3f0-40fb-a6ae-833e88305e31']
        assert set(expected).issubset(subset2.j['CityObjects']) == True
    
    def test_subset_bbox(self, zurich_subset):
        cm = zurich_subset
        extent = cm.j['metadata']['geographicalExtent']
        bbox = [extent[0], extent[1], extent[3] - ((extent[3] - extent[0]) / 2), extent[4] - ((extent[4] - extent[1]) / 2)]
        subset = cm.get_subset_bbox(bbox)
        for coid in subset.j['CityObjects']:
            centroid = subset.get_centroid(coid)
            if (centroid is not None):
                assert ((centroid[0] >= bbox[0]) and
                (centroid[1] >= bbox[1]) and
                (centroid[0] <  bbox[2]) and
                (centroid[1] <  bbox[3]))
    
    def test_subset_random(self, zurich_subset):
        subset = zurich_subset.get_subset_random(10)
        cnt = sum(1 for co in subset.j["CityObjects"].values() if co["type"] == "Building")
        assert cnt == 10
    
    def test_subset_cotype(self, zurich_subset):
        subset = zurich_subset.get_subset_cotype("Building")
        types = ["Building", "BuildingPart", "BuildingInstallation", "BuildingConstructiveElement", "BuildingFurniture", "BuildingStorey", "BuildingRoom", "BuildingUnit"]
        
        for co in subset.j['CityObjects']:
            assert subset.j['CityObjects'][co]['type'] in types

    def test_calculate_bbox(self):
        """Test the calculate_bbox function"""

        data = {"vertices": [
            [0, 0, 0],
            [1, 1, 1]
        ]}

        cm = cityjson.CityJSON(j=data)
        bbox = cm.calculate_bbox()

        assert bbox == [0, 0, 0, 1, 1, 1]
    
    def test_calculate_bbox_with_transform(self):
        """Test the calculate_bbox function"""

        data = {"vertices": [
            [0, 0, 0],
            [1, 1, 1]
        ],
        "transform": {
            "scale": [0.001, 0.001, 0.001],
            "translate": [100, 100, 100]
        }}

        cm = cityjson.CityJSON(j=data)
        bbox = cm.calculate_bbox()

        assert bbox == [100, 100, 100, 100.001, 100.001, 100.001]

    def test_add_lineage_item(self):
        """Test the add_lineage_item function"""

        test_desc = "We did something"

        cm = cityjson.CityJSON()

        cm.add_lineage_item(test_desc)

        assert cm.j["metadata"]["lineage"][0]["processStep"]["description"] == test_desc

        cm.add_lineage_item("Something else", features=["id1", "id2"], source=[{"description": "BAG"}], processor={"contactName": "3D geoinfo"})

        item = cm.j["metadata"]["lineage"][1]
        assert item["processStep"]["description"] == "Something else"
        assert len(item["featureIDs"]) == 2
        assert len(item["source"]) == 1
        assert item["processStep"]["processor"]["contactName"] == "3D geoinfo"

    def test_de_compression(self, delft):
        cm = copy.deepcopy(delft)
        assert cm.decompress() == True
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
        assert cubec.compress(2) == True
        assert len(cube.j["vertices"]) == len(cubec.j["vertices"])

    def test_reproject(self, delft_1b):
        cm = copy.deepcopy(delft_1b)
        cm.reproject(4937) #-- z values should stay the same
        v = cm.j["vertices"][0][0] * cm.j["transform"]["scale"][0] + cm.j["transform"]["translate"][0]
        assert isclose(v, 4.36772776578513, abs_tol=0.001)
        assert isclose(cm.j["metadata"]["geographicalExtent"][5] - cm.j["metadata"]["geographicalExtent"][2], 6.1, abs_tol=0.001)

    def test_convert_to_stl(self, delft):
         cm = copy.deepcopy(delft)
         obj = cm.export2stl()

    def test_triangulate(self, materials):
        """Test #101"""
        cm = materials
        for item in cm:
            item.triangulate()


    def test_is_triangulate(self,triangulated):
        cm = triangulated
        for item in cm:
            assert item.is_triangulated()

    def test_convert_to_jsonl(self, delft):
         cm = copy.deepcopy(delft)
         jsonl = cm.export2jsonl()
        
    def test_filter_lod(self, multi_lod):
        cm = multi_lod
        cm.filter_lod("2.2")
        for coid in cm.j['CityObjects']:
            if 'geometry' in cm.j['CityObjects']:
                for geom in cm.j['CityObjects'][coid]['geometry']:
                    assert geom["lod"] == "2.2"

    def test_merge_materials(materials):
        """Testing #100
        Merging two files with materials. One has the member 'values', the other has the
        member 'value' on their CityObjects.
        """
        cm1, cm2 = materials[:2]
        # cm1 contains the CityObject with 'value'. During the merge, the Material Object
        # from cm1 is appended to the list of Materials in cm2
        assert cm2.merge([cm1, ])
        assert len(cm2.j['CityObjects']) == 4
        # The value of 'value' in the CityObject from cm1 must be updated to point to the
        # correct Material Object in the materials list
        assert cm2.j['CityObjects']['NL.IMBAG.Pand.0518100001755018-0']['geometry'][0]['material']['default']['value'] == 1
