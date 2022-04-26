import pytest
from pathlib import Path

from clpipe.fmri_postprocess2 import *

def test_postprocess_fmriprep_dir(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)


    with pytest.raises(SystemExit):
        postprocess_subjects_controller(config_file=config, fmriprep_dir=fmriprep_dir, bids_dir=bids_dir,
            output_dir=postproc_dir, log_dir=log_dir)