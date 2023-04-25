import pytest

from clpipe.fmri_postprocess2 import *

def test_postprocess2_wf_2_steps(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_3_steps(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization", "TemporalFiltering"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_1_step(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


# This test won't work until properly processed confound file provided
def test_postprocess2_wf_confound_regression_last(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_postprocessed_confounds, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "ConfoundRegression"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_postprocessed_confounds,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_confound_regression_first(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_postprocessed_confounds, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["ConfoundRegression", "SpatialSmoothing"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_postprocessed_confounds,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

@pytest.mark.skip(reason="Test hangs")
def test_postprocess2_wf_aroma(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_melodic_mixing, sample_aroma_noise_ics, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["AROMARegression", "SpatialSmoothing", "IntensityNormalization"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        mixing_file=sample_melodic_mixing, noise_file=sample_aroma_noise_ics,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True

@pytest.mark.skip(reason="Test hangs")
def test_postprocess2_wf_aroma_last(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_melodic_mixing, sample_aroma_noise_ics, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "SpatialSmoothing", "IntensityNormalization", "AROMARegression"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        mixing_file=sample_melodic_mixing, noise_file=sample_aroma_noise_ics,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_no_mask(artifact_dir, postprocessing_config, request, sample_raw_image, 
    plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "SpatialSmoothing", "IntensityNormalization"]

    wf = build_image_postprocessing_workflow(
        postprocessing_config, sample_raw_image, out_path, tr=2,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_fslmaths_temporal_filter(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization", "TemporalFiltering"]
    postprocessing_config["ProcessingStepOptions"]["TemporalFiltering"]["Implementation"] = "fslmaths"

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        confounds_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_resample(artifact_dir, postprocessing_config, request, sample_raw_image, sample_reference, sample_raw_image_mask, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization", "TemporalFiltering", "Resample"]
    postprocessing_config["ProcessingStepOptions"]["Resample"]["ReferenceImage"] = str(sample_reference)

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_image_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, export_path=out_path, tr=2, mask_file=sample_raw_image_mask,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_prepare_confounds(sample_confounds_timeseries, postprocessing_config, artifact_dir, helpers, request):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    cf_workflow = build_confounds_processing_workflow(postprocessing_config, confounds_file=sample_confounds_timeseries,
        export_file=out_path, base_dir=test_path, crashdump_dir=test_path, tr=2)

    cf_workflow.run()
    
    assert True


def test_prepare_confounds_aroma(sample_confounds_timeseries, postprocessing_config, sample_melodic_mixing, sample_aroma_noise_ics,
    artifact_dir, helpers, request):

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    postprocessing_config["ProcessingSteps"] = ["AROMARegression", "TemporalFiltering", "IntensityNormalization"]

    cf_workflow = build_confounds_processing_workflow(postprocessing_config, confounds_file=sample_confounds_timeseries,
        export_file=out_path, mixing_file=sample_melodic_mixing, noise_file=sample_aroma_noise_ics,
        base_dir=test_path, crashdump_dir=test_path, tr=2)

    cf_workflow.run()
    
    assert True
