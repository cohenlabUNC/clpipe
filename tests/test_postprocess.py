import pytest
from clpipe.config.options import ProcessingStream

from clpipe.postprocutils.image_workflows import *
from clpipe.postprocess import *
from pathlib import Path


def test_postprocess_subjects(clpipe_fmriprep_dir):
    """Run the subjects setup of postprocessing. Builds output directories, including
    the BIDS index."""
    config_file = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config_file)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"

    postprocess_subjects(config_file=options, batch=True)


def test_postprocess_subjects_invalid_subject(clpipe_fmriprep_dir):
    """Run the subjects setup of postprocessing. Builds output directories, including
    the BIDS index."""
    config_file = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config_file)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"

    postprocess_subjects(subjects=["99"], config_file=options, batch=True)

def test_postprocess_subjects_stream(clpipe_fmriprep_dir):
    """Run postprocess subjects using a stream."""
    config_file = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config_file)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"

    postprocess_subjects(
        config_file=options,
        batch=True,
        processing_stream="functional_connectivity_default",
    )

def test_postprocess_subjects_stream_roi_extract(clpipe_fmriprep_dir):
    """Run postprocess subjects using a stream."""
    config_file = clpipe_fmriprep_dir / "clpipe_config.json"

    options = ProjectOptions.load(config_file)
    options.postprocessing.working_directory = clpipe_fmriprep_dir / "data_working"
    options.postprocessing.stats_options.roi_extract.include = True

    postprocess_subjects(
        config_file=options,
        batch=True,
        processing_stream="functional_connectivity_default",
    )


def test_apply_stream(artifact_dir, helpers, request):
    """Test that stream updates postprocessing config as expected."""

    options: ProjectOptions = ProjectOptions()

    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    options = apply_stream(options, "functional_connectivity_default")

    options.dump(test_dir / "clpipe_config_stream_applied.json")


def test_apply_nested_items(artifact_dir, helpers, request):
    """Test that stream updates postprocessing config as expected."""

    options: ProjectOptions = ProjectOptions()
    options.processing_streams.append(
        ProcessingStream(
            stream_name="nested_items",
            postprocessing_options={
                "processing_step_options": {"spatial_smoothing": {"fwhm": 8}},
                "confound_options": {
                    "columns": ["csf*", "white_matter*"],
                },
            },
        )
    )

    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)

    options = apply_stream(options, "nested_items")

    options.dump(test_dir / "clpipe_config_stream_applied.json")


def test_postprocess_image(clpipe_postprocess_subjects):
    run_config_file = (
        clpipe_postprocess_subjects / "data_working" / "default" / "run_config.json"
    )
    run_config: PostProcessingRunConfig = PostProcessingRunConfig.load(run_config_file)

    with pytest.raises(SystemExit) as e:
        postprocess_image(
            run_config_file=run_config,
            image_path=clpipe_postprocess_subjects
            / "data_fmriprep/sub-0/func/sub-0_task-gonogo_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
            subject_out_dir=clpipe_postprocess_subjects
            / "data_postprocess/default/sub-0",
            subject_working_dir=clpipe_postprocess_subjects
            / "data_working/default/sub-0",
            subject_log_dir=clpipe_postprocess_subjects
            / "logs/postprocess_logs/default/sub-0",
            confounds_only=False,
            debug=False,
            subject_mask=False,
            no_mask=False,
        )

    assert e.value.code == 0


def test_postprocess_image_roi_extract(clpipe_postprocess_subjects):
    run_config_file = (
        clpipe_postprocess_subjects / "data_working" / "default" / "run_config.json"
    )
    run_config: PostProcessingRunConfig = PostProcessingRunConfig.load(run_config_file)
    run_config.options.stats_options.roi_extract.include = True

    with pytest.raises(SystemExit) as e:
        postprocess_image(
            run_config_file=run_config,
            image_path=clpipe_postprocess_subjects
            / "data_fmriprep/sub-0/func/sub-0_task-gonogo_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
            subject_out_dir=clpipe_postprocess_subjects
            / "data_postprocess/default/sub-0",
            subject_working_dir=clpipe_postprocess_subjects
            / "data_working/default/sub-0",
            subject_log_dir=clpipe_postprocess_subjects
            / "logs/postprocess_logs/default/sub-0",
            confounds_only=False,
            debug=False,
        )

    assert e.value.code == 0


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
