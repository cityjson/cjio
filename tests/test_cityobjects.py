"""CityObject methods and functions"""

import pytest

from cjio import models


@pytest.fixture(scope="function")
def cm_rdam_subset(rotterdam_subset):
    rotterdam_subset.cityobjects = dict()
    for co_id, co in rotterdam_subset.j["CityObjects"].items():
        # do some verification here
        children = co["children"] if "children" in co else None
        parents = co["parents"] if "parents" in co else None
        attributes = co["attributes"] if "attributes" in co else None
        # cast to objects
        geometry = []
        for geom in co["geometry"]:
            semantics = geom["semantics"] if "semantics" in geom else None
            geometry.append(
                models.Geometry(
                    type=geom["type"],
                    lod=geom["lod"],
                    boundaries=geom["boundaries"],
                    semantics_obj=semantics,
                    vertices=rotterdam_subset.j["vertices"],
                )
            )
        rotterdam_subset.cityobjects[co_id] = models.CityObject(
            id=id,
            type=co["type"],
            attributes=attributes,
            children=children,
            parents=parents,
            geometry=geometry,
        )
    yield rotterdam_subset


class TestCityObject:
    def test_to_json(self, cm_rdam_subset):
        cm = cm_rdam_subset
        j_co = dict()
        for co_id, co in cm.cityobjects.items():
            j_co[co_id] = co.to_json()
        print(j_co)

    @pytest.mark.parametrize("lod", [1, 1.2, "1", "1.3"])
    def test_build_index(self, lod):
        co = models.CityObject(id="one")
        geom = models.Geometry(type="Solid", lod=lod)
        co.geometry.append(geom)
        geometry, vtx_lookup, vtx_idx = co.build_index()
        assert "semantics" not in geometry[0]
