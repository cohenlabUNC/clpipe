import pytest

from clpipe.postprocutils.workflows import *
from clpipe.postprocutils.confounds_workflows import *


def test_postprocess2_wf_2_steps(
    artifact_dir,
    postprocessing_config,
    sample_confounds_timeseries,
    write_graph,
    helpers,
    request,
):
    postprocessing_config["ProcessingSteps"] = [
        "IntensityNormalization",
        "TemporalFiltering",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed.csv"

    wf = build_confounds_processing_workflow(
        postprocessing_config,
        confounds_file=sample_confounds_timeseries,
        export_file=out_path,
        tr=2,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use=write_graph)

    wf.run()


def test_build_confounds_prep_workflow(
    artifact_dir,
    postprocessing_config,
    sample_confounds_timeseries,
    write_graph,
    helpers,
    request,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "prepped_confounds.csv"

    wf = build_confounds_prep_workflow(
        ["csf", "csf_derivative1", "white_matter", "white_matter_derivative1"],
        threshold=0.9,
        scrub_var="framewise_displacement",
        scrub_ahead=0,
        scrub_behind=0,
        scrub_contiguous=0,
        in_file=sample_confounds_timeseries,
        out_file=out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "confounds_flow", graph2use=write_graph)

    wf.run()


def test_build_get_scrub_targets_workflow(
    artifact_dir, sample_confounds_timeseries, request, helpers
):
    """Test getting scrub targets from confounds given an FD threshold."""

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    scrubbed_path = test_path / "scrubbed_confounds.tsv"

    wf = build_scrubbing_workflow(
        in_file=sample_confounds_timeseries,
        out_file=scrubbed_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()


def test_build_confounds_add_motion_outliers_workflow():
    pass
