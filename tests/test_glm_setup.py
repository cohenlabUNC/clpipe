import pytest
from pathlib import Path
from clpipe.glm_setup import glm_setup
import json

def test_glm_setup_basic(config_file: Path, glm_config_file: Path):
    """Check basic attempt to run fmriprep_process."""

    glm_setup(config_file=config_file, glm_config_file=glm_config_file)
    assert True


def test_glm_setup_deprecation_warning(config_file: Path, glm_config_file: Path):
    """Ensure glm_setup raises a deprecation warning."""

    with pytest.warns():
        glm_setup(config_file=config_file, glm_config_file=glm_config_file)


def test_glm_setup_backwards_compatible(config_file: Path):
    with open("data/old_GLMConfig.json", 'r') as old_glm_config_file:
        old_glm_config = json.load(old_glm_config_file)
