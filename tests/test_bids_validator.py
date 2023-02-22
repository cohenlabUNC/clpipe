import pytest
from clpipe.bids_validator import bids_validate

def test_bids_validate(config_file):
    """ Check basic attempt to run bids_validate."""

    bids_validate(config_file=config_file)
    assert True