import os.path
from copy import deepcopy

import pytest

from cjio import errors

def test_get_textures_location_subdir(rotterdam_subset, data_dir):
    """Textures are in a subdirectory to the city model"""
    d = rotterdam_subset.get_textures_location()
    loc = os.path.join(data_dir, 'rotterdam', 'appearances')
    assert d == loc

def test_get_textures_location_same(dummy, data_dir):
    """Textures are in same location with the city model"""
    d = dummy.get_textures_location()
    loc = os.path.join(data_dir, 'dummy')
    assert d == loc

def test_update_textures_relative(rotterdam_subset, data_dir):
    r = deepcopy(rotterdam_subset)
    npath = os.path.join(data_dir, 'rotterdam', 'textures')
    r.update_textures_location(npath, relative=True)
    dirs = []
    for t in r.j["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == 'textures' for p in dirs)

def test_update_textures_absolute(rotterdam_subset, data_dir):
    r = deepcopy(rotterdam_subset)
    npath = os.path.join(data_dir, 'rotterdam', 'textures')
    r.update_textures_location(npath, relative=False)
    dirs = []
    for t in r.j["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == npath for p in dirs)

def test_update_textures_nodir(rotterdam_subset, data_dir):
    r = deepcopy(rotterdam_subset)
    npath = os.path.join(data_dir, 'rotterdam', 'not_existing_dir')
    with pytest.raises(NotADirectoryError):
        r.update_textures_location(npath, relative=False)

def test_update_textures_url(rotterdam_subset):
    r = deepcopy(rotterdam_subset)
    npath = "http://www.balazs.com/images"
    r.update_textures_location(npath, relative=False)
    dirs = []
    for t in r.j["appearance"]["textures"]:
        dirs.append(os.path.dirname(t["image"]))
    assert all(p == npath for p in dirs)

def test_update_textures_none(dummy_noappearance):
    with pytest.raises(errors.InvalidOperation):
        dummy_noappearance.update_textures_location('somepath', relative=True)