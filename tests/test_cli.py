import pytest

from pathlib import Path

from clpipe.cli import *

def test_glm_l1_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l1_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l1_launch_cli([
            "-glm_config_file", str(glm_config_file),
            "-l1_name", "example"
        ])
    assert e.value.code == 0

def test_glm_l2_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l2_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l2_launch_cli([
            "-glm_config_file", str(glm_config_file),
            "-l2_name", "example"
        ])
    assert e.value.code == 0