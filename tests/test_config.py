import pytest

from clpipe.config import *


@pytest.mark.skip(reason="Test Not Implemented")
def test_config_default(clpipe_config_default):
    """ Ensure that the default config file (data/defaltConfig.json)
    is successfully loaded into the configuration object.
    """

    assert False
    # e.g. test a few fields 
    # assert config.project_title = ""
    # assert config.convert2bids.bids_dir = ""


@pytest.mark.skip(reason="Test Not Implemented")
def test_config_extra_fields(config_file):
    """ Ensure that the intial config for a test project is successfully loaded."""
    assert False


# Could consider creating test config files for these case-specific config tests
#   that follow. These could go in tests/data/config_files
# Or we could just load in a base config file and modify the dictionary in code to
#   get the test case we want.


@pytest.mark.skip(reason="Test Not Implemented")
def test_config_wrong_order():
    """ Ensure that a config file with fields in an unexpected order will successfully
    load.
    """
    assert False


@pytest.mark.skip(reason="Test Not Implemented")
def test_config_author_contributor():
    """ Check that the conversion of the Authors/Contributors to just 'Contributors'
    works successfully.
    """
    assert False