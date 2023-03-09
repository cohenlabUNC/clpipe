from setuptools import setup, find_packages

setup(name='clpipe',
      version='1.7.3.3',
      description='clpipe: MRI processing pipeline for high performance clusters',
      url='https://github.com/cohenlabUNC/clpipe',
      author='Maintainer: Teague Henry, Maintainer: Will Asciutto, Contributor: Deepak Melwani',
      author_email='trhenry@email.unc.edu',
      license='MIT',
      python_requires='>=3.7',
      include_package_data=True,
      packages=find_packages(),
      install_requires=['jsonschema',
                        'click',
                        'nipy',
                        'numpy>=1.18.5',
                        'pandas',
                        'nibabel>=3',
                        'scipy==1.2.2',
                        'sphinx_rtd_theme',
                        'psutil',
                        'parse',
                        'nilearn',
                        'dcm2bids',
                        'nipype',
                        'pybids>=0.14.0',
                        'templateflow',
                        'deepdiff',
                        "pydantic",
                        "matplotlib",
                        "heudiconv>=0.10.0",
                        "tqdm"],
      package_data={'clpipe': ['R_scripts/*.R']},
      entry_points='''
      [console_scripts]
      clpipe=clpipe.cli:cli
      project_setup=clpipe.cli:project_setup_cli
      convert2bids=clpipe.cli:convert2bids_cli
      bids_validate=clpipe.cli:bids_validate_cli
      fmriprep_process=clpipe.cli:fmriprep_process_cli
      fmri_postprocess=clpipe.cli:fmri_postprocess_cli
      fmri_postprocess2=clpipe.cli:fmri_postprocess2_cli
      postprocess_subject=clpipe.fmri_postprocess2:postprocess_subject_cli
      postprocess_image=clpipe.fmri_postprocess2:postprocess_image_cli
      glm_setup=clpipe.cli:glm_setup_cli
      glm_l1_preparefsf=clpipe.cli:glm_l1_preparefsf_cli
      glm_l1_launch=clpipe.cli:glm_l1_launch_cli
      glm_l2_preparefsf=clpipe.cli:glm_l2_preparefsf_cli
      glm_l2_launch=clpipe.cli:glm_l2_launch_cli
      fsl_onset_extract=clpipe.cli:fsl_onset_extract_cli
      fmri_process_check=clpipe.fmri_process_check:fmri_process_check
      get_reports=clpipe.cli:get_fmriprep_reports_cli
      get_config_file=clpipe.grab_config_file:get_config_file
      get_glm_config_file=clpipe.grab_config_file:get_glm_config_file
      fmri_roi_extraction=clpipe.cli:fmri_roi_extraction_cli
      test_batch_setup=clpipe.test_batch_setup:test_batch_setup
      susan_smoothing = clpipe.susan_smoothing:susan_smoothing
      get_available_atlases=clpipe.cli:get_available_atlases_cli
      update_config_file=clpipe.config_json_parser:update_config_file
      templateflow_setup=clpipe.template_flow:templateflow_setup
      test_func=clpipe.utils:test_func
      fmap_cleanup=clpipe.fmap_cleanup:fmap_cleanup
      reho_extract=clpipe.reho_extract:reho_extract
      t2star_extract=clpipe.t2star_extract:t2star_extract
      ''',
      zip_safe=False
      )
