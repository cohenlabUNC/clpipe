import pytest
from pathlib import Path
from clpipe.glm_launch import glm_launch

def test_glm_launch_controller(glm_config_file: Path):
    """Check running glm_launch controller."""

    glm_launch(glm_config_file=glm_config_file, level="L1", model="example_L1")