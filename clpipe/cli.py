import click
import sys
import pkg_resources

from .config import VERSION_HELP

CLICK_FILE_TYPE = click.Path(dir_okay=False, file_okay=True)
CLICK_FILE_TYPE_EXISTS = click.Path(
    exists=True, dir_okay=False, file_okay=True)
CLICK_DIR_TYPE = click.Path(dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_EXISTS = click.Path(exists=True, dir_okay=True, file_okay=False)
CLICK_DIR_TYPE_NOT_EXIST = click.Path(
    exists=False, dir_okay=True, file_okay=False)


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