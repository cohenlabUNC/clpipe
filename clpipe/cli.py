# Note: these imports must remain light to ensure the CLI runs quickly.
# Do not import any sub-command dependencies here directly! Lazy-load them by
#   importing within their respective CLI commands.
import click
import sys
from .config.cli import *
from .config.options import DEFAULT_PROCESSING_STREAM
from .config.package import VERSION

DEFAULT_HELP_PRIORITY = 5
CONTEXT_SETTINGS = dict(help_option_names=["-help"], show_default=True)

# Click path validation types
CLICK_FILE_TYPE = click.Path(dir_okay=False, file_okay=True)
CLICK_FILE_TYPE_EXISTS = click.Path(exists=True, dir_okay=False, file_okay=True)
CLICK_DIR_TYPE = click.Path(dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_EXISTS = click.Path(exists=True, dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_NOT_EXIST = click.Path(exists=False, dir_okay=True, file_okay=False)


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
        self.hidden_commands = []
        super(OrderedHelpGroup, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        self.list_commands = self.list_commands_for_help
        return super(OrderedHelpGroup, self).get_help(ctx)

    def list_commands_for_help(self, ctx):
        """reorder the list of commands when listing the help"""
        commands = super(OrderedHelpGroup, self).list_commands(ctx)
        commands = (
            c[1]
            for c in sorted(
                (
                    self.help_priorities.get(command, 1),
                    command if command not in self.hidden_commands else None,
                )
                for command in commands
            )
        )
        # commands = [command if command not in self.hidden_commands else None for command in commands]
        return commands

    def add_command(
        self,
        cmd: click.Command,
        name: str = None,
        help_priority: int = DEFAULT_HELP_PRIORITY,
        hidden: bool = False,
    ) -> None:
        """
        Behaves the same as `click.Group.add_command()`, except capture
        a priority for listing command names in help.
        """
        help_priorities = self.help_priorities
        help_priorities[cmd.name] = help_priority
        if hidden:
            self.hidden_commands.append(cmd.name)

        return super().add_command(cmd, name)


@click.group(
    cls=OrderedHelpGroup, context_settings=CONTEXT_SETTINGS, invoke_without_command=True
)
@click.pass_context
@click.option("-version", "-v", is_flag=True, default=False, help=VERSION_HELP)
def cli(ctx, version):
    """Welcome to clpipe.

    Please choose one of the commands below for more information.

    If you're not sure where to begin, please see the documentation at:
    https://clpipe.readthedocs.io/en/latest/index.html
    """

    if ctx.invoked_subcommand is None:
        if version:
            print(f"clpipe v{VERSION}")
            sys.exit(0)
        else:
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit()


@click.group("dicom")
def dicom_cli():
    """Raw DICOM Data Commands.

    Please choose one of the commands below for more information.
    """


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


@click.group("reports", cls=OrderedHelpGroup)
def reports_cli():
    """Generate reports for your project.

    Please choose one of the commands below for more information.
    """


@click.group("config", cls=OrderedHelpGroup)
def config_cli():
    """Configuration-related commands."""


def _add_commands():
    cli.add_command(project_setup_cli, help_priority=0)
    cli.add_command(convert2bids_cli, help_priority=10)
    cli.add_command(bids_validate_cli, help_priority=15)
    cli.add_command(templateflow_setup_cli, help_priority=17, hidden=True)
    cli.add_command(fmriprep_process_cli, help_priority=20)
    cli.add_command(postprocess_cli, help_priority=35)
    cli.add_command(flywheel_sync_cli, help_priority=55)
    cli.add_command(config_cli, help_priority=95)

    dicom_cli.add_command(flywheel_sync_cli)
    dicom_cli.add_command(convert2bids_cli)

    bids_cli.add_command(bids_validate_cli)

    # setup command hidden due to deprecation
    glm_cli.add_command(glm_prepare_cli, help_priority=3)
    glm_cli.add_command(glm_launch_cli, help_priority=4)
    glm_cli.add_command(glm_apply_mumford_workaround_cli, help_priority=5)
    glm_cli.add_command(fsl_onset_extract_cli, help_priority=2)
    glm_cli.add_command(report_outliers_cli, help_priority=7)
    glm_cli.add_command(get_glm_config_cli, help_priority=20)

    roi_cli.add_command(get_available_atlases_cli, help_priority=1)
    roi_cli.add_command(fmri_roi_extraction_cli, help_priority=2)

    reports_cli.add_command(get_fmriprep_reports_cli)

    config_cli.add_command(get_config_cli)
    config_cli.add_command(update_config_cli)

    cli.add_command(bids_cli, help_priority=11, hidden=True)
    cli.add_command(dicom_cli, help_priority=5, hidden=True)
    cli.add_command(glm_cli, help_priority=40)
    cli.add_command(roi_cli, help_priority=50)
    cli.add_command(reports_cli, help_priority=60)
    cli.add_command(status_cli, help_priority=70, hidden=True)


@click.command(SETUP_COMMAND_NAME, no_args_is_help=True)
@click.option("-project_title", required=False, default=None, help=PROJECT_TITLE_HELP)
@click.option(
    "-project_dir",
    required=True,
    type=CLICK_DIR_TYPE_NOT_EXIST,
    default=None,
    help=PROJECT_DIR_HELP,
)
@click.option("-source_data", type=CLICK_DIR_TYPE_EXISTS, help=SOURCE_DATA_HELP)
@click.option(
    "-move_source_data", is_flag=True, default=False, help=MOVE_SOURCE_DATA_HELP
)
@click.option("-symlink_source_data", is_flag=True, default=False, help=SYM_LINK_HELP)
@click.option('-profile', required=False, default=UNC, help=PROFILE_HELP)
@click.option("-debug", is_flag=True, help=DEBUG_HELP)
def project_setup_cli(
    project_title=None,
    project_dir=None,
    source_data=None,
    move_source_data=None,
    symlink_source_data=None, profile=None,
    debug=False,
):
    """Initialize a clpipe project."""
    # TODO: add prompts for more things like contributors, email, etc.
    if project_title is None:
        project_title = click.prompt("Please enter a name for your project:", type=str)

    from .project_setup import project_setup

    project_setup(
        project_title=project_title,
        project_dir=project_dir,
        source_data=source_data,
        move_source_data=move_source_data,
        symlink_source_data=symlink_source_data,
        profile=profile,
        debug=debug)


@click.command(CONVERSION_COMMAND_NAME, no_args_is_help=True)
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file", "-c", type=CLICK_FILE_TYPE_EXISTS, required=True, help=CONFIG_HELP
)
@click.option(
    "-conv_config_file",
    type=CLICK_FILE_TYPE_EXISTS,
    default=None,
    help=CONVERSION_CONFIG_HELP,
)
@click.option("-dicom_dir", "-i", type=CLICK_DIR_TYPE_EXISTS, help=DICOM_DIR_HELP)
@click.option("-dicom_dir_format", help=DICOM_DIR_FORMAT_HELP)
@click.option("-BIDS_dir", "-o", type=CLICK_DIR_TYPE_EXISTS, help=BIDS_DIR_HELP)
@click.option("-overwrite", is_flag=True, default=False, help=OVERWRITE_HELP)
@click.option(
    "-clear_cache",
    is_flag=True,
    default=False,
    help="Clear cached data for given subject.",
    hidden=True,
)
@click.option(
    "-clear_outputs",
    is_flag=True,
    default=False,
    help="Clear all BIDS data for given subject.",
    hidden=True,
)
@click.option("-log_dir", type=CLICK_DIR_TYPE_EXISTS, help=LOG_DIR_HELP)
@click.option("-subject", required=False, help=SUBJECT_HELP)
@click.option("-session", required=False, help=SESSION_HELP)
@click.option("-longitudinal", is_flag=True, default=False, help=LONGITUDINAL_HELP)
@click.option("-submit", "-s", is_flag=True, default=False, help=SUBMIT_HELP)
@click.option(
    "-batch/-no-batch", is_flag=True, default=True, help=BATCH_HELP, hidden=True
)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
@click.option(
    "-status_cache",
    default=None,
    type=CLICK_FILE_TYPE,
    help=STATUS_CACHE_HELP,
    hidden=True,
)
def convert2bids_cli(
    dicom_dir,
    dicom_dir_format,
    bids_dir,
    conv_config_file,
    config_file,
    overwrite,
    clear_cache,
    clear_outputs,
    log_dir,
    subject,
    subjects,
    session,
    longitudinal,
    submit,
    batch,
    debug,
    status_cache,
):
    """Convert DICOM files to BIDS format.

    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects:

    > clpipe convert2bids 123 124 125 ...

    Available subject IDs are determined by the dicom_dir_format string.
    """
    from .convert2bids import convert2bids

    convert2bids(
        dicom_dir=dicom_dir,
        dicom_dir_format=dicom_dir_format,
        bids_dir=bids_dir,
        conv_config_file=conv_config_file,
        config_file=config_file,
        overwrite=overwrite,
        clear_cache=clear_cache,
        clear_outputs=clear_outputs,
        log_dir=log_dir,
        batch=batch,
        subject=subject,
        subjects=subjects,
        session=session,
        longitudinal=longitudinal,
        submit=submit,
        status_cache=status_cache,
        debug=debug,
    )


@click.command(VALIDATOR_COMMAND_NAME, no_args_is_help=True)
@click.argument("bids_dir", type=CLICK_DIR_TYPE_EXISTS, required=False)
@click.option(
    "-config_file", "-c", type=CLICK_FILE_TYPE_EXISTS, required=True, help=CONFIG_HELP
)
@click.option("-log_dir", type=CLICK_FILE_TYPE_EXISTS, default=None, help=LOG_DIR_HELP)
@click.option("-verbose", "-v", is_flag=True, default=False, help=VERBOSE_HELP)
@click.option("-submit", "-s", is_flag=True, help=SUBMIT_HELP)
@click.option("-interactive", is_flag=True, default=False, help=INTERACTIVE_HELP)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
def bids_validate_cli(
    bids_dir, config_file, log_dir, interactive, submit, verbose, debug
):
    """Validate if a directory BIDS standard.

    Validates the directory at BIDS_DIR, or at the BIDS directory
    in your config file's DICOMToBIDSOptions if -config_file is given.

    Results are viewable in logs/bids_validation_logs unless -interactive is used.
    """
    from .bids_validator import bids_validate

    bids_validate(
        bids_dir=bids_dir,
        config_file=config_file,
        log_dir=log_dir,
        interactive=interactive,
        submit=submit,
        verbose=verbose,
        debug=debug,
    )


@click.command(FMRIPREP_COMMAND_NAME, no_args_is_help=True)
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file", "-c", required=True, type=CLICK_FILE_TYPE_EXISTS, help=CONFIG_HELP
)
@click.option("-bids_dir", "-i", type=CLICK_DIR_TYPE_EXISTS, help=BIDS_DIR_HELP)
@click.option("-working_dir", type=CLICK_DIR_TYPE, help=WORKING_DIR_HELP)
@click.option("-output_dir", "-o", type=CLICK_DIR_TYPE, help=FMRIPREP_OUTPUT_DIR_HELP)
@click.option("-log_dir", type=CLICK_DIR_TYPE, help=LOG_DIR_HELP)
@click.option("-submit", "-s", is_flag=True, default=False, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
@click.option(
    "-status_cache",
    default=None,
    type=CLICK_FILE_TYPE,
    help=STATUS_CACHE_HELP,
    hidden=True,
)
def fmriprep_process_cli(
    bids_dir,
    working_dir,
    output_dir,
    config_file,
    subjects,
    log_dir,
    submit,
    debug,
    status_cache,
):
    """Submit BIDS-formatted images to fMRIPrep.

    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects:

    > clpipe preprocess 123 124 125 ...
    """
    from .fmri_preprocess import fmriprep_process

    fmriprep_process(
        bids_dir=bids_dir,
        working_dir=working_dir,
        output_dir=output_dir,
        config_file=config_file,
        subjects=subjects,
        log_dir=log_dir,
        submit=submit,
        debug=debug,
        status_cache=status_cache,
    )


@click.command("fmriprep", no_args_is_help=True)
@click.option(
    "-config_file",
    "-c",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    default=None,
    help="The configuration file for the current data processing setup.",
)
@click.option(
    "-output_name",
    "-o",
    default="fMRIPrep_Reports",
    help='Path and name of the output archive. Defaults to current working directory and "fMRIPrep_Reports.zip"',
)
@click.option(
    "-clear_temp/-keep_temp",
    is_flag=True,
    default=True,
    help="Keep or clear the built temporary directory. Defaults to clear_temp.",
)
@click.option("-debug", "-d", is_flag=True, help="Print traceback on errors.")
def get_fmriprep_reports_cli(config_file, output_name, clear_temp, debug):
    """
    Create a .zip directory of all fMRIPrep reports.
    """
    from .get_reports import get_reports

    get_reports(config_file, output_name, debug, clear_temp=clear_temp)


@click.command("fmri-process-check", no_args_is_help=True)
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help="The configuration file for the current data processing setup.",
)
@click.option(
    "-output_file",
    help='Path and name of the output archive. Defaults to current working directory and "Report_Archive.zip"',
)
@click.option(
    "-debug", is_flag=True, help="Print traceback and detailed processing messages."
)
def get_fmri_process_check_cli(config_file, output_file=None, debug=False):
    """This command checks a BIDS dataset, an fMRIprep'ed dataset and a postprocessed
    dataset, and creates a CSV file that lists all scans across all three datasets.
    Use to find which subjects/scans failed processing."""
    from .fmri_process_check import fmri_process_check

    fmri_process_check(config_file, output_file, debug)


@click.command(POSTPROCESS_COMMAND_NAME, no_args_is_help=True)
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file", "-c", type=CLICK_FILE_TYPE_EXISTS, required=True, help=CONFIG_HELP
)
@click.option("-fmriprep_dir", "-i", type=CLICK_DIR_TYPE_EXISTS, help=FMRIPREP_DIR_HELP)
@click.option(
    "-output_dir",
    "-o",
    type=CLICK_DIR_TYPE,
    default=None,
    required=False,
    help=OUTPUT_DIR_HELP,
)
@click.option(
    "-processing_stream",
    "-p",
    default=DEFAULT_PROCESSING_STREAM,
    required=False,
    help=PROCESSING_STREAM_HELP,
)
@click.option(
    "-log_dir",
    type=CLICK_DIR_TYPE_EXISTS,
    default=None,
    required=False,
    help=LOG_DIR_HELP,
)
@click.option(
    "-index_dir", type=CLICK_DIR_TYPE, default=None, required=False, help=INDEX_HELP
)
@click.option(
    "-refresh_index",
    "-r",
    is_flag=True,
    default=False,
    required=False,
    help=REFRESH_INDEX_HELP,
)
@click.option("-batch/-no-batch", is_flag=True, default=True, help=BATCH_HELP)
@click.option("-cache/-no-cache", is_flag=True, default=True)
@click.option("-submit", "-s", is_flag=True, default=False, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, default=False, help=DEBUG_HELP)
def postprocess_cli(
    subjects,
    config_file,
    fmriprep_dir,
    output_dir,
    processing_stream,
    batch,
    submit,
    log_dir,
    index_dir,
    refresh_index,
    debug,
    cache,
):
    """Additional processing for GLM or connectivity analysis.

    Providing no SUBJECTS will default to all subjects.
    List subject IDs in SUBJECTS to process specific subjects:

    > clpipe postprocess2 123 124 125 ...
    """
    from .postprocess import postprocess_subjects

    postprocess_subjects(
        subjects=subjects,
        config_file=config_file,
        fmriprep_dir=fmriprep_dir,
        output_dir=output_dir,
        processing_stream=processing_stream,
        batch=batch,
        submit=submit,
        log_dir=log_dir,
        pybids_db_path=index_dir,
        refresh_index=refresh_index,
        debug=debug,
        cache=cache,
    )


@click.command()
@click.argument("run_config_file", type=CLICK_FILE_TYPE)
@click.argument("image_file", type=CLICK_FILE_TYPE)
@click.argument("subject_out_dir", type=CLICK_DIR_TYPE)
@click.argument("subject_working_dir", type=CLICK_DIR_TYPE)
@click.argument("subject_log_dir", type=CLICK_DIR_TYPE)
@click.option("-debug", is_flag=True, default=False, help=DEBUG_HELP)
@click.option("--fmriprep_mask", is_flag=True, default=False, help="Add description here.")
@click.option("--no_mask", is_flag=True, default=False, help="Add description here.")
def postprocess_image_cli(
    run_config_file,
    image_file,
    subject_out_dir,
    subject_working_dir,
    subject_log_dir,
    debug,
    use_fmriprep_mask,
    no_mask,
):
    """Used to distribute postprocessing jobs for individual images.
    Not intended for direct use by user - this is called by the main postprocess
    command."""
    from .postprocess import postprocess_image

    postprocess_image(
        run_config_file,
        image_file,
        subject_out_dir,
        subject_working_dir,
        subject_log_dir,
        debug=debug,
        use_fmriprep_mask=use_fmriprep_mask,
        no_mask=no_mask,
    )


@click.command(GLM_PREPARE_COMMAND_NAME, no_args_is_help=True)
@click.argument("level")
@click.argument("model")
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help=CONFIG_HELP,
)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
def glm_prepare_cli(level, model, glm_config_file, debug):
    """Propagate an .fsf file template for L1 or L2 GLM analysis.

    LEVEL is the level of anlaysis, L1 or L2

    MODEL must be a a corresponding L1 or L2 model from your GLM configuration file.
    """
    from .glm_prepare import glm_prepare

    glm_prepare(glm_config_file=glm_config_file, level=level, model=model, debug=debug)


@click.command(L1_PREPARE_FSF_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help="Your GLM configuration file.",
)
@click.option(
    "-l1_name",
    default=None,
    required=True,
    help="Name for a given L1 model as defined in your GLM configuration file.",
)
@click.option(
    "-debug",
    "-d",
    is_flag=True,
    help="Flag to enable detailed error messages and traceback",
)
def glm_l1_preparefsf_cli(glm_config_file, l1_name, debug):
    """Propagate an .fsf file template for L1 GLM analysis.

    You must create a template .fsf file in FSL's FEAT GUI first.
    """
    from .glm_prepare import glm_prepare

    glm_prepare(glm_config_file=glm_config_file, level="L1", model=l1_name, debug=debug)


@click.command(L2_PREPARE_FSF_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "-glm_config_file",
    "-g",
    type=CLICK_FILE_TYPE_EXISTS,
    default=None,
    required=True,
    help="Your GLM configuration file.",
)
@click.option("-l2_name", default=None, required=True, help="Name for a given L2 model")
@click.option(
    "-debug",
    "-d",
    is_flag=True,
    help="Flag to enable detailed error messages and traceback",
)
def glm_l2_preparefsf_cli(glm_config_file, l2_name, debug):
    """Propagate an .fsf file template for L2 GLM analysis.

    You must create a group-level template .fsf file in FSL's FEAT GUI first.
    """
    from .glm_prepare import glm_prepare

    glm_prepare(glm_config_file=glm_config_file, level="L2", model=l2_name, debug=debug)


@click.command(APPLY_MUMFORD_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "-glm_config_file",
    "-g",
    type=CLICK_FILE_TYPE_EXISTS,
    default=None,
    required=False,
    help="Your GLM configuration file.",
)
@click.option(
    "-l1_feat_folders_path",
    type=CLICK_DIR_TYPE_EXISTS,
    default=None,
    required=False,
    help="Directory containing your L1 FEAT folders.",
)
@click.option(
    "-remove_reg_standard",
    is_flag=True,
    default=False,
    help="Remove reg_standard folders (generated by L2) in addition to reg.",
)
@click.option(
    "-debug",
    "-d",
    is_flag=True,
    default=False,
    help="Flag to enable detailed error messages and traceback",
)
def glm_apply_mumford_workaround_cli(
    glm_config_file, l1_feat_folders_path, remove_reg_standard, debug
):
    """
    Apply the Mumford registration workaround to L1 FEAT folders.

    Applied by default in glm-l2-preparefsf. This command is useful for applying
    the Mumford workaround to single-run subjects who skip L2, allowing you to still
    combine them with multiple-run subjects at L3.

    Must provide GLM config file OR a path to your L1 FEAT folders.
    """
    from .glm_prepare import glm_apply_mumford_workaround

    if not (glm_config_file or l1_feat_folders_path):
        click.echo(
            (
                "Error: At least one of either option '-glm_config_file' "
                "or '-l1_feat_folders_path' required."
            )
        )
    glm_apply_mumford_workaround(
        glm_config_file=glm_config_file,
        l1_feat_folders_path=l1_feat_folders_path,
        debug=debug,
        remove_reg_standard=remove_reg_standard,
    )


@click.command(GLM_LAUNCH_COMMAND_NAME, no_args_is_help=True)
@click.argument("level")
@click.argument("model")
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help=CONFIG_HELP,
)
@click.option("-test_one", is_flag=True, help=TEST_ONE_HELP)
@click.option("-submit", "-s", is_flag=True, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
def glm_launch_cli(level, model, glm_config_file, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 or L2 GLM analysis.

    LEVEL is the level of anlaysis, L1 or L2

    MODEL must be a a corresponding L1 or L2 model from your GLM configuration file.
    """
    from .glm_launch import glm_launch

    glm_launch(
        glm_config_file=glm_config_file,
        level=level,
        model=model,
        test_one=test_one,
        submit=submit,
        debug=debug,
    )


@click.command(no_args_is_help=True)
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help=CONFIG_HELP,
)
@click.option("-l1_name", required=True, help=L1_MODEL_HELP)
@click.option("-test_one", is_flag=True, help=TEST_ONE_HELP)
@click.option("-submit", "-s", is_flag=True, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
def glm_l1_launch_cli(glm_config_file, l1_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L1 GLM analysis."""
    from .glm_launch import glm_launch

    glm_launch(
        glm_config_file=glm_config_file,
        level="L1",
        model=l1_name,
        test_one=test_one,
        submit=submit,
        debug=debug,
    )


@click.command(no_args_is_help=True)
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help=CONFIG_HELP,
)
@click.option("-l2_name", required=True, help=L2_MODEL_HELP)
@click.option("-test_one", is_flag=True, help=TEST_ONE_HELP)
@click.option("-submit", "-s", is_flag=True, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, help=DEBUG_HELP)
def glm_l2_launch_cli(glm_config_file, l2_name, test_one, submit, debug):
    """Launch all prepared .fsf files for L2 GLM analysis."""
    from .glm_launch import glm_launch

    glm_launch(
        glm_config_file=glm_config_file,
        level="L2",
        model=l2_name,
        test_one=test_one,
        submit=submit,
        debug=debug,
    )


@click.command(ONSET_EXTRACT_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "-config_file",
    "-c",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
    help="Use a given configuration file.",
)
@click.option(
    "-glm_config_file",
    "-g",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    required=True,
    help="Use a given GLM configuration file.",
)
@click.option(
    "-debug",
    "-d",
    is_flag=True,
    default=False,
    help="Print detailed processing information and traceback for errors.",
)
def fsl_onset_extract_cli(config_file, glm_config_file, debug):
    """Convert onset files to FSL's 3 column format."""
    from .fsl_onset_extract import fsl_onset_extract

    fsl_onset_extract(
        config_file=config_file, glm_config_file=glm_config_file, debug=debug
    )


@click.command("extract", no_args_is_help=True)
@click.argument("subjects", nargs=-1, required=False, default=None)
@click.option(
    "-config_file",
    "-c",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories. This will extract all ROI sets specified in the configuration file.",
)
@click.option(
    "-target_dir",
    "-i",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Which postprocessed directory to process. If a configuration file is provided with a target directory, this argument is not necessary.",
)
@click.option(
    "-target_suffix",
    help="Which target suffix to process. If a configuration file is provided with a target suffix, this argument is not necessary.",
)
@click.option(
    "-output_dir",
    "-o",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put the ROI extracted data. If a configuration file is provided with a output directory, this argument is not necessary.",
)
@click.option(
    "-task", help="Which task to process. If none, then all tasks are processed."
)
@click.option(
    "-atlas_name",
    help="What atlas to use. Use the command 'clpipe roi atlases'  to see which are available. When specified for a custom atlas, this is what the output files will be named.",
)
@click.option(
    "-custom_atlas",
    help="A custom atlas image, in .nii or .nii.gz for label or maps, or a .txt tab delimited set of ROI coordinates if for a sphere atlas. Not needed if specified in config.",
)
@click.option(
    "-custom_label",
    help="A custom atlas label file. Not needed if specified in config.",
)
@click.option(
    "-custom_type",
    help="What type of atlas? (label, maps, or sphere). Not needed if specified in config.",
)
@click.option(
    "-sphere_radius",
    help="Sphere radius in mm. Only applies to sphere atlases.",
    default="5",
)
@click.option(
    "-overlap_ok", is_flag=True, default=False, help="Are overlapping ROIs allowed?"
)
@click.option(
    "-overwrite", is_flag=True, default=False, help="Overwrite existing ROI timeseries?"
)
@click.option(
    "-log_output_dir",
    type=click.Path(dir_okay=True, file_okay=False),
    help="Where to put HPC output files (such as SLURM output files). If not specified, defaults to <outputDir>/batchOutput.",
)
@click.option(
    "-submit",
    "-s",
    is_flag=True,
    default=False,
    help="Flag to submit commands to the HPC",
)
@click.option(
    "-single",
    is_flag=True,
    default=False,
    help="Flag to directly run command. Used internally.",
)
@click.option(
    "-debug",
    "-d",
    is_flag=True,
    help="Flag to enable detailed error messages and traceback",
)
def fmri_roi_extraction_cli(
    subjects,
    config_file,
    target_dir,
    target_suffix,
    output_dir,
    task,
    log_output_dir,
    atlas_name,
    custom_atlas,
    custom_label,
    custom_type,
    sphere_radius,
    submit,
    single,
    overlap_ok,
    debug,
    overwrite,
):
    """Extract ROIs with a given atlas."""
    from .roi_extractor import fmri_roi_extraction

    fmri_roi_extraction(
        subjects=subjects,
        config_file=config_file,
        target_dir=target_dir,
        target_suffix=target_suffix,
        output_dir=output_dir,
        task=task,
        log_output_dir=log_output_dir,
        atlas_name=atlas_name,
        custom_atlas=custom_atlas,
        custom_label=custom_label,
        custom_type=custom_type,
        sphere_radius=sphere_radius,
        submit=submit,
        single=single,
        overlap_ok=overlap_ok,
        debug=debug,
        overwrite=overwrite,
    )


@click.command("atlases")
def get_available_atlases_cli():
    """Display all available atlases."""
    from .roi_extractor import get_available_atlases

    get_available_atlases()


@click.command(OUTLIERS_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "--confounds_dir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to a directory containing subjects and confounds files.",
)
@click.option(
    "--confounds_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Path to confounds file",
)
@click.option(
    "--output_file",
    type=click.Path(dir_okay=False, file_okay=True),
    help="Path to save outlier count results.",
)
@click.option(
    "--confound_suffix",
    help="Confound file to search for, like 'confounds.tsv'",
    default="confounds.tsv",
)
def report_outliers_cli(confounds_dir, confounds_file, output_file, confound_suffix):
    """Generate a confound outliers report.

    Must provide one of either --confounds_dir or --confounds_file.
    """
    from .outliers_report import get_study_outliers, get_image_confounds

    if confounds_dir:
        get_study_outliers(confounds_dir, output_file, confound_suffix)
    else:
        get_image_confounds(confounds_file)


@click.command(STATUS_COMMAND_NAME, no_args_is_help=True)
@click.option(
    "-config_file", "-c", type=CLICK_FILE_TYPE_EXISTS, help=CONFIG_HELP, required=False
)
@click.option(
    "-cache_file", type=CLICK_FILE_TYPE_EXISTS, help=CACHE_FILE_HELP, required=False
)
def status_cli(config_file, cache_file):
    """Check the status of your project."""
    from .status import show_latest_by_step

    show_latest_by_step(config_file=config_file, cache_path=cache_file)


@click.command("flywheel_sync", no_args_is_help=True)
@click.option(
    "-config_file", "-c", type=CLICK_FILE_TYPE_EXISTS, help=CONFIG_HELP, required=False
)
@click.option(
    "-source_url",
    help='The path to your project in Flywheel. Starts with fw://. You can browse your available projects with "fw ls"',
)
@click.option("-dropoff_dir", type=CLICK_DIR_TYPE, help="Where to sync your files.")
@click.option("-submit", "-s", is_flag=True, default=False, help=SUBMIT_HELP)
@click.option("-debug", "-d", is_flag=True, default=False, help=DEBUG_HELP)
def flywheel_sync_cli(config_file, source_url, dropoff_dir, submit, debug):
    """
    Sync your DICOM data with Flywheel.

    You must first login to Flywheel with 'fw login' to sync. See the clpipe
    documentation on flywheel_sync for further help.
    """
    from .source import flywheel_sync

    flywheel_sync(
        config_file=config_file,
        source_url=source_url,
        dropoff_dir=dropoff_dir,
        submit=submit,
        debug=debug,
    )


@click.command("get_default", no_args_is_help=True)
@click.option(
    "-outputFile",
    "-o",
    default="clpipe_config_DEFAULT.json",
    help="Filepath for the outputted configuration file.",
)
def get_config_cli(output_file):
    """Generates a default configuration file for your project."""
    from .config.options import get_config_file

    get_config_file(output_file)


@click.command("get_default_config", no_args_is_help=True)
@click.option(
    "-outputFile",
    "-o",
    default="AGLMConfigFile.json",
    help="Filepath for the outputted configuration file.",
)
def get_glm_config_cli(output_file):
    """Generates a default GLM configuration file for your project."""
    from .grab_config_file import get_glm_config_file

    get_glm_config_file(output_file)


@click.command("update", no_args_is_help=True)
@click.option(
    "-config_file",
    "-c",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    required=True,
    help="Configuration file to update.",
)
@click.option(
    "-backup",
    is_flag=True,
    default=False,
    help="Automatically backup the previous configuration file",
)
def update_config_cli(config_file, backup):
    """Updates an existing configuration file with any new fields. Does not modify existing fields."""
    from .config.options import update_config_file

    if not backup:
        if click.confirm("Would you like to back up your config file before updating?"):
            backup = True
    update_config_file(config_file, backup)


@click.command("templateflow_setup")
@click.option(
    "-config_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help="Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.",
)
@click.option(
    "-debug", is_flag=True, help="Flag to enable detailed error messages and traceback"
)
def templateflow_setup_cli(config_file, debug):
    """Installs the templates for preprocessing listed in TemplateFlowTemplates.
    If you don't run this, fMRIPrep defaults to MNI152NLin2009cAsym. If you do,
    fMRIPrep will create a copy of each image in every space listed."""
    from .template_flow import templateflow_setup

    templateflow_setup(config_file, debug)


_add_commands()
