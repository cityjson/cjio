"""CityObject methods and functions

"""
import pytest

from cjio import models

@pytest.fixture(scope='module')
def cm_rdam_subset(rotterdam_subset):
    rotterdam_subset.cityobjects = dict()
    for co_id, co in rotterdam_subset.j['CityObjects'].items():
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
                    vertices=rotterdam_subset.j['vertices']
                )
            )
        rotterdam_subset.cityobjects[co_id] = models.CityObject(
            id=id,
            type=co['type'],
            attributes=attributes,
            children=children,
            parents=parents,
            geometry=geometry
        )
    yield rotterdam_subset


class TestCityObject:
    def test_to_json(self, cm_rdam_subset):
        cm = cm_rdam_subset
        j_co = dict()
        for co_id,co in cm.cityobjects.items():
            j_co[co_id] = co.to_json()
        print(j_co)