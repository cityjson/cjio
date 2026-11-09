import copy
import json

import pytest
from click.testing import CliRunner

from cjio import cityjson
from cjio.cjio import cli


def model(name="building", scale=0.001):
    return {
        "type": "CityJSON",
        "version": "2.0",
        "transform": {"scale": [scale] * 3, "translate": [100, 200, 10]},
        "vertices": [[0, 0, 0], [1000, 0, 0], [0, 1000, 0]],
        "CityObjects": {
            name: {
                "type": "Building",
                "attributes": {"name": name},
                "geometry": [
                    {
                        "type": "MultiSurface",
                        "lod": "2",
                        "boundaries": [[[0, 1, 2]]],
                    }
                ],
            }
        },
        "metadata": {
            "title": "Retain primary metadata",
            "referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/7415",
        },
    }


def empty(transform=True):
    result = model()
    result["CityObjects"] = {}
    result["vertices"] = []
    if transform:
        result["transform"] = {"scale": [0, 0, 0], "translate": [0, 0, 0]}
    else:
        del result["transform"]
    return result


def decoded(j):
    cm = cityjson.CityJSON(j=copy.deepcopy(j))
    cm.decompress()
    return cm.j["vertices"]


@pytest.mark.parametrize(
    "positions", [(False, True), (True, False), (True, False, True, True)]
)
def test_empty_merge_preserves_geometry_and_metadata(positions):
    inputs = [
        cityjson.CityJSON(j=empty() if is_empty else model()) for is_empty in positions
    ]
    inputs[0].j["metadata"]["title"] = "Keep primary title"
    for incoming in inputs[1:]:
        incoming.j["metadata"]["title"] = "Do not replace primary title"
    original = model()
    assert inputs[0].merge(inputs[1:])
    result = inputs[0].j
    assert decoded(result) == decoded(original)
    assert result["CityObjects"] == original["CityObjects"]
    assert result["transform"]["scale"] == [0.001] * 3
    assert result["metadata"]["title"] == "Keep primary title"
    assert (
        result["metadata"]["referenceSystem"] == original["metadata"]["referenceSystem"]
    )


@pytest.mark.parametrize("count", [1, 3])
@pytest.mark.parametrize("transform", [False, True])
def test_all_empty_merge_has_finite_identity_transform(count, transform):
    inputs = [cityjson.CityJSON(j=empty(transform)) for _ in range(count)]
    assert inputs[0].merge(inputs[1:])
    result = inputs[0].j
    assert result["vertices"] == []
    assert result["CityObjects"] == {}
    assert result["transform"] == {"scale": [1.0] * 3, "translate": [0, 0, 0]}
    assert result["metadata"]["title"] == "Retain primary metadata"
    assert result["metadata"]["geographicalExtent"] == [0] * 6


def test_empty_attribute_only_object_is_not_discarded():
    attributes = empty()
    attributes["CityObjects"] = {
        "information": {"type": "Building", "attributes": {"note": "keep"}}
    }
    cm = cityjson.CityJSON(j=model())
    assert cm.merge([cityjson.CityJSON(j=attributes)])
    assert (
        cm.j["CityObjects"]["information"] == attributes["CityObjects"]["information"]
    )
    assert decoded(cm.j) == decoded(model())


@pytest.mark.parametrize("empty_first", [False, True])
def test_untransformed_empty_model_does_not_set_precision(empty_first):
    inputs = [empty(False), model()] if empty_first else [model(), empty(False)]
    cm = cityjson.CityJSON(j=inputs[0])
    assert cm.merge([cityjson.CityJSON(j=inputs[1])])
    assert decoded(cm.j) == decoded(model())
    assert cm.j["transform"]["scale"] == [0.001] * 3


def test_empty_transform_does_not_force_excess_precision():
    no_coordinates = empty()
    no_coordinates["transform"]["scale"] = [0.000001] * 3
    cm = cityjson.CityJSON(j=model())
    assert cm.merge([cityjson.CityJSON(j=no_coordinates)])
    assert cm.j["transform"]["scale"] == [0.001] * 3


def test_ordinary_merge_keeps_precision_and_both_objects():
    first, second = model("first", 0.01), model("second", 0.001)
    cm = cityjson.CityJSON(j=copy.deepcopy(first))
    assert cm.merge([cityjson.CityJSON(j=copy.deepcopy(second))])
    assert cm.j["transform"]["scale"] == [0.001] * 3
    assert set(cm.j["CityObjects"]) == {"first", "second"}
    points = decoded(cm.j)
    for original in [first, second]:
        geometry = cm.j["CityObjects"][next(iter(original["CityObjects"]))]["geometry"][
            0
        ]
        assert [points[i] for i in geometry["boundaries"][0][0]] == decoded(original)
    assert cm.j["metadata"]["title"] == first["metadata"]["title"]


@pytest.mark.parametrize(
    "scale",
    [[0, 0, 0], [-0.01] * 3, [float("nan")] * 3, [float("inf")] * 3],
)
@pytest.mark.parametrize("invalid_first", [False, True])
def test_nonempty_invalid_scale_is_not_accepted(scale, invalid_first):
    invalid = model("invalid")
    invalid["transform"]["scale"] = scale
    inputs = [invalid, model()] if invalid_first else [model(), invalid]
    with pytest.raises((ValueError, OverflowError)):
        cityjson.CityJSON(j=inputs[0]).merge([cityjson.CityJSON(j=inputs[1])])


@pytest.mark.parametrize(
    "scale",
    [[0.01, -0.01, 0.01], [0.01, 0, 0.01], [0.01, 0.01, 0], [0.01, 0.01, -0.01]],
)
@pytest.mark.parametrize("special_first", [False, True])
def test_finite_yz_scales_keep_existing_geometry(scale, special_first):
    special = model("special", 0.01)
    # A referenced triangle remains nondegenerate when either Y or Z is zero.
    special["vertices"] = [[0, 0, 0], [100, 0, 0], [0, 100, 100]]
    special["transform"]["scale"] = scale
    control = model("control", 0.01)
    control["transform"]["translate"] = [300, 400, 50]
    originals = [special, control] if special_first else [control, special]
    inputs = [cityjson.CityJSON(j=copy.deepcopy(j)) for j in originals]
    assert inputs[0].merge(inputs[1:])
    result = inputs[0].j
    points = decoded(result)
    assert result["transform"]["scale"] == [0.01] * 3
    for original in originals:
        name = next(iter(original["CityObjects"]))
        geometry = result["CityObjects"][name]["geometry"][0]
        assert [points[i] for i in geometry["boundaries"][0][0]] == decoded(original)
        assert (
            result["CityObjects"][name]["attributes"]
            == original["CityObjects"][name]["attributes"]
        )


@pytest.mark.parametrize(
    "positions", [(False, True), (True, False), (True, False, True), (True, True, True)]
)
def test_cli_merge_real_files(tmp_path, positions):
    paths = []
    for i, is_empty in enumerate(positions):
        path = tmp_path / f"input-{i}.json"
        path.write_text(json.dumps(empty() if is_empty else model()), encoding="utf-8")
        paths.append(path)
    output = tmp_path / "merged.json"
    # Input zero is the CLI's primary input; the glob includes only its siblings.
    extra = tmp_path / "extra"
    extra.mkdir()
    for path in paths[1:]:
        path.rename(extra / path.name)
    result = CliRunner().invoke(
        cli, [str(paths[0]), "merge", str(extra / "*.json"), "save", str(output)]
    )
    assert result.exit_code == 0, (result.output, result.exception)
    merged = json.loads(output.read_text(encoding="utf-8"))
    if all(positions):
        assert merged["CityObjects"] == {}
        assert merged["vertices"] == []
        assert merged["transform"] == {"scale": [1.0] * 3, "translate": [0, 0, 0]}
    else:
        assert merged["CityObjects"] == model()["CityObjects"]
        assert decoded(merged) == decoded(model())
        assert merged["transform"]["scale"] == [0.001] * 3
    assert merged["metadata"]["title"] == "Retain primary metadata"
