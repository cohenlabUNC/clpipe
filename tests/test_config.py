import pytest
import json
import yaml
import os
from pkg_resources import resource_stream

from clpipe.config import *
from clpipe.newConfig.clpipe_config import getConfig
from clpipe.newConfig.config_converter import convertConfig

"""
Removed tests for lack of fields and extra fields as this test will always pass
because we will always load the config object from the new config file only
"""

def test_json_load(config_file):
    """ Ensure that the config class loads in .json data as expected. """
    config = getConfig(json_file=config_file)
    assert config is not None
    assert config.ProjectTitle == "test_project"
    assert config.PostProcessingOptions2.ProcessingStepOptions.TemporalFiltering.FilteringHighPass == 0.008

def test_yaml_load(config_file, tmp_path):
    """ Ensure that the config class loads from .yaml as expected. """
    with open(config_file, 'r') as json_file:
        conf_json = json.load(json_file)
        
    with open(os.path.join(tmp_path,'config.yaml'), 'w') as yaml_file:
        yaml.dump(conf_json, yaml_file, sort_keys=False)
    config = getConfig(yaml_file=os.path.join(tmp_path,'config.yaml'))
    assert config is not None
    assert config.ProjectTitle == "test_project"
    assert config.PostProcessingOptions2.ProcessingStepOptions.TemporalFiltering.FilteringHighPass == 0.008

# Using dictionaries over file references from this point on - no need to test
#   json.load()

def test_default(clpipe_config_default):
    """ Ensure that data from the default config file (data/defaltConfig.json)
    is successfully loaded into the configuration object.
    """
    config = getConfig()
    assert config.ProjectTitle == clpipe_config_default["ProjectTitle"]
    assert config.Authors == clpipe_config_default["Authors/Contributors"]
    assert config.SourceOptions.MemUsage == clpipe_config_default["SourceOptions"]["MemUsage"]

def test_wrong_order(config_file, tmp_path):
    """ Ensure that a configuration with fields in an unexpected order will successfully
    load.
    """

    with resource_stream(__name__, 'data/wrongOrder_defaultConfig.json') as f:
        oldConf = json.load(f)
        
    with open(config_file, 'r') as f:
        newConf = json.load(f)

    convertedConfig = convertConfig(oldConf, newConf)
    with open(os.path.join(tmp_path,'convertedConfig.json'), 'w') as f:
        json.dump(convertedConfig, f)

    convertedConfig = getConfig(json_file=os.path.join(tmp_path,'convertedConfig.json'))
    correctConfig = getConfig()
    assert correctConfig == convertedConfig

def test_author_contributor(config_file):
    """ Check that the conversion of the Authors/Contributors to just 'Contributors'
    works successfully.
    """
    config = getConfig(json_file=config_file)
    assert config is not None
    assert config.Authors == ""