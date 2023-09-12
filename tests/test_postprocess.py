import pytest

from clpipe.postprocutils.image_workflows import *
from clpipe.postprocess import *
from pathlib import Path


def test_postprocess_subjects(clpipe_fmriprep_dir):
    """Run the subjects setup of postprocessing. Builds output directories, including
    the BIDS index."""
    config = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"

    postprocess_subjects(
        config_file=options
    )


def test_postprocess_subjects_dir_invalid_subject(
    clpipe_fmriprep_dir, artifact_dir, helpers, request
):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        postprocess_subjects(
            subjects=["99"],
            config_file=config,
            fmriprep_dir=fmriprep_dir,
            output_dir=postproc_dir,
            log_dir=log_dir,
        )


@pytest.mark.skip(reason="Need BIDS db fixture.")
def test_postprocess_image(
    artifact_dir,
    config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    with pytest.raises(SystemExit):
        postprocess_image(
            config_file,
            image_path,
            bids_dir,
            fmriprep_dir,
            pybids_db_path,
            out_dir,
            subject_out_dir,
            subject_working_dir,
            log_dir,
        )


def test_build_export_path_image(clpipe_fmriprep_dir: Path):
    """Test that the correct export path for given inputs is constructed."""

    # Build the fMRIPrep input image path
    image_name = "sub-0_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    image_path = fmriprep_dir / "sub-0" / "func" / image_name

    # Build the output path
    subject_out_dir = clpipe_fmriprep_dir / "data_postproc2" / "sub-0"

    # Build full export path
    export_path = build_export_path(image_path, "0", fmriprep_dir, subject_out_dir)

    assert str(export_path) == str(
        subject_out_dir
        / "func"
        / "sub-0_task-rest_space-MNI152NLin2009cAsym_desc-postproc_bold.nii.gz"
    )


def test_build_export_path_confounds(clpipe_fmriprep_dir: Path):
    """Test that the correct export path for given inputs is constructed."""

    # Build the fMRIPrep input image path
    confounds_name = "sub-0_task-rest_desc-confounds_timeseries.tsv"
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    confounds_path = fmriprep_dir / "sub-0" / "func" / confounds_name

    # Build the output path
    subject_out_dir = clpipe_fmriprep_dir / "data_postproc2" / "sub-0"

    # Build full export path
    export_path = build_export_path(confounds_path, "0", fmriprep_dir, subject_out_dir)

    assert str(export_path) == str(
        subject_out_dir / "func" / "sub-0_task-rest_desc-confounds_timeseries.tsv"
    )
