import click
import sys
import pkg_resources

from .config import VERSION_HELP

from .project_setup import project_setup_cli
from .bids_validator import bids_validate_cli
from .dcm2bids_wrapper import convert2bids_cli
from .fmri_preprocess import fmriprep_process_cli
from .fmri_postprocess import fmri_postprocess_cli
from .fmri_postprocess2 import fmri_postprocess2_cli
from .glm_setup import glm_setup_cli
from .glm_l1 import glm_l1_preparefsf_cli
from .glm_l2 import glm_l2_preparefsf_cli, glm_apply_mumford_workaround_cli
from .glm_launch import glm_launch_cli
from .fsl_onset_extract import fsl_onset_extract_cli
from .outliers_report import report_outliers_cli
from .status import status_cli

DEFAULT_HELP_PRIORITY = 5


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


@click.group(cls=OrderedHelpGroup, invoke_without_command=True)
@click.pass_context
@click.option("-v", "--version", is_flag=True, default=False, 
        help=VERSION_HELP)
def cli(ctx, version):
    """Welcome to clpipe. Please choose a processing command."""

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
    """GLM Commands"""


@click.group("bids")
def bids_cli():
    """BIDS Commands"""


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

cli.add_command(bids_cli, help_priority=2)
cli.add_command(glm_cli)
