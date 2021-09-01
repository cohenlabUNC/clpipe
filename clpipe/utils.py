import click
import os
@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def test_func( config_file=None, subjects=None,submit=False, debug=False):
    ctx = click.get_current_context()
    ctx.info_name


def command_log(config):
    ctx = click.get_current_context()
    print(ctx.info_name)
    print(os.getlogin())

def parse_dir_subjects(directory_path: str, prefix='sub-'):
    """Generates a list of subjects based on the folder names of a given directory.

    Args:
        directory_path (str): [description]
        subjects (list, optional): [description]. Defaults to None.

    Returns:
        list: list of subject ids
    """
    sublist = [o.replace(prefix, '') for o in os.listdir(directory_path)
                if os.path.isdir(os.path.join(directory_path, o)) and prefix in o]

    return sublist

def build_arg_string(**kwargs):
    """Builds a string based on keyword arguments for debug display.
    """
    out = " Submitted Args:\n"
    for arg in kwargs:
        out += f"\t{arg}: {str(kwargs[arg])}\n"

    return(out)
