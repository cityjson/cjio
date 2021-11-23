import os.path
from click.testing import CliRunner

from cjio import convert
from cjio import cjio


class TestGltf:

    def test_convert_to_glb(self, delft):
        glb = convert.to_glb(delft.j)


class TestB3dm:

    def test_convert_to_b3dm(self, delft):
        glb = convert.to_glb(delft.j)
        b3dm = convert.to_b3dm(delft, glb)


class Test3dtiles:

    def test_export_3dtiles_cmd(self, data_dir, data_output_dir):
        """Debugging"""
        p = os.path.join(data_dir, 'delft.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[p,
                                     'export',
                                     '--format', '3dtiles',
                                     data_output_dir])

    def test_export_3dtiles_partition_cmd(self, data_dir, data_output_dir):
        """Debugging"""
        p = os.path.join(data_dir, 'delft.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[p,
                                     'partition',
                                     'export',
                                     '--format', '3dtiles',
                                     data_output_dir])