import pytest
from clpipe.config.options import ProjectOptions, ScrubColumn, ScrubTimepoints

from clpipe.postprocutils.image_workflows import *
from clpipe.postprocutils.global_workflows import *


def test_build_postprocessing_wf(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    postprocessing_config = ProjectOptions().postprocessing

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


def test_build_postprocessing_wf_no_mask(
    artifact_dir,
    request,
    sample_raw_image,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "IntensityNormalization",
        "TemporalFiltering",
        "SpatialSmoothing",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


def test_build_postprocessing_wf_2_steps(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "SpatialSmoothing",
        "TemporalFiltering",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_build_postprocessing_wf_1_step(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "TemporalFiltering",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


def test_postprocess2_wf_confound_regression_last(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "TemporalFiltering",
        "ConfoundRegression",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


def test_postprocess2_wf_confound_regression_first(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "ConfoundRegression",
        "TemporalFiltering",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


@pytest.mark.skip(reason="Test runs long")
def test_postprocess2_wf_aroma(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "AROMARegression",
        "TemporalFiltering",
        "SpatialSmoothing",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


@pytest.mark.skip(reason="Test runs long")
def test_postprocess2_wf_aroma_last(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "TemporalFiltering",
        "SpatialSmoothing",
        "AROMARegression",
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_scrubbing(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.confound_options.columns = [
        "framewise_displacement",
        "csf",
        "csf_derivative1",
        "white_matter",
        "white_matter_derivative1",
    ]
    postprocessing_config.processing_steps = ["TemporalFiltering", "ScrubTimepoints"]

    # Setup target & threshold to ensure some scrubbing happens
    postprocessing_config.processing_step_options.scrub_timepoints.scrub_columns = [
        ScrubColumn(target_variable="csf", threshold=332.44),
        ScrubColumn(target_variable="trans_y*", threshold=0.1),
    ]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


@pytest.mark.skip("Test runs long")
def test_postprocess2_wf_scrubbing_aroma(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.confound_options.columns = [
        "framewise_displacement",
        "csf",
        "csf_derivative1",
        "white_matter",
        "white_matter_derivative1",
    ]
    postprocessing_config.processing_steps = [
        "TemporalFiltering",
        "SpatialSmoothing",
        "AROMARegression",
        "ScrubTimepoints",
    ]

    # Setup target & threshold to ensure some scrubbing happens
    postprocessing_config.processing_step_options.scrub_timepoints = ScrubTimepoints(
        insert_na=True,
        scrub_columns=[ScrubColumn(target_variable="csf", threshold=332.44)],
    )

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_scrubbing_confound_regression(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.confound_options.columns = [
        "framewise_displacement",
        "csf",
        "csf_derivative1",
        "white_matter",
        "white_matter_derivative1",
    ]
    postprocessing_config.processing_steps = [
        "TemporalFiltering",
        "SpatialSmoothing",
        "ConfoundRegression",
        "ScrubTimepoints",
    ]

    # Setup target & threshold to ensure some scrubbing happens
    # Setup target & threshold to ensure some scrubbing happens
    postprocessing_config.processing_step_options.scrub_timepoints = ScrubTimepoints(
        insert_na=True,
        scrub_columns=[ScrubColumn(target_variable="csf", threshold=332.44)],
    )

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        mixing_file=sample_melodic_mixing,
        noise_file=sample_aroma_noise_ics,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_build_multiple_scrubbing_workflow(
    sample_confounds_timeseries,
    helpers,
    artifact_dir,
    request,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_step_options.scrub_timepoints = ScrubTimepoints(
        insert_na=True,
        scrub_columns=[
            ScrubColumn(target_variable="csf", threshold=332.44),
            ScrubColumn(target_variable="framewise_displacement", threshold=0.13),
        ],
    )

    test_wf = build_multiple_scrubbing_workflow(
        postprocessing_config.processing_step_options.scrub_timepoints,
        sample_confounds_timeseries,
    )

    # Passing in the inputs externally
    test_wf.inputs.inputnode.confounds_file = sample_confounds_timeseries

    # Write the workflow graph
    test_wf.write_graph(
        graph2use="colored",
        dotfilename=os.path.join(test_path, "test_wf_graph.dot"),
    )

    # Run the workflow
    test_wf.base_dir = os.path.join(
        test_path, "work_dir"
    )  # specify the working directory for the workflow
    test_wf.run()


def test_build_postprocessing_wf_roi_extract(
    artifact_dir,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postprocessed_image.nii.gz"
    confounds_out_path = test_path / "postprocessed_confounds.tsv"

    postprocessing_config = ProjectOptions().postprocessing
    postprocessing_config.processing_steps = [
        "IntensityNormalization",
        "TemporalFiltering",
        "SpatialSmoothing",
        "ROIExtract",
    ]

    wf = build_postprocessing_wf(
        postprocessing_config,
        image_file=sample_raw_image,
        image_export_path=out_path,
        tr=2,
        mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        confounds_export_path=confounds_out_path,
        base_dir=test_path,
        crashdump_dir=test_path,
    )

    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")
    wf.run()


def test_build_sphere_extract_wf(
    artifact_dir,
    sample_raw_image,
    sample_raw_image_mask,
    sample_roi_coordinates,
    request,
    helpers,
):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)

    sphere_extract_path = test_path / "sphere_extract.nii.gz"

    wf = build_sphere_extract_workflow(
        in_file=sample_raw_image,
        out_file=sphere_extract_path,
        mask_file=sample_raw_image_mask,
        sphere_radius=5,
        coordinates_file=sample_roi_coordinates,
        base_dir=test_path,
        crashdump_dir=test_path,
    )
    wf.write_graph(dotfilename=test_path / "workflow_graph", graph2use="colored")

    wf.run()

    #helpers.plot_3D_img(sphere_extract_path, "sphere_extract.png")