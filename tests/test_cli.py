import pytest

from pathlib import Path

from clpipe.cli import *
from click.testing import CliRunner


def test_cli():
    """Simple test to ensure the main clpipe commmand runs without error."""

    with pytest.raises(SystemExit) as e:
        cli([])

    assert e.value.code == 0

def test_source_cli(clpipe_dicom_dir: Path):
    """Simple test to ensure the source commmand runs without error."""

    runner = CliRunner()
    result = runner.invoke(flywheel_sync_cli, ["-c", str(clpipe_dicom_dir / "clpipe_config.json")])
    print(result.output)
    assert result.exit_code == 0

def test_project_setup_cli(scatch_dir: Path):
    """Check basic functionality."""

    runner = CliRunner()
    result = runner.invoke(
        project_setup_cli,
        ["-project_dir", str(scatch_dir)],
        input="prompt-created project title",
    )
    print(result.output)
    assert result.exit_code == 0


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


def test_update_config_cli(legacy_config_dir: Path):
    """Check basic functionality."""

    runner = CliRunner()
    result = runner.invoke(
        update_config_cli,
        ["-config_file", str(legacy_config_dir / "clpipe_config.json")],
    )
    assert result.exit_code == 0


def test_update_config_cli_input_backup(legacy_config_dir: Path):
    """Check that backup is created when chosen from the prompt."""

    runner = CliRunner()
    result = runner.invoke(
        update_config_cli,
        ["-config_file", str(legacy_config_dir / "clpipe_config.json")],
        input="y",
    )
    assert result.exit_code == 0


def test_update_config_cli_input_no_backup(legacy_config_dir: Path):
    """Check that no backup is created when chosen from prompt."""

    runner = CliRunner()
    result = runner.invoke(
        update_config_cli,
        ["-config_file", str(legacy_config_dir / "clpipe_config.json")],
        input="n",
    )
    assert result.exit_code == 0


def test_update_config_cli_option_backup(legacy_config_dir: Path):
    """Check that backup can be turned on with option prompt, and no input."""

    runner = CliRunner()
    result = runner.invoke(
        update_config_cli,
        ["-config_file", str(legacy_config_dir / "clpipe_config.json"), "-backup"],
    )
    assert result.exit_code == 0
