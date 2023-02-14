import pytest
from pathlib import Path
import traceback

from click.testing import CliRunner

from clpipe.postprocutils.workflows import *
from clpipe.fmri_postprocess2 import *
from clpipe.cli import fmri_postprocess2_cli

def test_postprocess_cli_debug(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    """Note: this test always passes because click does its own exit code handling - but this lets one trace through the cli with a debugger"""

    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(SystemExit):
        fmri_postprocess2_cli(['-config_file', str(config),
                                '-target_dir', str(fmriprep_dir),
                                '-output_dir', str(postproc_dir),
                                '-glm_config_file', str(glm_config),
                                '-log_dir', str(log_dir),
                                '-no-batch', '-debug'])


def test_postprocess_cli(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    runner = CliRunner()
    result = runner.invoke(
        fmri_postprocess2_cli, 
        ['-config_file', str(config),
        '-target_dir', str(fmriprep_dir),
        '-output_dir', str(postproc_dir),
        '-glm_config_file', str(glm_config),
        '-log_dir', str(log_dir),
        'dsfdsf', '-debug']
    )
    traceback.print_exc(result.exception)
    assert result.stderr == 0


def test_postprocess_subjects_dir(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subjects(config_file=config, glm_config_file=glm_config, fmriprep_dir=fmriprep_dir,
        output_dir=postproc_dir, log_dir=log_dir)


def test_postprocess_subjects_dir_config_only(clpipe_fmriprep_dir):
    config = clpipe_fmriprep_dir / "clpipe_config.json"

    with pytest.raises(SystemExit):
        postprocess_subjects(config_file=config, submit=True, batch=False)


def test_postprocess_subjects_dir_invalid_subject(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subjects(subjects=['99'], config_file=config, glm_config_file=glm_config, fmriprep_dir=fmriprep_dir,
        output_dir=postproc_dir, log_dir=log_dir)


def test_postprocess2_wf_2_steps(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
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
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
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
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


# This test won't work until properly processed confound file provided
def test_postprocess2_wf_confound_regression_last(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "ConfoundRegression"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_confound_regression_first(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["ConfoundRegression", "SpatialSmoothing"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_aroma(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_melodic_mixing, sample_aroma_noise_ics, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["AROMARegression", "SpatialSmoothing", "IntensityNormalization"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        mixing_file=sample_melodic_mixing, noise_file=sample_aroma_noise_ics,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess2_wf_aroma_last(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_melodic_mixing, sample_aroma_noise_ics, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["TemporalFiltering", "SpatialSmoothing", "IntensityNormalization", "AROMARegression"]

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
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
    
    wf = build_postprocessing_workflow(postprocessing_config, sample_raw_image, out_path, 2,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True


def test_postprocess_subjects_job(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    #pybids_db_path = Path(test_dir / "bids_index")
    pybids_db_path = None

    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subjects(bids_dir, fmriprep_dir, postproc_dir, config,
        log_dir=log_dir, pybids_db_path=pybids_db_path)


def test_prepare_confounds(sample_confounds_timeseries, postprocessing_config, artifact_dir, helpers, request):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    cf_workflow = build_confounds_processing_workflow(postprocessing_config, confound_file=sample_confounds_timeseries,
        out_file=out_path, base_dir=test_path, crashdump_dir=test_path, tr=2)

    cf_workflow.run()
    
    assert True


def test_prepare_confounds_aroma(sample_confounds_timeseries, postprocessing_config, sample_melodic_mixing, sample_aroma_noise_ics,
    artifact_dir, helpers, request):

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    postprocessing_config["ProcessingSteps"] = ["AROMARegression", "TemporalFiltering", "IntensityNormalization"]

    cf_workflow = build_confounds_processing_workflow(postprocessing_config, confound_file=sample_confounds_timeseries,
        out_file=out_path, mixing_file=sample_melodic_mixing, noise_file=sample_aroma_noise_ics,
        base_dir=test_path, crashdump_dir=test_path, tr=2)

    cf_workflow.run()
    
    assert True


def test_postprocess_subject_job_setup(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    pybids_db_path = test_dir / "BIDS_index"

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_job(clpipe_fmriprep_dir, config_file, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    pybids_db_path = test_dir / "BIDS_index"

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_with_confounds(clpipe_fmriprep_dir, config_file_confounds, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_confounds, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_aroma(clpipe_fmriprep_dir, config_file_aroma, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_aroma, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess_subject_aroma_with_confound_processing(clpipe_fmriprep_dir, config_file_aroma_confounds, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    bids_dir = clpipe_fmriprep_dir / "data_BIDS"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    pybids_db_path = test_dir / "bids_index"
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_subject('1', bids_dir, fmriprep_dir, postproc_dir, config_file_aroma_confounds, pybids_db_path=pybids_db_path, log_dir=log_dir)


def test_postprocess2_wf_fslmaths_temporal_filter(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    sample_confounds_timeseries, plot_img, write_graph, helpers):

    postprocessing_config["ProcessingSteps"] = ["SpatialSmoothing", "IntensityNormalization", "TemporalFiltering"]
    postprocessing_config["ProcessingStepOptions"]["TemporalFiltering"]["Algorithm"] = "fslmaths"

    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        confound_file=sample_confounds_timeseries,
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
    
    wf = build_postprocessing_workflow(postprocessing_config, in_file=sample_raw_image, out_file=out_path, tr=2, mask_file=sample_raw_image_mask,
        base_dir=test_path, crashdump_dir=test_path)
    
    wf.run()

    if write_graph:
        wf.write_graph(dotfilename = test_path / "postProcessSubjectFlow", graph2use=write_graph)
   
    if plot_img:
        helpers.plot_4D_img_slice(out_path, "postProcessed.png")

    assert True
