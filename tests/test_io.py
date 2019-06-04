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
