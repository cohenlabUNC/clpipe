import pytest

from clpipe.postprocutils.image_workflows import *
from clpipe.postprocutils.global_workflows import *

def test_build_postprocessing_wf(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
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

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )


def test_build_postprocessing_wf_no_mask(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    
def test_build_postprocessing_wf_2_steps(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_build_postprocessing_wf_1_step(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering"]

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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )


def test_postprocess2_wf_confound_regression_last(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )


def test_postprocess2_wf_confound_regression_first(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )


def test_postprocess2_wf_aroma(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_aroma_last(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_scrubbing(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "ScrubTimepoints"]
    postprocessing_config["ConfoundOptions"]["Columns"] = [
        "framewise_displacement",
        "csf",
        "csf_derivative1",
        "white_matter",
        "white_matter_derivative1",
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_scrubbing_aroma(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
        "TemporalFiltering",
        "SpatialSmoothing",
        "AROMARegression",
        "ScrubTimepoints",
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")


def test_postprocess2_wf_scrubbing_confound_regression(
    artifact_dir,
    postprocessing_config,
    request,
    sample_raw_image,
    sample_raw_image_mask,
    sample_confounds_timeseries,
    sample_melodic_mixing,
    sample_aroma_noise_ics,
    helpers,
):
    postprocessing_config["ProcessingSteps"] = [
        "TemporalFiltering",
        "SpatialSmoothing",
        "ConfoundRegression",
        "ScrubTimepoints",
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
        crashdump_dir=test_path
    )

    wf.run()

    wf.write_graph(
        dotfilename=test_path / "workflow_graph", graph2use='colored'
    )

    helpers.plot_timeseries(out_path, sample_raw_image)
    helpers.plot_4D_img_slice(out_path, "postprocessed.png")