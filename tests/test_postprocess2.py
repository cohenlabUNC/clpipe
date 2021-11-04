import pytest

import nipype.pipeline.engine as pe
import nibabel as nib

from clpipe.fmri_postprocess2 import PostProcessSubjectJob
from clpipe.postprocutils.workflows import build_10000_global_median_workflow, build_100_voxel_mean_workflow, build_spatial_smoothing_workflow
from clpipe.postprocutils.nodes import ButterworthFilter

@pytest.mark.skip(reason="Needs refactor")
def test_postprocess_subject(clpipe_config_default, tmp_path, sample_raw_image):
    postProcessSubjectJob = PostProcessSubjectJob(sample_raw_image, tmp_path / "postProcessed.nii.gz", tmp_path)
    postProcessSubjectJob.wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='flat')
    postProcessSubjectJob.run()
    assert True


def test_spatial_smoothing_wf(tmp_path, random_nii, random_nii_mask):
    out_path = tmp_path / "smoothed.nii.gz"
    wf = build_spatial_smoothing_workflow(in_file=random_nii, out_file=out_path, fwhm_mm=6, 
        mask_path=random_nii_mask, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "spatialSmoothFlow", graph2use='flat')
    
    assert True

def test_calculate_100_voxel_mean_wf(tmp_path, sample_raw_image):
    out_path = tmp_path / "normalized.nii.gz"
    wf = build_100_voxel_mean_workflow(in_file=sample_raw_image, out_file=out_path, base_dir=tmp_path, crashdump_dir=tmp_path)
    wf.run()
    wf.write_graph(dotfilename = tmp_path / "calc100voxelMeanFlow", graph2use='flat')

    assert True
    
def test_butterworth_filter(tmp_path, sample_raw_image, workflow_base):
    filtered_path = tmp_path / "Test_Workflow" / "Butterworth_Filter" / "sample_raw_filtered.nii"
    
    butterworth_node = pe.Node(ButterworthFilter(in_file=sample_raw_image,
                                hp=.008,lp=-1,order=2,tr=2), name="Butterworth_Filter")
    workflow_base.add_nodes([butterworth_node])
    workflow_base.run()
    workflow_base.write_graph(dotfilename = tmp_path / "filteredflow", graph2use='flat')

    newImage = nib.load(filtered_path)
    print(newImage)
    
    assert True
