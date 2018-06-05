import os.path
from copy import deepcopy

import pytest
from tests.conftest import rotterdam_subset

from cjio import errors

def test_get_textures_location_subdir(rotterdam_subset):
    """Textures are in a subdirectory to the city model"""
    d = rotterdam_subset.get_textures_location()
    loc = os.path.abspath('example_data/rotterdam/appearances')
    assert d == loc

def test_get_textures_location_same(dummy):
    """Textures are in same location with the city model"""
    d = dummy.get_textures_location()
    loc = os.path.abspath('example_data/dummy')
    assert d == loc

def test_update_textures_relative(rotterdam_subset):
#     r = deepcopy(rotterdam_subset)
    npath = os.path.abspath('example_data/rotterdam/textures')
    rotterdam_subset.update_textures_location(npath, relative=True)
    dirs = []
    for t in ["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == 'textures' for p in dirs)
    print(rotterdam_subset.get_textures_location())

def test_update_textures_absolute(rotterdam_subset):
    npath = os.path.abspath('example_data/rotterdam/textures')
    rotterdam_subset.update_textures_location(npath, relative=False)
    dirs = []
    for t in ["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == npath for p in dirs)

def test_update_textures_url(rotterdam_subset):
    npath = "http://www.balazs.com/images"
    rotterdam_subset.update_textures_location(npath, relative=False)
    dirs = []
    for t in ["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == npath for p in dirs)

def test_update_textures_none(dummy_noappearance):
    with pytest.raises(errors.InvalidOperation):
        dummy_noappearance.update_textures_location('somepath', relative=True)