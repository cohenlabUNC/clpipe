from setuptools import setup, find_packages


setup(name='clpipe',
      version='0.1',
      description='Cohen Lab MRI processing pipeline',
      url = 'https://github.com/cohenlabUNC/clpipe',
      author = 'Cohen Lab (Maintainer: Teague Henry)',
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
                        'scipy'],
      entry_points='''
      [console_scripts]
      fmriprep_process=clpipe.fmri_preprocess:fmriprep_process
      dicom_to_nifti_to_bids_converter_setup=clpipe.dicom_to_bids_converter:dicom_to_nifti_to_bids_converter_setup
      bids_validate=clpipe.bids_validator:bids_validate
      fmri_postprocess=clpipe.fmri_postprocess:fmri_postprocess
      fmri_process_check=clpipe.fmri_process_check:fmri_process_check
      ''',
      zip_safe=False
      )