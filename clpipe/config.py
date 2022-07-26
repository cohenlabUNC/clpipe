import click

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