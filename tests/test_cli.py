import pytest
import traceback

from pathlib import Path
from click.testing import CliRunner

from clpipe.cli import *

def test_glm_l1_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l1_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l1_launch_cli([
            "-glm_config_file", str(glm_config_file),
            "-l1_name", "example_L1"
        ])
    assert e.value.code == 0

def test_glm_l2_launch_cli(glm_config_file: Path):
    """Test that 'classic' style glm_l2_launch_cli launch command works"""

    with pytest.raises(SystemExit) as e:
        glm_l2_launch_cli([
            "-glm_config_file", str(glm_config_file),
            "-l2_name", "tworun_gngreg"
        ])
    assert e.value.code == 0

def test_fmri_postprocess2_cli_debug(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    """Note: this test always passes because click does its own exit code handling - but this lets one trace through the cli with a debugger"""

    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit) as e:
        fmri_postprocess2_cli(['-config_file', str(config),
                                '-target_dir', str(fmriprep_dir),
                                '-output_dir', str(postproc_dir),
                                '-glm_config_file', str(glm_config),
                                '-log_dir', str(log_dir),
                                '-no-batch', '-debug'])
    assert e.value.code == 0


def test_fmri_postprocess2_cli(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    runner = CliRunner()
    result = runner.invoke(
        fmri_postprocess2_cli, 
        ['-config_file', str(config),
        '-target_dir', str(fmriprep_dir),
        '-output_dir', str(postproc_dir),
        '-glm_config_file', str(glm_config),
        '-log_dir', str(log_dir),
        'dsfdsf', '-debug']
    )
    traceback.print_exc(result.exception)
    assert result.stderr == 0