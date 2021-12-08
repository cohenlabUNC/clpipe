import io
import pytest
from pathlib import Path
import traceback

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img
from click.testing import CliRunner

from clpipe.postprocutils.workflows import *
from clpipe.postprocutils.confounds import prepare_confounds
from clpipe.fmri_postprocess2 import PostProcessSubjectJobs, PostProcessSubjectJob, postprocess_fmriprep_dir, fmri_postprocess2_cli

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
        hngprep_cli, 
        ['-config_file', str(config),
        '-target_dir', str(fmriprep_dir),
        '-output_dir', str(postproc_dir),
        '-glm_config_file', str(glm_config),
        '-log_dir', str(log_dir),
        'dsfdsf', '-debug']
    )
    traceback.print_exc(result.exception)
    assert result.stderr == 0

def test_postprocess_fmriprep_dir(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_fmriprep_dir(config_file=config, glm_config_file=glm_config, fmriprep_dir=fmriprep_dir,
        output_dir=postproc_dir, log_dir=log_dir)

def test_postprocess_fmriprep_dir_invalid_subject(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    config = clpipe_fmriprep_dir / "clpipe_config.json"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    postprocess_fmriprep_dir(subjects=['99'], config_file=config, glm_config_file=glm_config, fmriprep_dir=fmriprep_dir,
        output_dir=postproc_dir, log_dir=log_dir)

def test_postprocess2_wf(artifact_dir, postprocessing_config, request, sample_raw_image, sample_raw_image_mask, 
    plot_img, write_graph, helpers):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "postProcessed.nii.gz"
    
    wf = build_postprocessing_workflow(postprocessing_config, sample_raw_image, out_path, 2, mask_file=sample_raw_image_mask,
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


def test_postprocess2(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    jobs = PostProcessSubjectJobs(fmriprep_dir, postproc_dir, glm_config,
        log_dir=log_dir)
    jobs.run()

def test_prepare_confounds(sample_confounds_timeseries, postprocessing_config, artifact_dir, helpers, request):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    prepare_confounds(sample_confounds_timeseries, out_path, postprocessing_config)
    
    assert True

def test_postprocess_subject(clpipe_fmriprep_dir, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    glm_config = clpipe_fmriprep_dir / "glm_config.json"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    postproc_dir.mkdir(exist_ok=True)
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    subject = PostProcessSubjectJob('1', clpipe_fmriprep_dir, postproc_dir, glm_config, log_dir=log_dir)
    subject.run()


