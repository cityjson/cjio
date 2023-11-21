import typing as t

import numpy as np
import numpy.typing as npt
import pytest

from cjio.geom_help import get_normal_newell


@pytest.mark.parametrize(
    ["poly", "expected_normal"],
    [
        (
            [
                [2195013, 353200, 12283],
                [2195013, 353200, 8680],
                [2182302, 347931, 8680],
                [2182302, 347931, 12159],
                [2182302, 347931, 12178],
            ],
            np.array([-0.38292729, 0.92377848, 0.0]),
        ),
        (
            [
                [2203406, 332904, 12622],
                [2203406, 332904, 8680],
                [2204954, 333543, 8680],
                [2204954, 333543, 12223],
                [2204954, 333543, 12584],
            ],
            np.array([0.38156054, -0.92434385, 0.0]),
        ),
    ],
)
def test_get_normal_valid_poly(poly: t.List[t.List[int]], expected_normal: npt.NDArray[t.Any]) -> None:
    normal, success = get_normal_newell(poly=poly)
    assert success
    np.testing.assert_almost_equal(actual=normal, desired=expected_normal)


@pytest.mark.parametrize(
    ["poly", "expected_normal"],
    [
        (
            [[1041, 1009, 1025, 1054, 1087]],
            np.array([0.0, 0.0, 0.0]),
        ),
        (
            [[[1099, 1098]]],
            np.array([0.0, 0.0, 0.0]),
        ),
    ],
)
def test_get_normal_invalid_poly(poly: t.List[t.List[int]], expected_normal: npt.NDArray[t.Any]) -> None:
    normal, success = get_normal_newell(poly=poly)
    assert not success
    np.testing.assert_almost_equal(actual=normal, desired=expected_normal)
