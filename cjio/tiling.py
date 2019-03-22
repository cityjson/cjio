"""Partitioning a CityJSON file"""

def create_grid(cellsize: tuple(int, int)):
    """Create an equal area, rectangular grid of the given cell size for the area

    :param cellsize: Size of the grid cell. Values are integers and in
     the units of the CRS of the city model. Values are provided as (x, y)
    """

def partitioner():
    """Create a CityJSON for each cell in the partition"""