import pytest

from cjio import tiling


class TestPartitioning:

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
        quadtree = tiling.create_grid(rectangle, depth=3)
        # test with sth WGS84

    def test_grid2(self, rotterdam_subset):
        """Test that each cell has the required size"""
        # test with RDNew
        quadtree = tiling.create_grid(rotterdam_subset, depth=3)

    @pytest.mark.parametrize("bbox, point, result", [
        ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], (0.5, 0.5, 0.5), True),
        ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], (0.0, 0.01, 0.5), True),
        ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], (1.0, 0.75, 0.5), False),
        ([0.0, 0.0, 0.0, 1.0, 1.0, 1.0], (1.1, 0.75, 1.5), False),
        ([90865.3615, 435614.88, 0.0, 91002.41900000001, 435723.21425, 18.29],
         (90966.26400000001, 435676.738, 15.581),
         True)
    ])
    def test_point_in_bbox(self, bbox, point, result):
        """Test that a point is within the bbox of a cell"""
        assert tiling._point_in_bbox(bbox, point) == result


    @pytest.mark.parametrize("in3d, depth", [
        (True, 1),
        (False, 1),
        (True, 2),
        (False, 2),
        (True, 3),
        (False, 3)
    ])
    def test_flatten_grid(self, in3d, depth):
        bbox = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        base = 8 if in3d else 4
        grid = tiling._subdivide(bbox, depth, octree=in3d)
        partition = tiling._flatten_grid(grid)
        assert len(partition) == base**depth

    def test_generate_index(self):
        grid = [[1], [2], [3], [4], [5]]
        print(tiling._generate_index(grid))

    @pytest.mark.parametrize("boundary", [
        [2, 44, 0, 7],
        [[2, 3, 5], [77, 55, 212]],
        [[[0, 3, 2, 1]], [[4, 5, 6, 7]], [[0, 1, 5, 4]]],
        [[[[0, 3, 2, 1, 22]], [[4, 5, 6, 7]], [[0, 1, 5, 4]], [[1, 2, 6, 5]]], [[[240, 243, 124]], [[244, 246, 724]], [[34, 414, 45]], [[111, 246, 5]]]]
    ])
    def test_first_vertex(self, boundary):
        assert isinstance(tiling._first_vertex(boundary), int)

    def test_partitioner(self, rotterdam_subset):
        """Test if the city model is partitioned according to the grid"""
        pytest.fail("Not implemented")

class Test3DTiles:

    def test_tileset_json(self):
        tileset = tiling.generate_tileset_json()
        top_level = ['asset', 'geometricError', 'root']
        assert sorted(tileset.keys()) == sorted(top_level)