"""Demonstrate what is when we define the CityModel-objects in a top-down approach

"""
import json
from copy import deepcopy
import collections
from typing import Iterable, Mapping

# TODO BD: this iteration is not really nice, maybe implement it in a way that don't need to use .items() and .values()
# for co_id, co in cm.cityobjects.items():
#     for geom in co.geometry:
#         for srf in geom.surfaces.values():

class CityObject(object):
    """CityObject class"""
    def __init__(self, id,
                 type: str=None, geometry: Iterable=None,
                 attributes: Mapping=None,
                 children: Iterable=None, parents: Iterable=None):
        self.id = id
        self.type = type
        self.geometry = [] if geometry is None else geometry
        self.attributes = {} if attributes is None else attributes
        self.children = [] if children is None else children
        self.parents = [] if parents is None else parents

    def __repr__(self):
        return self._get_info()

    def _get_info(self):
        """Print information about the object"""
        info = collections.OrderedDict()
        info['id'] = self.id
        info['type'] = self.type
        info['attributes'] = self.attributes
        info['children'] = self.children
        info['parents'] = self.parents
        gt = set()
        gl = set()
        sf = set()
        if len(self.geometry) > 0:
            for geom in self.geometry:
                gt.add(geom.type)
                gl.add(geom.lod)
                if geom.surfaces:
                    for s_i, srf in geom.surfaces.items():
                        sf.add(srf['type'])
        info['geometry_type'] = list(gt)
        info['geometry_lod'] = list(gl)
        info['semantic_surfaces'] = list(sf)
        return json.dumps(info, indent=2)

    def get_vertices(self):
        """Dump the vertex coordinates of the CityObject into a list"""
        vtx = []
        for geom in self.geometry:
            vtx += geom.get_vertices()
        return vtx

    def build_index(self, vtx_lookup: Mapping=None, vtx_idx: int=0):
        """Build a coordinate list and index the vertices for Geometry objects
        in the CityObject.
        """
        vtx_lookup = {} if vtx_lookup is None else vtx_lookup
        geometry = []
        for geom in self.geometry:
            geom_idx, vtx_lookup, vtx_idx = geom.build_index(vtx_lookup, vtx_idx)
            j = geom.to_json()
            j['boundaries'] = geom_idx
            if isinstance(geom.lod, int) or isinstance(geom.lod, float):
                if geom.lod >=2.0:
                    geom.build_semantic_surface_index()
                    j['semantics'] = geom.semantics
            elif geom.lod >= '2':
                geom.build_semantic_surface_index()
                j['semantics'] = geom.semantics
            geometry.append(j)
        return (geometry, vtx_lookup, vtx_idx)

    def to_json(self):
        """Return a dictionary that conforms the CityJSON schema"""
        j = dict()
        j['type'] = self.type
        j['geometry'] = []
        if self.attributes:
            j['attributes'] = self.attributes
        if self.children:
            j['children'] = self.children
        if self.parents:
            j['parents'] = self.parents
        return j

class Geometry(object):
    """CityJSON Geometry object"""
    def __init__(self, type: str=None, lod: str=None,
                 boundaries: Iterable=None, semantics_obj: Mapping=None,
                 vertices=None, transform=None, texture_obj=None, appearance=None):
        self.type = type # TODO: use a property for allowing only the specified types
        self.lod = lod
        self.boundaries = self._dereference_boundaries(type, boundaries, vertices, transform)
        self.surfaces = self._dereference_surfaces(semantics_obj)
        self.semantics = {}
        self.texture = self._dereference_textures(texture_obj, appearance)

    @staticmethod
    def _index_surface_boundaries(values):
        """Create an index of the Surfaces which have semantic value in a Geometry boundary

        It creates a lookup table for the indicies to the Surfaces in a boundary that have semantics.
        The key of the lookup table are the indices of the SemanticSurface objects in the Geometry.surfaces array.
        The idea is that by using the index, the geometry of the Surface can be retrieved from
        the boundary in O(1) time, instead of looping through the 'semantics.values' and
        'boundaries' each time the geometry of a semantic surface needs to be retrieved.

        .. note:: Only works with MultiSurface or more complex boundaries

        :param values: The array of values from a Geometry Object's `semantics` member
        :return: A dict of indices to the surfaces in a boundary.
        """
        # TODO BD optimize: Again, here recursion seems to be like a nice alternative
        surface_idx = dict()
        if not values or len(values) == 0:
            return surface_idx
        else:
            for i, idx in enumerate(values):
                if idx is not None:
                    if isinstance(idx, list):
                        for j, jdx in enumerate(idx):
                            if jdx is not None:
                                if isinstance(jdx, list):
                                    for k, kdx in enumerate(jdx):
                                        if isinstance(kdx, list):
                                            raise TypeError("The 'values' member of 'semantics' is too many levels deep")
                                        if kdx is not None:
                                            if kdx not in surface_idx.keys():
                                                surface_idx[kdx] = [[i,j,k]]
                                            else:
                                                surface_idx[kdx].append([i,j,k])
                                else:
                                    if jdx not in surface_idx.keys():
                                        surface_idx[jdx] = [[i,j]]
                                    else:
                                        surface_idx[jdx].append([i,j])
                    else:
                        if idx not in surface_idx.keys():
                            surface_idx[idx] = [[i]]
                        else:
                            surface_idx[idx].append([i])
            return surface_idx

    @staticmethod
    def _vertex_mapper(ring, vertices, transform):
        """Maps vertex coordinates to vertex indices and/or apply transformation on them
        :param ring: A ring defined as an array of vertex indices pointing to ``vertices``
        :param vertices: The array of vertices from the CityJSON file
        :param transform: A Transform object from CityJSON
        :return: The ring with the vertex indices replaced with the vertices
        """
        # NOTE BD: it might be ok to simply return the iterator from map()
        if vertices is not None:
            return list(map(lambda v_i: Geometry._transform_vertex(vertices[v_i], transform), ring))
        else:
            return [Geometry._transform_vertex(vtx, transform) for vtx in ring]

    @staticmethod
    def _transform_vertex(vertex, transform):
        """Apply the tranformation from a Transform object to a vertex
        :param vertex: A vertex with 3 coordinates, typically (x,y,z)
        :type vertex: sequence
        :param transform: Transform object from CityJSON
        :type transform: dict.
        :return: A vertex with transformed coordinates
        :type return: sequence
        """
        if transform is None:
            return vertex
        else:
            x = deepcopy((vertex[0] * transform["scale"][0]) + transform["translate"][0])
            y = deepcopy((vertex[1] * transform["scale"][1]) + transform["translate"][1])
            z = deepcopy((vertex[2] * transform["scale"][2]) + transform["translate"][2])
            return x,y,z


    @staticmethod
    def _vertex_indexer(geom, vtx_lookup, vtx_idx):
        ret = []
        for g in geom:
            if not isinstance(g, tuple):
                gt = tuple(g)
            else:
                gt = g
            if gt not in vtx_lookup:
                vtx_lookup[gt] = vtx_idx
                ret.append(vtx_idx)
                vtx_idx += 1
            else:
                ret.append(vtx_lookup[gt])
        return (ret, vtx_lookup, vtx_idx)

    def transform(self, transform: dict):
        """Apply coordinate transformation to the boundary

        :param transform: `Transform object <https://www.cityjson.org/specs/latest/#transform-object>`__ from CityJSON
        :return: A copy of the Geometry object with a boundary with transformed coordinates
        """
        vertices = None
        self_cp = deepcopy(self)
        if not self_cp.boundaries:
            return self_cp
        if self_cp.type.lower() == 'multipoint':
            self_cp.boundaries = self_cp._vertex_mapper(self_cp.boundaries, vertices, transform)
        elif self_cp.type.lower() == 'multilinestring':
            self_cp.boundaries = [self_cp._vertex_mapper(ring, vertices, transform) for ring in self_cp.boundaries]
        elif self_cp.type.lower() == 'multisurface' or self_cp.type.lower() == 'compositesurface':
            s = list()
            for surface in self_cp.boundaries:
                s.append([self_cp._vertex_mapper(ring, vertices, transform) for ring in surface])
            self_cp.boundaries = s
        elif self_cp.type.lower() == 'solid':
            sh = list()
            for shell in self_cp.boundaries:
                s = list()
                for surface in shell:
                    s.append([self_cp._vertex_mapper(ring, vertices, transform) for ring in surface])
                sh.append(s)
            self_cp.boundaries = sh
        elif self_cp.type.lower() == 'multisolid' or self_cp.type.lower() == 'compositesolid':
            solids = list()
            for solid in self_cp.boundaries:
                sh = list()
                for shell in solid:
                    s = list()
                    for surface in shell:
                        s.append([self_cp._vertex_mapper(ring, vertices, transform) for ring in surface])
                    sh.append(s)
                solids.append(sh)
            self_cp.boundaries = solids
        return self_cp

    def _dereference_boundaries(self, btype, boundaries, vertices, transform=None):
        """Replace vertex indices with vertex coordinates in the geomery boundary

        :param btype: Boundary type
        :param boundaries: Boundary list
        :param vertices: Vertex list of CityJSON
        :return: Boundary list with the vertex indices replaced with vertex coordinates from the vertex list
        """
        # TODO BD optimize: would be much faster with recursion
        if not boundaries:
            return list()
        if btype.lower() == 'multipoint':
            if not isinstance(boundaries[0], int):
                raise TypeError("Boundary definition does not correspond to MultiPoint")
            return self._vertex_mapper(boundaries, vertices, transform)
        elif btype.lower() == 'multilinestring':
            if not isinstance(boundaries[0][0], int):
                raise TypeError("Boundary definition does not correspond to MultiPoint")
            return [self._vertex_mapper(b, vertices, transform) for b in boundaries]
        elif btype.lower() == 'multisurface' or btype.lower() == 'compositesurface':
            s = list()
            if not isinstance(boundaries[0][0][0], int):
                raise TypeError("Boundary definition does not correspond to MultiSurface or CompositeSurface")
            for surface in boundaries:
                s.append([self._vertex_mapper(ring, vertices, transform) for ring in surface])
            return s
        elif btype.lower() == 'solid':
            sh = list()
            if not isinstance(boundaries[0][0][0][0], int):
                raise TypeError("Boundary definition does not correspond to Solid")
            for shell in boundaries:
                s = list()
                for surface in shell:
                    s.append([self._vertex_mapper(ring, vertices, transform) for ring in surface])
                sh.append(s)
            return sh
        elif btype.lower() == 'multisolid' or btype.lower() == 'compositesolid':
            solids = list()
            if not isinstance(boundaries[0][0][0][0][0], int):
                raise TypeError("Boundary definition does not correspond to MultiSolid or CompositeSolid")
            for solid in boundaries:
                sh = list()
                for shell in solid:
                    s = list()
                    for surface in shell:
                        s.append([self._vertex_mapper(ring, vertices, transform) for ring in surface])
                    sh.append(s)
                solids.append(sh)
            return solids
        else:
            raise TypeError("Unknown geometry type: {}".format(btype))

    def _dereference_surfaces(self, semantics_obj):
        """Dereferene a semantic surface

        :param semantics_obj: Semantic Surface object as extracted from CityJSON file
        """
        semantic_surfaces = dict()
        if not semantics_obj or not semantics_obj['values']:
            return semantic_surfaces
        else:
            srf_idx = self._index_surface_boundaries(semantics_obj['values'])
            for i,srf in enumerate(semantics_obj['surfaces']):
                attributes = dict()
                semantic_surfaces[i] = {'surface_idx': srf_idx[i]}
                for key,value in srf.items():
                    if key == 'type':
                        semantic_surfaces[i]['type'] = value
                    elif key == 'children':
                        semantic_surfaces[i]['children'] = value
                    elif key == 'parent':
                        semantic_surfaces[i]['parent'] = value
                    else:
                        attributes[key] = value
                if len(attributes) > 0:
                    semantic_surfaces[i]['attributes'] = attributes
            return semantic_surfaces

    def _dereference_textures(self, texture_obj, appearance):
        '''
        Creates a mapping from surfaces to associated textures and vertices-texture
        '''
        if texture_obj == None or appearance == None:
            return {}
        texture_idx = {}
        num_surfaces = len(self.boundaries)
        if self.type == 'Solid':
            num_surfaces = len(self.boundaries[0])
        for c in range(num_surfaces):
            t = {}
            for ele in texture_obj:
                textures = texture_obj[ele]['values']
                if self.type == 'Solid':
                    textures = textures[0]
                textures = textures[c]
                d = {'texture':[],'vertices-texture':[]}
                for texture_list in textures:
                    if texture_list == [None]:
                        continue
                    d['texture'].append(appearance['textures'][texture_list[0]])
                    vt = []
                    for i in texture_list[1:]:
                        vt.append(appearance['vertices-texture'][i])
                    d['vertices-texture'].append(vt)
                t[ele] = d
            texture_idx[c] = t
        return texture_idx

    def get_vertices(self):
        """Dump the vertex coordinates into a list"""
        # TODO BD optimize: would be much faster with recursion
        if not self.boundaries:
            return list()
        if self.type.lower() == 'multipoint':
            return self.boundaries
        elif self.type.lower() == 'multilinestring':
            return [b for b in self.boundaries]
        elif self.type.lower() == 'multisurface' or self.type.lower() == 'compositesurface':
            vtx = list()
            for surface in self.boundaries:
                for ring in surface:
                    vtx += ring
            return vtx
        elif self.type.lower() == 'solid':
            vtx = list()
            for shell in self.boundaries:
                for surface in shell:
                    for ring in surface:
                        vtx += ring
            return vtx
        elif self.type.lower() == 'multisolid' or self.type.lower() == 'compositesolid':
            vtx = list()
            for solid in self.boundaries:
                for shell in solid:
                    for surface in shell:
                        for ring in surface:
                            vtx += ring
            return vtx
        else:
            raise TypeError("Unknown geometry type: {}".format(self.type))

    def get_surface_boundaries(self, surface):
        """Get the surface at the index location from the Geometry boundary

        .. note:: Interior surfaces don't have semantics and they are returned with the exterior.

        :param surface: A semantic surface
        :return: Surfaces from the boundary that correspond to the index.
        """
        # TODO BD: essentially, this function is meant to returns a MultiSurface,
        # which is a collection of surfaces that have semantics --> consider returning
        # a Geometry object of MultiSufrace type
        if not isinstance(surface, dict):
            raise TypeError("surface must be a dict")
        if (len(surface) > 0 and 'surface_idx' not in surface):
            raise TypeError("surface must be a single surface")
        if not surface['surface_idx'] or len(surface['surface_idx']) == 0:
            return []
        else:
            return (self.boundaries[i[0]] if len(i) == 1
                    else self.boundaries[i[0]][i[1]] if len(i) == 2
                    else self.boundaries[i[0]][i[1]][i[2]]
                    for i in surface['surface_idx'])

    def build_index(self, vtx_lookup: Mapping=None, vtx_idx: int=0):
        """Build a coordinate list and index the vertices in the boundary.

        This method is used when converting the Geometry to the JSON output.
        """
        vtx_lookup = {} if vtx_lookup is None else vtx_lookup
        if not self.boundaries:
            return ([], vtx_lookup, vtx_idx)
        if self.type.lower() == 'multipoint':
            bdry, vtx_lookup, vtx_idx = self._vertex_indexer(self.boundaries, vtx_lookup, vtx_idx)
            return (bdry, vtx_lookup, vtx_idx)
        elif self.type.lower() == 'multilinestring':
            mline = list()
            for _boundary in self.boundaries:
                bdry, vtx_lookup, vtx_idx = self._vertex_indexer(_boundary, vtx_lookup, vtx_idx)
                mline.append(bdry)
            return (mline, vtx_lookup, vtx_idx)
        elif self.type.lower() == 'multisurface' or self.type.lower() == 'compositesurface':
            msurface = list()
            for _surface in self.boundaries:
                r = list()
                for _ring in _surface:
                    bdry, vtx_lookup, vtx_idx = self._vertex_indexer(_ring, vtx_lookup, vtx_idx)
                    r.append(bdry)
                msurface.append(r)
            return (msurface, vtx_lookup, vtx_idx)
        elif self.type.lower() == 'solid':
            shell = list()
            for _shell in self.boundaries:
                msurface = list()
                for _surface in _shell:
                    r = list()
                    for _ring in _surface:
                        bdry, vtx_lookup, vtx_idx = self._vertex_indexer(_ring, vtx_lookup, vtx_idx)
                        r.append(bdry)
                    msurface.append(r)
                shell.append(msurface)
            return (shell, vtx_lookup, vtx_idx)
        elif self.type.lower() == 'multisolid' or self.type.lower() == 'compositesolid':
            msolid = list()
            for solid in self.boundaries:
                shell = list()
                for _shell in solid:
                    msurface = list()
                    for _surface in _shell:
                        r = list()
                        for _ring in _surface:
                            bdry, vtx_lookup, vtx_idx = self._vertex_indexer(_ring, vtx_lookup, vtx_idx)
                            r.append(bdry)
                        msurface.append(r)
                    shell.append(msurface)
                msolid.append(shell)
            return (msolid, vtx_lookup, vtx_idx)
        else:
            raise TypeError("Unknown geometry type: {}".format(self.type))

    def build_semantic_surface_index(self):
        """Index the semantic surfaces in way that is stored in JSON."""
        # TODO: handle parent-children
        self.semantics['surfaces'] = []
        if self.type.lower() == 'multisurface':
            self.semantics['values'] = [None for i in range(len(self.boundaries))]
        elif self.type.lower() == 'solid':
            self.semantics['values'] = []
            for i in range(len(self.boundaries)):
                self.semantics['values'].append([])
                for j in range(len(self.boundaries[i])):
                    self.semantics['values'][i].append(None)
        else:
            raise ValueError(f"{self.type} is not supported at the moment for semantic surfaces")
        for i,srf in self.surfaces.items():
            _surface = dict()
            _surface['type'] = srf['type']
            if 'attributes' in srf:
                for attr, value in srf['attributes'].items():
                    _surface[attr] = value
                    # TODO: make it work with null-s in semantic surfaces
            self.semantics['surfaces'].append(_surface)
            # TODO: optimize for loop by switching it with the conditional
            for bdry in srf['surface_idx']:
                if len(bdry) == 1:
                    self.semantics['values'][bdry[0]] = i
                elif len(bdry) == 2:
                    self.semantics['values'][bdry[0]][bdry[1]] = i


    def get_surfaces(self, type: str=None, lod: str=None):
        """Get the semantic surfaces of the given type

        The whole boundary is returned if a geometry does not have semantics, or has a LoD < 2,
        or the surface type is not provided.

        :param type: Semantic Surface type. If not provided, the whole boundary is returned.
        :param lod: Level of Detail
        :return: Return a subset of the specific surfaces of the geometry
        """
        if (type is None) or (lod and float(lod) < 2.0) or len(self.surfaces) == 0:
            return self.boundaries
        else:
            return {i:srf for i,srf in self.surfaces.items() if srf['type'].lower() == type.lower()}

    def to_json(self):
        """Return a dict that in the CityJSON schema"""
        j = dict()
        j['type'] = self.type
        j['lod'] = self.lod
        j['boundaries'] = []
        if self.surfaces:
            j['semantics'] = {}
        return j
