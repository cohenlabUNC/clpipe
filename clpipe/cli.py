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


@click.group(invoke_without_command=True)
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


cli.add_command(project_setup_cli)
cli.add_command(bids_validate_cli)
cli.add_command(convert2bids_cli)
cli.add_command(fmriprep_process_cli)
cli.add_command(fmri_postprocess_cli)
cli.add_command(fmri_postprocess2_cli)
cli.add_command(glm_setup_cli)