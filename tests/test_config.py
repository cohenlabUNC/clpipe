import pytest
import json
import yaml
import os
from typing import Tuple
from pkg_resources import resource_stream

from clpipe.config.options import *

"""
Removed tests for lack of fields and extra fields as this test will always pass
because we will always load the config object from the new config file only
"""


def test_json_load(config_file):
    """ Ensure that the config class loads in .json data as expected. """
    
    options = ProjectOptions.load(config_file)
    assert options is not None
    assert options.project_title == "test_project"
    assert (
        options.postprocessing.processing_step_options.temporal_filtering.filtering_high_pass
        == 0.008
    )


def test_yaml_load(config_file, tmp_path):
    """Ensure that the config class loads from .yaml as expected."""
    
    options = ProjectOptions.load(config_file)
    options.dump(os.path.join(tmp_path, "config.yaml"))
    options_yaml = ProjectOptions.load(os.path.join(tmp_path, "config.yaml"))

    assert options_yaml.project_title == "test_project"
    assert (
        options_yaml.postprocessing.processing_step_options.temporal_filtering.filtering_high_pass
        == 0.008
    )


def test_default(legacy_config_path):
    """Ensure that data from the default config file (data/defaltConfig.json)
    is successfully loaded into the configuration object.
    """
    options = ProjectOptions.load(legacy_config_path)
    assert options.project_title == "test_project"
    assert options.contributors == "SET AUTHOR"
    assert (
        options.source.mem_usage
        == "10G"
    )


@pytest.mark.skip(reason="Need to generate wrong order from correct order dict")
def test_wrong_order(config_file, tmp_path):
    """Ensure that a configuration with fields in an unexpected order will successfully
    load.
    """

    with resource_stream(__name__, "data/wrongOrder_defaultConfig.json") as f:
        oldConf = json.load(f)

    with open(config_file, "r") as f:
        newConf = json.load(f)

    convertedConfig = convert_project_config(oldConf, newConf)
    with open(os.path.join(tmp_path,'convertedConfig.json'), 'w') as f:
        json.dump(convertedConfig, f)

    convertedConfig = ProjectOptions.load(os.path.join(tmp_path,'convertedConfig.json'))
    correctConfig = ProjectOptions.load()
    assert correctConfig == convertedConfig


def test_author_contributor(legacy_config_path):
    """Check that the conversion of the Authors/Contributors to just 'Contributors'
    works successfully.
    """
    config = ProjectOptions.load(legacy_config_path)
    assert config.contributors == "SET AUTHOR"


# Why is this getting setup options run?
def test_dump_project_config_yaml_default(helpers, artifact_dir, request):
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    ProjectOptions().dump(test_dir / 'test_project_options.yaml')


def test_dump_project_config_json_default(helpers, artifact_dir, request):
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    ProjectOptions().dump(test_dir / 'test_project_options.json')


def test_dump_project_config_json(helpers, artifact_dir, request):
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    config:ProjectOptions = ProjectOptions()
    config.populate_project_paths(test_dir, "test_source")
    config.dump(test_dir / 'test_project_options.json')


def test_dump_project_config_yaml(helpers, artifact_dir, request):
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    config:ProjectOptions = ProjectOptions()
    config.populate_project_paths(test_dir, "test_source")
    config.dump(test_dir / 'test_project_options.yaml')

def test_update_config_file_legacy(legacy_config_dir):
    """Test to ensure legacy config update to new format works."""
    config_file = legacy_config_dir / "clpipe_config.json"

    update_config_file(config_file)

def test_update_config_file_legacy_relative(legacy_config_dir):
    """Test to ensure legacy config update to new format works when using
        just 'clpipe_config.json' within clpipe dir."""
    original_dir = os.getcwd()
    os.chdir(legacy_config_dir)
    
    update_config_file("clpipe_config.json")

    # Make sure to reset to original directory to not mess up other tests.
    os.chdir(original_dir)

def test_update_config_file_legacy_backup(legacy_config_dir):
    """Test to ensure legacy config update to new format works when using
        just 'clpipe_config.json' within clpipe dir."""
    config_file = legacy_config_dir / "clpipe_config.json"
    
    update_config_file(config_file, backup=True)
