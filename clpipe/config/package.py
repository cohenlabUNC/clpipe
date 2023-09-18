PACKAGE_NAME = 'clpipe'
VERSION = '1.9.0'

DESCRIPTION = 'clpipe: MRI processing pipeline for high performance clusters'
REPO_URL = 'https://github.com/cohenlabUNC/clpipe'
AUTHORS = (
      'Author/Maintainer: Teague Henry, Maintainer: Will Asciutto, '
      'Contributor: Bhvaith Manapoty, Contributor: Deepak Melwani'
)
AUTHOR_EMAIL = 'ycp6wm@virginia.edu'
LICENSE = 'MIT'

# Python version tested against
PYTHON_VERSION = '3.7'
# Allows versions greater than the test baseline
PYTHON_REQUIRES = f'>={PYTHON_VERSION}'

# List of all dependency packages, to be automatically installed alongside clpipe
INSTALL_REQUIRES = [
      'jsonschema==4.17.3',
      'click==8.1.3',
      'nipy==0.5.0',
      'numpy>=1.18.5',
      'pandas==1.3.5',
      'nibabel>=3',
      'scipy==1.2.2',
      'sphinx_rtd_theme==1.2.0',
      'psutil==5.9.5',
      'parse==1.19.0',
      'nilearn==0.9.0',
      'dcm2bids==2.1.9',
      'nipype==1.8.6',
      'pybids>=0.14.0',
      'templateflow==23.0.0',
      "pydantic==1.10.7",
      "matplotlib==3.5.3",
      "heudiconv>=0.10.0",
      "tqdm==4.65.0",
      "marshmallow-dataclass==8.5.14",
      "PyYAML==6.0"
],

PACKAGE_DATA = {'clpipe': ['R_scripts/*.R']}

# These entries register bash aliases to click commands. The aliases are available for
#   use upon package installation, and are implemented by auto-generated scripts in
#   <python env>/bin
ENTRY_POINTS = '''
      [console_scripts]
      clpipe=clpipe.cli:cli
      project_setup=clpipe.cli:project_setup_cli
      convert2bids=clpipe.cli:convert2bids_cli
      bids_validate=clpipe.cli:bids_validate_cli
      fmriprep_process=clpipe.cli:fmriprep_process_cli
      fmri_postprocess=clpipe.cli:fmri_postprocess_cli
      fmri_postprocess2=clpipe.cli:fmri_postprocess2_cli
      postprocess_image=clpipe.cli:postprocess_image_cli
      glm_l1_preparefsf=clpipe.cli:glm_l1_preparefsf_cli
      glm_l1_launch=clpipe.cli:glm_l1_launch_cli
      glm_l2_preparefsf=clpipe.cli:glm_l2_preparefsf_cli
      glm_l2_launch=clpipe.cli:glm_l2_launch_cli
      fsl_onset_extract=clpipe.cli:fsl_onset_extract_cli
      fmri_process_check=clpipe.cli:fmriprep_process_cli
      get_reports=clpipe.cli:get_fmriprep_reports_cli
      get_config_file=clpipe.cli:get_config_cli
      get_glm_config_file=clpipe.cli:get_glm_config_cli
      fmri_roi_extraction=clpipe.cli:fmri_roi_extraction_cli
      test_batch_setup=clpipe.test_batch_setup:test_batch_setup
      get_available_atlases=clpipe.cli:get_available_atlases_cli
      update_config_file=clpipe.cli:update_config_cli
      templateflow_setup=clpipe.cli:templateflow_setup_cli
      test_func=clpipe.utils:test_func
      fmap_cleanup=clpipe.fmap_cleanup:fmap_cleanup
      reho_extract=clpipe.reho_extract:reho_extract
      t2star_extract=clpipe.t2star_extract:t2star_extract
'''