"""Geometry methods and functions

"""
import pytest

from cjio import model


@pytest.fixture(scope='module')
def data_semantics():
    geom = [
        [
            [
                [[0, 3, 2, 1, 22]], [[4, 5, 6, 7]], [[0, 1, 5, 4]], [[1, 2, 6, 5]]
            ],
            [
                [[240, 243, 124]], [[244, 246, 724]], [[34, 414, 45]], [[111, 246, 5]]
            ]
        ],
        [
            [[[666, 667, 668]], [[74, 75, 76]], [[880, 881, 885]], [[111, 122, 226]]]
        ]
    ]

    sa = {
        "surfaces": [
            {
                "type": "WallSurface",
                "slope": 33.4,
                "children": [2],
                "parent": 1
            },
            {
                "type": "RoofSurface",
                "slope": 66.6,
                "children": [0]
            },
            {
                "type": "Door",
                "parent": 0,
                "colour": "blue"
            }
        ],
        "values": [
            [[2, 1, 0, None], [2, 1, 0, None]],
            [None]
        ]
    }

    yield (geom, sa)


class TestGeometry:
    @pytest.mark.parametrize("type, boundary, result", [
        ('multipoint', [], []),
        ('multipoint',
         [2,4,5],
         [(2.0,1.0,0.0),(4.0,1.0,0.0),(5.0,1.0,0.0)]),
        ('multisurface',
         [[[2,4,5]]],
         [[[(2.0,1.0,0.0),(4.0,1.0,0.0),(5.0,1.0,0.0)]]]),
        ('multisurface',
         [[[2,4,5],[2,4,5]]],
         [[[(2.0,1.0,0.0),(4.0,1.0,0.0),(5.0,1.0,0.0)],[(2.0,1.0,0.0),(4.0,1.0,0.0),(5.0,1.0,0.0)]]]),
        ('solid',
         [
             [ [[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]] ],
             [ [[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]] ]
         ],
         [
             [ [[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]], [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
               [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]],
             [ [[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]], [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
               [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]
         ]
         ),
        ('compositesolid',
         [
            [ [ [[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]] ] ],
            [ [ [[0, 3, 2]], [[4, 5, 1]], [[0, 1, 5]] ] ]
        ],
         [
             [[[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]], [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
               [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]],
             [[[[(0.0, 1.0, 0.0), (3.0, 1.0, 0.0), (2.0, 1.0, 0.0)]], [[(4.0, 1.0, 0.0), (5.0, 1.0, 0.0), (1.0, 1.0, 0.0)]],
               [[(0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (5.0, 1.0, 0.0)]]]]
         ]
         )
    ])
    def test_dereference_boundary(self, vertices, type, boundary, result):
        geom = model.Geometry(type=type, boundaries=boundary, vertices=vertices)
        assert geom.boundaries == result

    @pytest.mark.parametrize('surface_idx, boundaries, surfaces', [
        (
                (),
                [],
                []
        ),
        (
                None,
                [],
                []
        ),
        (
                ((0,),),  # 1. surface in a MultiSurface
                [[[0]], [[1]]],
                [[[0]]]
        ),
        (
                ((0,), (1,)),  # 1.,2. surface in a MultiSurface
                [[[0], [1]], [[2]]],
                [[[0], [1]], [[2]]]
        ),
        (
                ((0, 1), (0, 2), (1, 0)),
                # 2.,3. surface in exterior shell of Solid, 1. surface in interior shell of Solid
                [[[[0, 0]], [[0, 1]], [[0, 2]]], [[[1, 0]], [[1, 1]], [[1, 2]]]],
                [[[0, 1]], [[0, 2]], [[1, 0]]]
        ),
        (
                ((0, 0, 0), (0, 0, 2), (1, 0, 0)),
                # 1.,3. surf. of exterior of 1. Solid, 1. surface of exterior of 2. Solid
                [[[[[0, 0, 0]], [[0, 0, 1]], [[0, 0, 2]]]], [[[[1, 0, 0]], [[1, 0, 1]], [[1, 0, 2]]]]],
                [[[0, 0, 0]], [[0, 0, 2]], [[1, 0, 0]]]
        )
    ])
    def test_get_surface_boundaries(self, boundaries, surface_idx, surfaces):
        res = model.Geometry._get_surface_boundaries(boundaries, surface_idx)
        assert res == surfaces


class TestSemanticSurface:
    def test_dereference_surfaces(self, data_semantic):
        boundary, semantics_obj = data_semantics
        geom = model.Geometry(type='CompositeSurface')
        geom.boundaries = boundary
        geom.semantics = geom._dereference_surfaces(semantics_obj)
        result = [
            model.SemanticSurface(
                type='WallSurface',
                surface_idx=[[[2],[2]]],
                children=[2]
            ),
            model.SemanticSurface(
                type='RoofSurface',
                surface_idx=[[[1],[1]]],
                children=[0]
            )
        ]
        assert geom.semantics == result


    def test_get_surfaces(self, data_semantics):
        boundary, semantics = data_semantics
        geom = model.Geometry(type='CompositeSurface')
        geom.boundaries = boundary
        geom.semantics = [
            model.SemanticSurface(
                type='WallSurface',
                surface_idx=[[[2],[2]]],
                children=model.SemanticSurface(
                    type='Door',
                    surface_idx=[[[0],[0]]]
                )
            ),
            model.SemanticSurface(
                type='RoofSurface',
                surface_idx=[[[1],[1]]]
            )
        ]
        roof = geom.get_surfaces('roofsurface')
        wall = geom.get_surfaces('wallsurface')
        door = geom.get_surfaces('door')
        assert roof == [ [[4, 5, 6, 7]], [[244, 246, 724]] ]
        assert wall == [ [[0, 1, 5, 4]], [[34, 414, 45]] ]
        assert door == [ [[0, 3, 2, 1, 22]], [[240, 243, 124]] ]


