import pytest
import os

from cjio import convert, cityjson


@pytest.fixture(scope="function",
                params=[
                    ("rotterdam", 'rotterdam_subset.json'),
                    ('delft.json',)
                ])
def several_cms(data_dir, request):
    p = os.path.join(data_dir, *request.param)
    with open(p, 'r') as f:
        yield cityjson.CityJSON(file=f)

class TestGltf:

    @pytest.mark.slow
    def test_convert_to_glb(self, several_cms):
        glb = several_cms.export2glb()

    def test_debug_den_haag_glb(self, data_dir):
        p = os.path.join(data_dir, "DH_01_subs.city.json")
        with open(p, 'r') as f:
            cm = cityjson.CityJSON(file=f)
        glb = cm.export2glb()

    def test_debug_delft_glb(self, data_dir, data_output_dir):
        # CityJSON v1.1
        p = os.path.join(data_dir, "DH_01_subs.city.json")
        with open(p, 'r') as f:
            cm = cityjson.CityJSON(file=f)
        glb = cm.export2glb(do_triangulate=False)
        glb.seek(0)
        with open(f"{data_output_dir}/DH_01_subs.glb", mode='wb') as bo:
            bo.write(glb.getvalue())


class TestB3dm:

    @pytest.mark.slow
    def test_convert_to_b3dm(self, delft):
        glb = delft.export2glb()
        b3dm = convert.to_b3dm(delft, glb)
