import json
import os
import struct

import pytest

from cjio import convert, cityjson


@pytest.fixture(
    scope="function", params=[("rotterdam", "rotterdam_subset.json"), ("delft.json",)]
)
def several_cms(data_dir, request):
    p = os.path.join(data_dir, *request.param)
    with open(p, "r") as f:
        yield cityjson.CityJSON(file=f)


class TestGltf:
    def test_empty_citymodel_exports_a_json_only_glb(self):
        data = cityjson.CityJSON().export2glb().getvalue()
        magic, version, length = struct.unpack_from("<4sII", data)
        assert (magic, version, length) == (b"glTF", 2, len(data))

        size, kind = struct.unpack_from("<I4s", data, 12)
        assert kind == b"JSON"
        assert size == len(data) - 20
        assert size % 4 == 0
        scene = json.loads(data[20:].decode("utf-8"))
        assert scene["asset"]["version"] == "2.0"
        assert scene["scenes"][scene["scene"]] == {}
        assert "buffers" not in scene

    @pytest.mark.slow
    def test_convert_to_glb(self, several_cms):
        _ = several_cms.export2glb()

    def test_debug_den_haag_glb(self, data_dir):
        p = os.path.join(data_dir, "DH_01_subs.city.json")
        with open(p, "r") as f:
            cm = cityjson.CityJSON(file=f)
        _ = cm.export2glb()

    def test_debug_delft_glb(self, data_dir, data_output_dir):
        # CityJSON v1.1
        p = os.path.join(data_dir, "DH_01_subs.city.json")
        with open(p, "r") as f:
            cm = cityjson.CityJSON(file=f)
        glb = cm.export2glb(do_triangulate=False)
        glb.seek(0)
        with open(f"{data_output_dir}/DH_01_subs.glb", mode="wb") as bo:
            bo.write(glb.getvalue())


class TestB3dm:
    def test_empty_citymodel_exports_an_empty_tile(self):
        assert cityjson.CityJSON().export2b3dm().getvalue() == b""

    @pytest.mark.slow
    def test_convert_to_b3dm(self, delft):
        glb = delft.export2glb()
        _ = convert.to_b3dm(delft, glb)
