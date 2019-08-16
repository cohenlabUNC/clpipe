from setuptools import setup, find_packages

setup(name='clpipe',
      version='1.3',
      description='Cohen Lab MRI processing pipeline',
      url='https://github.com/cohenlabUNC/clpipe',
      author='Cohen Lab (Maintainer: Teague Henry)',
      author_email='trhenry@email.unc.edu',
      license='MIT',
      python_requires='>=3.6',
      include_package_data=True,
      packages=find_packages(),
      install_requires=['jsonschema',
                        'click',
                        'nipy',
                        'numpy',
                        'pandas',
                        'scipy',
                        'sphinx_rtd_theme',
                        'psutil',
                        'parse',
                        'nilearn',
                        'dcm2bids',
                        'nipype'],
      entry_points='''
      [console_scripts]
      fmriprep_process=clpipe.fmri_preprocess:fmriprep_process
      dicom_to_nifti_to_bids_converter_setup=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter_setup
      dicom_to_nifti_to_bids_converter=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter
      bids_validate=clpipe.bids_validator:bids_validate
      fmri_postprocess=clpipe.fmri_postprocess:fmri_postprocess
      fmri_process_check=clpipe.fmri_process_check:fmri_process_check
      get_reports=clpipe.get_reports:get_reports
      grab_config_file=clpipe.grab_config_file:get_config_file
      fmri_roi_extraction=clpipe.roi_extractor:fmri_roi_extraction
      convert2bids=clpipe.dcm2bids_wrapper:convert2bids
      project_setup=clpipe.project_setup:project_setup
      test_batch_setup=clpipe.test_batch_setup:test_batch_setup
      susan_smoothing = clpipe.susan_smoothing:susan_smoothing
      ''',
      zip_safe=False
      )
