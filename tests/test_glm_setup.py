import pytest
from pathlib import Path
from clpipe.glm_setup import glm_setup


def test_glm_setup_basic(config_file: Path, glm_config_file: Path):
    """ Check basic attempt to run glm_setup.
        Should not work due to this command being deprecated.
    """

    with pytest.raises(SystemExit) as excinfo:
        glm_setup(config_file=config_file, glm_config_file=glm_config_file)

    assert excinfo.value.code == 1


def test_glm_setup_backwards_compatible(clpipe_dir_old_glm_config: Path):
    """ Ensure glm_setup still works with the old glm config settings and that
        it raises a deprecation warning.
    """
    config_file = clpipe_dir_old_glm_config / "clpipe_config.json"
    glm_config_file = clpipe_dir_old_glm_config / "glm_config.json"

    with pytest.warns():
        glm_setup(config_file=config_file, glm_config_file=glm_config_file)
