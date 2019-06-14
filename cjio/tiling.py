"""Partitioning a CityJSON file"""

import warnings
from typing import List, Tuple, Dict, Iterable, Generator

from cjio.cityjson import CityJSON

def _subdivide_helper_quadtree(bbox: List[float], depth: int, cntr: int) -> List[List]:
    if cntr == depth:
        return bbox
    else:
        cntr += 1
        center_x = (bbox[0] + bbox[3]) / 2
        center_y = (bbox[1] + bbox[4]) / 2
        # need to lift the top a bit, because the top surface is not inclusive in the point_in_bbox
        lifted_top = bbox[5] + (bbox[5] * 0.001)
        sw_0 = [bbox[0], bbox[1], bbox[2], center_x, center_y, bbox[5]]
        se_0 = [center_x, bbox[1], bbox[2], bbox[3], center_y, bbox[5]]
        ne_0 = [center_x, center_y, bbox[2], bbox[3], bbox[4], bbox[5]]
        nw_0 = [bbox[0], center_y, bbox[2], center_x, bbox[4], bbox[5]]
        return [_subdivide_helper_quadtree(nw_0, depth, cntr), _subdivide_helper_quadtree(ne_0, depth, cntr),
                _subdivide_helper_quadtree(sw_0, depth, cntr), _subdivide_helper_quadtree(se_0, depth, cntr)]


def _subdivide_helper_octree(bbox: List[float], depth: int, cntr: int) -> List[List]:
    if cntr == depth:
        return bbox
    else:
        cntr += 1
        center_x = (bbox[0] + bbox[3]) / 2
        center_y = (bbox[1] + bbox[4]) / 2
        center_z = (bbox[2] + bbox[5]) / 2
        sw_0 = [bbox[0], bbox[1], bbox[2], center_x, center_y, center_z]
        se_0 = [center_x, bbox[1], bbox[2], bbox[3], center_y, center_z]
        ne_0 = [center_x, center_y, bbox[2], bbox[3], bbox[4], center_z]
        nw_0 = [bbox[0], center_y, bbox[2], center_x, bbox[4], center_z]
        sw_1 = [bbox[0], bbox[1], center_z, center_x, center_y, bbox[5]]
        se_1 = [center_x, bbox[1], center_z, bbox[3], center_y, bbox[5]]
        ne_1 = [center_x, center_y, center_z, bbox[3], bbox[4], bbox[5]]
        nw_1 = [bbox[0], center_y, center_z, center_x, bbox[4], bbox[5]]
        return [_subdivide_helper_octree(nw_0, depth, cntr), _subdivide_helper_octree(ne_0, depth, cntr),
                _subdivide_helper_octree(sw_0, depth, cntr), _subdivide_helper_octree(se_0, depth, cntr),
                _subdivide_helper_octree(nw_1, depth, cntr), _subdivide_helper_octree(ne_1, depth, cntr),
                _subdivide_helper_octree(sw_1, depth, cntr), _subdivide_helper_octree(se_1, depth, cntr)]

def _subdivide(bbox: List[float], depth: int, octree: bool=False) -> List[List]:
    """Recursively subdivide the BBOX

    :param octree: If True, subdivide in 3D. If False, subdivide in 2D
    """
    if depth != 2:
        raise ValueError("Sorry, at the moment only depth=2 works")
    if octree:
        return _subdivide_helper_octree(bbox, depth, 0)
    else:
        return _subdivide_helper_quadtree(bbox, depth, 0)


def create_grid(bbox: List, depth: int, cellsize: List[float]=None) -> Dict:
    """Create an equal area, rectangular octree or quadtree for the area
    .. note:: Both the quadtree and octree is composed of 3D bounding boxes,
    but in case of the octree the original bbox is also subdivided vertically. In
    case of the quadtree the bbox is partitioned on the xy-plane, while the height
    of each cell equals the height of the original bbox. Finally, this function
    flattens the octree/quadtree into a simple grid.

    .. todo:: implement for cellsize

    :param bbox: Bounding box of the city model
    :param depth: The number of times to subdivide the BBOX of the city model
    :param cellsize: Size of the grid cell. Values are floats and in
     the units of the CRS of the city model. Values are provided as (x, y, z).
     If you don't want to partition the city model with 3D cells, then omit the
     z-value.

    :return: A nested list, containing the bounding boxes of the grid.
    """

    if cellsize:
        raise ValueError("Sorry, at the moment cellsize is not supported")
        dx = bbox[3] - bbox[0]
        dy = bbox[4] - bbox[1]
        dz = bbox[5] - bbox[2]

        if len(cellsize) > 2:
            raise ValueError("Must provide at least 2 values for the cellsize")
        elif len(cellsize) == 2:
            print("2D partitioning")
            in3d = False
        else:
            print("3D partitioning")
            in3d = True
        if dx < cellsize[0] and dy < cellsize[1] and dz < cellsize[2]:
            raise ValueError("Cellsize is larger than bounding box, returning")
    else:
        in3d = False

    tree = _subdivide(bbox, depth, octree=in3d)
    grid = _flatten_grid(tree)
    grid_idx = _generate_index(grid)
    return grid_idx


def _point_in_bbox(bbox: List[float], point: Tuple[float, float, float]) -> bool:
    """Determine if a point is within a bounding box

    Within includes the bottom, south, west face of the cube,
    but does not include the top, north, east face.

    :param bbox: A bounding box as defined in CityJSON
    :param point: A tuple of (x,y,z) coordinates
    """
    if len(point) < 3:
        raise ValueError("Must provide a tuple of (x,y,z) coordinates")
    if len(bbox) < 6:
        raise ValueError("Must provide a valid bbox")
    x_in_cell = bbox[0] <= point[0] < bbox[3]
    y_in_cell = bbox[1] <= point[1] < bbox[4]
    z_in_cell = bbox[2] <= point[2] < bbox[5]
    return x_in_cell and y_in_cell and z_in_cell

def _flatten_grid(grid: List[List]) -> List[List]:
    """Recursively unnest a multi-level list of bbox-es
    .. todo:: only works with depth 2, nothing else...
    """
    if grid == [] or isinstance(grid[0], float):
        return grid
    else:
        return grid[0] + _flatten_grid(grid[1:])

def _generate_index(grid: List[List]) -> Dict:
    """Creates an index for the grid
    .. todo:: maybe use some spatial ordering for naming the cells (eg. Morton)
    """
    return {i: e for i,e in enumerate(grid)}

def _first_vertex(boundary: List) -> int:
    """Finds the index of the vertex in the geometry boundary that encountered first"""
    if isinstance(boundary, int):
        return boundary
    else:
        return _first_vertex(boundary[0])

def partitioner(j: CityJSON, grid_idx: Dict) -> Dict:
    """Assign the CityObjects to the cell they belong

    .. todo:: implement with centroid of the object
    .. todo:: How do we break the CM into partitions? Do we clip the geometry or not? Eg. a TIN must be clipped, but buildings are better as a whole.

    It checks if the first vertex of a CityObject is within a
    cell.

    :param grid_idx: The grid index, returned by `py:func:create_grid`
    :return: A list of CityObject IDs for each cell
    """
    partitions = {idx: [] for idx in grid_idx.keys()}

    try:
        scale = (j.j['transform']['scale'][0],
                 j.j['transform']['scale'][1],
                 j.j['transform']['scale'][2])
        translate = (j.j['transform']['translate'][0],
                     j.j['transform']['translate'][1],
                     j.j['transform']['translate'][2])
    except KeyError:
        scale = (1.0, 1.0, 1.0)
        translate = (0.0, 0.0, 0.0)

    for theid in j.j['CityObjects'].keys():
        for geom in j.j['CityObjects'][theid]['geometry']:
            vi = _first_vertex(geom['boundaries'])
            for idx,bbox in grid_idx.items():
                v = j.j['vertices'][vi]
                x = (v[0] * scale[0]) + translate[0]
                y = (v[1] * scale[1]) + translate[1]
                z = (v[2] * scale[2]) + translate[2]
                if _point_in_bbox(bbox, (x,y,z)):
                    partitions[idx] += [theid]
    return partitions


def compute_obb(bbox):
    """Compute the oriented bounding box for 3dtiles, from the city model's bbox

    The output is an array of 12 numbers that define an oriented bounding box in a
    right-handed 3-axis (x, y, z) Cartesian coordinate system where the z-axis is up.
    The first three elements define the x, y, and z values for the center of the box.
    The next three elements (with indices 3, 4, and 5) define the x-axis direction and half-length.
    The next three elements (indices 6, 7, and 8) define the y-axis direction and half-length.
    The last three elements (indices 9, 10, and 11) define the z-axis direction and half-length.
    """
    obb = [
        bbox[3]/2, bbox[4]/2, bbox[5]/2,
        (bbox[3]-bbox[0])/2, 0, 0,
        0, (bbox[4]-bbox[1])/2, 0,
        0, 0, (bbox[5]-bbox[2])/2
    ]
    return obb


def compute_root_obb(bbox_list):
    """Compute the BBOX for the root node from the BBOXes of the children"""
    bbox = [9e9, 9e9, 9e9, -9e9, -9e9, -9e9]
    for b in bbox_list:
        for i in range(3):
            if b[i] < bbox[i]:
                bbox[i] = b[i]
        for i in range(3,6):
            if b[i] > bbox[i]:
                bbox[i] = b[i]
    return compute_obb(bbox)


def generate_tileset_json():
    """Generate the skeleton for tileset.json"""
    tileset = {
        "asset": { "version": "1.0" },
        "geometricError": 100.0,
        "root": {
            "boundingVolume": {"box": [0.0, 0.0, 0.0,
                                       0.0, 0.0, 0.0,
                                       0.0, 0.0, 0.0,
                                       0.0, 0.0, 0.0]},
            "geometricError": 0.0,
            "refine": "ADD",
            "content": {
                "boundingVolume": {"box": [0.0, 0.0, 0.0,
                                           0.0, 0.0, 0.0,
                                           0.0, 0.0, 0.0,
                                           0.0, 0.0, 0.0]},
                "uri": "root_tile.b3dm"
            },
            "children": []
        }
    }
    return tileset


def generate_tile_json():
    """Generate a skeleton for a tile in a tileset"""
    tile = {
        "boundingVolume": {"box": [0.0, 0.0, 0.0,
                                   0.0, 0.0, 0.0,
                                   0.0, 0.0, 0.0,
                                   0.0, 0.0, 0.0]},
        "geometricError": 0.0,
        "content": {
            "uri": "tile.b3dm"
        }
    }
    return tile

# convert the partitions to b3dm

# convert the BBOX of CityJSON to boundingVolume region

# generate the root tile for the whole city model

# generate tiles for each partition, incl. reporject to EPSG:4979

# assemble