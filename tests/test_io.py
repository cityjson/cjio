"""Test loading, saving and exporting cityjson files

"""
import os

import pytest

from cjio import cityjson

class TestLoading:
    @pytest.mark.parametrize("file", (
        ('rotterdam', 'rotterdam_subset.json'),
        ('dummy', 'dummy.json') # Issue #19 with loading GeometryInstance
    ))
    def test_from_path(self, data_dir, file):
        p = os.path.join(data_dir, *file)
        cm = cityjson.load(p)
        assert hasattr(cm, 'cityobjects')
        # assert '{71B60053-BC28-404D-BAB9-8A642AAC0CF4}' in cm.cityobjects

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

    def test_to_dataframe(self, data_dir):
        p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
        cm = cityjson.load(p)
        df = cm.to_dataframe()
        assert len(df) == len(cm.cityobjects)
