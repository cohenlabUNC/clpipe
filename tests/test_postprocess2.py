from clpipe.fmri_postprocess2 import PostProcessSubjectJob

def test_hngprep_subject(clpipe_config_default, tmp_path, sample_raw_image):
    postProcessSubjectJob = PostProcessSubjectJob(clpipe_config_default, 'sub-0', sample_raw_image, tmp_path / "postProcessed.nii.gz")
    postProcessSubjectJob.wf.write_graph(dotfilename = tmp_path / "postProcessSubjectFlow", graph2use='flat')
    postProcessSubjectJob.run()
    assert True

    # expected_path = Path(hngprep_config.config['HNGPrepOptions']['OutputDirectory']) \
    #     / "TBD" \
    #     / "sub-0" \
    #     / "sub-0_task-rest_run-1_space-MNI152NLin2009cAsym_desc-hngprep_bold.nii.gz"

    #assert expected_path.exists(), f"Expected path {expected_path} not found."
