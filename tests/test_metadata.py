"""Test metadata

"""
import copy



class TestMetadata:
    def test_update_metadata(self, delft):
        cm = copy.deepcopy(delft)
        cm.update_metadata(overwrite=True)
        assert len(cm.j['metadata']['cityfeatureMetadata']) == len(delft.j['metadata']['cityfeatureMetadata'])
        for type in cm.j['metadata']['cityfeatureMetadata']:
            assert cm.j['metadata']['cityfeatureMetadata'][type]['uniqueFeatureCount'] == delft.j['metadata']['cityfeatureMetadata'][type]['uniqueFeatureCount']
            assert cm.j['metadata']['cityfeatureMetadata'][type]['aggregateFeatureCount'] == delft.j['metadata']['cityfeatureMetadata'][type]['aggregateFeatureCount']
            assert cm.j['metadata']['cityfeatureMetadata'][type]['presentLoDs']["1"] == delft.j['metadata']['cityfeatureMetadata'][type]['presentLoDs']["1"]
        
        assert cm.j['metadata']['presentLoDs'] == delft.j['metadata']['presentLoDs']
        assert cm.j['metadata']['geographicalExtent'] == delft.j['metadata']['geographicalExtent']