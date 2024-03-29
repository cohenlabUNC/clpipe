import pytest
from pathlib import Path
from clpipe import glm_prepare


def test_glm_prepare_controller_L1(glm_config_file: Path):
    """Check running glm_launch controller for L1."""

    # Monkeypatch helper function so that controller can be tested in isolation
    glm_prepare._glm_l1_propagate = _glm_l1_propagate_return

    with pytest.raises(SystemExit) as e:
        glm_prepare.glm_prepare(
            glm_config_file=glm_config_file, level="L1", model="example"
        )

    assert e.value.code == 0


def _glm_l1_propagate_return(l1_block, task_name, reference_image, logger):
    """Do nothing except check some config values."""
    assert l1_block["FSFPrototype"] == "SET PROTOTYPE PATH"
    assert l1_block["ImageExcludeList"] == ""
    assert l1_block["ImageIncludeList"] == ""
    assert task_name == "SET TASK NAME"
    assert reference_image == "SET REFERENCE"


def test_glm_prepare_controller_L2(glm_config_file: Path):
    """Check running glm_launch controller for L2."""

    # Monkeypatch helper function so that controller can be tested in isolation
    glm_prepare._glm_l2_propagate = _glm_l2_propagate_return

    with pytest.raises(SystemExit) as e:
        glm_prepare.glm_prepare(
            glm_config_file=glm_config_file, level="L2", model="example"
        )

    assert e.value.code == 0


def _glm_l2_propagate_return(l2_block, reference_image, logger):
    """Do nothing except check some config values."""
    assert l2_block["FSFPrototype"] == "SET PROTOTYPE PATH"
    assert l2_block["SubjectFile"] == "l2_sublist.csv"
    assert l2_block["ModelName"] == "example"
    assert reference_image == "SET REFERENCE"
