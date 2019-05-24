"""Demonstrate what is when we define the CityModel-objects in a top-down approach

"""

from typing import List, Dict


class CityModel(object):
    """Equivalent to the main CityJSON object in the data model"""
    type = 'CityJSON'
    cityjson_version = '1.0'

    def __init__(self, cityobjects):
        self.cityobjects = cityobjects

    def get_cityobjects(self, type=None):
        """Return a generator over the CityObjects of the given type

        If type=None, return all CityObjects
        """
        if type is None:
            return self.cityobjects
        else:
            if not isinstance(type, str):
                raise TypeError("type parameter must be a string")
            target = type.lower()
            return (co for co in self.cityobjects if co.type.lower() == target)


class CityObject(object):
    """CityObject class"""
    def __init__(self, id, type, geometry):
        self.id = id
        self.type = type
        self.geometry = geometry


class SemanticSurface(object):
    """SemanticSurface class

    It doesn't store the coordinates as Geometry, just pointers to parts of the Geometry
    """


class Geometry(object):
    """CityJSON Geometry object"""
    def __init__(self, type: str=None, lod: int=None,
                 boundaries: List=None, semantics_obj: Dict=None,
                 vertices=None):
        self.type = type
        self.lod = lod
        self.boundaries = self.dereference_boundary(type, boundaries, vertices)
        self.semantics_obj = semantics_obj

    @staticmethod
    def vertex_mapper(boundary, vertices):
        """Maps vertex coordinates to vertex indices"""
        # NOTE BD: it might be ok to simply return the iterator from map()
        return list(map(lambda x: vertices[x], boundary))

    def dereference_boundary(self, type, boundary, vertices):
        """Replace vertex indices with vertex coordinates in the geomery boundary"""
        # TODO BD: would be much faster with recursion
        if type.lower() == 'multipoint':
            return self.vertex_mapper(boundary, vertices)
        elif type.lower() == 'multilinestring':
            return [self.vertex_mapper(b, vertices) for b in boundary]
        elif type.lower() == 'multisurface' or type.lower() == 'compositesurface':
            s = []
            for surface in boundary:
                s.append([self.vertex_mapper(b, vertices) for b in surface])
            return s
        elif type.lower() == 'solid':
            sh = []
            for shell in boundary:
                s = []
                for surface in shell:
                    s.append([self.vertex_mapper(b, vertices) for b in surface])
                sh.append(s)
            return sh
        elif type.lower() == 'multisolid' or type.lower() == 'compositesolid':
            solids = []
            for solid in boundary:
                sh = []
                for shell in solid:
                    s = []
                    for surface in shell:
                        s.append([self.vertex_mapper(b, vertices) for b in surface])
                    sh.append(s)
                solids.append(sh)
            return solids


    @property
    def semantics(self):
        """The Semantic Surface types in the Geometry"""
        return (s['type'] for s in self.semantics_obj['surfaces'])
