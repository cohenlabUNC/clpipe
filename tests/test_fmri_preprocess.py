import pytest
from pathlib import Path
from clpipe.fmri_preprocess import fmriprep_process


def test_fmriprep_process_no_working(config_file: Path):
    """Check basic attempt to run fmriprep_process without setting working dir."""

    with pytest.raises(SystemExit) as e:
        fmriprep_process(config_file=config_file)

    assert e.value.code == 1


def test_fmriprep_process_templateflow(config_file: Path, clpipe_dir: Path):
    """Check that a cache for templateflow is created in user's home directory."""

    templateflow_path = Path.home() / ".cache" / "templateflow"

    with pytest.raises(SystemExit) as e:
        fmriprep_process(config_file=config_file, working_dir=clpipe_dir)

    assert e.value.code == 0
    assert templateflow_path.exists()
