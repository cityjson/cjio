"""Test metadata

"""
import copy



class TestMetadata:
    def test_update_metadata(self, delft):
        delft.compute_metadata_extended()
        cm = copy.deepcopy(delft)
        assert len(cm.j['+metadata-extended']['cityfeatureMetadata']) == len(delft.j['+metadata-extended']['cityfeatureMetadata'])
        for type in cm.j['+metadata-extended']['cityfeatureMetadata']:
            assert cm.j['+metadata-extended']['cityfeatureMetadata'][type]['uniqueFeatureCount'] == delft.j['+metadata-extended']['cityfeatureMetadata'][type]['uniqueFeatureCount']
            assert cm.j['+metadata-extended']['cityfeatureMetadata'][type]['aggregateFeatureCount'] == delft.j['+metadata-extended']['cityfeatureMetadata'][type]['aggregateFeatureCount']
            assert cm.j['+metadata-extended']['cityfeatureMetadata'][type]['presentLoDs']["1"] == delft.j['+metadata-extended']['cityfeatureMetadata'][type]['presentLoDs']["1"]
        assert cm.j['+metadata-extended']['presentLoDs'] == delft.j['+metadata-extended']['presentLoDs']
