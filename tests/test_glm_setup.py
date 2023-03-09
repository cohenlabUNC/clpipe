import pytest
from pathlib import Path
from clpipe.glm_setup import glm_setup

def test_glm_setup_basic(config_file: Path, glm_config_file: Path):
    """Check basic attempt to run fmriprep_process."""

    glm_setup(config_file=config_file, glm_config_file=glm_config_file)
    assert True


def test_glm_setup_deprecation_warning(config_file: Path, glm_config_file: Path):
    """Check basic attempt to run fmriprep_process."""

    with pytest.raises(DeprecationWarning):
        glm_setup(config_file=config_file, glm_config_file=glm_config_file)