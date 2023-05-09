import pytest

from clpipe.postprocutils.workflows import *
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

    postprocessing_config["ProcessingSteps"] = [
        "AROMARegression"
    ]

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


def test_build_confounds_add_motion_outliers_workflow():
    pass