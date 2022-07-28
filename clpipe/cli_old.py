import click
import pkg_resources
import sys

from .project_setup import project_setup as project_setup_logic
from .dcm2bids_wrapper import convert2bids as convert2bids_logic
from .bids_validator import bids_validate as bids_validate_logic
from .fmri_preprocess import fmriprep_process as fmriprep_process_logic
from .fmri_postprocess import fmri_postprocess as fmri_postprocess_logic
from .fmri_postprocess2 import postprocess_image_controller,\
    postprocess_subject_controller, postprocess_subjects_controller,\
    DEFAULT_PROCESSING_STREAM_NAME
from .glm_setup import glm_setup as glm_setup_logic
from .glm_l1 import glm_l1_preparefsf as glm_l1_preparefsf_logic,\
    glm_l1_launch_controller
from .glm_l2 import glm_l2_preparefsf as glm_l2_preparefsf_logic
from .fsl_onset_extract import fsl_onset_extract as fsl_onset_extract_logic
from .outliers_report import get_study_outliers, get_image_confounds

CLICK_FILE_TYPE = click.Path(dir_okay=False, file_okay=True)
CLICK_FILE_TYPE_EXISTS = click.Path(
    exists=True, dir_okay=False, file_okay=True)
CLICK_DIR_TYPE = click.Path(dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_EXISTS = click.Path(exists=True, dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_NOT_EXIST = click.Path(
    exists=False, dir_okay=True, file_okay=False)

CONFIG_HELP = "Uses a given configuration file"
LOG_DIR_HELP = "Where to put HPC output files (such as SLURM output files)"
SUBMIT_HELP = "Flag to submit commands to the HPC"
DEBUG_HELP = "Flag to enable detailed error messages and traceback"
STATUS_CACHE_HELP = "Path to a status cache file for pipeline automation."
INTERACTIVE_HELP = (
    "Run in an interactive session. Only use in an interactive "
    "compute session."
)
VERSION_HELP = "Display clpipe's version."

# project_setup


# convert2bids
CONVERSION_CONFIG_HELP = (
    "The configuration file for the study, use if you have a custom "
    "batch configuration."
)
DICOM_DIR_HELP = "The folder where subject dicoms are located."
DICOM_DIR_FORMAT_HELP = (
    "Format string for how subjects/sessions are organized within the "
    "dicom_dir."
)
CONVERT2BIDS_BIDS_DIR_HELP = "The dicom info output file name."
OVERWRITE_HELP = "Overwrite existing BIDS data?"
CONVERT2BIDS_SUBJECT_HELP = (
    "A subject  to convert using the supplied configuration file. "
    "Use to convert single subjects, else leave empty."
)
CONVERT2BIDS_SESSION_HELP = (
    "A session  to convert using the supplied configuration file. Use in "
    "combination with -subject to convert single subject/sessions, "
    "else leave empty"
)

# bids_validate
BIDS_VALIDATE_VERBOSE_HELP = (
    "Creates verbose validator output. Use if you want to see ALL files "
    "with errors/warnings."
)

# fmriprep_process
FMRIPREP_CONFIG_HELP = (
    "Use a given configuration file. If left blank, uses the default config "
    "file, requiring definition of BIDS, working and output directories."
)
FMRIPREP_BIDS_DIR_HELP = (
    "Which BIDS directory to process. If a configuration file is provided "
    "with a BIDS directory, this argument is not necessary."
)
FMRIPREP_WORKING_DIR_HELP = (
    "Where to generate the working directory. If a configuration file is "
    "provided with a working directory, this argument is not necessary."
)
FMRIPREP_OUTPUT_DIR_HELP = (
    "Where to put the preprocessed data. If a configuration file is provided "
    "with a output directory, this argument is not necessary."
)





@cli.command()
@click.option('-config_file', type=CLICK_FILE_TYPE_EXISTS, default=None, 
              help=CONFIG_HELP)
@click.argument('bids_dir', type=CLICK_DIR_TYPE_EXISTS, required=False)
@click.option('-log_dir', type=CLICK_FILE_TYPE_EXISTS, default=None,
              help=LOG_DIR_HELP)
@click.option('-verbose', is_flag=True, default=False,
              help=BIDS_VALIDATE_VERBOSE_HELP)
@click.option('-submit', is_flag=True, help=SUBMIT_HELP)
@click.option('-interactive', is_flag=True, default=False,
              help=INTERACTIVE_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
def bids_validate(bids_dir, config_file, log_dir, interactive, submit,
                  verbose, debug):
    """Check that the given directory conforms to the BIDS standard"""

    bids_validate_logic(
        bids_dir=bids_dir, config_file=config_file, log_dir=log_dir, 
        interactive=interactive, submit=submit, verbose=verbose, debug=debug)


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', default=None, type=CLICK_FILE_TYPE_EXISTS, 
              help=FMRIPREP_CONFIG_HELP)
@click.option('-bids_dir', type=CLICK_DIR_TYPE_EXISTS,
              help=FMRIPREP_BIDS_DIR_HELP)
@click.option('-working_dir', type=CLICK_DIR_TYPE, 
              help=FMRIPREP_WORKING_DIR_HELP)
@click.option('-output_dir', type=CLICK_DIR_TYPE,
              help=FMRIPREP_OUTPUT_DIR_HELP)
@click.option('-log_dir', type=CLICK_DIR_TYPE, help=LOG_DIR_HELP)
@click.option('-submit', is_flag=True, default=False, help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
@click.option('-status_cache', default=None, type=CLICK_FILE_TYPE, 
              help=STATUS_CACHE_HELP)
def fmriprep_process(bids_dir, working_dir, output_dir, config_file, subjects, 
                     log_dir, submit, debug, status_cache):
    """Submit BIDS-formatted images to fMRIPrep"""

    fmriprep_process_logic(
        bids_dir=bids_dir, working_dir=working_dir,
        output_dir=output_dir, config_file=config_file, 
        subjects=subjects, log_dir=log_dir, submit=submit, debug=debug, 
        status_cache=status_cache)


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help='Which fmriprep directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary. Note, must point to the ``fmriprep`` directory, not its parent directory.')
@click.option('-target_suffix', help= 'Which file suffix to use. If a configuration file is provided with a target suffix, this argument is not necessary. Defaults to "preproc_bold.nii.gz"')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put the postprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-output_suffix', help = 'What suffix to append to the postprocessed files. If a configuration file is provided with a output suffix, this argument is not necessary.')
@click.option('-task', help = 'Which task to postprocess. If left blank, defaults to all tasks.')
@click.option('-TR', help = 'The TR of the scans. If a config file is not provided, this option is required. If a config file is provided, this information is found from the sidecar jsons.')
@click.option('-processing_stream', help = 'Optional processing stream selector.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False), help = 'Where to put HPC output files. If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-beta_series', is_flag = True, default = False, help = "Flag to activate beta-series correlation correlation. ADVANCED METHOD, refer to the documentation.")
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True, help = 'Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess(config_file=None, subjects=None, target_dir=None, 
                     target_suffix=None, output_dir=None,
                     output_suffix=None, log_dir=None,
                     submit=False, batch=True, task=None, tr=None, 
                     processing_stream = None, debug = False, 
                     beta_series = False):
    """Additional preprocessing for connectivity analysis"""

    fmri_postprocess_logic(
        config_file=config_file, subjects=subjects, target_dir=target_dir, 
        target_suffix=target_suffix, output_dir=output_dir, 
        output_suffix=output_suffix, log_dir=log_dir, submit=submit, 
        batch=batch, task=task, tr=tr, processing_stream=processing_stream, 
        debug=debug, beta_series=beta_series)


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required=True,
              help='Use a given configuration file.')
@click.option('-fmriprep_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="""Which fmriprep directory to process. 
    If a configuration file is provided with a BIDS directory, this argument is not necessary. 
    Note, must point to the ``fmriprep`` directory, not its parent directory.""")
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False, help = """Where to put the postprocessed data. 
    If a configuration file is provided with a output directory, this argument is not necessary.""")
@click.option('-processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME, required=False, help="Specify a processing stream to use defined in your configuration file.")
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False, help = 'Path to the logging directory.')
@click.option('-index_dir', type=click.Path(dir_okay=True, file_okay=False), default=None, required=False,
              help='Give the path to an existing pybids index database.')
@click.option('-refresh_index', is_flag=True, default=False, required=False,
              help='Refresh the pybids index database to reflect new fmriprep artifacts.')
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.option('-debug', is_flag = True, default=False, help = 'Print detailed processing information and traceback for errors.')
def fmri_postprocess2(subjects, config_file, fmriprep_dir, output_dir, 
                      processing_stream, batch, submit, log_dir, index_dir, 
                      refresh_index, debug):
    """Perform additional processing on fMRIPrepped data"""

    postprocess_subjects_controller(
        subjects=subjects, config_file=config_file,fmriprep_dir=fmriprep_dir, 
        output_dir=output_dir, processing_stream=processing_stream,
        batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir,
        refresh_index=refresh_index, debug=debug)


@click.command()
@click.argument('subject_id')
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME)
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.option('-batch/-no-batch', is_flag = True, default=True, help = 'Flag to create batch jobs without prompt.')
@click.option('-submit', is_flag = True, default=False, help = 'Flag to submit commands to the HPC without prompt.')
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_subject_cli(subject_id, bids_dir, fmriprep_dir, output_dir, 
                            processing_stream, config_file, index_dir, 
                            batch, submit, log_dir):
    
    postprocess_subject_controller(
        subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, 
        batch, submit, log_dir, processing_stream=processing_stream)


@click.command()
@click.argument('config_file', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('image_path', type=click.Path(dir_okay=False, file_okay=True))
@click.argument('bids_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('fmriprep_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('index_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('out_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('subject_out_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('processing_stream', default=DEFAULT_PROCESSING_STREAM_NAME)
@click.argument('subject_working_dir', type=click.Path(dir_okay=True, file_okay=False))
@click.argument('log_dir', type=click.Path(dir_okay=True, file_okay=False))
def postprocess_image_cli(config_file, image_path, bids_dir, fmriprep_dir, 
                          index_dir, out_dir, subject_out_dir, 
                          processing_stream, subject_working_dir, log_dir):
    
    postprocess_image_controller(
        config_file, image_path, bids_dir, fmriprep_dir, index_dir, out_dir, 
        subject_out_dir, subject_working_dir, log_dir, 
        processing_stream=processing_stream)


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-drop_tps', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = False,
              help='Drop timepoints csv sheet')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC.')
@click.option('-batch/-single', default=True,
              help='Submit to batch, or run in current session. Mainly used internally.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_setup(subjects, config_file, glm_config_file, submit, batch, debug, 
              drop_tps):
    """Prepare task images and confound files for GLM analysis"""

    glm_setup_logic(
        subjects=subjects, config_file=config_file, 
        glm_config_file=glm_config_file,
        submit=submit, batch=batch, debug=debug, drop_tps=drop_tps)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l1_preparefsf(glm_config_file, l1_name, debug):
    """Propagate an .fsf file template for L1 GLM analysis"""
    
    glm_l1_preparefsf_logic(
        glm_config_file=glm_config_file, l1_name=l1_name, debug=debug)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, 
              file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model')
@click.option('-test_one', is_flag=True,
              help='Only submit one job for testing purposes.')
@click.option('-submit', is_flag=True,
              help='Flag to submit commands to the HPC.')
@click.option('-debug', is_flag=True, 
              help='Flag to enable detailed error messages and traceback')
def glm_l1_launch(glm_config_file, l1_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 GLM analysis"""
    
    glm_l1_launch_controller(glm_config_file=glm_config_file, l1_name=l1_name,
                             test_one=test_one, submit=submit, debug=debug)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l2_name',  default=None, required = True,
              help='Name for a given L2 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l2_preparefsf(glm_config_file, l2_name, debug):
    """Propagate an .fsf file template for L2 GLM analysis"""
    glm_l2_preparefsf_logic(glm_config_file=glm_config_file, l2_name=l2_name, debug=debug)
@click.option('-l1_feat_folders_path', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False,
              help='Location of your L1 FEAT folders.')
def glm_apply_mumford_workaround(glm_config_file, l1_feat_folders_path):
    """
    Apply the Mumford registration workaround to L1 FEAT folders. 
    Applied by default in glm-l2-preparefsf.
    """
    if not (glm_config_file or l1_feat_folders_path):
        click.echo("Error: At least one of either option '-glm_config_file' or '-l1_feat_folders_path' required.")
        sys.exit()


@cli.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def glm_onset_extract(config_file, glm_config_file, debug):
    """Convert onset files to FSL's 3 column format"""
    fsl_onset_extract_logic(
        config_file=config_file, glm_config_file=glm_config_file, debug=debug)


@cli.command()
@click.option('--confounds_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="Path to a directory containing subjects and confounds files.")
@click.option('--confounds_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), help="Path to confounds file")
@click.option('--output_file', type=click.Path(dir_okay=False, file_okay=True), help="Path to save outlier count results.")
@click.option('--confound_suffix', help="Confound file to search for, like 'confounds.tsv'", default='confounds.tsv')
def report_outliers(confounds_dir, confounds_file, output_file, 
                    confound_suffix):
    """Generate a confound outliers report."""
    
    if confounds_dir:
        get_study_outliers(confounds_dir, output_file, confound_suffix)
    else:
        get_image_confounds(confounds_file)
