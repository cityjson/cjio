import os.path
import pytest
from click import ClickException

from cjio import utils


@pytest.fixture(scope='session',
                params=[("doesnt_exist.json", False),
                        ("example_data/rotterdam", True),
                        ("example_data/rotterdam/", True),
                        ("example_data/delft.json", False),
                        ("example_data/doesnt_exist", True)
])
def valid_path(request):
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield (os.path.join(package_dir, request.param[0]), request.param[1])

@pytest.fixture(scope='session',
                params=[("example_data/doesnt_exist/doesnt_exist.json", False),
                        ("example_data/doesnt_exist/other_dir", True)
])
def invalid_path(request):
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield (os.path.join(package_dir, request.param[0]), request.param[1])


class TestFileNamesPaths():

    def test_verify_filenames_valid(valid_path):
        res = utils.verify_filename(valid_path[0])
        assert res['dir'] == valid_path[1]

    def test_verify_filenames_invalid(invalid_path):
        with pytest.raises(ClickException) as e:
            utils.verify_filename(invalid_path[0])

    def test_file(self, data_dir):
        """When the user passes a path to a file as output"""
        extension = 'b3dm'
        p = os.path.join(data_dir, 'delft.json')
        filepath = utils.generate_filepath(p, extension)
        pass

    def test_dir(self, data_dir):
        """When the user passes a path to a directory as output"""
        extension = 'b3dm'
        filepath = utils.generate_filepath(data_dir, extension)
        pass

    def test_partitioned_file(self, data_dir):
        """User passed a path to a file, but the input is partitioned"""
        pass

    def test_partitioned_dir(self, data_dir, data_output_dir):
        """User passed a path to a directory, but the input is partitioned"""
        pass