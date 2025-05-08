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
        assert "Options" in result.output

    def test_help_subcommand_cli(self):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=["validate", "--help"])
        assert result.exit_code == 0
        assert "Options" in result.output

    def test_attribute_remove_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "attribute_remove.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[sample_input_path, "attribute_remove", "bgt_status", "save", p_out],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_attribute_rename_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "attribute_rename.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                sample_input_path,
                "attribute_rename",
                "hoek",
                "angle",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_crs_assign_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "crs_assign.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "crs_assign", "4326", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_crs_reproject_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "crs_reproject.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                sample_input_path,
                "crs_reproject",
                "--digit",
                "7",
                "4979",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_crs_translate_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "crs_translate.city.json")
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

    def test_export_obj_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.obj")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "export", "obj", p_out]
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_glb_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.glb")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "export", "glb", p_out]
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_b3dm_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.b3dm")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "export", "b3dm", p_out]
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_stl_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.stl")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "export", "stl", p_out]
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_jsonl_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "delft.city.jsonl")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "export", "jsonl", p_out]
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_export_wrong_file_cli(self, wrong_input_path):
        p_out = os.path.join("tests", "data", "delft_non.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[wrong_input_path, "export", "jsonl", p_out]
        )

        assert not os.path.exists(p_out)
        assert result.exit_code != 0

    def test_info_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "info"])

        assert result.exit_code == 0

    def test_lod_filter_cli(self, multi_lod_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "filtered_lod.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[multi_lod_path, "lod_filter", "1.2", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)
        assert "1.2" in result.output

        os.remove(p_out)

    def test_materials_remove_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "materials_remove.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[rotterdam_subset_path, "materials_remove", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_merge_cli(self, sample_input_path, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "merge.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[sample_input_path, "merge", rotterdam_subset_path, "save", p_out],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_metadata_extended_remove_cli(
        self, sample_with_ext_metadata_input_path, data_output_dir
    ):
        p_out = os.path.join(data_output_dir, "cleaned_file.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                sample_with_ext_metadata_input_path,
                "metadata_extended_remove",
                "save",
                p_out,
            ],
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_metadata_get_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "metadata_get"])

        assert result.exit_code == 0

    def test_print_cli(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "print"])
        assert result.exit_code == 0
        assert result.exit_code == 0
        assert "CityJSON" in result.output
        assert "EPSG" in result.output

    def test_save_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "save.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "save", "--indent", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_save_with_texture_cli(
        self, rotterdam_subset_path, data_output_dir, temp_texture_dir
    ):
        p_out = os.path.join(data_output_dir, "save_texture.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "save",
                "--textures",
                temp_texture_dir,
                "--indent",
                p_out,
            ],
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        result2 = runner.invoke(
            cjio.cli,
            args=[
                p_out,
                "textures_locate",
            ],
        )
        assert result2.exit_code == 0
        assert temp_texture_dir in result2.output

        os.remove(p_out)

    def test_subset_id_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "subset.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "subset",
                "--id",
                "{23D8CA22-0C82-4453-A11E-B3F2B3116DB4}",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_subset_bbox_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "subset_bbox.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "subset",
                "--bbox",
                90970,
                435620,
                91000,
                435650,
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_subset_radius_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "subset_radius.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "subset",
                "--radius",
                90970,
                435620,
                20.0,
                "--exclude",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_subset_random_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "subset_random.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "subset",
                "--random",
                3,
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_subset_cotype_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "subset_cotype.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                sample_input_path,
                "subset",
                "--cotype",
                "Bridge",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_textures_locate_cli_no_textures(self, sample_input_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "textures_locate"])

        assert result.exit_code == 0
        assert "This file does not have textures" in result.output

    def test_textures_locate_cli_with_textures(self, rotterdam_subset_path):
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[rotterdam_subset_path, "textures_locate"]
        )

        assert result.exit_code == 0
        assert "rotterdam/appearances" in result.output

    def test_textures_remove_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "textures_remove.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[rotterdam_subset_path, "textures_remove", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        result2 = runner.invoke(cjio.cli, args=[p_out, "textures_locate"])

        assert result2.exit_code == 0
        assert "This file does not have textures" in result2.output

        os.remove(p_out)

    def test_textures_update_cli(
        self, rotterdam_subset_path, data_output_dir, temp_texture_dir
    ):
        p_out = os.path.join(data_output_dir, "updated_textures.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "textures_update",
                temp_texture_dir,
                "save",
                p_out,
            ],
        )
        assert result.exit_code == 0
        assert os.path.exists(p_out)

        result2 = runner.invoke(cjio.cli, args=[p_out, "textures_locate"])

        assert result2.exit_code == 0
        assert temp_texture_dir in result2.output

        os.remove(p_out)

    def test_triangulate_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "triangulated.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "triangulate", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_triangulate_sloppy_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "triangulated.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "triangulate", "--sloppy", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_upgrade_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "upgrade.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "upgrade", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_validate_cli(self, sample_input_path):
        if not cityjson.MODULE_CJVAL_AVAILABLE:  # pragma: no cover
            pytest.skip("cjvalpy module not available")
        runner = CliRunner()
        result = runner.invoke(cjio.cli, args=[sample_input_path, "validate"])

        assert result.exit_code == 0

    def test_vertices_clean_cli(self, sample_input_path, data_output_dir):
        p_out = os.path.join(data_output_dir, "clean.city.json")
        runner = CliRunner()
        result = runner.invoke(
            cjio.cli, args=[sample_input_path, "vertices_clean", "save", p_out]
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_chained_commands_cli(self, rotterdam_subset_path, data_output_dir):
        """
        Test chaining multiple commands to ensure process_pipeline is invoked correctly.
        """
        p_out = os.path.join(data_output_dir, "pipeline_output.city.json")
        runner = CliRunner()

        result = runner.invoke(
            cjio.cli,
            args=[
                rotterdam_subset_path,
                "subset",
                "--id",
                "{23D8CA22-0C82-4453-A11E-B3F2B3116DB4}",
                "vertices_clean",
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_off_input_cli(self, sample_off_file, data_output_dir):
        """
        Test that the CLI works with a .off input file."""
        p_out = os.path.join(data_output_dir, "box.city.json")
        runner = CliRunner()

        result = runner.invoke(
            cjio.cli,
            args=[
                sample_off_file,
                "save",
                p_out,
            ],
        )

        assert result.exit_code == 0
        assert os.path.exists(p_out)

        os.remove(p_out)

    def test_wrong_extension_cli(self, sample_wrong_suffix):
        """
        Test that the CLI gives a warning when the file extension is not supported.
        """
        runner = CliRunner()

        result = runner.invoke(
            cjio.cli,
            args=[
                sample_wrong_suffix,
                "subset",
                "--id",
                "{23D8CA22-0C82-4453-A11E-B3F2B3116DB4}",
                "vertices_clean",
                "save",
                "output.city.json",
            ],
        )
        assert result.exit_code != 0
        assert "File type not supported" in result.output
