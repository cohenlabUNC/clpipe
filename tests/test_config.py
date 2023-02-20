import pytest

from clpipe.config import *

@pytest.mark.skip(reason="Test Not Implemented")
def test_json_load(config_file):
    """ Ensure that the config class loads in .json data as expected. """

    assert False


@pytest.mark.skip(reason="Feature Not Implemented")
def test_yaml_load():
    """ Ensure that the config class loads from .yaml as expected. """

    assert False


# Using dictionaries over file references from this point on - no need to test
#   json.load()

@pytest.mark.skip(reason="Test Not Implemented")
def test_default(clpipe_config_default):
    """ Ensure that data from the default config file (data/defaltConfig.json)
    is successfully loaded into the configuration object.
    """

    assert False
    # e.g. test a few fields 
    # assert config.project_title = ""
    # assert config.convert2bids.bids_dir = ""


@pytest.mark.skip(reason="Test Not Implemented")
def test_extra_fields(clpipe_config):
    """ Ensure that the intial config for a test project is successfully loaded."""
    assert False


@pytest.mark.skip(reason="Test Not Implemented")
def test_wrong_order(clpipe_config):
    """ Ensure that a configuration with fields in an unexpected order will successfully
    load.
    """
    assert False


@pytest.mark.skip(reason="Test Not Implemented")
def test_author_contributor(clpipe_config):
    """ Check that the conversion of the Authors/Contributors to just 'Contributors'
    works successfully.
    """
    assert False