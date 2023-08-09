import pytest

from clpipe.postprocutils.image_workflows import *
from clpipe.postprocutils.confounds_workflows import *


def test_build_confounds_processing_workflow_2_steps(
    artifact_dir,
    postprocessing_config,
    sample_confounds_timeseries,
    helpers,
    request,
):
    """Check that confounds processing works with IN and TF."""

    postprocessing_config["ProcessingSteps"] = [
        "IntensityNormalization",
        "TemporalFiltering",
    ]
    postprocessing_config["ConfoundOptions"]["MotionOutliers"]["Threshold"] = 0.13

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed.tsv"

    wf = build_confounds_processing_workflow(
        postprocessing_config,
        confounds_file=sample_confounds_timeseries,
        export_file=out_path,
        tr=2,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use="colored")

    wf.run()


def test_build_confounds_processing_workflow_aroma_regression(
    artifact_dir,
    postprocessing_config,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
    request,
):
    """Check that confounds processing works with IN and TF."""

    postprocessing_config["ProcessingSteps"] = ["AROMARegression"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed.tsv"

    wf = build_confounds_processing_workflow(
        postprocessing_config,
        confounds_file=sample_confounds_timeseries,
        export_file=out_path,
        tr=2,
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use="colored")

    wf.run()


def test_build_confounds_processing_workflow_2_steps_no_scrub(
    artifact_dir,
    postprocessing_config,
    sample_confounds_timeseries,
    helpers,
    request,
):
    """Check that confounds generated without scrubbing works properly."""

    postprocessing_config["ProcessingSteps"] = [
        "IntensityNormalization",
        "TemporalFiltering",
    ]
    postprocessing_config["ConfoundOptions"]["MotionOutliers"]["Include"] = False

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed.tsv"

    wf = build_confounds_processing_workflow(
        postprocessing_config,
        confounds_file=sample_confounds_timeseries,
        export_file=out_path,
        tr=2,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use="colored")

    wf.run()


## THIS IS IMPORTATN COPY THIS AND ADD SPLAT
def test_build_confounds_prep_workflow(
    artifact_dir,
    sample_confounds_timeseries,
    helpers,
    request,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "prepped_confounds.tsv"

    wf = build_confounds_prep_workflow(
        [
            "framewise_displacement",
            "csf*",
            "white_matter",
            "white_matter_derivative1",
        ],
        scrub_threshold=0.9,
        scrub_target_variable="framewise_displacement",
        scrub_ahead=0,
        scrub_behind=0,
        scrub_contiguous=0,
        in_file=sample_confounds_timeseries,
        out_file=out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use="colored")

    wf.run()


def test_build_confounds_prep_workflow_no_scrubs(
    artifact_dir,
    sample_confounds_timeseries,
    helpers,
    request,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "prepped_confounds.tsv"

    wf = build_confounds_prep_workflow(
        ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1"],
        scrub_threshold=None,
        scrub_target_variable=None,
        scrub_ahead=None,
        scrub_behind=None,
        scrub_contiguous=None,
        in_file=sample_confounds_timeseries,
        out_file=out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use="colored")

    wf.run()


def test_build_confounds_add_motion_outliers_workflow():
    pass
