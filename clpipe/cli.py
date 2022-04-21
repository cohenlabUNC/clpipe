import click
import pkg_resources
import sys

from clpipe.project_setup import project_setup as project_setup_logic
from clpipe.dcm2bids_wrapper import convert2bids as convert2bids_logic
from clpipe.bids_validator import bids_validate as bids_validate_logic
from clpipe.fmri_preprocess import fmriprep_process as fmriprep_process_logic
from clpipe.glm_setup import glm_setup as glm_setup_logic
from clpipe.glm_l2 import glm_apply_mumford_workaround as glm_apply_mumford_workaround_logic

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


@click.command()
@click.argument('bids_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), required=False)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, help = 'Uses a given configuration file')
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
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = False,
              help='Use a given GLM configuration file.')
@click.option('-l1_feat_folders_path', type=click.Path(exists=True, dir_okay=True, file_okay=False), default=None, required = False,
              help='Location of your L1 FEAT folders.')
def glm_apply_mumford_workaround(glm_config_file, l1_feat_folders_path):
    """Apply the Mumford registration workaround to L1 FEAT folders. Applied by default in glm-l2-preparefsf. """
    if not (glm_config_file or l1_feat_folders_path):
        click.echo("Error: At least one of either option '-glm_config_file' or '-l1_feat_folders_path' required.")
        sys.exit()

    glm_apply_mumford_workaround_logic(glm_config_file=glm_config_file, l1_feat_folders_path=l1_feat_folders_path)