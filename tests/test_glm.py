import pytest
from clpipe.glm_setup import glm_setup

def test_glm_setup(config_file: Path, glm_config_file: Path) -> None:
    """Check basic attempt to run fmriprep_process."""

    glm_setup(config_file=config_file, glm_config_file=glm_config_file)
    assert True