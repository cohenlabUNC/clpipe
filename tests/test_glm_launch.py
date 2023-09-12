import pytest
from pathlib import Path
from clpipe.glm_launch import glm_launch


def test_glm_launch_controller_L1(glm_config_file: Path):
    """Check running glm_launch controller."""

    with pytest.raises(SystemExit) as e:
        glm_launch(glm_config_file=glm_config_file, level="L1", model="example")

    assert e.value.code == 0



def test_glm_launch_controller_L2(glm_config_file: Path):
    """Check running glm_launch controller."""

    with pytest.raises(SystemExit) as e:
.        glm_launch(glm_config_file=glm_config_file, level="L2", model="example")

    assert e.value.code == 0



def test_glm_launch_controller_invalid_level(glm_config_file: Path):
    """Check that launch controller rejects an invalid level."""

    with pytest.raises(SystemExit) as e:
        glm_launch(glm_config_file=glm_config_file, level="L4", model="example_L1")

    assert e.value.code == 1
