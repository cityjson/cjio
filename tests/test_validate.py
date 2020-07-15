"""Test validation

"""
import pytest
import copy
from cjio import cityjson,models



class TestValidate:
    def test_minimal(self, minimal):
        (isValid, woWarnings, es, ws) = minimal.validate()
        assert isValid == True






