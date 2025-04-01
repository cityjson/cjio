import os.path
import pytest
from click import ClickException

from cjio import utils


@pytest.fixture(
    scope="session",
    params=[
        ("doesnt_exist.json", False),
        ("tests/data/rotterdam", True),
        ("tests/data/rotterdam/", True),
        ("tests/data/delft.json", False),
        ("tests/data/doesnt_exist", True),
    ],
)
def valid_path(request):
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield (os.path.join(package_dir, request.param[0]), request.param[1])


@pytest.fixture(
    scope="session",
    params=[
        ("tests/data/doesnt_exist/doesnt_exist.json", False),
        ("tests/data/doesnt_exist/other_dir", True),
    ],
)
def invalid_path(request):
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield (os.path.join(package_dir, request.param[0]), request.param[1])


class TestFileNamesPaths:
    def test_verify_filenames_valid(self, valid_path):
        res = utils.verify_filename(valid_path[0])
        assert res["dir"] == valid_path[1]

    def test_verify_filenames_invalid(self, invalid_path):
        with pytest.raises(ClickException):
            utils.verify_filename(invalid_path[0])
