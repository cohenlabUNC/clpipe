import pytest
from pathlib import Path
from clpipe.glm_setup import glm_setup


def test_glm_setup_basic(config_file: Path, glm_config_file: Path):
    """Check basic attempt to run glm_setup.
    Should not work due to this command being deprecated.
    """

    with pytest.raises(SystemExit) as excinfo:
        glm_setup(config_file=config_file, glm_config_file=glm_config_file)

    assert excinfo.value.code == 1
