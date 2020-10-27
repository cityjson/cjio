"""Geometry methods and functions

"""
import pytest
from math import isclose

from cjio import models


@pytest.fixture(scope='function')
def data_geometry():
    vertices = [
        (0.0,1.0,0.0),
        (1.0,1.0,0.0),
        (2.0,1.0,0.0),
        (3.0,1.0,0.0),
        (4.0,1.0,0.0),
        (5.0,1.0,0.0)
    ]
    
    geometry = [{
        'type': 'CompositeSolid',
        'lod': 2,
        'boundaries': [
            [
                [
                    [[0, 0, 0, 0, 0]], [[1, 1, 1, 1]], [[2, 2, 2, 2]], [[3, 3, 3, 3]]
                ],
                [
                    [[2, 2, 2, 2]], [[3, 3, 3, 3]], [[4, 4, 4, 4]], [[5, 5, 5, 5]]
                ]
            ],
            [
                [[[0, 0, 0, 0, 0]], [[1, 1, 1, 1]], [[2, 2, 2, 2]], [[3, 3, 3, 3]]]
            ]
        ],
        'semantics': {
            'surfaces': [
                {
                    'type': 'WallSurface',
                    'slope': 33.4,
                    'children': [2,3],
                    'parent': 1
                },
                {
                    'type': 'RoofSurface',
                    'slope': 66.6,
                    'children': [0]
                },
                {
                    'type': 'Door',
                    'parent': 0,
                    'colour': 'blue'
                },
                {
                    'type': 'Door',
                    'parent': 0,
                    'colour': 'red'
                }
            ],
            'values': [
                [[2, 1, 0, 3], [2, 1, 0, 3]],
                [None]
            ]
        }
    }]

    yield (geometry, vertices)


@pytest.fixture(scope='function')
def surfaces():
    srf = {
        0: {
            'type': 'WallSurface',
            'attributes': {
                'slope': 33.4,
            },
            'children': [2,3],
            'parent': 1,
            'surface_idx': [[0, 0, 2], [0, 1, 2]]
        },
        1: {
            'type': 'RoofSurface',
            'attributes': {
                'slope': 66.6,
            },
            'children': [0],
            'surface_idx': [[0, 0, 1], [0, 1, 1]]
        },
        2: {
            'type': 'Door',
            'attributes': {
                'colour': 'blue'
            },
            'parent': 0,
            'surface_idx': [[0, 0, 0], [0, 1, 0]]
        },
        3: {
            'type': 'Door',
            'attributes': {
                'colour': 'red'
            },
            'parent': 0,
            'surface_idx': [[0, 0, 3], [0, 1, 3]]
        }
    }
    yield srf


@pytest.fixture(scope='function',
                params=[
                    ('multipoint', [], [], []),
                    ('multipoint',
                     [2, 4, 5],
                     [(2.0, 1.0, 0.0), (4.0, 1.0, 0.0), (5.0, 1.0, 0.0)],
                     [
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0)
                     ]
                     ),
                    ('multisurface',
                     [[[2, 4, 5]]],
                     [[[(2.0, 1.0, 0.0), (4.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]],
                     [
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0)
                     ]
                     ),
                    ('multisurface',
                     [[[2, 4, 5], [2, 4, 5]]],
                     [[[(2.0, 1.0, 0.0), (4.0, 1.0, 0.0), (5.0, 1.0, 0.0)],
                       [(2.0, 1.0, 0.0), (4.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]],
                     [
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0)
                     ]
                     ),
                    ('solid',
                     [
                         [[[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]]],
                         [[[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]]]
                     ],
                     [
                         [[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]],
                          [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
                          [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]],
                         [[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]],
                          [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
                          [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]
                     ],
                     [
                         (0.0, 1.0, 0.0),
                         (3.0, 1.0, 0.0),
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (3.0, 1.0, 0.0),
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                     ]
                     ),
                    ('compositesolid',
                     [
                         [[[[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]]]],
                         [[[[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]]]]
                     ],
                     [
                         [[[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]],
                           [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
                           [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]],
                         [[[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]],
                           [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
                           [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]]
                     ],
                     [
                         (0.0, 1.0, 0.0),
                         (3.0, 1.0, 0.0),
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (3.0, 1.0, 0.0),
                         (2.0, 1.0, 0.0),
                         (4.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (0.0, 1.0, 0.0),
                         (1.0, 1.0, 0.0),
                         (5.0, 1.0, 0.0),
                     ]
                     )
                ]
                )
def data_vtx_idx(request):
    type, boundary, result, vertex_list = request.param
    yield (type, boundary, result, vertex_list)


class TestGeometry:
    @pytest.mark.parametrize('vtx_original, vtx_transformed', [
        ([52496,601650,10188], [90461.816, 436042.09, 10.188])
    ])
    def test_transform_vertex(self, vtx_original, vtx_transformed):
        transform = {"scale":[0.001,0.001,0.001],"translate":[90409.32,435440.44,0.0]}
        res = models.Geometry._transform_vertex(vtx_original, transform)
        assert all([isclose(res[i], v) for i,v in enumerate(vtx_transformed)])

    def test_dereference_boundaries(self, data_geometry, data_vtx_idx):
        type, boundary, result, vertex_list = data_vtx_idx
        vertices = data_geometry[1]
        geom = models.Geometry(type=type, boundaries=boundary, vertices=vertices)
        assert geom.boundaries == result


    def test_dereference_boundaries_wrong_type(self, data_geometry):
        geometry, vertices = data_geometry
        geometry[0]['type'] = 'CompositeSurface'
        with pytest.raises(TypeError) as e:
            models.Geometry(type=geometry[0]['type'],
                            boundaries=geometry[0]['boundaries'],
                            vertices=vertices)
            assert e == "Boundary definition does not correspond to MultiSurface or CompositeSurface"

    def test_build_index(self, data_geometry, data_vtx_idx):
        type, boundary, result, vertex_list = data_vtx_idx
        vertices = data_geometry[1]
        geom = models.Geometry(type=type, boundaries=boundary, vertices=vertices)
        geom_idx, vertex_lookup, vertex_index = geom.build_index()
        print(geom_idx, vertex_lookup)


    @pytest.mark.balazs
    def test_vertex_indexer(self, ms_triangles):
        vtx_lookup = {}
        vtx_idx = 0
        geom = models.Geometry(type='MultiSurface', lod=1)
        for record in ms_triangles:
            msurface = list()
            for _surface in record:
                r = list()
                for _ring in _surface:
                    bdry, vtx_lookup, vtx_idx = geom._vertex_indexer(_ring,
                                                                     vtx_lookup,
                                                                     vtx_idx)
                    r.append(bdry)
                msurface.append(r)


    def test_to_json(self, data_geometry,data_vtx_idx):
        type, boundary, result, vertex_list = data_vtx_idx
        vertices = data_geometry[1]
        geom = models.Geometry(type=type, boundaries=boundary, vertices=vertices)
        j = geom.to_json()
        print(j)

    def test_vertices(self, data_geometry, data_vtx_idx):
        type, boundary, result, vertex_list = data_vtx_idx
        vertices = data_geometry[1]
        geom = models.Geometry(type=type, boundaries=boundary, vertices=vertices)
        assert geom.get_vertices() == vertex_list

    @pytest.mark.parametrize('values, surface_idx', [
        (
            None,
            dict()
        ),
        (
            [None],
            dict()
        ),
        (
            [[[0, 1, 2, None], [0, 1, 2, None]], [None]],
            {0: [[0, 0, 0],[0, 1, 0]],
             1: [[0, 0, 1],[0, 1, 1]],
             2: [[0, 0, 2],[0, 1, 2]]}
        )
    ])
    def test_index_surface_boundaries(self, values, surface_idx):
        res = models.Geometry._index_surface_boundaries(values)
        assert res == surface_idx


    @pytest.mark.parametrize('surface, boundaries, surfaces', [
        (
                {'surface_idx': []},
                [],
                []
        ),
        (
                {'surface_idx': None},
                [],
                []
        ),
        (
                {'surface_idx': [[0]]},  # 1. surface in a MultiSurface
                [[[0]], [[1]]],
                [[[0]]]
        ),
        (
                {'surface_idx': [[0], [1]]},  # 1.,2. surface in a MultiSurface
                [[[0], [1]], [[2]]],
                [[[0], [1]], [[2]]]
        ),
        (
                {'surface_idx': [[0, 1], [0, 2], [1, 0]]},
                # 2.,3. surface in exterior shell of Solid, 1. surface in interior shell of Solid
                [[[[0, 0]], [[0, 1]], [[0, 2]]], [[[1, 0]], [[1, 1]], [[1, 2]]]],
                [[[0, 1]], [[0, 2]], [[1, 0]]]
        ),
        (
                {'surface_idx': [[0, 0, 0], [0, 0, 2], [1, 0, 0]]},
                # 1.,3. surf. of exterior of 1. Solid, 1. surface of exterior of 2. Solid
                [[[[[0, 0, 0]], [[0, 0, 1]], [[0, 0, 2]]]], [[[[1, 0, 0]], [[1, 0, 1]], [[1, 0, 2]]]]],
                [[[0, 0, 0]], [[0, 0, 2]], [[1, 0, 0]]]
        )
    ])
    def test_get_surface_boundaries(self, boundaries, surface, surfaces):
        geom = models.Geometry()
        geom.boundaries = boundaries
        res = list(geom.get_surface_boundaries(surface))
        assert res == surfaces


    @pytest.mark.parametrize('surface', [
        {
            0: {'surface_idx': [[0]]},
            1: {'surface_idx': [[0]]}
        },
        [
            {'surface_idx': [[0]]}
        ]
    ])
    def test_get_surface_boundaries_errors(self, surface):
        geom = models.Geometry()
        with pytest.raises(TypeError):
            geom.get_surface_boundaries(surface)


    def test_dereference_surfaces(self, data_geometry, surfaces):
        geometry, vertices = data_geometry
        geom = models.Geometry(type='CompositeSolid')
        geom.boundaries = geometry[0]['boundaries']
        geom.surfaces = geom._dereference_surfaces(geometry[0]['semantics'])
        assert geom.surfaces == surfaces


    def test_get_surfaces(self, data_geometry, surfaces):
        geometry, vertices = data_geometry
        geom = models.Geometry(type='CompositeSolid')
        geom.boundaries = geometry[0]['boundaries']
        geom.surfaces = surfaces
        roof = geom.get_surfaces('roofsurface')
        wall = geom.get_surfaces('wallsurface')
        door = geom.get_surfaces('door')
        assert roof == {1: {
            'type': 'RoofSurface',
            'attributes': {
                'slope': 66.6,
            },
            'children': [0],
            'surface_idx': [[0, 0, 1], [0, 1, 1]]
        }}
        assert wall == {0: {
            'type': 'WallSurface',
            'attributes': {
                'slope': 33.4,
            },
            'children': [2,3],
            'parent': 1,
            'surface_idx': [[0, 0, 2], [0, 1, 2]]
        }}
        assert door == {
            2: {
                'type': 'Door',
                'attributes': {
                    'colour': 'blue'
                },
                'parent': 0,
                'surface_idx': [[0, 0, 0], [0, 1, 0]]
            },
            3: {
                'type': 'Door',
                'attributes': {
                    'colour': 'red'
                },
                'parent': 0,
                'surface_idx': [[0, 0, 3], [0, 1, 3]]
            }
        }

    def test_get_surface_children(self, surfaces):
        geom = models.Geometry(type='CompositeSolid')
        geom.surfaces = surfaces
        res = {
            2: {
            'type': 'Door',
            'attributes': {
                'colour': 'blue'
            },
            'parent': 0,
            'surface_idx': [[0, 0, 0], [0, 1, 0]]
            },
            3: {
                'type': 'Door',
                'attributes': {
                    'colour': 'red'
                },
                'parent': 0,
                'surface_idx': [[0, 0, 3], [0, 1, 3]]
            }
        }
        wall = {
            0: {
                'type': 'WallSurface',
                'attributes': {
                    'slope': 33.4,
                },
                'children': [2, 3],
                'parent': 1,
                'surface_idx': [[0, 0, 2], [0, 1, 2]]
            }
        }
        surface = wall[0]
        if 'children' in surface:
            children = {j:geom.surfaces[j] for j in surface['children']}
            assert children == res
        else:
            pytest.xfail("surface does not have children")

    def test_get_surface_parent(self, surfaces):
        geom = models.Geometry(type='CompositeSolid')
        geom.surfaces = surfaces
        door = {
            2: {
            'type': 'Door',
            'attributes': {
                'colour': 'blue'
            },
            'parent': 0,
            'surface_idx': [[0, 0, 0], [0, 1, 0]]
            },
        }
        res = {
            0: {
                'type': 'WallSurface',
                'attributes': {
                    'slope': 33.4,
                },
                'children': [2, 3],
                'parent': 1,
                'surface_idx': [[0, 0, 2], [0, 1, 2]]
            }
        }
        surface = door[2]
        if 'parent' in surface:
            i = surface['parent']
            parent = {i: geom.surfaces[i]}
            assert parent == res
        else:
            pytest.xfail("surface does not have parent")


class TestGeometryIntegration:
    """Integration tests for operations on Geometry objects

    These tests mainly meant to mimic user workflow and test concepts
    """
    def test_get_surface_boundaries(self, data_geometry):
        """Test how to get the boundaries (geometry) of semantic surfaces"""
        geometry, vertices = data_geometry
        geom = models.Geometry(type=geometry[0]['type'],
                               lod=geometry[0]['lod'],
                               boundaries=geometry[0]['boundaries'],
                               semantics_obj=geometry[0]['semantics'],
                               vertices=vertices)
        roofsurfaces = geom.get_surfaces('roofsurface')
        rsrf_bndry = [list(geom.get_surface_boundaries(rsrf))
                      for i,rsrf in roofsurfaces.items()]
        roof_geom = [
            [
                [[(1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
                [[(3.0, 1.0, 0.0), (3.0, 1.0, 0.0), (3.0, 1.0, 0.0), (3.0, 1.0, 0.0)]]
            ]
        ]
        assert rsrf_bndry == roof_geom

        doorsurfaces = geom.get_surfaces('door')
        dsrf_bndry = [list(geom.get_surface_boundaries(dsrf))
                      for i,dsrf in doorsurfaces.items()]
        door_geom = [
            [
                [[(0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0)]],
                [[(2.0, 1.0, 0.0), (2.0, 1.0, 0.0), (2.0, 1.0, 0.0), (2.0, 1.0, 0.0)]]
            ],
            [
                [[(3.0, 1.0, 0.0), (3.0, 1.0, 0.0), (3.0, 1.0, 0.0), (3.0, 1.0, 0.0)]],
                [[(5.0, 1.0, 0.0), (5.0, 1.0, 0.0), (5.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]
            ]
        ]
        assert dsrf_bndry == door_geom

    def test_set_surface_attributes(self, data_geometry):
        """Test how to set attributes on semantic surfaces"""
        geometry, vertices = data_geometry
        geom = models.Geometry(type=geometry[0]['type'],
                               lod=geometry[0]['lod'],
                               boundaries=geometry[0]['boundaries'],
                               semantics_obj=geometry[0]['semantics'],
                               vertices=vertices)
        roofsurfaces = geom.get_surfaces('roofsurface')
        for i, rsrf in roofsurfaces.items():
            if 'attributes' in rsrf.keys():
                rsrf['attributes']['colour'] = 'red'
            else:
                rsrf['attributes'] = {}
                rsrf['attributes']['colour'] = 'red'
            # overwrite the surface directly in the Geometry object
            geom.surfaces[i] = rsrf
        roofsurfaces_new = geom.get_surfaces('roofsurface')
        for i,rsrf in roofsurfaces_new.items():
            assert rsrf['attributes']['colour'] == 'red'

    def test_split_semantics(self, data_geometry):
        """Test how to split surfaces by creating new semantics"""
        geometry, vertices = data_geometry
        geom = models.Geometry(type=geometry[0]['type'],
                               lod=geometry[0]['lod'],
                               boundaries=geometry[0]['boundaries'],
                               semantics_obj=geometry[0]['semantics'],
                               vertices=vertices)
        roofsurfaces = geom.get_surfaces('roofsurface')
        max_id = max(geom.surfaces.keys()) # surface keys are always integers
        old_ids = []
        for i,rsrf in roofsurfaces.items():
            old_ids.append(i)
            boundaries = geom.get_surface_boundaries(rsrf)
            for i,boundary_geometry in enumerate(boundaries):
                surface_index = rsrf['surface_idx'][i]
                for multisurface in boundary_geometry:
                    # Do any geometry operation here
                    x,y,z = multisurface[0]
                    # Assign new semantics based on the result
                    if x < 2.0:
                        new_srf = {
                            'type': rsrf['type'],
                            'children': rsrf['children'], # it should be checked if surface has children
                            'surface_idx': surface_index
                        }
                        if 'attributes' in rsrf.keys():
                            rsrf['attributes']['orientation'] = 'north'
                        else:
                            rsrf['attributes'] = {}
                            rsrf['attributes']['orientation'] = 'north'
                        new_srf['attributes'] = rsrf['attributes']
                    else:
                        new_srf = {
                            'type': rsrf['type'],
                            'children': rsrf['children'],
                            'surface_idx': surface_index
                        }
                        if 'attributes' in rsrf.keys():
                            rsrf['attributes']['orientation'] = 'south'
                        else:
                            rsrf['attributes'] = {}
                            rsrf['attributes']['orientation'] = 'south'
                        new_srf['attributes'] = rsrf['attributes']
                    if i in geom.surfaces.keys():
                        del geom.surfaces[i]
                    max_id = max_id + 1
                    geom.surfaces[max_id] = new_srf

        roofsurfaces_new = geom.get_surfaces('roofsurface')
        for i,rsrf in roofsurfaces_new.items():
            assert i not in old_ids
            assert 'orientation' in rsrf['attributes'].keys()




