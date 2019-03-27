import pytest

from cjio import tiling

@pytest.mark.parametrize("bbox, iteration", [
    ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], 2),
    ([0.0, 0.0, 0.0, 1.0, 1.0, 0.0], 2),
])
def test_subdivide(bbox, iteration):
    octree = tiling._subdivide(bbox, iteration, octree=True)
    # some random tests
    # ne_1[ne_1] top corner
    assert octree[5][5][3:] == bbox[3:]
    # ne_1[ne_0] z-value
    assert octree[5][1][5] == bbox[5] - (bbox[5] / 2**iteration)



def test_grid(rectangle):
    """Test that each cell has the required size"""
    cellsize = (0.25, 0.25)
    grid = tiling.create_grid(rectangle, cellsize)
    print(grid)
    # test with sth WGS84
    # test with RDNew
    pytest.fail("Not implemented")


def test_partitioner():
    """Test if the city model is partitioned according to the grid"""
    pytest.fail("Not implemented")