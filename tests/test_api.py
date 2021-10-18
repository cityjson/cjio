"""End-to-end testing of the API

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

class TestAPI:
    def test_get_surfaces(self, cm_rdam_subset):
        """Get all roof geometries"""
        cm = cm_rdam_subset
        roof_geoms = []
        for co in cm.cityobjects.values():
            for geom in co.geometry:
                if float(geom.lod) >= 2.0:
                    for i, rsrf in geom.get_surfaces('roofsurface').items():
                        roof_geoms.append(
                            list(geom.get_surface_boundaries(rsrf))
                        )
        # But since we don't have geometry classes, the user needs to know
        # how the boundaries are defined in cityjson, eg. this is one multisurface
        assert isinstance(roof_geoms[0][0][0][0][0], int)

    def test_set_surface_attribute(self, cm_rdam_subset):
        """Color all the roofsurfaces red"""
        cm = cm_rdam_subset
        new_cos = {}
        for co_id, co in cm.cityobjects.items():
            new_geoms = []
            for geom in co.geometry:
                if float(geom.lod) >= 2.0:
                    for i, rsrf in geom.get_surfaces('roofsurface').items():
                        if 'attributes' in rsrf.keys():
                            rsrf['attributes']['colour'] = 'red'
                        else:
                            rsrf['attributes'] = {}
                            rsrf['attributes']['colour'] = 'red'
                        geom.surfaces[i] = rsrf
                    new_geoms.append(geom)
                else:
                    # add the old geometry
                    new_geoms.append(geom)
            co.geometry = new_geoms
            new_cos[co_id] = co
        cm.cityobjects = new_cos

        ## Verify results
        for co_id, co in cm.cityobjects.items():
            new_geoms = []
            for geom in co.geometry:
                if float(geom.lod) >= 2.0:
                    for i, rsrf in geom.get_surfaces('roofsurface').items():
                        assert rsrf['attributes']['colour'] == 'red'

    def test_create_surface_attribute(self, cm_rdam_subset):
        """Assign orientation attribute to WallSurfaces"""
        cm = cm_rdam_subset
        new_cos = {}
        for co_id, co in cm.cityobjects.items():
            new_geoms = []
            for geom in co.geometry:
                if float(geom.lod) >= 2.0:
                    max_id = max(geom.surfaces.keys())
                    old_ids = []
                    for w_i, wsrf in geom.get_surfaces('wallsurface').items():
                        old_ids.append(w_i)
                        boundaries = geom.get_surface_boundaries(wsrf)
                        for j, boundary_geometry in enumerate(boundaries):
                            surface_index = wsrf['surface_idx'][j]
                            for multisurface in boundary_geometry:
                                # do any geometry operation here
                                x, y, z = multisurface[0]
                                if j % 2 > 0:
                                    new_srf = {
                                        'type': wsrf['type'],
                                        'surface_idx': surface_index
                                    }
                                    if 'attributes' in wsrf.keys():
                                        wsrf['attributes']['orientation'] = 'north'
                                    else:
                                        wsrf['attributes'] = {}
                                        wsrf['attributes']['orientation'] = 'north'
                                    new_srf['attributes'] = wsrf['attributes']
                                else:
                                    new_srf = {
                                        'type': wsrf['type'],
                                        'surface_idx': surface_index
                                    }
                                    if 'attributes' in wsrf.keys():
                                        wsrf['attributes']['orientation'] = 'south'
                                    else:
                                        wsrf['attributes'] = {}
                                        wsrf['attributes']['orientation'] = 'south'
                                    new_srf['attributes'] = wsrf['attributes']
                                if j in geom.surfaces.keys():
                                    del geom.surfaces[j]
                                max_id = max_id + 1
                                geom.surfaces[max_id] = new_srf
                    new_geoms.append(geom)
                else:
                    # add the old geometry
                    new_geoms.append(geom)
            co.geometry = new_geoms
            new_cos[co_id] = co
        cm.cityobjects = new_cos

        # Verify results
        for co_id, co in cm.cityobjects.items():
            for geom in co.geometry:
                if float(geom.lod) >= 2.0:
                    for w_i, wsrf in geom.get_surfaces('wallsurface').items():
                        if wsrf['type'] == 'WallSurface':
                            assert 'orientation' in wsrf['attributes']

    def test_load_unused_semantics(self, mt_1_path):
        """Test #102
        If unused Semantics Objects are stored on the geometry, it shouldn't break the
        API.
        """
        cm = cityjson.load(mt_1_path)
        assert len(cm.cityobjects) == 2
