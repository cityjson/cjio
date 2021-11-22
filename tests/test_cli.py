import os
import os.path
from click.testing import CliRunner
import json
from cjio import cjio


class TestCLI:
    def test_crs_assign_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'crs_assign.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'crs_assign', '4326', 
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_vertices_clean_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'clean.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'vertices_clean',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_export_jsonl_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'delft.jsonl')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'export',
                                     '--format', 'jsonl',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        with open(p_out, 'r') as f:
            for l in f.readlines():
                # Check if valid JSON
                json.loads(l)
                
        os.remove(p_out)
                
    def test_export_glb_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'delft.glb')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'export',
                                     '--format', 'glb',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
        
    def test_export_b3dm_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'delft.b3dm')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'export',
                                     '--format', 'b3dm',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
        
    def test_export_obj_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'delft.obj')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'export',
                                     '--format', 'obj',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
    
        os.remove(p_out)
    
    def test_lod_filter_cli(self, multi_lod_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'lod_filter.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[multi_lod_path,
                                     'lod_filter', '1.2',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_metadata_get_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'metadata_get'])
        
        assert result.exit_code == 0    
    
    def test_info_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'info'])
        
        assert result.exit_code == 0    
    
    def test_textures_locate_cli(self, rotterdam_subset_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'textures_locate'])
        
        assert result.exit_code == 0    
    
    def test_merge_cli(self, delft_path, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'merge.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'merge', rotterdam_subset_path,
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_attribute_remove_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'attribute_remove.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'attribute_remove', 'bgt_status',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
        
    def test_materials_remove_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'materials_remove.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'materials_remove',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_textures_remove_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'textures_remove.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'textures_remove',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_attribute_rename_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'attribute_rename.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'attribute_rename', 'hoek', 'angle',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_save_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'save.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'save', '--indent',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_subset_ids_cli(self, zurich_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'subset_ids.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[zurich_subset_path,
                                     'subset',
                                     '--id', 'UUID_583c776f-5b0c-4d42-9c37-5b94e0c21a30',
                                     '--id', 'UUID_60ae78b4-7632-49ca-89ed-3d1616d5eb80',
                                     '--id', 'UUID_5bd1cee6-b3f0-40fb-a6ae-833e88305e31',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_subset_random_cli(self, zurich_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'subset_random.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[zurich_subset_path,
                                     'subset', '--random',
                                     '10',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_subset_cotype_cli(self, zurich_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'subset_cotype.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[zurich_subset_path,
                                     'subset', '--cotype',
                                     'Building',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)

    def test_crs_translate_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'crs_translate.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'crs_translate',
                                     '--values', '-1', '-1', '-1',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_metadata_update_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'metadata_update.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'metadata_update',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    def test_textures_update_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'textures_update.json')
        t_path = os.path.join(os.path.dirname(rotterdam_subset_path), 'appearances_test')
        os.makedirs(t_path, exist_ok=True)
        
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'textures_update', t_path,
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
        os.rmdir(t_path)

    def test_upgrade_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'upgrade.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'upgrade',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)

    def test_validate_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'validate'])
        
        assert result.exit_code == 0
        
