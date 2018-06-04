import os.path

import pytest

def test_get_texture_location_subdir(rotterdam_subset):
    d = rotterdam_subset.get_texture_location()
    loc = os.path.abspath('example_data/rotterdam/appearances')
    assert d == loc

def test_get_texture_location_same(dummy):
    d = dummy.get_texture_location()
    loc = os.path.abspath('example_data/dummy')
    assert d == loc