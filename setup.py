from setuptools import setup, find_packages

setup(name='clpipe',
      version='1.5.1',
      description='clpipe: MRI processing pipeline for high performance clusters',
      url='https://github.com/cohenlabUNC/clpipe',
      author='Maintainer: Teague Henry, Contributor: Will Asciutto, Contributor: Deepak Melwani',
      author_email='trhenry@email.unc.edu',
      license='MIT',
      python_requires='>=3.6',
      include_package_data=True,
      packages=find_packages(),
      install_requires=['jsonschema',
                        'click',
                        'nipy',
                        'numpy==1.18.5',
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
                        "pydantic"],
      package_data={'clpipe': ['R_scripts/*.R']},
      entry_points='''
      [console_scripts]
      fmri_postprocess2=clpipe.cli:fmri_postprocess2
      postprocess_subject=clpipe.cli:postprocess_subject_cli
      postprocess_image=clpipe.cli:postprocess_image_cli
      clpipe=clpipe.cli:cli
      fmriprep_process=clpipe.cli:fmriprep_process
      dicom_to_nifti_to_bids_converter_setup=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter_setup
      dicom_to_nifti_to_bids_converter=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter
      bids_validate=clpipe.cli:bids_validate
      fmri_postprocess=clpipe.cli:fmri_postprocess
      fmri_process_check=clpipe.fmri_process_check:fmri_process_check
      get_reports=clpipe.get_reports:get_reports
      get_config_file=clpipe.grab_config_file:get_config_file
      get_glm_config_file=clpipe.grab_config_file:get_glm_config_file
      fmri_roi_extraction=clpipe.roi_extractor:fmri_roi_extraction
      convert2bids=clpipe.cli:convert2bids
      project_setup=clpipe.cli:project_setup
      test_batch_setup=clpipe.test_batch_setup:test_batch_setup
      susan_smoothing = clpipe.susan_smoothing:susan_smoothing
      get_available_atlases=clpipe.roi_extractor:get_available_atlases
      update_config_file=clpipe.config_json_parser:update_config_file
      templateflow_setup=clpipe.template_flow:templateflow_setup
      test_func=clpipe.utils:test_func
      fmap_cleanup=clpipe.fmap_cleanup:fmap_cleanup
      glm_setup=clpipe.cli:glm_setup
      glm_l1_preparefsf=clpipe.cli:glm_l1_preparefsf
      glm_l1_launch=clpipe.cli:glm_l1_launch
      glm_l2_preparefsf=clpipe.cli:glm_l2_preparefsf
      fsl_onset_extract=clpipe.cli:glm_onset_extract
      reho_extract=clpipe.reho_extract:reho_extract
      t2star_extract=clpipe.t2star_extract:t2star_extract
      ''',
      zip_safe=False
      )
