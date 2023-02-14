import pytest

from clpipe.postprocutils.workflows import *
from clpipe.fmri_postprocess2 import *
from pathlib import Path


def test_postprocess_subjects_dir(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        postprocess_subjects(config_file=config, fmriprep_dir=fmriprep_dir, bids_dir=bids_dir,
            output_dir=postproc_dir, log_dir=log_dir)


def test_postprocess_subjects_dir(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        postprocess_subjects(config_file=config, fmriprep_dir=fmriprep_dir,
            output_dir=postproc_dir, log_dir=log_dir)


def test_postprocess_subjects_dir_config_only(clpipe_fmriprep_dir):
    config = clpipe_fmriprep_dir / "clpipe_config.json"

    with pytest.raises(SystemExit):
        postprocess_subjects(config_file=config, submit=True, batch=False)


def test_postprocess_subjects_dir_invalid_subject(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        postprocess_subjects(subjects=['99'], config_file=config, fmriprep_dir=fmriprep_dir,
            output_dir=postproc_dir, log_dir=log_dir)


def test_postprocess_subject_job_setup(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    pybids_db_path = test_dir / "BIDS_index"

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_job(clpipe_fmriprep_dir, config_file, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    pybids_db_path = test_dir / "BIDS_index"

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_with_confounds(clpipe_fmriprep_dir, config_file_confounds, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_confounds, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_aroma(clpipe_fmriprep_dir, config_file_aroma, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_aroma, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_aroma_with_confound_processing(clpipe_fmriprep_dir, config_file_aroma_confounds, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_aroma_confounds, pybids_db_path=pybids_db_path, log_dir=log_dir)
