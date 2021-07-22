import os
import os.path
from click.testing import CliRunner
import json
from cjio import cjio


class TestCLI:
    """assign_epsg"""
    def test_assign_epsg_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'assign_epsg.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'assign_epsg', '4326', 
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    
    """clean"""
    def test_clean_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'clean.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'clean',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    
    """export"""
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
        
    def test_export_stl_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'delft.stl')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'export',
                                     '--format', 'stl',
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
    
    
    """filter_lod"""
    def test_filter_lod_cli(self, multi_lod_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'filter_lod.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[multi_lod_path,
                                     'filter_lod', '1.2',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """get_metadata"""
    def test_get_metadata_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'get_metadata'])
        
        assert result.exit_code == 0    
    
    
    """info"""
    def test_info_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'info'])
        
        assert result.exit_code == 0    
    
    
    """locate_textures"""
    def test_locate_textures_cli(self, rotterdam_subset_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'locate_textures'])
        
        assert result.exit_code == 0    
    
    
    """merge"""
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
    
    
    """remove_attribute"""
    def test_remove_attribute_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'remove_attribute.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'remove_attribute', 'bgt_status',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """remove_duplicate_vertices"""
    def test_remove_duplicate_vertices_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'remove_duplicate_vertices.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'remove_duplicate_vertices',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """remove_materials"""
    def test_remove_materials_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'remove_materials.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'remove_materials',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """remove_orphan_vertices"""
    def test_remove_orphan_vertices_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'remove_orphan_vertices.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'remove_orphan_vertices',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """remove_textures"""
    def test_remove_textures_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'remove_textures.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'remove_textures',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """rename_attribute"""
    def test_rename_attribute_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'rename_attribute.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'rename_attribute', 'hoek', 'angle',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """reproject"""
    def test_reproject_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'reproject.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'reproject', '4326',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """save"""
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
    
    
    """subset"""
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
    
    
    """subset"""
    def test_subset_bbox_cli(self, zurich_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'subset_bbox.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[zurich_subset_path,
                                     'subset', '--bbox',
                                     '2678219.194', '1243078.7249999999', '2682811.964', '1248058.2475',
                                     'save',
                                     p_out])
    
        print(result.stdout_bytes)
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """subset"""
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
    
    
    """subset"""
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


    """translate"""
    def test_translate_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'translate.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'translate',
                                     '--values', '-1', '-1', '-1',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """update_metadata"""
    def test_update_metadata_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'update_metadata.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'update_metadata',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """update_textures"""
    def test_update_textures_cli(self, rotterdam_subset_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'update_textures.json')
        t_path = os.path.join(os.path.dirname(rotterdam_subset_path), 'appearances_test')
        os.makedirs(t_path, exist_ok=True)
        
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[rotterdam_subset_path,
                                     'update_textures', t_path,
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
        os.rmdir(t_path)
    
    
    """upgrade_version"""
    def test_upgrade_version_cli(self, delft_path, data_output_dir):
        p_out = os.path.join(data_output_dir, 'upgrade_version.json')
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'upgrade_version',
                                     'save',
                                     p_out])
        
        assert result.exit_code == 0
        assert os.path.exists(p_out) == True
        
        os.remove(p_out)
    
    
    """validate"""
    def test_validate_cli(self, delft_path):
        runner = CliRunner()
        result = runner.invoke(cjio.cli,
                               args=[delft_path,
                                     'validate'])
        
        assert result.exit_code == 0
        
