import click
import sys
import pkg_resources

from .config import *

DEFAULT_HELP_PRIORITY = 5

CONTEXT_SETTINGS = dict(help_option_names=['-h', '-help', '--help'])


class OrderedHelpGroup(click.Group):
    """
    A click.Group sub-class which allows sub commands to define their
    own display order within the main help command.

    Code adapted from Stephen Rauch's answer at:
        https://stackoverflow.com/questions/47972638/
        how-can-i-define-the-order-of-click-sub-commands-in-help
    """
    def __init__(self, *args, **kwargs):
        self.help_priorities = {}
        super(OrderedHelpGroup, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(OrderedHelpGroup, self).get_help(ctx)

    def list_commands_for_help(self, ctx):
        """reorder the list of commands when listing the help"""
        commands = super(OrderedHelpGroup, self).list_commands(ctx)
        return (c[1] for c in sorted(
            (self.help_priorities.get(command, 1), command)
                for command in commands)
        )

    def add_command(self, cmd: click.Command, name: str = None, 
                    help_priority: int=DEFAULT_HELP_PRIORITY) -> None:
        """
        Behaves the same as `click.Group.add_command()`, except capture
        a priority for listing command names in help.
        """
        help_priorities = self.help_priorities
        help_priorities[cmd.name] = help_priority
        
        return super().add_command(cmd, name)


@click.group(cls=OrderedHelpGroup, context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True)
@click.pass_context
@click.option("-v", "--version", is_flag=True, default=False, 
        help=VERSION_HELP)
def cli(ctx, version):
    """Welcome to clpipe.
    
    Please choose one of the commands below for more information.

    If you're not sure where to begin, please see the documentation at:
    https://clpipe.readthedocs.io/en/latest/index.html
    """

    if ctx.invoked_subcommand is None:
        if version:
            clpipe_version = pkg_resources.get_distribution("clpipe").version
            print(f"clpipe v{clpipe_version}")
            sys.exit(0)
        else:
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit()


@click.group("glm", cls=OrderedHelpGroup)
def glm_cli():
    """General Linear Model (GLM) Commands.
    
    Please choose one of the commands below for more
    information.
    """


@click.group("bids")
def bids_cli():
    """BIDS Commands.
    
    Please choose one of the commands below for more information.
    """

@click.group("roi", cls=OrderedHelpGroup)
def roi_cli():
    """Region of Interest (ROI) Commands.
    
    Please choose one of the commands below for more information.
    """

def _add_commands():
    cli.add_command(project_setup_cli, help_priority=1)
    cli.add_command(fmriprep_process_cli, help_priority=3)
    cli.add_command(fmri_postprocess_cli, help_priority=4)
    cli.add_command(fmri_postprocess2_cli, help_priority=4)
    cli.add_command(status_cli)

    bids_cli.add_command(convert2bids_cli)
    bids_cli.add_command(bids_validate_cli)

    glm_cli.add_command(glm_setup_cli, help_priority=1)
    glm_cli.add_command(glm_l1_preparefsf_cli, help_priority=3)
    glm_cli.add_command(glm_launch_cli, help_priority=4)
    glm_cli.add_command(glm_l2_preparefsf_cli, help_priority=6)
    glm_cli.add_command(glm_apply_mumford_workaround_cli, help_priority=5)
    glm_cli.add_command(fsl_onset_extract_cli, help_priority=2)
    glm_cli.add_command(report_outliers_cli, help_priority=7)

    roi_cli.add_command(get_availablea_atlases_cli, help_priority=1)
    roi_cli.add_command(fmri_roi_extraction_cli, help_priority=2)

    cli.add_command(bids_cli, help_priority=2)
    cli.add_command(glm_cli)
    cli.add_command(roi_cli)


@click.command(SETUP_COMMAND_NAME, no_args_is_help=True)
@click.option('-project_title', required=True, default=None)
@click.option('-project_dir', required=True ,type=CLICK_DIR_TYPE_NOT_EXIST,
              default=None, help=PROJECT_DIR_HELP)
@click.option('-source_data', type=CLICK_DIR_TYPE_EXISTS,
              help=SOURCE_DATA_HELP)
@click.option('-move_source_data', is_flag=True, default=False,
              help=MOVE_SOURCE_DATA_HELP)
@click.option('-symlink_source_data', is_flag=True, default=False,
              help=SYM_LINK_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
def project_setup_cli(project_title=None, project_dir=None, source_data=None, 
                      move_source_data=None, symlink_source_data=None,
                      debug=False):
    """Set up a clpipe project."""
    from .project_setup import project_setup
    project_setup(
        project_title=project_title, 
        project_dir=project_dir, source_data=source_data, 
        move_source_data=move_source_data,
        symlink_source_data=symlink_source_data,debug=debug)


@click.command(CONVERSION_COMMAND_NAME, no_args_is_help=True)
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', '-c', type=CLICK_FILE_TYPE_EXISTS, default=None,
              help=CONFIG_HELP)
@click.option('-conv_config_file', type=CLICK_FILE_TYPE_EXISTS, default=None, 
              help=CONVERSION_CONFIG_HELP)
@click.option('-dicom_dir', '-i', type=CLICK_DIR_TYPE_EXISTS, help=DICOM_DIR_HELP)
@click.option('-dicom_dir_format', help=DICOM_DIR_FORMAT_HELP)
@click.option('-BIDS_dir', '-o', type=CLICK_DIR_TYPE_EXISTS,
              help=BIDS_DIR_HELP)
@click.option('-overwrite', is_flag=True, default=False, help=OVERWRITE_HELP)
@click.option('-clear_cache', is_flag=True, default=False, help="Clear cached data for given subject.",
    hidden=True)
@click.option('-clear_outputs', is_flag=True, default=False, help="Clear all BIDS data for given subject.",
    hidden=True)
@click.option('-log_dir', type=CLICK_DIR_TYPE_EXISTS, help=LOG_DIR_HELP)
@click.option('-subject', required=False, help=SUBJECT_HELP)
@click.option('-session', required=False, help=SESSION_HELP)
@click.option('-longitudinal', is_flag=True, default=False,
              help=LONGITUDINAL_HELP)
@click.option('-submit', '-s', is_flag=True, default=False, help=SUBMIT_HELP)
@click.option('-batch/-no-batch', is_flag = True, default=True, 
              help=BATCH_HELP, hidden=True)
@click.option('-debug', '-d', is_flag=True, help=DEBUG_HELP)
@click.option('-dcm2bids/-heudiconv', default=True, help=MODE_HELP)
@click.option('-status_cache', default=None, type=CLICK_FILE_TYPE, 
              help=STATUS_CACHE_HELP, hidden=True)
def convert2bids_cli(dicom_dir, dicom_dir_format, bids_dir, 
                     conv_config_file, dcm2bids,
                     config_file, overwrite, clear_cache, clear_outputs, 
                     log_dir, subject, subjects, session, 
                     longitudinal, submit, batch, debug, status_cache):
    """Convert DICOM files to BIDS format.
    
    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects: 

    > clpipe bids convert 123 124 125 ...

    Available subject IDs are determined by the dicom_dir_format string.
    """
    from .bids_conversion import convert2bids
    convert2bids(
        dicom_dir=dicom_dir, dicom_dir_format=dicom_dir_format, 
        bids_dir=bids_dir, conv_config_file=conv_config_file,
        config_file=config_file, overwrite=overwrite, clear_cache=clear_cache, clear_outputs=clear_outputs, 
        log_dir=log_dir, batch=batch, subject=subject, subjects=subjects, session=session, 
        longitudinal=longitudinal, submit=submit, status_cache=status_cache, debug=debug, dcm2bids=dcm2bids)


@click.command(VALIDATOR_COMMAND_NAME, no_args_is_help=True)
@click.argument('bids_dir', type=CLICK_DIR_TYPE_EXISTS, required=False)
@click.option('-config_file', type=CLICK_FILE_TYPE_EXISTS, default=None, 
              help=CONFIG_HELP)
@click.option('-log_dir', type=CLICK_FILE_TYPE_EXISTS, default=None,
              help=LOG_DIR_HELP)
@click.option('-verbose', is_flag=True, default=False,
              help=VERBOSE_HELP)
@click.option('-submit', is_flag=True, help=SUBMIT_HELP)
@click.option('-interactive', is_flag=True, default=False,
              help=INTERACTIVE_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
def bids_validate_cli(bids_dir, config_file, log_dir, interactive, submit,
                      verbose, debug):
    """Validate if a directory BIDS standard.

    Validates the directory at BIDS_DIR, or at the BIDS directory 
    in your config file's DICOMToBIDSOptions if -config_file is given.

    Results are viewable in logs/bids_validation_logs unless -interactive is used.
    """
    from .bids_validator import bids_validate
    bids_validate(
        bids_dir=bids_dir, config_file=config_file, log_dir=log_dir, 
        interactive=interactive, submit=submit, verbose=verbose, debug=debug)


@click.command(FMRIPREP_COMMAND_NAME, no_args_is_help=True)
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', default=None, type=CLICK_FILE_TYPE_EXISTS, 
              help=CONFIG_HELP)
@click.option('-bids_dir', type=CLICK_DIR_TYPE_EXISTS,
              help=BIDS_DIR_HELP)
@click.option('-working_dir', type=CLICK_DIR_TYPE, 
              help=WORKING_DIR_HELP)
@click.option('-output_dir', type=CLICK_DIR_TYPE,
              help=FMRIPREP_OUTPUT_DIR_HELP)
@click.option('-log_dir', type=CLICK_DIR_TYPE, help=LOG_DIR_HELP)
@click.option('-submit', is_flag=True, default=False, help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, help=DEBUG_HELP)
@click.option('-status_cache', default=None, type=CLICK_FILE_TYPE, 
              help=STATUS_CACHE_HELP, hidden=True)
def fmriprep_process_cli(bids_dir, working_dir, output_dir, config_file, 
                         subjects, log_dir, submit, debug, status_cache):
    """Submit BIDS-formatted images to fMRIPrep.
    
    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects: 

    > clpipe preprocess 123 124 125 ...
    """
    from .fmri_preprocess import fmriprep_process
    fmriprep_process(
        bids_dir=bids_dir, working_dir=working_dir,
        output_dir=output_dir, config_file=config_file, 
        subjects=subjects, log_dir=log_dir, submit=submit, debug=debug, 
        status_cache=status_cache)


@click.command(POSTPROCESS_COMMAND_NAME, no_args_is_help=True)
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
def fmri_postprocess_cli(config_file=None, subjects=None, target_dir=None, 
                         target_suffix=None, output_dir=None,
                         output_suffix=None, log_dir=None,
                         submit=False, batch=True, task=None, tr=None, 
                         processing_stream = None, debug = False, 
                         beta_series = False):
    """Additional processing for connectivity analysis.
    
    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects: 

    > clpipe postprocess 123 124 125 ...
    """
    from .fmri_postprocess import fmri_postprocess
    fmri_postprocess(
        config_file=config_file, subjects=subjects, target_dir=target_dir, 
        target_suffix=target_suffix, output_dir=output_dir, 
        output_suffix=output_suffix, log_dir=log_dir, submit=submit, 
        batch=batch, task=task, tr=tr, processing_stream=processing_stream, 
        debug=debug, beta_series=beta_series)


@click.command(POSTPROCESS2_COMMAND_NAME, no_args_is_help=True)
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', '-c', type=CLICK_FILE_TYPE_EXISTS, default=None, 
              required=True, help=CONFIG_HELP)
@click.option('-fmriprep_dir', '-i', type=CLICK_DIR_TYPE_EXISTS, 
              help=FMRIPREP_DIR_HELP)
@click.option('-output_dir', '-o', type=CLICK_DIR_TYPE, default=None, required=False,
              help=OUTPUT_DIR_HELP)
@click.option('-processing_stream', '-p', default=DEFAULT_PROCESSING_STREAM_NAME, 
required=False, help=PROCESSING_STREAM_HELP)
@click.option('-log_dir', '-l', type=CLICK_DIR_TYPE_EXISTS, default=None, 
              required=False, help=LOG_DIR_HELP)
@click.option('-index_dir', type=CLICK_DIR_TYPE, default=None, required=False,
              help=INDEX_HELP)
@click.option('-refresh_index', '-r', is_flag=True, default=False, required=False,
              help=REFRESH_INDEX_HELP)
@click.option('-batch/-no-batch', is_flag = True, default=True, 
              help=BATCH_HELP)
@click.option('-cache/-no-cache', is_flag=True, default=True)
@click.option('-submit', '-s', is_flag = True, default=False, help=SUBMIT_HELP)
@click.option('-debug', '-d', is_flag = True, default=False, help=DEBUG_HELP)
def fmri_postprocess2_cli(subjects, config_file, fmriprep_dir, output_dir, 
                          processing_stream, batch, submit, log_dir, index_dir, 
                          refresh_index, debug, cache):
    """Additional processing for GLM or connectivity analysis.
    
    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects: 

    > clpipe postprocess2 123 124 125 ...
    """
    from .fmri_postprocess2 import postprocess_subjects
    postprocess_subjects(
        subjects=subjects, config_file=config_file,fmriprep_dir=fmriprep_dir, 
        output_dir=output_dir, processing_stream=processing_stream,
        batch=batch, submit=submit, log_dir=log_dir, pybids_db_path=index_dir,
        refresh_index=refresh_index, debug=debug, cache=cache)


@click.command(GLM_SETUP_COMMAND_NAME, no_args_is_help=True)
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
def glm_setup_cli(subjects, config_file, glm_config_file, submit, batch, debug, 
                  drop_tps):
    """Additional preprocessing for GLM analysis.
    
    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects: 

    > clpipe glm setup 123 124 125 ...
    """
    from .glm_setup import glm_setup
    glm_setup(
        subjects=subjects, config_file=config_file, 
        glm_config_file=glm_config_file,
        submit=submit, batch=batch, debug=debug, drop_tps=drop_tps)


@click.command(L1_PREPARE_FSF_COMMAND_NAME, no_args_is_help=True)
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None, required = True,
              help='Your GLM configuration file.')
@click.option('-l1_name',  default=None, required = True,
              help='Name for a given L1 model as defined in your GLM configuration file.')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def glm_l1_preparefsf_cli(glm_config_file, l1_name, debug):
    """Propagate an .fsf file template for L1 GLM analysis.
    
    You must create a template .fsf file in FSL's FEAT GUI first.
    """
    from .glm_l1 import glm_l1_preparefsf
    glm_l1_preparefsf(
        glm_config_file=glm_config_file, l1_name=l1_name, debug=debug)


@click.command(L2_PREPARE_FSF_COMMAND_NAME, no_args_is_help=True)
@click.option('-glm_config_file', type=CLICK_FILE_TYPE_EXISTS, default=None,
              required=True, help='Your GLM configuration file.')
@click.option('-l2_name', default=None, required=True,
              help='Name for a given L2 model')
@click.option('-debug', is_flag=True,
              help='Flag to enable detailed error messages and traceback')
def glm_l2_preparefsf_cli(glm_config_file, l2_name, debug):
    """Propagate an .fsf file template for L2 GLM analysis.
    
    You must create a group-level template .fsf file in FSL's FEAT GUI first.
    """
    from .glm_l2 import glm_l2_preparefsf
    glm_l2_preparefsf(glm_config_file=glm_config_file, l2_name=l2_name,
                      debug=debug)


@click.command(APPLY_MUMFORD_COMMAND_NAME, no_args_is_help=True)
@click.option('-glm_config_file', type=CLICK_FILE_TYPE_EXISTS, default=None,
              required=False,
              help='Your GLM configuration file.')
@click.option('-l1_feat_folders_path', type=CLICK_DIR_TYPE_EXISTS,
              default=None, required=False,
              help='Directory containing your L1 FEAT folders.')
@click.option('-remove_reg_standard', is_flag=True, default=False,
              help='Remove reg_standard folders (generated by L2) in addition to reg.')
@click.option('-debug', is_flag=True, default=False,
              help='Flag to enable detailed error messages and traceback')
def glm_apply_mumford_workaround_cli(glm_config_file, l1_feat_folders_path,
                                     remove_reg_standard, debug):
    """
    Apply the Mumford registration workaround to L1 FEAT folders. 
    
    Applied by default in glm-l2-preparefsf. This command is useful for applying
    the Mumford workaround to single-run subjects who skip L2, allowing you to still
    combine them with multiple-run subjects at L3.

    Must provide GLM config file OR a path to your L1 FEAT folders.
    """
    from .glm_l2 import glm_apply_mumford_workaround
    if not (glm_config_file or l1_feat_folders_path):
        click.echo(("Error: At least one of either option '-glm_config_file' "
                    "or '-l1_feat_folders_path' required."))
    glm_apply_mumford_workaround(
        glm_config_file=glm_config_file,
        l1_feat_folders_path=l1_feat_folders_path, debug=debug,
        remove_reg_standard=remove_reg_standard
    )


@click.command(GLM_LAUNCH_COMMAND_NAME, no_args_is_help=True)
@click.argument('level')
@click.argument('model')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, 
              file_okay=True), default=None, required = True,
              help=CONFIG_HELP)
@click.option('-test_one', is_flag=True,
              help=TEST_ONE_HELP)
@click.option('-submit', is_flag=True,
              help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, 
              help=DEBUG_HELP)
def glm_launch_cli(level, model, glm_config_file, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 or L2 GLM analysis.
    
    L1 can be any of: 1, L1, l1, or level1.

    L2 can be any of: 2, L2, l2, or level2.

    MODEL must be a a corresponding L1 or L2 model from your GLM configuration file.
    """
    from .glm_launch import glm_launch_controller
    glm_launch_controller(glm_config_file=glm_config_file, level=level, 
                          model=model, test_one=test_one, 
                          submit=submit, debug=debug)


@click.command(no_args_is_help=True)
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, 
              file_okay=True), default=None, required = True,
              help=CONFIG_HELP)
@click.option('-l1_name',  default=None, required = True,
              help=L1_MODEL_HELP)
@click.option('-test_one', is_flag=True,
              help=TEST_ONE_HELP)
@click.option('-submit', is_flag=True,
              help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, 
              help=DEBUG_HELP)
def glm_l1_launch_cli(glm_config_file, l1_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 GLM analysis."""
    from .glm_launch import glm_launch_controller
    glm_launch_controller(glm_config_file=glm_config_file, model=l1_name,
                          test_one=test_one, submit=submit, debug=debug)


@click.command(no_args_is_help=True)
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, 
              file_okay=True), default=None, required = True,
              help=CONFIG_HELP)
@click.option('-l2_name',  default=None, required = True,
              help=L2_MODEL_HELP)
@click.option('-test_one', is_flag=True,
              help=TEST_ONE_HELP)
@click.option('-submit', is_flag=True,
              help=SUBMIT_HELP)
@click.option('-debug', is_flag=True, 
              help=DEBUG_HELP)
def glm_l2_launch_cli(glm_config_file, l2_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L2 GLM analysis."""
    from .glm_launch import glm_launch_controller
    glm_launch_controller(glm_config_file=glm_config_file, level="L2", 
                          model=l2_name, test_one=test_one, submit=submit,
                          debug=debug)


@click.command(ONSET_EXTRACT_COMMAND_NAME, no_args_is_help=True)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), 
              default=None, required = True,
              help='Use a given configuration file.')
@click.option('-glm_config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), 
              default=None, required = True,
              help='Use a given GLM configuration file.')
@click.option('-debug', is_flag=True, default=False,
              help='Print detailed processing information and traceback for errors.')
def fsl_onset_extract_cli(config_file, glm_config_file, debug):
    """Convert onset files to FSL's 3 column format."""
    from .fsl_onset_extract import fsl_onset_extract
    fsl_onset_extract(
        config_file=config_file, glm_config_file=glm_config_file, debug=debug)


@click.command("extract", no_args_is_help=True)
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories. This will extract all ROI sets specified in the configuration file.')
@click.option('-target_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help='Which postprocessed directory to process. If a configuration file is provided with a target directory, this argument is not necessary.')
@click.option('-target_suffix',
              help='Which target suffix to process. If a configuration file is provided with a target suffix, this argument is not necessary.')
@click.option('-output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put the ROI extracted data. If a configuration file is provided with a output directory, this argument is not necessary.')
@click.option('-task', help = 'Which task to process. If none, then all tasks are processed.')
@click.option('-atlas_name', help = "What atlas to use. Please refer to documentation, or use the command get_available_atlases to see which are available. When specified for a custom atlas, this is what the output files will be named.")
@click.option('-custom_atlas', help = 'A custom atlas image, in .nii or .nii.gz for label or maps, or a .txt tab delimited set of ROI coordinates if for a sphere atlas. Not needed if specified in config.')
@click.option('-custom_label', help = 'A custom atlas label file. Not needed if specified in config.')
@click.option('-custom_type', help = 'What type of atlas? (label, maps, or spheres). Not needed if specified in config.')
@click.option('-radius', help = "If a sphere atlas, what radius sphere, in mm. Not needed if specified in config.", default = '5')
@click.option('-overlap_ok', is_flag=True, default=False, help = "Are overlapping ROIs allowed?")
@click.option('-overwrite', is_flag=True, default=False, help = "Overwrite existing ROI timeseries?")
@click.option('-log_output_dir', type=click.Path(dir_okay=True, file_okay=False),
              help='Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-single', is_flag=True, default=False, help='Flag to directly run command. Used internally.')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def fmri_roi_extraction_cli(subjects, config_file, target_dir, target_suffix, 
                            output_dir, task, log_output_dir, atlas_name, custom_atlas,
                            custom_label, custom_type, radius, submit, single, 
                            overlap_ok, debug, overwrite):
    """Extract ROIs with a given atlas."""
    from .roi_extractor import fmri_roi_extraction
    fmri_roi_extraction(
        subjects=subjects,config_file=config_file, target_dir=target_dir,
        target_suffix=target_suffix, output_dir=output_dir, task=task,
        log_output_dir=log_output_dir, atlas_name=atlas_name, custom_atlas=custom_atlas,
        custom_label=custom_label, custom_type=custom_type, radius=radius,
        submit=submit, single=single, overlap_ok=overlap_ok, debug=debug,
        overwrite=overwrite)


@click.command("atlases")
def get_availablea_atlases_cli():
    """Display all available atlases."""
    from .roi_extractor import get_available_atlases
    get_available_atlases()


@click.command(OUTLIERS_COMMAND_NAME, no_args_is_help=True)
@click.option('--confounds_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False), 
              help="Path to a directory containing subjects and confounds files.")
@click.option('--confounds_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), 
              help="Path to confounds file")
@click.option('--output_file', type=click.Path(dir_okay=False, file_okay=True), 
              help="Path to save outlier count results.")
@click.option('--confound_suffix', help="Confound file to search for, like 'confounds.tsv'", 
              default='confounds.tsv')
def report_outliers_cli(confounds_dir, confounds_file, output_file, 
                    confound_suffix):
    """Generate a confound outliers report.
    
    Must provide one of either --confounds_dir or --confounds_file.
    """
    from .outliers_report import get_study_outliers, get_image_confounds
    if confounds_dir:
        get_study_outliers(confounds_dir, output_file, confound_suffix)
    else:
        get_image_confounds(confounds_file)


@click.command(STATUS_COMMAND_NAME)
@click.option('-config_file', type=CLICK_FILE_TYPE_EXISTS,
              help=CONFIG_HELP, required=False)
@click.option('-cache_file', type=CLICK_FILE_TYPE_EXISTS,
              help=CACHE_FILE_HELP, required=False)
def status_cli(config_file, cache_file):
    """Check the status of your project."""
    from .status import show_latest_by_step
    show_latest_by_step(config_file=config_file, cache_path=cache_file)

_add_commands()
