import pytest
import json
import yaml
import os
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
    assert options.project_title == "A Neuroimaging Project"
    assert (
        options.postprocessing.processing_step_options.temporal_filtering.filtering_high_pass
        == 0.008
    )


def test_yaml_load(config_file, tmp_path):
    """Ensure that the config class loads from .yaml as expected."""
    
    with open(config_file, "r") as json_file:
        conf_json = json.load(json_file)

    with open(os.path.join(tmp_path, "config.yaml"), "w") as yaml_file:
        yaml.dump(conf_json, yaml_file, sort_keys=False)
    options = ProjectOptions.load(os.path.join(tmp_path,'config.yaml'))
    assert options is not None
    assert options.project_title == "A Neuroimaging Project"
    assert (
        options.postprocessing.processing_step_options.temporal_filtering.filtering_high_pass
        == 0.008
    )


def test_default(legacy_config_path, clpipe_config_default):
    """Ensure that data from the default config file (data/defaltConfig.json)
    is successfully loaded into the configuration object.
    """
    options = ProjectOptions.load(legacy_config_path)
    assert options.project_title == clpipe_config_default["ProjectTitle"]
    assert options.contributors == clpipe_config_default["Authors/Contributors"]
    assert (
        options.source.mem_usage
        == clpipe_config_default["SourceOptions"]["MemUsage"]
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


def test_author_contributor(config_file):
    """Check that the conversion of the Authors/Contributors to just 'Contributors'
    works successfully.
    """
    config = ProjectOptions.load(config_file)
    assert config is not None
    assert config.contributors == "SET CONTRIBUTORS"


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
