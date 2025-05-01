import os
import os.path
from click.testing import CliRunner
from cjio import cjio, cityjson, __version__
import pytest


class TestCLI:
    def test_version_cli(self):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output

    def test_help_cli(self):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=["--help"])
        assert result.exit_code == 0

    def test_print_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "print"]
        )
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert result.exit_code == 0
        assert "CityJSON" in result.output
        assert "EPSG" in result.output

    def test_info_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "info"]
        )
        print(sample_input_path)
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
    
    def test_crs_assign_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "crs_assign.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "crs_assign", "4326", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_vertices_clean_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "clean.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "vertices_clean", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_obj_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.obj")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "export", "obj", p_out])
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_glb_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.glb")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "export", "glb", p_out])
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_b3dm_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.b3dm")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "export", "b3dm", p_out])
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_stl_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.stl")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "export", "stl", p_out])
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_jsonl_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.city.jsonl")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "export", "jsonl", p_out])
        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_wrong_file_cli(self, wrong_input_path):
        p_out = os.path.join("tests", "data", "delft_non.json")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[wrong_input_path, "export", "jsonl", p_out])
        print(f"CLI returned '{result.output}'")
        assert not os.path.exists(p_out)
        assert result.exit_code != 0

    def test_metadata_get_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "metadata_get"])

        assert result.exit_code == 0


    def test_merge_cli(self, sample_input_path, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "merge.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "merge", rotterdam_subset_path, "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_attribute_remove_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "attribute_remove.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "attribute_remove", "bgt_status", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_textures_remove_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "textures_remove.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[rotterdam_subset_path, "textures_remove", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_attribute_rename_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "attribute_rename.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[sample_input_path, "attribute_rename", "hoek", "angle", "save", p_out],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_save_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "save.json")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "save", "--indent", p_out])

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_crs_translate_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "crs_translate.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                sample_input_path,
                "crs_translate",
                "--minxyz",
                "-1",
                "-1",
                "-1",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_upgrade_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "upgrade.json")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "upgrade", "save", p_out])

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_validate_cli(self, sample_input_path):
        if not cityjson.MODULE_CJVAL_AVAILABLE:  # pragma: no cover
            pytest.skip("cjvalpy module not available")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "validate"])

        print(f"CLI returned '{result.output}'")
        assert result.exit_code == 0
