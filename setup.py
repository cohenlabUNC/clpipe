from setuptools import setup, find_packages

setup(name='clpipe',
      version='1.4.2',
      description='clpipe: MRI processing pipeline for high performance clusters',
      url='https://github.com/cohenlabUNC/clpipe',
      author='Maintainer: Teague Henry, Contributor: Deepak Melwani',
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
                        'templateflow',
                        'deepdiff'],
      entry_points='''
      [console_scripts]
      fmriprep_process=clpipe.fmri_preprocess:fmriprep_process_cli
      dicom_to_nifti_to_bids_converter_setup=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter_setup
      dicom_to_nifti_to_bids_converter=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter
      bids_validate=clpipe.bids_validator:bids_validate_cli
      fmri_postprocess=clpipe.fmri_postprocess:fmri_postprocess
      fmri_process_check=clpipe.fmri_process_check:fmri_process_check
      get_reports=clpipe.get_reports:get_reports
      get_config_file=clpipe.grab_config_file:get_config_file
      get_glm_config_file=clpipe.grab_config_file:get_glm_config_file
      fmri_roi_extraction=clpipe.roi_extractor:fmri_roi_extraction
      convert2bids=clpipe.dcm2bids_wrapper:convert2bids_cli
      project_setup=clpipe.project_setup:project_setup_cli
      test_batch_setup=clpipe.test_batch_setup:test_batch_setup
      susan_smoothing = clpipe.susan_smoothing:susan_smoothing
      get_available_atlases=clpipe.roi_extractor:get_available_atlases
      update_config_file=clpipe.config_json_parser:update_config_file
      templateflow_setup=clpipe.template_flow:templateflow_setup
      test_func=clpipe.utils:test_func
      fmap_cleanup=clpipe.fmap_cleanup:fmap_cleanup
      glm_setup=clpipe.glm_setup:glm_setup_cli
      glm_l1_preparefsf=clpipe.glm_l1:glm_l1_preparefsf
      glm_l2_preparefsf=clpipe.glm_l2:glm_l2_preparefsf
      fsl_onset_extract=clpipe.fsl_onset_extract:fsl_onset_extract
      reho_extract=clpipe.reho_extract:reho_extract
      t2star_extract=clpipe.t2star_extract:t2star_extract
      ''',
      zip_safe=False
      )
