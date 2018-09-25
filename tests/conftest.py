import os.path

import pytest

from cjio import cityjson


@pytest.fixture(scope='session')
def data_dir():
    yield os.path.abspath('example_data')

@pytest.fixture(scope='session')
def rotterdam(data_dir):
    p = os.path.join(data_dir, 'rotterdam', '3-20-DELFSHAVEN_uncompressed.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def rotterdam_subset(data_dir):
    p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
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

