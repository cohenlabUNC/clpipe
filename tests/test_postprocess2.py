from pathlib import Path

import pytest

import nipype.pipeline.engine as pe
import nibabel as nib
from nilearn import plotting
from nilearn.image import load_img, index_img

from clpipe.postprocutils.workflows import *
from clpipe.postprocutils.confounds import prepare_confounds
from clpipe.fmri_postprocess2 import PostProcessSubjectJobs

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


def test_postprocess2(clpipe_fmriprep_dir, postprocessing_config, artifact_dir, helpers, request):
    fmriprep_dir = clpipe_fmriprep_dir / "data_fmriprep" / "fmriprep"
    test_dir = helpers.create_test_dir(artifact_dir, request.node.name)
    postproc_dir = Path(test_dir / "data_postprocessed")
    log_dir = Path(test_dir / "logs" / "postproc_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    jobs = PostProcessSubjectJobs(fmriprep_dir, postproc_dir, postprocessing_config,
        log_dir=log_dir)
    jobs.run()

def test_prepare_confounds(sample_confounds_timeseries, postprocessing_config, artifact_dir, helpers, request):
    test_path = helpers.create_test_dir(artifact_dir, request.node.name)
    out_path = test_path / "new_confounds.tsv"

    prepare_confounds(sample_confounds_timeseries, out_path, postprocessing_config)
    
    assert True

