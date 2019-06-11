"""Test loading, saving and exporting cityjson files

"""
import os
from cjio import cityjson
from cjio.models import CityObject, Geometry

class TestLoading:
    def test_from_path(self, data_dir):
        p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
        cm = cityjson.load(p)
        assert hasattr(cm, 'cityobjects')
        assert '{71B60053-BC28-404D-BAB9-8A642AAC0CF4}' in cm.cityobjects

class TestExport:
    def test_save_to_path(self, data_dir):
        p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
        cm = cityjson.load(p)
        new_cos = {}
        for co_id, co in cm.cityobjects.items():
            co.attributes['cjio_test'] = 'made by Balázs'
            new_cos[co_id] = co
        cm.cityobjects = new_cos
        p_out = os.path.join(data_dir, 'rotterdam_subset_cjio_test.json')
        cityjson.save(cm, p_out)
