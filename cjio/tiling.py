"""Partitioning a CityJSON file"""

import warnings
from typing import List

from cjio.cityjson import CityJSON

def _subdivide_helper_quadtree(bbox: List[float], iteration: int, cntr: int) -> List[List]:
    if cntr == iteration:
        return bbox
    else:
        cntr += 1
        center_x = (bbox[0] + bbox[3]) / 2
        center_y = (bbox[1] + bbox[4]) / 2
        sw_0 = [bbox[0], bbox[1], bbox[2], center_x, center_y, bbox[2]]
        se_0 = [center_x, bbox[1], bbox[2], bbox[3], center_y, bbox[2]]
        ne_0 = [center_x, center_y, bbox[2], bbox[3], bbox[4], bbox[2]]
        nw_0 = [bbox[0], center_y, bbox[2], center_x, bbox[4], bbox[2]]
        return [_subdivide_helper_quadtree(nw_0, iteration, cntr), _subdivide_helper_quadtree(ne_0, iteration, cntr),
                _subdivide_helper_quadtree(sw_0, iteration, cntr), _subdivide_helper_quadtree(se_0, iteration, cntr)]


def _subdivide_helper_octree(bbox: List[float], iteration: int, cntr: int) -> List[List]:
    if cntr == iteration:
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
        return [_subdivide_helper_octree(nw_0, iteration, cntr), _subdivide_helper_octree(ne_0, iteration, cntr),
                _subdivide_helper_octree(sw_0, iteration, cntr), _subdivide_helper_octree(se_0, iteration, cntr),
                _subdivide_helper_octree(nw_1, iteration, cntr), _subdivide_helper_octree(ne_1, iteration, cntr),
                _subdivide_helper_octree(sw_1, iteration, cntr), _subdivide_helper_octree(se_1, iteration, cntr)]

def _subdivide(bbox: List[float], iteration: int, octree: bool=False) -> List[List]:
    """Recursively subdivide the BBOX

    :param octree: If True, subdivide in 3D. If False, subdivide in 2D
    """
    if octree:
        return _subdivide_helper_octree(bbox, iteration, 0)
    else:
        return _subdivide_helper_quadtree(bbox, iteration, 0)

def create_grid(j: CityJSON, cellsize: List[float]) -> None:
    """Create an equal area, rectangular grid of the given cell size for the area

    :param j: The city model
    :param cellsize: Size of the grid cell. Values are floats and in
     the units of the CRS of the city model. Values are provided as (x, y, z).
     If you don't want to partition the city model with 3D cells, then omit the
     z-value.
    """
    bbox = j.update_bbox()
    dx = bbox[3] - bbox[0]
    dy = bbox[4] - bbox[1]
    dz = bbox[5] - bbox[2]

    if len(cellsize) > 2:
        raise ValueError("Must provide at least 2 values for the cellsize")
    elif len(cellsize) == 2:
        print("2D partitioning")
        cellsize.append(dz)
    else:
        print("3D partitioning")
    if dx < cellsize[0] and dy < cellsize[1] and dz < cellsize[2]:
        raise ValueError("Cellsize is larger than bounding box, returning")




def partitioner():
    """Create a CityJSON for each cell in the partition"""