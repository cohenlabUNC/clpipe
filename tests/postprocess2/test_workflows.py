import pytest

from clpipe.postprocutils.workflows import *


def test_spatial_smoothing_wf(
    artifact_dir, request, sample_raw_image, sample_raw_image_mask, helpers
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    out_path = test_path / "smoothed.nii.gz"
    wf = build_SUSAN_workflow(
        in_file=sample_raw_image,
        out_file=out_path,
        fwhm_mm=6,
        mask_path=sample_raw_image_mask,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "filteredflow", graph2use="colored")

    wf.run()

    helpers.plot_4D_img_slice(out_path, "smoothed.png")
    helpers.plot_timeseries(out_path, sample_raw_image)


def test_spatial_smoothing_wf_no_mask(artifact_dir, request, sample_raw_image, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    out_path = test_path / "smoothed.nii.gz"
    wf = build_SUSAN_workflow(
        in_file=sample_raw_image,
        out_file=out_path,
        fwhm_mm=6,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "filteredflow", graph2use="colored")

    wf.run()

    helpers.plot_4D_img_slice(out_path, "smoothed.png")
    helpers.plot_timeseries(out_path, sample_raw_image)


def test_calculate_100_voxel_mean_wf(
    artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    out_path = test_path / "normalized_100vm.nii.gz"
    wf = build_100_voxel_mean_workflow(
        in_file=sample_raw_image,
        out_file=out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    if write_graph:
        wf.write_graph(
            dotfilename=test_path / "calc100voxelMeanFlow", graph2use=write_graph
        )

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "normalized_100vm.png")

    assert True


def test_calculate_10000_global_median_wf(
    artifact_dir,
    sample_raw_image,
    sample_raw_image_mask,
    plot_img,
    write_graph,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    out_path = test_path / "normalized_10000gm.nii.gz"

    wf = build_10000_global_median_workflow(
        in_file=sample_raw_image,
        out_file=out_path,
        mask_file=sample_raw_image_mask,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)

    if write_graph:
        wf.write_graph(
            dotfilename=test_path / "calc10000globalMedianFlow", graph2use=write_graph
        )

    if plot_img:
        helpers.plot_4D_img_slice(out_path, "normalized_10000gm.png")

    assert True


def test_butterworth_filter_wf(
    artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    filtered_path = test_path / "sample_raw_filtered.nii"

    wf = build_butterworth_filter_workflow(
        hp=0.008,
        lp=-1,
        tr=2,
        order=2,
        in_file=sample_raw_image,
        out_file=filtered_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename=test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(filtered_path, "filtered.png")

    assert True


def test_fslmath_temporal_filter_wf(
    artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    filtered_path = test_path / "sample_raw_filtered.nii.gz"

    wf = build_fslmath_temporal_filter(
        hp=0.008,
        lp=-1,
        tr=2,
        in_file=sample_raw_image,
        out_file=filtered_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    helpers.plot_timeseries(filtered_path, sample_raw_image)

    if write_graph:
        wf.write_graph(dotfilename=test_path / "filteredflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(filtered_path, "filtered.png")

    assert True


def test_confound_regression_fsl_glm_wf(
    artifact_dir,
    sample_raw_image,
    sample_postprocessed_confounds,
    sample_raw_image_mask,
    plot_img,
    write_graph,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    regressed_path = test_path / "sample_raw_regressed.nii"

    wf = build_confound_regression_fsl_glm_workflow(
        confound_file=sample_postprocessed_confounds,
        in_file=sample_raw_image,
        out_file=regressed_path,
        mask_file=sample_raw_image_mask,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename=test_path / "regressedFlow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(regressed_path, "regressed.png")


def test_confound_regression_afni_3dTproject_wf(
    artifact_dir,
    sample_raw_image,
    sample_postprocessed_confounds,
    sample_raw_image_mask,
    plot_img,
    write_graph,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    regressed_path = test_path / "sample_raw_regressed.nii.gz"

    wf = build_confound_regression_afni_3dTproject(
        confounds_file=sample_postprocessed_confounds,
        in_file=sample_raw_image,
        out_file=regressed_path,
        mask_file=sample_raw_image_mask,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    helpers.plot_timeseries(regressed_path, sample_raw_image)

    if write_graph:
        wf.write_graph(dotfilename=test_path / "regressedFlow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(regressed_path, "regressed.png")


def test_apply_aroma_fsl_regfilt_wf(
    artifact_dir,
    sample_raw_image,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    sample_raw_image_mask,
    plot_img,
    write_graph,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    regressed_path = test_path / "sample_raw_aroma.nii.gz"

    wf = build_aroma_workflow_fsl_regfilt(
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        in_file=sample_raw_image,
        out_file=regressed_path,
        mask_file=sample_raw_image_mask,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    helpers.plot_timeseries(regressed_path, sample_raw_image)

    if write_graph:
        wf.write_graph(dotfilename=test_path / "aromaflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(regressed_path, "aromaaplied.png")


# TODO: Provide reference image
def test_resample_wf(
    artifact_dir,
    sample_raw_image,
    sample_reference,
    plot_img,
    write_graph,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    resampled_path = test_path / "resampled.nii.gz"

    wf = build_resample_workflow(
        reference_image=sample_reference,
        in_file=sample_raw_image,
        out_file=resampled_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename=test_path / "resampleflow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(resampled_path, "resample.png")


def test_scrubbing_wf(
    artifact_dir, sample_raw_image, plot_img, write_graph, request, helpers
):
    """Test that a list of arbitrary timepoints can be scrubbed from an image."""

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    scrubbed_path = test_path / "scrubbed.nii.gz"

    scrub_targets = []

    wf = build_scrubbing_workflow(
        in_file=sample_raw_image,
        scrub_targets=scrub_targets,
        out_file=scrubbed_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename=test_path / "scrubbed_flow", graph2use=write_graph)

    if plot_img:
        helpers.plot_4D_img_slice(scrubbed_path, "scrubbed.png")


def test_scrubbing_wf_confounds(
    artifact_dir, sample_confounds_timeseries, request, helpers
):
    """Test that a list of arbitrary timepoints can be scrubbed from a confounds file."""

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    scrubbed_path = test_path / "scrubbed_confounds.tsv"

    wf = build_scrubbing_workflow(
        in_file=sample_confounds_timeseries,
        out_file=scrubbed_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()


def test_scrubbing_wf_confounds(artifact_dir, sample_melodic_mixing, request, helpers):
    """Test that a list of arbitrary timepoints can be scrubbed from an
    AROMA mixing file."""

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    scrubbed_path = test_path / "scrubbed_melodic_mixing.tsv"

    wf = build_scrubbing_workflow(
        in_file=sample_melodic_mixing,
        out_file=scrubbed_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.run()
