import os.path
import pytest
from click.testing import CliRunner

from cjio import convert
from cjio import cjio


class TestGltf:

    def test_convert_to_gltf(self, delft):
        out_gltf, out_bin = convert.to_gltf(delft.j)

    def test_export_gltf_cmd(self, data_dir, data_output_dir):
        """Debugging"""
        p = os.path.join(data_dir, 'delft.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[p,
                                     'export',
                                     '--format', 'gltf',
                                     data_output_dir])


class TestB3dm:

    def test_convert_to_b3dm(self, delft):
        out_gltf, out_bin = convert.to_gltf(delft.j)
        b3dm = convert.to_b3dm(delft, out_bin)