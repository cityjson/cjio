"""Test validation

"""
import pytest
import pytest_check as check
import copy
from cjio import cityjson,models



class TestValidate:
    def test_delft(self, delft):
            (isValid, woWarnings, es, ws) = delft.validate()
            assert isValid == True
            
            
    def test_delft_1b(self, delft_1b):
            (isValid, woWarnings, es, ws) = delft_1b.validate()
            assert isValid == True
            
            
    def test_rotterdam_subset(self, rotterdam_subset):
            (isValid, woWarnings, es, ws) = rotterdam_subset.validate()
            assert isValid == True
			
			
    def test_zurich_subset(self, zurich_subset):
            (isValid, woWarnings, es, ws) = zurich_subset.validate()
            assert isValid == True
    
    
    def test_dummy(self, dummy):
            (isValid, woWarnings, es, ws) = dummy.validate()
            assert isValid == True
					
			
    def test_dummy_noappearance(self, dummy_noappearance):
            (isValid, woWarnings, es, ws) = dummy_noappearance.validate()
            assert isValid == True
            
            
    def test_cube(self, cube):
        (isValid, woWarnings, es, ws) = cube.validate()
        assert isValid == True


    def test_cube_compressed(self, cube_compressed):
        (isValid, woWarnings, es, ws) = cube_compressed.validate()
        assert isValid == True
			
            
    def test_minimal(self, minimal):
        (isValid, woWarnings, es, ws) = minimal.validate()
        assert isValid == True

			
    def test_rectangle(self, rectangle):
            (isValid, woWarnings, es, ws) = rectangle.validate()
            assert isValid == True
			
			
    def test_multi_lod(self, multi_lod):
            (isValid, woWarnings, es, ws) = multi_lod.validate()
            assert isValid == True
            
