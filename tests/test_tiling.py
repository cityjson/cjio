import pytest

from cjio import tiling

def test_grid():
    """Test that each cell has the required size"""
    cellsize = (50, 50)
    grid = tiling.create_grid(cellsize)
    print(grid)
    pytest.fail("Not implemented")


def test_partitioner():
    """Test if the city model is partitioned according to the grid"""
    pytest.fail("Not implemented")