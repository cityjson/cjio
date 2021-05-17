"""Test validation

"""
import pytest
import pytest_check as check
import copy
from cjio import cityjson,models



class TestValidate:
    def test_minimal(self, minimal):
        (isValid, woWarnings, es, ws) = minimal.validate()
        assert isValid == True
            
    def test_all(self, all_cms):
        for id, cm in all_cms.items():
            (isValid, woWarnings, es, ws) = cm.validate()
            check.equal(isValid, True, "Validity of %s" %id)