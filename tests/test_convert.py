import pytest
import os

from cjio import convert, cityjson


@pytest.fixture(scope="function",
                params=[
                    ('rotterdam', 'rotterdam_subset.json'),
                    ('delft.json',)
                ])
def several_cms(data_dir, request):
    p = os.path.join(data_dir, *request.param)
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

class TestGltf:

    def test_convert_to_glb(self, several_cms):
        glb = convert.to_glb(several_cms.j)


class TestB3dm:

    def test_convert_to_b3dm(self, delft):
        glb = convert.to_glb(delft.j)
        b3dm = convert.to_b3dm(delft, glb)
