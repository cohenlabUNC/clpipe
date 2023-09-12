import pytest

from pathlib import Path

from clpipe.cli import *


def test_cli():
    """Simple test to ensure the main clpipe commmand runs without error."""

    with pytest.raises(SystemExit) as e:
        cli([])

    assert e.value.code == 0


def test_glm_l1_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l1_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l1_launch_cli(
            ["-glm_config_file", str(glm_config_file), "-l1_name", "example"]
        )
    assert e.value.code == 0


def test_glm_l2_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l2_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l2_launch_cli(
            ["-glm_config_file", str(glm_config_file), "-l2_name", "example"]
        )
    assert e.value.code == 0

def test_update_config_cli(legacy_config_dir: Path):
    """Check that legacy config update works as intended."""
    with pytest.raises(SystemExit) as e:
        update_config_cli(
            ["-config_file", str(legacy_config_dir / "clpipe_config.json")]
        )
    assert e.value.code == 0