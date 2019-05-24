"""Geometry methods and functions

"""
import pytest

def vertex_mapper(boundary, vertices):
    """Maps vertex coordinates to vertex indices"""
    return list(map(lambda x: vertices[x], boundary))

def dereference_boundary(type, boundary, vertices):
    """Replace vertex indices with vertex coordinates in the geomery boundary"""
    if type.lower() == 'multipoint':
        return vertex_mapper(boundary, vertices)
    elif type.lower() == 'multilinestring':
        return [vertex_mapper(b, vertices) for b in boundary]
    elif type.lower() == 'multisurface' or type.lower() == 'compositesurface':
        s = []
        for surface in boundary:
            s.append([vertex_mapper(b, vertices) for b in surface])
        return s
    elif type.lower() == 'solid':
        sh = []
        for shell in boundary:
            s = []
            for surface in shell:
                s.append([vertex_mapper(b, vertices) for b in surface])
            sh.append(s)
        return sh
    elif type.lower() == 'multisolid' or type.lower() == 'compositesolid':
        solids = []
        for solid in boundary:
            sh = []
            for shell in solid:
                s = []
                for surface in shell:
                    s.append([vertex_mapper(b, vertices) for b in surface])
                sh.append(s)
            solids.append(sh)
        return solids


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
def test_dereference_boundary(vertices, type, boundary, result):
    res = dereference_boundary(type, boundary, vertices)
    assert res == result