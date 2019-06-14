import os.path

import pytest

from cjio import cityjson


@pytest.fixture(scope='session')
def data_dir():
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield os.path.join(package_dir, 'example_data')

@pytest.fixture(scope='session')
def data_output_dir():
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    d = os.path.join(package_dir, "tmp")
    os.makedirs(d, exist_ok=True)
    yield d

@pytest.fixture(scope='session')
def delft(data_dir):
    p = os.path.join(data_dir, 'delft.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def rotterdam_subset(data_dir):
    p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def zurich_subset(data_dir):
    p = os.path.join(data_dir, 'zurich', 'zurich_subset_lod2.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def dummy(data_dir):
    p = os.path.join(data_dir, 'dummy', 'dummy.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def dummy_noappearance(data_dir):
    p = os.path.join(data_dir, 'dummy', 'dummy_noappearance.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def cube(data_dir):
    p = os.path.join(data_dir, 'dummy', 'cube.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def rectangle(data_dir):
    p = os.path.join(data_dir, 'dummy', 'rectangle.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def vertices():
    yield  [
        (0.0,1.0,0.0),
        (1.0,1.0,0.0),
        (2.0,1.0,0.0),
        (3.0,1.0,0.0),
        (4.0,1.0,0.0),
        (5.0,1.0,0.0)
    ]