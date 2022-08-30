import os.path
import pickle
import glob

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

@pytest.fixture(scope='function')
def data_dir():
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    yield os.path.join(package_dir, 'tests', 'data')

@pytest.fixture(scope='function')
def data_output_dir():
    package_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    d = os.path.join(package_dir, "tmp")
    os.makedirs(d, exist_ok=True)
    yield d

@pytest.fixture(scope='function')
def delft(data_dir):
    p = os.path.join(data_dir, 'delft.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)
        
@pytest.fixture(scope='function')
def delft_path(data_dir):
    p = os.path.join(data_dir, 'delft.json')
    yield p

@pytest.fixture(scope='function')
def delft_1b(data_dir):
    p = os.path.join(data_dir, 'delft_1b.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def rotterdam_subset(data_dir):
    p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)
        
@pytest.fixture(scope='function')
def rotterdam_subset_path(data_dir):
    p = os.path.join(data_dir, 'rotterdam', 'rotterdam_subset.json')
    yield p

@pytest.fixture(scope='function')
def zurich_subset(data_dir):
    p = os.path.join(data_dir, 'zurich', 'zurich_subset_lod2.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)
        
@pytest.fixture(scope='function')
def zurich_subset_path(data_dir):
    p = os.path.join(data_dir, 'zurich', 'zurich_subset_lod2.json')
    yield p

@pytest.mark.balazs
@pytest.fixture(scope='function')
def ms_triangles(data_dir):
    """Long list of triangulated MultiSurfaces with EPSG:7514 corodinates."""
    p = os.path.join(data_dir, 'multisurface_triangulated.pickle')
    with open(p, 'rb') as fo:
        yield pickle.load(fo)

@pytest.fixture(scope='function')
def dummy(data_dir):
    p = os.path.join(data_dir, 'dummy', 'dummy.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def dummy_noappearance(data_dir):
    p = os.path.join(data_dir, 'dummy', 'dummy_noappearance.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def cube(data_dir):
    p = os.path.join(data_dir, 'cube.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def cube_compressed(data_dir):
    p = os.path.join(data_dir, 'cube.c.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def minimal(data_dir):
    p = os.path.join(data_dir, 'minimal.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def rectangle(data_dir):
    p = os.path.join(data_dir, 'dummy', 'rectangle.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)
        
@pytest.fixture(scope='function')
def multi_lod(data_dir):
    p = os.path.join(data_dir, 'multi_lod.json')
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)
        
@pytest.fixture(scope='function')
def multi_lod_path(data_dir):
    p = os.path.join(data_dir, 'multi_lod.json')
    yield p

@pytest.fixture(scope='function')
def vertices():
    yield [
        (0.0,1.0,0.0),
        (1.0,1.0,0.0),
        (2.0,1.0,0.0),
        (3.0,1.0,0.0),
        (4.0,1.0,0.0),
        (5.0,1.0,0.0)
    ]


@pytest.fixture(scope='function',
                params=[
                    ('material', 'mt-1.json'),
                    ('material', 'mt-2.json'),
                    ('dummy', 'composite_solid_with_material.json'),
                    ('dummy', 'dummy.json'),
                    ('dummy', 'multisurface_with_material.json')
                ])
def materials(data_dir, request):
    p = os.path.join(data_dir, *request.param)
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

@pytest.fixture(scope='function')
def materials_two(data_dir):
    """Two models with materials for testing their merging"""
    cms = []
    p = os.path.join(data_dir, 'material', 'mt-1.json')
    with open(p, 'r') as f:
        cms.append(cityjson.CityJSON(file=f))
    p = os.path.join(data_dir, 'material', 'mt-2.json')
    with open(p, 'r') as f:
        cms.append(cityjson.CityJSON(file=f))
    yield cms

@pytest.fixture(scope='function',
                params=[
                    ('material', 'mt-1-triangulated.json'),
                    ('material', 'mt-2-triangulated.json'),
                ])
def triangulated(data_dir, request):
    p = os.path.join(data_dir, *request.param)
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)


@pytest.fixture(scope='function')
def mt_1_path(data_dir):
    return os.path.join(data_dir, 'material', 'mt-1.json')
