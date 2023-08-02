import pytest
from pathlib import Path
from clpipe.fmri_process_check import fmri_process_check
import os


def test_fmriprep_process_check(clpipe_fmriprep_dir):
    """Check basic attempt to run fmriprep_process_check."""
    fmri_process_check(os.path.join(clpipe_fmriprep_dir, "clpipe_config.json"))
    assert os.path.isfile(os.path.join(clpipe_fmriprep_dir, "Checker-Output.csv"))


def test_legacy_fmriprep_process_check(clpipe_legacy_fmriprep_dir):
    """Check basic attempt to run fmriprep_process_check on the legacy directory structure."""
    fmri_process_check(
        os.path.join(clpipe_legacy_fmriprep_dir, "clpipe_config.json"),
        os.path.join(clpipe_legacy_fmriprep_dir, "Checker-Output.csv"),
    )
    assert os.path.isfile(
        os.path.join(clpipe_legacy_fmriprep_dir, "Checker-Output.csv")
    )
