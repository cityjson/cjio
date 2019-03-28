import pytest

from cjio import tiling

class TestPartitioning():

    @pytest.mark.parametrize("bbox, iteration", [
        ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], 2),
        ([0.0, 0.0, 0.0, 1.0, 1.0, 0.0], 2),
    ])
    def test_subdivide(self, bbox, iteration):
        octree = tiling._subdivide(bbox, iteration, octree=True)
        # some random tests
        # ne_1[ne_1] top corner
        assert octree[5][5][3:] == bbox[3:]
        # ne_1[ne_0] z-value
        assert octree[5][1][5] == bbox[5] - (bbox[5] / 2**iteration)


    def test_grid1(self, rectangle):
        """Test that each cell has the required size"""
        quadtree = tiling.create_grid(rectangle, nr_divisions=3)
        # test with sth WGS84

    def test_grid2(self, rotterdam_subset):
        """Test that each cell has the required size"""
        # test with RDNew
        quadtree = tiling.create_grid(rotterdam_subset, nr_divisions=3)

    @pytest.mark.parametrize("point, result", [
        ((0.5, 0.5, 0.5), True),
        ((0.0, 0.01, 0.5), True),
        ((1.0, 0.75, 0.5), False),
        ((1.1, 0.75, 1.5), False)
    ])
    def test_point_in_cell(self, point, result):
        """Test that a point is within the bbox of a cell"""
        bbox = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        assert tiling.point_in_bbox(bbox, point) == result

    def test_partitioner(self):
        """Test if the city model is partitioned according to the grid"""
        pytest.fail("Not implemented")