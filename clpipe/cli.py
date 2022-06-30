import click
import pkg_resources
import sys

from .fmri_postprocess2 import postprocess_image_controller,\
    postprocess_subject_controller, postprocess_subjects_controller,\
    DEFAULT_PROCESSING_STREAM_NAME
from .project_setup import project_setup as project_setup_logic
from .dcm2bids_wrapper import convert2bids as convert2bids_logic
from .bids_validator import bids_validate as bids_validate_logic
from .fmri_preprocess import fmriprep_process as fmriprep_process_logic
from .glm_setup import glm_setup as glm_setup_logic
from .glm_l1 import glm_l1_preparefsf as glm_l1_preparefsf_logic,\
    glm_l1_launch_controller
from .glm_l2 import glm_l2_preparefsf as glm_l2_preparefsf_logic
from .fsl_onset_extract import fsl_onset_extract as fsl_onset_extract_logic


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('-v', '--version', is_flag = True, default=False, help="Display clpipe's version.")
def cli(ctx, version):
    """Welcome to clpipe. Please choose a processing command."""
    if ctx.invoked_subcommand is None:
        if version:
            clpipe_version = pkg_resources.get_distribution('clpipe').version
            print(f"clpipe v{clpipe_version}")
            sys.exit(0)
        else:
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit()

@cli.command()
@click.option('-project_title', required=True, default=None)
@click.option('-project_dir', required = True ,type=click.Path(exists=False, dir_okay=True, file_okay=True), default=None,
              help='Where the project will be located.')
@click.option('-source_data', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Where the raw data (usually DICOMs) are located.')
@click.option('-move_source_data', is_flag = True, default = False,
              help='Move source data into project/data_DICOMs folder. USE WITH CAUTION.')
@click.option('-symlink_source_data', is_flag = True, default = False,
              help = 'symlink the source data into project/data_dicoms. Usually safe to do.')
def project_setup(project_title = None, project_dir = None, source_data = None, move_source_data = None,
                  symlink_source_data = None):
    """Set up a clpipe project"""
    project_setup_logic(project_title = project_title, project_dir = project_dir, source_data = source_data, move_source_data = move_source_data,
                  symlink_source_data = symlink_source_data)

@cli.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-conv_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default = None, help = 'The configuration file for the study, use if you have a custom batch configuration.')
@click.option('-dicom_dir', help = 'The folder where subject dicoms are located.')
@click.option('-dicom_dir_format', help = 'Format string for how subjects/sessions are organized within the dicom_dir.')
@click.option('-BIDS_dir', help = 'The dicom info output file name.')
@click.option('-overwrite', is_flag = True, default = False, help = "Overwrite existing BIDS data?")
@click.option('-log_dir', help = 'Where to put the log files. Defaults to Batch_Output in the current working directory.')
@click.option('-subject', required = False, help = 'A subject  to convert using the supplied configuration file.  Use to convert single subjects, else leave empty')
@click.option('-session', required = False, help = 'A session  to convert using the supplied configuration file.  Use in combination with -subject to convert single subject/sessions, else leave empty')
@click.option('-longitudinal', is_flag = True, default = False, help = 'Convert all subjects/sessions into individual pseudo-subjects. Use if you do not want T1w averaged across sessions during FMRIprep')
@click.option('-submit', is_flag=True, default=False, help = 'Submit jobs to HPC')
def convert2bids(dicom_dir, dicom_dir_format, bids_dir, conv_config_file, config_file, overwrite, log_dir, subject, session, longitudinal, submit):
    """Convert DICOM files to BIDS format"""
    convert2bids_logic(dicom_dir=dicom_dir, dicom_dir_format=dicom_dir_format, bids_dir=bids_dir, conv_config_file=conv_config_file, config_file=config_file, overwrite=overwrite,
        log_dir=log_dir, subject=subject, session=session, longitudinal=longitudinal, submit=submit)


@cli.command()
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Uses a given configuration file')
@click.argument('bids_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), required=False)
@click.option('-log_dir', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Set the log output path.')
@click.option('-verbose', is_flag = True, default=False, help = 'Creates verbose validator output. Use if you want to see ALL files with errors/warnings.')
@click.option('-submit', is_flag = True, help = 'Submit command to HPC.')
@click.option('-interactive', is_flag = True, default=False, help = 'Run in an interactive session. Only use in an interactive compute session.')
@click.option('-debug', is_flag=True, help = 'Produce detailed debug and traceback.')
def bids_validate(bids_dir, config_file, log_dir, interactive, submit, verbose, debug):
    bids_validate_logic(bids_dir=bids_dir, config_file=config_file, log_dir=log_dir, interactive=interactive, submit=submit, verbose=verbose, debug=debug)


@cli.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-bids_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which BIDS directory to process. If a configuration file is provided with a BIDS directory, this argument is not necessary.')
@click.option('-working_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to generate the working directory. If a configuration file is provided with a working directory, this argument is not necessary.')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the preprocessed data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-log_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files (such as SLURM output files)')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def fmriprep_process(bids_dir, working_dir, output_dir, config_file, subjects, log_dir, submit, debug):
    """Submit BIDS-formatted images to fMRIPrep"""
    fmriprep_process_logic(bids_dir=bids_dir, working_dir=working_dir, output_dir=output_dir, config_file=config_file, subjects=subjects,log_dir=log_dir,submit=submit, debug=debug)


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
def fmri_postprocess2(subjects, config_file, fmriprep_dir, output_dir, processing_stream, batch, submit, log_dir, index_dir, refresh_index, debug):
    """Perform additional processing on fMRIPrepped data"""
    postprocess_subjects_controller(subjects=subjects, config_file=config_file, fmriprep_dir=fmriprep_dir, output_dir=output_dir, 
        processing_stream=processing_stream, batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir, refresh_index=refresh_index, debug=debug)


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
def postprocess_subject_cli(subject_id, bids_dir, fmriprep_dir, output_dir, processing_stream, config_file, index_dir, 
    batch, submit, log_dir):
    
    postprocess_subject_controller(subject_id, bids_dir, fmriprep_dir, output_dir, config_file, index_dir, 
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
def postprocess_image_cli(config_file, image_path, bids_dir, fmriprep_dir, index_dir, 
    out_dir, subject_out_dir, processing_stream, subject_working_dir, log_dir):
    
    postprocess_image_controller(config_file, image_path, bids_dir, fmriprep_dir, 
    index_dir, out_dir, subject_out_dir, subject_working_dir, log_dir, processing_stream=processing_stream)


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
def glm_setup(subjects, config_file, glm_config_file, submit, batch, debug, drop_tps):
    """Prepare task images and confound files for GLM analysis"""
    glm_setup_logic(subjects = subjects, config_file=config_file, glm_config_file = glm_config_file,
                     submit=submit, batch=batch, debug = debug, drop_tps = drop_tps)


@cli.command()
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l1_preparefsf(glm_config_file, l1_name, debug):
    """Propagate an .fsf file template for L1 GLM analysis"""
    glm_l1_preparefsf_logic(glm_config_file=glm_config_file, l1_name=l1_name, debug=debug)


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
    """Apply the Mumford registration workaround to L1 FEAT folders. Applied by default in glm-l2-preparefsf. """
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
    fsl_onset_extract_logic(config_file=config_file, glm_config_file = glm_config_file, debug = debug)


@cli.command()
@click.option('--confounds_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), help="Path to a directory containing subjects and confounds files.")
@click.option('--confounds_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), help="Path to confounds file")
@click.option('--output_file', type=click.Path(dir_okay=False, file_okay=True), help="Path to save outlier count results.")
@click.option('--confound_suffix', help="Confound file to search for, like 'confounds.tsv'", default='confounds.tsv')
def report_outliers(confounds_dir, confounds_file, output_file, confound_suffix):
    """Generate a confound outliers report."""
    
    if confounds_dir:
        get_study_outliers(confounds_dir, output_file, confound_suffix)
    else:
        get_image_confounds(confounds_file)
