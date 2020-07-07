"""Test the CityJSON class

"""
import pytest
import copy
from cjio import cityjson,models

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

    def test_compression(self, delft):
        cm = copy.deepcopy(delft)
        cm.compress(3)
        assert cm.j["transform"]["scale"][0] == 0.001
        assert len(delft.j["vertices"]) == len(cm.j["vertices"])
        v1 = delft.j["vertices"][0][0]
        v2 = cm.j["vertices"][0][0]
        assert isinstance(v1, float)
        assert isinstance(v2, int)
