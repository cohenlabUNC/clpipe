import pytest

from clpipe.postprocutils.workflows import *


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
