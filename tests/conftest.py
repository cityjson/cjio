import os.path
import pickle

import pytest

from cjio import cityjson

#------------------------------------ add option for running the full test set
def pytest_addoption(parser):
    parser.addoption("--balazs", action="store_true",
                     default=False, help="run tests against Balázs' local data")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--balazs"):
        return
    skip_balazs = pytest.mark.skip(reason="need --balazs option to run")
    for item in items:
        if "balazs" in item.keywords:
            item.add_marker(skip_balazs)

@pytest.fixture(scope='session')
def data_dir():
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield os.path.join(package_dir, 'tests', 'data')

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
def delft_1b(data_dir):
    p = os.path.join(data_dir, 'delft_1b.json')
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

@pytest.mark.balazs
@pytest.fixture(scope='function')
def ms_triangles(data_dir):
    """Long list of triangulated MultiSurfaces with EPSG:7514 corodinates."""
    p = os.path.join(data_dir, 'multisurface_triangulated.pickle')
    with open(p, 'rb') as fo:
        yield pickle.load(fo)

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
    p = os.path.join(data_dir, 'cube.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def cube_compressed(data_dir):
    p = os.path.join(data_dir, 'cube.c.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def minimal(data_dir):
    p = os.path.join(data_dir, 'minimal.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def rectangle(data_dir):
    p = os.path.join(data_dir, 'dummy', 'rectangle.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='session')
def vertices():
    yield [
        (0.0,1.0,0.0),
        (1.0,1.0,0.0),
        (2.0,1.0,0.0),
        (3.0,1.0,0.0),
        (4.0,1.0,0.0),
        (5.0,1.0,0.0)
    ]


@pytest.fixture(scope='session')
def materials(data_dir):
    p1 = os.path.join(data_dir, 'material', 'mt-1.json')
    p2 = os.path.join(data_dir, 'material', 'mt-2.json')
    cj = []
    for p in (p1, p2):
        with open(p, 'r') as f:
            cj.append(cityjson.CityJSON(file=f))
    return cj


@pytest.fixture(scope='session')
def mt_1_path(data_dir):
    return os.path.join(data_dir, 'material', 'mt-1.json')
